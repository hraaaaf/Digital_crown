#!/usr/bin/env python3
"""FAC-03 D3E.11: validate file watcher and inherited SACL metadata aggregates.

FileSystemWatcher Changed is a metadata notification, not a content write or
process attribution. SACL file-readback counts do not prove complete 4663 audit
delivery, or permit clinical writes.
"""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d3e9_dependency", HERE / "facad_314_d3e9_arm_gate.py")
d3e9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d3e9)

FIELDS = {
    "schema", "source", "arm", "changed_size_file_count",
    "filesystem_watcher_started", "filesystem_watcher_error_reported",
    "filesystem_watcher_received_event_count",
    "changed_size_files_with_notification_count",
    "file_sacl_checked_changed_file_count", "file_sacl_unchecked_changed_file_count",
    "changed_files_with_current_sid_write_audit_count",
    "changed_files_with_inherited_current_sid_write_audit_count",
    "file_content_read", "file_identifiers_or_paths_or_sizes_exported",
    "notification_delivery_complete_proven", "writer_pid_proven",
    "change_caused_by_set_acl_proven", "shared_app_storage_isolation_verified",
    "clinical_edit_allowed", "verdict",
}


class InvalidD3E11(ValueError):
    pass


def validate(prior, observed, arm):
    try:
        d3e9.validate(prior, arm)
    except (ValueError, TypeError, KeyError) as exc:
        raise InvalidD3E11("D3E9_SOURCE_INVALID") from exc
    if not isinstance(observed, dict) or set(observed) != FIELDS:
        raise InvalidD3E11("FIELDS_INVALID")
    if (observed["schema"] != "facad314_d3e11_fsw_sacl_aggregate_v1"
            or observed["source"] != "NATIVE_CHANGE_NOTIFICATION_AND_FILE_AUDIT_RULE_METADATA_ONLY"
            or observed["arm"] != arm
            or observed["verdict"] != "FSW_SACL_COVERAGE_OBSERVATION_NOT_CAUSALITY"):
        raise InvalidD3E11("PROVENANCE_INVALID")
    nums = (
        "changed_size_file_count", "filesystem_watcher_received_event_count",
        "changed_size_files_with_notification_count", "file_sacl_checked_changed_file_count",
        "file_sacl_unchecked_changed_file_count",
        "changed_files_with_current_sid_write_audit_count",
        "changed_files_with_inherited_current_sid_write_audit_count",
    )
    for field in nums:
        if type(observed[field]) is not int or not 0 <= observed[field] <= 5000:
            raise InvalidD3E11("BAD_COUNT")
    n = observed["changed_size_file_count"]
    if n != prior["changed_size_count"]:
        raise InvalidD3E11("DRIFT_MISMATCH")
    if (observed["changed_size_files_with_notification_count"] > n
            or observed["changed_size_files_with_notification_count"]
            > observed["filesystem_watcher_received_event_count"]):
        raise InvalidD3E11("NOTIFICATION_FILE_COUNT_MISMATCH")
    if (observed["file_sacl_checked_changed_file_count"]
            + observed["file_sacl_unchecked_changed_file_count"] != n):
        raise InvalidD3E11("SACL_FILE_INSPECTION_INCOMPLETE_OR_INCONSISTENT")
    if (observed["changed_files_with_current_sid_write_audit_count"]
            > observed["file_sacl_checked_changed_file_count"]
            or observed["changed_files_with_inherited_current_sid_write_audit_count"]
            > observed["changed_files_with_current_sid_write_audit_count"]):
        raise InvalidD3E11("AUDIT_COVERAGE_COUNT_MISMATCH")
    if (observed["filesystem_watcher_started"] is not True
            or type(observed["filesystem_watcher_error_reported"]) is not bool):
        raise InvalidD3E11("WATCHER_SETUP_INVALID")
    if (observed["filesystem_watcher_error_reported"]
            and observed["changed_size_files_with_notification_count"] != 0):
        raise InvalidD3E11("WATCHER_ERROR_CANNOT_CLAIM_MATCHES")
    for field in (
        "file_content_read", "file_identifiers_or_paths_or_sizes_exported",
        "notification_delivery_complete_proven", "writer_pid_proven",
        "change_caused_by_set_acl_proven", "shared_app_storage_isolation_verified",
        "clinical_edit_allowed",
    ):
        if observed[field] is not False:
            raise InvalidD3E11("FORGED_WRITER_OR_ISOLATION_OR_PRIVACY_CLAIM")
    return {
        "schema": "facad314_d3e11_checked_aggregate_v1",
        "arm": arm,
        "changed_size_file_count": n,
        "watcher_received_event_count": observed["filesystem_watcher_received_event_count"],
        "watcher_reported_error": observed["filesystem_watcher_error_reported"],
        "changed_size_files_with_notification_count":
            observed["changed_size_files_with_notification_count"],
        "sacl_checked_changed_file_count": observed["file_sacl_checked_changed_file_count"],
        "sacl_unchecked_changed_file_count": observed["file_sacl_unchecked_changed_file_count"],
        "changed_files_with_current_sid_write_audit_count":
            observed["changed_files_with_current_sid_write_audit_count"],
        "changed_files_with_inherited_current_sid_write_audit_count":
            observed["changed_files_with_inherited_current_sid_write_audit_count"],
        "writer_pid_proven": False,
        "notification_delivery_complete_proven": False,
        "clinical_edit_allowed": False,
        "shared_app_storage_isolation_verified": False,
        "verdict": "NATIVE_WATCHER_AND_SACL_READBACK_NOT_CAUSALITY",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--d3e9-arm", type=Path, required=True)
    parser.add_argument("--d3e11-evidence", type=Path, required=True)
    parser.add_argument("--arm", choices=sorted(d3e9.ARMS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        prior = json.loads(args.d3e9_arm.read_text(encoding="utf-8-sig"))
        obs = json.loads(args.d3e11_evidence.read_text(encoding="utf-8-sig"))
        result = validate(prior, obs, args.arm)
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf8")
        print("D3E11_VERDICT=" + result["verdict"])
        print("D3E11_ARM=" + result["arm"])
        print("D3E11_FSW_MATCHED_SIZE_FILE_COUNT="
              + str(result["changed_size_files_with_notification_count"]))
        print("D3E11_SACL_CURRENT_SID_AUDITED_CHANGED_FILES="
              + str(result["changed_files_with_current_sid_write_audit_count"]))
        print("D3E11_SACL_INSPECTION_UNAVAILABLE_COUNT="
              + str(result["sacl_unchecked_changed_file_count"]))
        return 0
    except (ValueError, TypeError, UnicodeError, KeyError, OSError):
        print("D3E11_VERDICT=BLOCKED_INVALID_OR_INCOMPLETE_PROVENANCE_EVIDENCE")
        return 2
    finally:
        print("D3E11_WRITER_PID_PROVEN=false")
        print("D3E11_CLINICAL_EDIT_ALLOWED=false")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")


if __name__ == "__main__":
    raise SystemExit(main())
