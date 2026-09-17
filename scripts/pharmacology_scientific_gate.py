#!/usr/bin/env python3
"""Deterministic pharmacology safety gate.

This gate checks repository invariants that are objectively machine-verifiable.
It is deliberately NOT a scientific or clinical approval and never replaces the
independent scientific-reviewer or clinician gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "backend/data/medications_ma_ammps_rcp_manifest_2026.json"
REVIEWER = ROOT / ".claude/agents/scientific-reviewer.md"
REVIEW_SKILL = ROOT / ".claude/skills/review-scientific-pull-request/SKILL.md"
SOURCE_SKILL = ROOT / ".claude/skills/scientific-source-research/SKILL.md"
ALLOWED_STATUSES = {"PENDING_DOWNLOAD", "SNAPSHOT_VERIFIED", "UNAVAILABLE_VERIFIED"}
OFFICIAL_HOSTS = {"ammps.gov.ma", "www.ammps.gov.ma"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UNAVAILABLE_EVIDENCE = "OFFICIAL_SOURCE_EXPLICIT_NO_RCP"


def _official_ammps_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and parsed.hostname in OFFICIAL_HOSTS


def _strict_date(value: Any) -> bool:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value.strip()):
        return False
    try:
        date.fromisoformat(value.strip())
    except ValueError:
        return False
    return True


def _safe_pdf_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = PurePosixPath(value.strip())
    return bool(not path.is_absolute() and ".." not in path.parts and len(path.parts) > 3 and path.parts[:3] == ("backend", "data", "rcp") and path.suffix.lower() == ".pdf")


def _require_file(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing required governance file: {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def _validate_reviewer_contract(errors: list[str]) -> dict[str, bool]:
    reviewer = _require_file(REVIEWER, errors)
    review_skill = _require_file(REVIEW_SKILL, errors)
    source_skill = _require_file(SOURCE_SKILL, errors)
    checks = {
        "reviewer_named": "name: scientific-reviewer" in reviewer,
        "reviewer_read_only": "read-only" in reviewer.lower(),
        "reviewer_independent": "independent" in reviewer.lower(),
        "reviewer_plan_mode": "permissionMode: plan" in reviewer,
        "review_skill_attached": "review-scientific-pull-request" in reviewer,
        "source_skill_attached": "scientific-source-research" in reviewer,
        "review_decision_contract": all(token in review_skill for token in ("approve", "approve_with_reservations", "request_changes", "blocked")),
        "source_research_non_activation": "Research never activates a rule" in source_skill,
    }
    for name, ok in checks.items():
        if not ok:
            errors.append(f"scientific reviewer governance contract failed: {name}")
    return checks


def _validate_manifest(errors: list[str]) -> tuple[int, dict[str, int]]:
    if not MANIFEST.is_file():
        errors.append("missing AMMPS RCP manifest")
        return 0, {}
    try:
        raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid AMMPS RCP manifest JSON: {exc}")
        return 0, {}
    entries = raw.get("entries") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        errors.append("AMMPS RCP manifest must contain an entries list")
        return 0, {}
    counts = {status: 0 for status in sorted(ALLOWED_STATUSES)}
    seen_ids: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"entry[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        regulatory_id = entry.get("regulatory_presentation_id")
        if not isinstance(regulatory_id, str) or not regulatory_id.strip():
            errors.append(f"{prefix}: missing regulatory_presentation_id")
        elif regulatory_id in seen_ids:
            errors.append(f"{prefix}: duplicate regulatory_presentation_id {regulatory_id}")
        else:
            seen_ids.add(regulatory_id)
        status = entry.get("capture_status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{prefix}: invalid capture_status {status!r}")
            continue
        counts[status] += 1
        if not _official_ammps_url(entry.get("source_page_url")):
            errors.append(f"{prefix}: source_page_url must be official AMMPS HTTPS")
        extracted = entry.get("extracted_clinical_fields")
        if not isinstance(extracted, dict):
            errors.append(f"{prefix}: extracted_clinical_fields must be an object")
            extracted = None
        if status == "PENDING_DOWNLOAD":
            if any(entry.get(field) is not None for field in ("rcp_sha256", "rcp_checked_at", "local_artifact_path", "unavailability_evidence")):
                errors.append(f"{prefix}: PENDING_DOWNLOAD contains verification metadata")
            if extracted != {}:
                errors.append(f"{prefix}: PENDING_DOWNLOAD must not contain clinical extraction")
            rcp_url = entry.get("rcp_url")
            if rcp_url is not None and not _official_ammps_url(rcp_url):
                errors.append(f"{prefix}: pending rcp_url is not official AMMPS HTTPS")
            continue
        if status == "UNAVAILABLE_VERIFIED":
            if not _strict_date(entry.get("rcp_checked_at")):
                errors.append(f"{prefix}: UNAVAILABLE_VERIFIED requires strict checked date")
            if entry.get("unavailability_evidence") != UNAVAILABLE_EVIDENCE:
                errors.append(f"{prefix}: UNAVAILABLE_VERIFIED lacks explicit official absence proof")
            if any(entry.get(field) is not None for field in ("rcp_url", "rcp_sha256", "local_artifact_path")):
                errors.append(f"{prefix}: UNAVAILABLE_VERIFIED must not carry an RCP artifact")
            if extracted != {}:
                errors.append(f"{prefix}: UNAVAILABLE_VERIFIED must not contain clinical extraction")
            continue
        rcp_url = entry.get("rcp_url")
        sha256 = entry.get("rcp_sha256")
        local_path = entry.get("local_artifact_path")
        if not _official_ammps_url(rcp_url):
            errors.append(f"{prefix}: SNAPSHOT_VERIFIED requires official AMMPS RCP URL")
        if not isinstance(sha256, str) or not SHA256_RE.fullmatch(sha256):
            errors.append(f"{prefix}: SNAPSHOT_VERIFIED requires lowercase SHA-256")
        if not _strict_date(entry.get("rcp_checked_at")):
            errors.append(f"{prefix}: SNAPSHOT_VERIFIED requires strict checked date")
        if not _safe_pdf_path(local_path):
            errors.append(f"{prefix}: SNAPSHOT_VERIFIED requires safe backend/data/rcp/*.pdf path")
            continue
        artifact = ROOT.joinpath(*PurePosixPath(str(local_path)).parts).resolve()
        try:
            artifact.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{prefix}: artifact escapes repository root")
            continue
        if not artifact.is_file():
            errors.append(f"{prefix}: SNAPSHOT_VERIFIED artifact is missing")
            continue
        payload = artifact.read_bytes()
        if not payload.startswith(b"%PDF-"):
            errors.append(f"{prefix}: SNAPSHOT_VERIFIED artifact is not a PDF")
        if isinstance(sha256, str) and SHA256_RE.fullmatch(sha256) and hashlib.sha256(payload).hexdigest() != sha256:
            errors.append(f"{prefix}: SNAPSHOT_VERIFIED artifact hash mismatch")
    return len(entries), counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="audit/out/pharmacology-scientific-gate")
    args = parser.parse_args()
    errors: list[str] = []
    warnings = ["This deterministic gate does not constitute scientific or clinical approval.", "Independent scientific-reviewer and clinician gates remain applicable where required."]
    reviewer_checks = _validate_reviewer_contract(errors)
    entry_count, status_counts = _validate_manifest(errors)
    result = {"schema_version": "pharmacology-deterministic-scientific-safety.1", "gate_type": "DETERMINISTIC_SAFETY_NOT_SCIENTIFIC_APPROVAL", "candidate_head": os.environ.get("PRODUCT_HEAD") or os.environ.get("GITHUB_SHA"), "status": "PASS" if not errors else "FAIL", "independent_scientific_review_required": True, "clinical_activation_authorized": False, "reviewer_contract": reviewer_checks, "manifest_entry_count": entry_count, "manifest_status_counts": status_counts, "errors": errors, "warnings": warnings}
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = ["# Pharmacology deterministic scientific safety gate", "", f"- status: **{result['status']}**", f"- candidate HEAD: `{result['candidate_head']}`", f"- manifest entries: {entry_count}", f"- status counts: `{json.dumps(status_counts, sort_keys=True)}`", "- scientific approval: **NO**", "- independent scientific review still required: **YES**", "", "## Errors"]
    summary.extend([f"- {item}" for item in errors] or ["- none"])
    summary.extend(["", "## Boundaries", *[f"- {item}" for item in warnings]])
    (out / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 1
    print("PASS: deterministic pharmacology safety invariants verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
