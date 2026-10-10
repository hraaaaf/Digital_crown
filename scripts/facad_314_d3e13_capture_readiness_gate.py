#!/usr/bin/env python3
"""FAC-03 D3E13: pre-capture design contract, never grants Windows capture.

This is a source-only reviewer gate. It does not trace, access Facad, or
authorize shared-storage operations. Modifying a JSON manifest cannot turn a
dangerous native trial or a clinical action on.
"""
import argparse
import json
from pathlib import Path

BASE_SHA = "35c7798d2a8c7ee9d2c05e89ffabff6ea2e0468b"
BASE_RUN = 38079398064
EXPECTED = {
    "schema": "facad314_d3e13_capture_readiness_v1",
    "phase": "DESIGN_ONLY",
    "authorized_subject": "OFFICIAL_ROBERT_QUICK_DEMO_ONLY",
    "validated_synthetic_commit": BASE_SHA,
    "validated_synthetic_windows_run": BASE_RUN,
    "kernel_etw_provider": "Microsoft-Windows-Kernel-File",
    "kernel_etw_keyword_mask": "0x280",
    "planned_independent_arms": 4,
    "planned_max_capture_seconds": 8,
    "planned_max_etl_megabytes": 12,
    "planned_max_event_records": 20000,
    "kernel_etw_captures_unrelated_system_activity": True,
    "raw_traces_may_contain_sensitive_file_paths": True,
    "requirement_runner_is_ephemeral_and_nonclinical": True,
    "requirement_copy_official_demo_only": True,
    "requirement_aggregate_only_public_output": True,
    "requirement_private_in_memory_correlation_only": True,
    "requirement_terminate_trace_and_delete_raw_before_upload": True,
    "requirement_fail_closed_on_lost_events_or_cleanup_errors": True,
    "requirement_never_export_paths_pids_hashes_precise_timestamps": True,
    "requirement_no_patient_load_save_or_license_profile_inspection": True,
    "independent_privacy_review_complete": False,
    "independent_evidence_review_complete": False,
    "real_quickdemo_etw_trial_performed": False,
    "writer_causality_proven": False,
    "complete_event_delivery_proven": False,
    "shared_app_storage_isolation_verified": False,
    "clinical_edit_allowed": False,
    "live_capture_authorized": False,
    "actual_capture_script_implemented": False,
    "verdict": "D3E13_DESIGN_ONLY_CAPTURE_BLOCKED",
}
NATIVE_CAPTURE_MARKER = "D3E13_LIVE_QUICKDEMO_ETW_CAPTURE"
DESIGN_ONLY_OUTPUT = {
    "schema": "facad314_d3e13_design_checked_v1",
    "based_on_synthetic_sha": BASE_SHA,
    "based_on_synthetic_windows_run": BASE_RUN,
    "design_contract_checked": True,
    "independent_privacy_review_complete": False,
    "independent_evidence_review_complete": False,
    "real_quickdemo_etw_trial_performed": False,
    "writer_causality_proven": False,
    "complete_event_delivery_proven": False,
    "capture_authorized": False,
    "shared_app_storage_isolation_verified": False,
    "clinical_edit_allowed": False,
    "verdict": "DESIGN_REVIEW_READY_BUT_CAPTURE_BLOCKED",
}


class InvalidReadiness(ValueError):
    pass


def validate(plan):
    if not isinstance(plan, dict) or set(plan) != set(EXPECTED):
        raise InvalidReadiness("D3E13_CONTRACT_FIELDS_INVALID")
    for field, expected in EXPECTED.items():
        # bool is a subclass of int: prevent True being accepted as "1".
        if type(plan[field]) is not type(expected) or plan[field] != expected:
            raise InvalidReadiness("D3E13_CONTRACT_VALUE_INVALID")
    return dict(DESIGN_ONLY_OUTPUT)


def check_repository(repo_root):
    """Check D3E13 is truly design-only, not wired into a native capture job."""
    root = Path(repo_root)
    if not (root / ".github/workflows/facad-314-d3-snapshot-validator.yml").is_file():
        raise InvalidReadiness("D3E13_WORKFLOW_NOT_FOUND")
    workflows = list((root / ".github/workflows").glob("*.yml"))
    if not workflows:
        raise InvalidReadiness("D3E13_WORKFLOWS_NOT_FOUND")
    for path in workflows:
        text = path.read_text(encoding="utf-8", errors="strict")
        if NATIVE_CAPTURE_MARKER in text:
            raise InvalidReadiness("D3E13_NATIVE_CAPTURE_WIRED")
    if (root / "scripts/facad_314_d3e13_native_capture.ps1").exists():
        raise InvalidReadiness("D3E13_NATIVE_COLLECTOR_PREMATURE")
    # ETW synthetic workflow must explicitly affirm it never captures Ilexis.
    synthetic = root / ".github/workflows/facad-314-d3e12-etw-feasibility.yml"
    if not synthetic.is_file():
        raise InvalidReadiness("D3E12_SYNTHETIC_BASELINE_MISSING")
    if "D3E12_REAL_ILEXIS_TRACE_CAPTURED=false" not in synthetic.read_text(encoding="utf-8"):
        raise InvalidReadiness("D3E12_SYNTHETIC_SCOPE_NOT_GUARDED")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract", required=True, type=Path)
    ap.add_argument("--repo-root", type=Path, default=None)
    args = ap.parse_args()
    try:
        if args.contract.stat().st_size > 16000:
            raise InvalidReadiness("D3E13_INPUT_TOO_LARGE")
        p = json.loads(args.contract.read_text(encoding="utf-8-sig"))
        result = validate(p)
        if args.repo_root is not None:
            check_repository(args.repo_root)
        # No user-controlled keys or values printed: only safe allowlisted state.
        print("D3E13_DESIGN_CONTRACT=VALID")
        print("D3E13_NATIVE_WINDOWS_CAPTURE=NOT_PERFORMED")
        print("D3E13_CAPTURE_AUTHORIZED=false")
        print("D3E13_INDEPENDENT_REVIEWS=NOT_COMPLETED")
        print("D3E13_WRITER_CAUSALITY=NOT_PROVEN")
        print("D3E13_VERDICT=" + result["verdict"])
        return 0
    except (InvalidReadiness, TypeError, ValueError, OSError, UnicodeError):
        print("D3E13_DESIGN_CONTRACT=BLOCKED_INVALID_OR_UNSAFE")
        return 2
    finally:
        print("FAC03_D3=OPEN_RED")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_EDIT_ALLOWED=false")


if __name__ == "__main__":
    raise SystemExit(main())
