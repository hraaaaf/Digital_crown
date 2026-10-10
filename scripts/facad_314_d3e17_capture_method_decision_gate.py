#!/usr/bin/env python3
"""FAC-03 D3E17: source-only capture-method safety decision gate.

A passing review contract NEVER grants live Quick-demo capture, attribution,
shared storage isolation, clinical writes, a merge, or a deployment.
"""
import argparse
import json
from pathlib import Path

BASE_SHA = "eb9f2c2bd316ef85ff91e76759f293e869fec655"
METHODS = [
    ("KERNEL_FILE_ETW", "HOST_WIDE", "SYNTHETIC_ONLY",
     "UNRELATED_FILE_ACTIVITY_IN_RAW_TRACE"),
    ("ETW_PID_FILTER", "PROVIDER_SUPPORT_NOT_PROVEN",
     "NOT_PROVEN_FOR_KERNEL_FILE",
     "USER_MODE_FILTER_CANNOT_BE_ASSUMED_FOR_KERNEL_PROVIDER"),
    ("FILE_SYSTEM_SACL_4663", "MATCHING_SACL_WITH_SYSTEM_OR_USER_AUDIT",
     "NOT_AVAILABLE_ON_D3E14_RUNNER",
     "POLICY_REQUIRED_AND_SECURITY_LOG_SHARED"),
    ("FILESYSTEMWATCHER", "DIRECTORY_NOTIFICATION", "NO_PID",
     "BUFFER_LOSS_AND_NOTIFICATION_NOT_CAUSALITY"),
    ("SYSMON", "EVENT_FILTERED_SYSTEM_SERVICE_AND_DRIVER",
     "NOT_GENERAL_WRITE_COMPLETION",
     "FILTERED_LOG_NOT_PROVEN_CAPTURE_CONFINEMENT"),
    ("MINIFILTER_DRIVER", "KERNEL_IO_CALLBACK",
     "DESIGN_POSSIBLE_NOT_TESTED",
     "SIGNED_KERNEL_DRIVER_INSTALLATION_AND_GLOBAL_CALLBACK_RISK"),
    ("PROC_MONITOR", "KERNEL_MONITORING_SCOPE_UNPROVEN", "NOT_VALIDATED",
     "POTENTIAL_UNRELATED_ACTIVITY_IN_TRACE"),
    ("DEDICATED_GUEST_ETW", "GUEST_WIDE_ONLY", "SYNTHETIC_ONLY",
     "GUEST_PURPOSE_LIMITED_BUT_ETW_STILL_GUEST_WIDE"),
]
REQUIREMENTS = {
    "INDEPENDENT_EPHEMERAL_WINDOWS_GUEST",
    "NO_ACCOUNT_CONNECTORS_OR_PRODUCTION_SECRETS",
    "OFFICIAL_NONCLINICAL_DEMO_PROVENANCE_AND_CHECKS",
    "NO_PATIENT_LOAD_SAVE_OR_LICENSE_INSPECTION",
    "NO_SHARED_STORAGE_OR_HOST_CLINICAL_MOUNTS",
    "NO_GUEST_TO_HOST_EXPORT_OF_RAW_EVENTS",
    "ALL_SENSITIVE_TRACE_PROCESSING_GUEST_LOCAL",
    "AGGREGATE_ALLOWLIST_WITH_MINIMUM_DISCLOSURE",
    "TRACE_STOP_CLEANUP_GUEST_DESTRUCTION_VERIFIED",
    "PID_FILEOBJECT_TIMESTAMP_AND_LOSS_EVIDENCE_PREDEFINED",
    "TWO_REAL_INDEPENDENT_REVIEWS_ON_SAME_HEAD",
    "EXPLICIT_APPROVAL_FOR_LATER_EXPERIMENT",
}
CHECKS = {
    "isolated_guest_verified", "host_mounts_absent_verified",
    "production_secrets_absent_verified", "official_demo_provenance_verified",
    "source_filters_complete_verified", "raw_trace_non_export_verified",
    "cleanup_and_guest_destruction_verified",
    "fileobject_pid_correlation_verified_on_quickdemo",
    "event_loss_excluded", "independent_privacy_review_complete",
    "independent_evidence_review_complete",
    "explicit_experiment_authorization", "real_quickdemo_trace_performed",
    "real_ilexis_writer_proven", "shared_app_storage_isolation_verified",
    "clinical_edit_allowed", "merge_or_deployment_authorized",
}
TOP_FIELDS = {
    "schema", "phase", "baseline_sha", "baseline_ci_run_id",
    "baseline_windows_readonly_run_id", "recommendation", "reason",
    "methods", "guest_architecture_requirements", "checks",
    "converged", "live_capture_authorized", "verdict",
}
METHOD_FIELDS = {
    "id", "scope", "writer_pid_proof", "risk", "capture_authorized",
}


class UnsafeD3E17(ValueError):
    pass


def validate(doc):
    if not isinstance(doc, dict) or set(doc) != TOP_FIELDS:
        raise UnsafeD3E17("DOCUMENT_FIELDS_INVALID")
    fixed = {
        "schema": "facad314_d3e17_capture_method_decision_v1",
        "phase": "DESIGN_ONLY_NO_LIVE_CAPTURE",
        "baseline_sha": BASE_SHA,
        "baseline_ci_run_id": 38086797632,
        "baseline_windows_readonly_run_id": 38086797658,
        "recommendation": "ISOLATED_GUEST_SECURITY_REVIEW_ONLY",
        "reason": "NO_CURRENT_MECHANISM_PROVES_PER_FILE_WRITER_WITHOUT_NEW_UNREVIEWED_RISKS",
        "converged": False,
        "live_capture_authorized": False,
        "verdict": "D3E17_DESIGN_VALIDATION_ONLY_NO_SAFE_CAPTURE_CLEARED",
    }
    for field, expected in fixed.items():
        if type(doc[field]) is not type(expected) or doc[field] != expected:
            raise UnsafeD3E17("UNSUPPORTED_PROVENANCE_OR_APPROVAL")
    if not isinstance(doc["methods"], list) or len(doc["methods"]) != len(METHODS):
        raise UnsafeD3E17("METHOD_COUNT_INVALID")
    for candidate, expected in zip(doc["methods"], METHODS):
        if not isinstance(candidate, dict) or set(candidate) != METHOD_FIELDS:
            raise UnsafeD3E17("METHOD_FIELDS_INVALID")
        values = tuple(candidate[f] for f in
                       ("id", "scope", "writer_pid_proof", "risk"))
        if values != expected or candidate["capture_authorized"] is not False:
            raise UnsafeD3E17("FORGED_SAFE_METHOD_OR_UNSUPPORTED_CAPABILITY")
    req = doc["guest_architecture_requirements"]
    if (not isinstance(req, list) or len(req) != len(REQUIREMENTS)
            or any(type(x) is not str for x in req)
            or set(req) != REQUIREMENTS):
        raise UnsafeD3E17("GUEST_GATES_INCOMPLETE")
    flags = doc["checks"]
    if not isinstance(flags, dict) or set(flags) != CHECKS:
        raise UnsafeD3E17("UNVERIFIED_CHECK_MISSING")
    if any(flags[k] is not False for k in CHECKS):
        raise UnsafeD3E17("FORGED_REVIEW_OR_ISOLATION_CLEARANCE")
    return {
        "schema": "facad314_d3e17_checked_decision_v1",
        "baseline_sha": BASE_SHA,
        "alternatives_reviewed_count": len(METHODS),
        "recommended_next": "ISOLATED_GUEST_SECURITY_REVIEW_ONLY",
        "capture_ready": False,
        "live_capture_performed": False,
        "independent_privacy_review_complete": False,
        "independent_evidence_review_complete": False,
        "writer_proven": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "converged": False,
        "verdict": "SOURCE_REVIEW_COMPLETE_NATIVE_CAPTURE_BLOCKED",
    }


def verify_repo_design_only(repo):
    root = Path(repo)
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        raise UnsafeD3E17("REPO_WORKFLOWS_UNAVAILABLE")
    forbidden_script = root / "scripts" / "facad_314_d3e17_native_capture.ps1"
    if forbidden_script.exists():
        raise UnsafeD3E17("PREMATURE_NATIVE_CAPTURE_IMPLEMENTED")
    if not (workflows / "facad-314-d3-snapshot-validator.yml").is_file():
        raise UnsafeD3E17("SOURCE_ONLY_CI_MISSING")
    for workflow in workflows.glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        if "D3E17_REAL_CAPTURE_ENABLED" in text:
            raise UnsafeD3E17("NATIVE_CAPTURE_WIRED_WITHOUT_REVIEWS")
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract", required=True, type=Path)
    p.add_argument("--repo-root", type=Path)
    args = p.parse_args()
    try:
        if args.contract.stat().st_size > 25000:
            raise UnsafeD3E17("DOCUMENT_TOO_LARGE")
        plan = json.loads(args.contract.read_text(encoding="utf-8-sig"))
        checked = validate(plan)
        if args.repo_root is not None:
            verify_repo_design_only(args.repo_root)
        print("D3E17_METHODS_REVIEWED=8")
        print("D3E17_DECISION=" + checked["verdict"])
        print("D3E17_CAPTURE_AUTHORIZED=false")
        print("D3E17_INDEPENDENT_REVIEWS=NOT_COMPLETE")
        return 0
    except (UnsafeD3E17, ValueError, OSError, UnicodeError, TypeError, KeyError):
        print("D3E17_DECISION=BLOCKED_INVALID_OR_UNSAFE_REVIEW")
        return 2
    finally:
        print("FAC03_D3=OPEN_RED")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_EDIT_ALLOWED=false")


if __name__ == "__main__":
    raise SystemExit(main())
