#!/usr/bin/env python3
"""Read-only RESTORE-03 INSTALLABLE readiness evidence on GitHub Actions.

No certificate issuance, model publication, installation, merge or deployment.
An existing external SRPose38 artifact is checked against the exact scientific
pin on the PR head and current master. A successful CODE_CERTIFIED job does
NOT by itself prove Sigstore verification or an INSTALLABLE release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = "hraaaaf/Digital_crown"
WORKFLOW = "cabinet-release-certification.yml"
MODEL_NAME = "srpose38-tta-1024.onnx"
PROVENANCE_RUN = 34281082926
PROVENANCE_ARTIFACT_ID = 10077697721


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def registry_pin(document: dict) -> dict:
    assets = document.get("assets")
    if not isinstance(assets, list):
        raise ValueError("SCIENTIFIC_REGISTRY_ASSETS_MISSING")
    matches = [x for x in assets if isinstance(x, dict) and x.get("id") == "cephalo_sota"]
    if len(matches) != 1:
        raise ValueError("EXPECTED_ONE_SRPOSE38_PIN")
    item = matches[0]
    if item.get("canonical_path") != "backend/ai_models/" + MODEL_NAME:
        raise ValueError("UNEXPECTED_CANONICAL_MODEL_PATH")
    if len(str(item.get("sha256", ""))) != 64 or not isinstance(item.get("size_bytes"), int):
        raise ValueError("SCIENTIFIC_PIN_NOT_COMPLETE")
    return item


def gh_api(path: str) -> dict:
    # Read-only GitHub CLI API; repo permission is explicitly actions:read.
    process = subprocess.run(
        ["gh", "api", f"repos/{REPO}/{path}"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=35,
    )
    if process.returncode != 0:
        raise RuntimeError("GITHUB_READ_ONLY_API_UNAVAILABLE")
    return json.loads(process.stdout)


def examine(code_runs: dict, master_sha: str) -> dict:
    runs = code_runs.get("workflow_runs")
    if not isinstance(runs, list):
        raise ValueError("MALFORMED_CODE_CERTIFICATION_RUNS")
    successes = [
        run for run in runs
        if run.get("head_sha") == master_sha
        and run.get("event") == "workflow_dispatch"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    ]
    for run in successes:
        run_id = int(run["id"])
        artifacts = gh_api(f"actions/runs/{run_id}/artifacts").get("artifacts", [])
        expected_name = f"code-certified-dc-cabinet-{master_sha[:12]}-run{run_id}"
        matching = [
            x for x in artifacts
            if x.get("name") == expected_name and x.get("expired") is False
        ]
        if len(matching) == 1:
            return {
                "status": "EXACT_MASTER_CODE_ARTIFACT_DISCOVERED_NOT_YET_HASH_OR_SIGSTORE_VERIFIED",
                "run_id": run_id,
                "artifact_id": matching[0]["id"],
                "artifact_name": expected_name,
                "artifact_digest": matching[0].get("digest"),
            }
    return {
        "status": "NO_NONEXPIRED_EXACT_MASTER_CODE_CERTIFIED_ARTIFACT",
        "matching_successful_code_runs": len(successes),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", required=True, type=Path)
    parser.add_argument("--code-runs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("GITHUB_ACTIONS_ONLY")
    actual_head = git("rev-parse", "HEAD")
    required_head = os.environ.get("RESTORE03_AUDIT_HEAD", "")
    if len(required_head) != 40 or actual_head != required_head:
        raise RuntimeError("PR_HEAD_MISMATCH")
    master_sha = git("rev-parse", "origin/master")
    expected_master = os.environ.get("RESTORE03_AUDIT_MASTER", "")
    if len(expected_master) != 40 or master_sha != expected_master:
        raise RuntimeError("MASTER_MOVED_DURING_AUDIT")

    checkout_reg = json.loads(Path("backend/scientific_assets.json").read_text(encoding="utf-8"))
    master_reg = json.loads(git("show", "origin/master:backend/scientific_assets.json"))
    checkout_pin, master_pin = registry_pin(checkout_reg), registry_pin(master_reg)
    model = args.download.resolve() / MODEL_NAME
    if not model.is_file() or model.is_symlink() or model.stat().st_size == 0:
        raise RuntimeError("SRPOSE38_MODEL_ARTIFACT_MISSING_OR_UNSAFE")
    measured_size = model.stat().st_size
    measured_sha = digest(model)
    source_pin_ok = (
        checkout_pin["sha256"].lower() == measured_sha
        and checkout_pin["size_bytes"] == measured_size
    )
    master_pin_ok = (
        master_pin["sha256"].lower() == measured_sha
        and master_pin["size_bytes"] == measured_size
    )
    if not source_pin_ok or not master_pin_ok:
        raise RuntimeError("SRPOSE38_SHA_SIZE_PIN_MISMATCH")
    code = examine(json.loads(args.code_runs.read_text(encoding="utf-8")), master_sha)

    report = {
        "marker": "RESTORE03_INSTALLABLE_READINESS_READ_ONLY_NO_INSTALLABLE_OR_CLINICAL_GO",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "pr_head": actual_head,
        "current_master_sha": master_sha,
        "pr_is_current_master": actual_head == master_sha,
        "srpose38_external_artifact": {
            "source_run": PROVENANCE_RUN,
            "artifact_id": PROVENANCE_ARTIFACT_ID,
            "sha256": measured_sha,
            "bytes": measured_size,
            "pr_scientific_pin": "MATCH",
            "master_scientific_pin": "MATCH",
        },
        "master_code_certification": code,
        "github_sigstore_attestation_verification": "NOT_RUN",
        "runtime_assets_certification": "NOT_RUN",
        "installable_release_composition": "NOT_RUN",
        "pyinstaller_build": "NOT_RUN",
        "cabinet_installation": "NOT_RUN",
        "clinical_go": False,
        "installable_ready": False,
        "blockers": [
            "CURRENT_PR_NOT_MERGED_TO_MASTER" if actual_head != master_sha else None,
            "EXACT_MASTER_CODE_ARTIFACT_MISSING"
            if code["status"] == "NO_NONEXPIRED_EXACT_MASTER_CODE_CERTIFIED_ARTIFACT"
            else "CODE_ARTIFACT_NOT_SIGSTORE_VERIFIED",
            "RUNTIME_ASSET_BUNDLE_NOT_YET_CERTIFIED_OR_COMPOSED",
        ],
    }
    report["blockers"] = [x for x in report["blockers"] if x]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SRPOSE38_PINNED_EXTERNAL_ASSET_BYTES_VERIFIED_FOR_PR_AND_MASTER")
    print("RESTORE03_INSTALLABLE_READINESS_AUDITED_BLOCKED_NO_GO")
    print("CODE_CERT_STATUS=" + code["status"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("RESTORE03_INSTALLABLE_READINESS_FAIL:" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2) from None
