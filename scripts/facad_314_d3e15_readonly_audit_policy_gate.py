#!/usr/bin/env python3
"""D3E.15 fail-closed validator of read-only per-user File System audit settings.

Policy inclusion is NOT confined to a file. Even an included Success setting
cannot authorize object capture, an Ilexis test, or clinical editing.
"""
import argparse
import json
from pathlib import Path

FIELDS = {
    "schema", "source", "file_system_audit_subcategory",
    "auditpol_system_query_succeeded", "auditpol_user_query_succeeded",
    "system_success_audit_status", "per_user_inclusion_success_audit_status",
    "runner_admin_membership_check_succeeded", "runner_is_local_administrator",
    "global_policy_modified", "per_user_policy_modified",
    "security_events_queried", "global_kernel_etw_capture_used",
    "synthetic_or_clinical_files_touched", "raw_auditpol_output_exported",
    "sid_or_username_exported", "private_paths_or_process_ids_exported",
    "per_user_audit_is_exclusive_to_one_file_proven", "real_ilexis_writer_proven",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed", "verdict",
}
POLICY = {"success_configured", "success_not_configured", "undetermined",
          "parse_error", "unavailable"}
BOOLEANS = {
    "auditpol_system_query_succeeded", "auditpol_user_query_succeeded",
    "runner_admin_membership_check_succeeded", "runner_is_local_administrator",
    "global_policy_modified", "per_user_policy_modified",
    "security_events_queried", "global_kernel_etw_capture_used",
    "synthetic_or_clinical_files_touched", "raw_auditpol_output_exported",
    "sid_or_username_exported", "private_paths_or_process_ids_exported",
    "per_user_audit_is_exclusive_to_one_file_proven", "real_ilexis_writer_proven",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed",
}
MUST_BE_FALSE = {
    "global_policy_modified", "per_user_policy_modified",
    "security_events_queried", "global_kernel_etw_capture_used",
    "synthetic_or_clinical_files_touched", "raw_auditpol_output_exported",
    "sid_or_username_exported", "private_paths_or_process_ids_exported",
    "per_user_audit_is_exclusive_to_one_file_proven", "real_ilexis_writer_proven",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed",
}


class InvalidD3E15(ValueError):
    pass


def validate(x):
    if not isinstance(x, dict) or set(x) != FIELDS:
        raise InvalidD3E15("FIELDS_INVALID")
    if (x["schema"] != "facad314_d3e15_readonly_per_user_policy_v1"
            or x["source"] != "CURRENT_EPHEMERAL_WINDOWS_RUNNER_READ_ONLY"
            or x["file_system_audit_subcategory"] != "FILE_SYSTEM"
            or x["verdict"] !=
            "READ_ONLY_PER_USER_AUDIT_POLICY_OBSERVATION_NOT_CAPTURE_AUTHORIZATION"):
        raise InvalidD3E15("PROVENANCE_INVALID")
    for k in BOOLEANS:
        if type(x[k]) is not bool:
            raise InvalidD3E15("BOOL_INVALID")
    for k in MUST_BE_FALSE:
        if x[k] is not False:
            raise InvalidD3E15("FORGED_MUTATION_SCOPE_OR_CLINICAL_CLAIM")
    if x["runner_admin_membership_check_succeeded"] is not True:
        raise InvalidD3E15("PRINCIPAL_CHECK_UNAVAILABLE")
    for query, status in (
        ("auditpol_system_query_succeeded", "system_success_audit_status"),
        ("auditpol_user_query_succeeded", "per_user_inclusion_success_audit_status"),
    ):
        if x[status] not in POLICY:
            raise InvalidD3E15("POLICY_STATUS_UNKNOWN")
        if not x[query] and x[status] != "unavailable":
            raise InvalidD3E15("POLICY_STATUS_WITHOUT_QUERY")
        if x[query] and x[status] == "unavailable":
            raise InvalidD3E15("POLICY_STATUS_MISSING_AFTER_QUERY")
    # Always produce a deliberately non-authorizing conclusion.
    return {
        "schema": "facad314_d3e15_checked_policy_v1",
        "system_success_audit_status": x["system_success_audit_status"],
        "per_user_inclusion_success_audit_status":
            x["per_user_inclusion_success_audit_status"],
        "auditpol_system_query_succeeded": x["auditpol_system_query_succeeded"],
        "auditpol_user_query_succeeded": x["auditpol_user_query_succeeded"],
        "runner_is_local_administrator": x["runner_is_local_administrator"],
        "global_policy_modified": False,
        "per_user_policy_modified": False,
        "security_events_queried": False,
        "capture_authorized": False,
        "user_policy_is_file_scoped_proven": False,
        "real_ilexis_writer_proven": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": "READONLY_POLICY_INFO_NOT_A_CAPTURE_OR_ISOLATION_PROOF",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 16000:
            raise InvalidD3E15("INPUT_TOO_LARGE")
        result = validate(json.loads(args.input.read_text(encoding="utf-8-sig")))
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
        print("D3E15_VERDICT=" + result["verdict"])
        print("D3E15_SYSTEM_POLICY=" + result["system_success_audit_status"])
        print("D3E15_PER_USER_POLICY=" + result["per_user_inclusion_success_audit_status"])
        print("D3E15_CAPTURE_AUTHORIZED=false")
        return 0
    except (ValueError, TypeError, KeyError, OSError, UnicodeError):
        print("D3E15_VERDICT=BLOCKED_INVALID_OR_PRIVATE_EVIDENCE")
        return 2
    finally:
        print("D3E15_GLOBAL_POLICY_MODIFIED=false")
        print("D3E15_PER_USER_POLICY_MODIFIED=false")
        print("D3E15_REAL_ILEXIS_CAPTURE_PERFORMED=false")
        print("FAC03_D3=OPEN_RED")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_EDIT_ALLOWED=false")


if __name__ == "__main__":
    raise SystemExit(main())
