#!/usr/bin/env python3
"""Fail closed when changed PR-triggered workflows omit latest-only concurrency.

Scope: changed workflow YAML files only, so the existing legacy workflow inventory
can be migrated incrementally without suppressing required checks.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def changed_workflows(base: str, head: str) -> list[Path]:
    output = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", base, head, "--", ".github/workflows"],
        text=True,
    )
    return [Path(path) for path in output.splitlines() if path.endswith((".yml", ".yaml"))]


def top_level_block(source: str, key: str) -> str:
    match = re.search(r"(?m)^" + re.escape(key) + r":\s*\n", source)
    if not match:
        return ""
    rest = source[match.end():]
    next_top_level = re.search(r"(?m)^[A-Za-z_][A-Za-z_0-9-]*:", rest)
    return rest[:next_top_level.start()] if next_top_level else rest


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    on_block = top_level_block(text, "on")
    if not re.search(r"(?m)^  pull_request\s*:", on_block):
        # Privileged pull_request_target and other event types are deliberately excluded.
        return []
    issues = []
    concurrency = top_level_block(text, "concurrency")
    if not concurrency:
        return [f"{path}: missing top-level concurrency for pull_request"]
    group = re.search(r"(?m)^  group:\s*(.+?)\s*$", concurrency)
    cancel = re.search(r"(?m)^  cancel-in-progress:\s*(.+?)\s*$", concurrency)
    if not group:
        issues.append(f"{path}: missing concurrency.group")
    elif path.stem not in group.group(1) and "github.workflow" not in group.group(1):
        issues.append(f"{path}: concurrency group must be unique per workflow")
    if not cancel:
        issues.append(f"{path}: missing concurrency.cancel-in-progress")
    elif cancel.group(1) not in ("true", "${{ github.event_name == 'pull_request' }}"):
        issues.append(f"{path}: cancel-in-progress must be true or PR-only expression")
    if re.search(r"(?m)^  (?:workflow_dispatch|push)\s*:", on_block):
        if not group or "github.run_id" not in group.group(1):
            issues.append(f"{path}: manual/push runs must use unique run_id fallback")
        if not cancel or cancel.group(1) != "${{ github.event_name == 'pull_request' }}":
            issues.append(f"{path}: manual/push runs must not be auto-cancelled")
    return issues


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: assert_pr_workflow_concurrency.py BASE_SHA HEAD_SHA", file=sys.stderr)
        return 2
    paths = changed_workflows(sys.argv[1], sys.argv[2])
    issues = [issue for path in paths for issue in check_file(path)]
    print(f"Checked {len(paths)} changed workflow files for PR concurrency policy")
    for issue in issues:
        print(f"ERROR: {issue}", file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
