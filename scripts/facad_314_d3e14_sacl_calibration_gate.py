#!/usr/bin/env python3
"""FAC-03 D3E.14 validate only object-scoped synthetic SACL calibration.

A 4663 write-access event and its PID do NOT prove a completed write, a
specific Ilexis writer, any causal relation to Set-Acl, or clinical isolation.
"""
import argparse
import json
from pathlib import Path

FIELDS = {
    "schema", "source", "audit_policy_queried",
    "audit_file_system_success_policy",
    "global_audit_policy_modified", "object_sacl_applied",
    "object_sacl_readback_confirmed", "synthetic_child_write_verified",
    "security_4663_query_outcome", "security_4663_query_error",
    "security_records_read_count",
    "matching_synthetic_file_write_access_event_count",
    "matching_synthetic_child_pid_access_event_count",
    "matching_unknown_or_other_pid_access_event_count",
    "synthetic_sacl_restored", "private_synthetic_files_deleted",
    "used_global_kernel_etw_capture", "raw_security_event_exported",
    "private_filename_or_pid_exported", "clinical_or_ilexis_file_touched",
    "write_completion_proven", "real_ilexis_writer_proven",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed", "verdict",
}
OUTCOMES = {"not_attempted", "records_returned", "no_matching_events",
            "query_error", "invalid_event", "probe_error"}
FORBIDDEN = (
    "global_audit_policy_modified", "used_global_kernel_etw_capture",
    "raw_security_event_exported", "private_filename_or_pid_exported",
    "clinical_or_ilexis_file_touched", "write_completion_proven",
    "real_ilexis_writer_proven", "shared_app_storage_isolation_verified",
    "clinical_edit_allowed",
)
BOOLEANS = (
    "audit_policy_queried", "global_audit_policy_modified",
    "object_sacl_applied", "object_sacl_readback_confirmed",
    "synthetic_child_write_verified", "security_4663_query_error",
    "synthetic_sacl_restored", "private_synthetic_files_deleted",
    "used_global_kernel_etw_capture", "raw_security_event_exported",
    "private_filename_or_pid_exported", "clinical_or_ilexis_file_touched",
    "write_completion_proven", "real_ilexis_writer_proven",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed",
)
COUNTS = (
    "security_records_read_count",
    "matching_synthetic_file_write_access_event_count",
    "matching_synthetic_child_pid_access_event_count",
    "matching_unknown_or_other_pid_access_event_count",
)


class InvalidD3E14(ValueError):
    pass


def validate(x):
    if not isinstance(x, dict) or set(x) != FIELDS:
        raise InvalidD3E14("UNKNOWN_FIELDS_OR_MISSING_EVIDENCE")
    if (x["schema"] != "facad314_d3e14_synthetic_object_sacl_v1"
            or x["source"] != "SYNTHETIC_FILE_OBJECT_AUDIT_ONLY"
            or x["verdict"] !=
            "SYNTHETIC_OBJECT_SCOPED_AUDIT_CALIBRATION_NOT_CLINICAL_CAUSALITY"
            or x["security_4663_query_outcome"] not in OUTCOMES):
        raise InvalidD3E14("INVALID_PROVENANCE")
    for f in BOOLEANS:
        if type(x[f]) is not bool:
            raise InvalidD3E14("INVALID_BOOL")
    for f in FORBIDDEN:
        if x[f] is not False:
            raise InvalidD3E14("FORGED_PRIVACY_CAUSALITY_OR_CLINICAL_CLAIM")
    if x["audit_file_system_success_policy"] not in {
            "success_configured", "success_not_configured", "undetermined"}:
        raise InvalidD3E14("AUDIT_SUCCESS_POLICY_ENUM_INVALID")
    if (not x["audit_policy_queried"]
            and x["audit_file_system_success_policy"] != "undetermined"):
        raise InvalidD3E14("AUDIT_POLICY_CLAIM_WITHOUT_QUERY")
    for f in COUNTS:
        if type(x[f]) is not int or not 0 <= x[f] <= 10000:
            raise InvalidD3E14("INVALID_COUNT")
    if not x["private_synthetic_files_deleted"]:
        raise InvalidD3E14("SYNTHETIC_FILES_NOT_CLEANED")
    if x["object_sacl_applied"] is not x["synthetic_sacl_restored"]:
        raise InvalidD3E14("SACL_RESTORE_INCOMPLETE")
    if x["object_sacl_readback_confirmed"] and not x["object_sacl_applied"]:
        raise InvalidD3E14("SACL_READBACK_WITHOUT_APPLY")
    if x["synthetic_child_write_verified"] and not x["object_sacl_readback_confirmed"]:
        raise InvalidD3E14("SYNTHETIC_WRITE_WITHOUT_EFFECTIVE_SACL")
    outcome = x["security_4663_query_outcome"]
    if x["security_4663_query_error"] != (outcome in {"query_error", "invalid_event"}):
        raise InvalidD3E14("QUERY_STATUS_AMBIGUOUS")
    records = x["security_records_read_count"]
    found = x["matching_synthetic_file_write_access_event_count"]
    own = x["matching_synthetic_child_pid_access_event_count"]
    other = x["matching_unknown_or_other_pid_access_event_count"]
    if found > records or own + other != found:
        raise InvalidD3E14("EVENT_COUNT_INCONSISTENCY")
    if outcome != "records_returned" and (records or found or own or other):
        raise InvalidD3E14("EVENT_COUNT_WHEN_UNAVAILABLE")
    if outcome == "records_returned" and records <= 0:
        raise InvalidD3E14("RECORDS_RETURNED_EMPTY")
    if found and not (x["object_sacl_readback_confirmed"]
                      and x["synthetic_child_write_verified"]):
        raise InvalidD3E14("MATCHED_EVENT_WITHOUT_SYNTHETIC_CONTROL")
    synthetic_link = bool(
        x["object_sacl_readback_confirmed"]
        and x["synthetic_child_write_verified"]
        and own > 0 and outcome == "records_returned"
        and not x["security_4663_query_error"]
    )
    return {
        "schema": "facad314_d3e14_synthetic_audit_checked_v1",
        "audit_policy_queried": x["audit_policy_queried"],
        "audit_file_system_success_policy": x["audit_file_system_success_policy"],
        "object_sacl_readback_confirmed": x["object_sacl_readback_confirmed"],
        "synthetic_child_write_verified": x["synthetic_child_write_verified"],
        "security_4663_query_outcome": outcome,
        "matching_synthetic_file_write_access_event_count": found,
        "matching_synthetic_child_pid_access_event_count": own,
        "object_scoped_synthetic_4663_pid_link_observed": synthetic_link,
        "global_audit_policy_modified": False,
        "used_global_kernel_etw_capture": False,
        "raw_security_event_exported": False,
        "real_ilexis_writer_proven": False,
        "write_completion_proven": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "private_synthetic_files_deleted": True,
        "verdict": (
            "SYNTHETIC_OBJECT_SACL_4663_PID_LINK_NOT_ILEXIS_CAUSALITY"
            if synthetic_link else "OBJECT_SCOPED_AUDIT_PID_FEASIBILITY_UNVERIFIED"
        ),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.input.stat().st_size > 16000:
            raise InvalidD3E14("INPUT_TOO_LARGE")
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = validate(data)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
        print("D3E14_VERDICT=" + result["verdict"])
        print("D3E14_4663_QUERY_OUTCOME=" + result["security_4663_query_outcome"])
        print("D3E14_FILE_SYSTEM_SUCCESS_POLICY=" + result["audit_file_system_success_policy"])
        print("D3E14_SYNTHETIC_CHILD_PID_LINK_OBSERVED="
              + str(result["object_scoped_synthetic_4663_pid_link_observed"]).lower())
        return 0
    except (InvalidD3E14, UnicodeError, OSError, TypeError, ValueError, KeyError):
        print("D3E14_VERDICT=BLOCKED_INVALID_OR_PRIVATE_PROVENANCE")
        return 2
    finally:
        print("D3E14_REAL_ILEXIS_WRITER_PROVEN=false")
        print("D3E14_GLOBAL_AUDIT_POLICY_MODIFIED=false")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_EDIT_ALLOWED=false")


if __name__ == "__main__":
    raise SystemExit(main())
