#!/usr/bin/env python3
"""D3E.10: validate only safe size/timestamp and 4663 counts from D3E.9 runners.

A 4663 access-use event is not proof of a completed file-content write or
process causality. Missing events are unknown, never proof of no writer.
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
    "schema", "source", "arm", "changed_size_count",
    "changed_size_and_last_write_timestamp_count",
    "changed_size_without_timestamp_change_count",
    "unchanged_size_changed_timestamp_count", "security_4663_query_attempted",
    "security_4663_records_available", "security_4663_query_outcome",
    "matching_write_data_or_append_access_event_count",
    "same_powershell_pid_matching_file_count", "other_pid_matching_file_count",
    "process_identity_exported", "file_identity_or_size_or_timestamp_exported",
    "file_content_read", "full_event_delivery_proven", "file_write_causality_proven",
    "clinical_edit_allowed", "shared_app_storage_isolation_verified", "verdict",
}


class InvalidD3E10(ValueError):
    pass


def validate(source, metadata, arm):
    try:
        d3e9.validate(source, arm)
    except (ValueError, TypeError, KeyError) as exc:
        raise InvalidD3E10("INVALID_PRIOR_D3E9_ARM") from exc
    if not isinstance(metadata, dict) or set(metadata) != FIELDS:
        raise InvalidD3E10("WRONG_D3E10_SCHEMA_FIELDS")
    if (metadata["schema"] != "facad314_d3e10_prelaunch_metadata_audit_v1"
            or metadata["source"] != "EPHEMERAL_D3E9_ARM_SIZE_TIMESTAMP_AND_4663_MATCH_AGGREGATE"
            or metadata["arm"] != arm
            or metadata["verdict"] != "METADATA_4663_BOUNDED_NOT_WRITER_CAUSALITY"):
        raise InvalidD3E10("INVALID_EVIDENCE_PROVENANCE")
    numbers = (
        "changed_size_count", "changed_size_and_last_write_timestamp_count",
        "changed_size_without_timestamp_change_count", "unchanged_size_changed_timestamp_count",
        "matching_write_data_or_append_access_event_count",
        "same_powershell_pid_matching_file_count", "other_pid_matching_file_count",
    )
    for key in numbers:
        value = metadata[key]
        if type(value) is not int or not 0 <= value <= 4000:
            raise InvalidD3E10("INVALID_COUNT")
    count = metadata["changed_size_count"]
    if (count != source["changed_size_count"]
            or metadata["changed_size_and_last_write_timestamp_count"]
            + metadata["changed_size_without_timestamp_change_count"] != count):
        raise InvalidD3E10("SIZE_TIMESTAMP_MISMATCH")
    if (metadata["unchanged_size_changed_timestamp_count"]
            > min(source["pre_intervention_file_count"], source["post_intervention_file_count"]) - count):
        raise InvalidD3E10("TIMESTAMP_WITHOUT_SIZE_COUNT_INVALID")
    for field in ("same_powershell_pid_matching_file_count", "other_pid_matching_file_count"):
        if metadata[field] > count:
            raise InvalidD3E10("AUDIT_KEY_COUNT_EXCEEDS_CHANGED_FILES")
        if metadata[field] > metadata["matching_write_data_or_append_access_event_count"]:
            raise InvalidD3E10("AUDIT_KEY_COUNT_EXCEEDS_EVENTS")
    if (metadata["security_4663_query_attempted"] is not True
            or type(metadata["security_4663_records_available"]) is not bool):
        raise InvalidD3E10("AUDIT_QUERY_NOT_ATTEMPTED")
    outcome = metadata["security_4663_query_outcome"]
    if outcome not in {"records_returned", "no_matching_events", "query_error", "invalid_event"}:
        raise InvalidD3E10("INVALID_AUDIT_QUERY_OUTCOME")
    if metadata["security_4663_records_available"] is not (outcome == "records_returned"):
        raise InvalidD3E10("AUDIT_QUERY_OUTCOME_FLAG_MISMATCH")
    if not metadata["security_4663_records_available"] and any(metadata[k] for k in (
        "matching_write_data_or_append_access_event_count",
        "same_powershell_pid_matching_file_count", "other_pid_matching_file_count",
    )):
        raise InvalidD3E10("FORGED_POSITIVE_AUDIT_MATCH_WITH_UNAVAILABLE_EVENTS")
    for field in (
        "process_identity_exported", "file_identity_or_size_or_timestamp_exported",
        "file_content_read", "full_event_delivery_proven", "file_write_causality_proven",
        "clinical_edit_allowed", "shared_app_storage_isolation_verified",
    ):
        if metadata[field] is not False:
            raise InvalidD3E10("FORGED_CONTENT_WRITER_OR_ISOLATION_CLAIM")
    return {
        "schema": "facad314_d3e10_checked_aggregate_v1",
        "arm": arm,
        "changed_size_count": count,
        "size_and_timestamp_changed_count": metadata["changed_size_and_last_write_timestamp_count"],
        "size_changed_timestamp_unchanged_count": metadata["changed_size_without_timestamp_change_count"],
        "same_size_timestamp_changed_count": metadata["unchanged_size_changed_timestamp_count"],
        "audit_event_records_available": metadata["security_4663_records_available"],
        "audit_query_outcome": outcome,
        "matching_4663_write_use_event_count": metadata["matching_write_data_or_append_access_event_count"],
        "own_process_4663_matched_file_count": metadata["same_powershell_pid_matching_file_count"],
        "other_process_4663_matched_file_count": metadata["other_pid_matching_file_count"],
        "writer_causality_proven": False,
        "file_content_read": False,
        "clinical_edit_allowed": False,
        "shared_app_storage_isolation_verified": False,
        "verdict": "BOUNDED_SIZE_AND_AUDIT_PROVENANCE_NOT_CAUSALITY",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--d3e9-arm", type=Path, required=True)
    parser.add_argument("--d3e10-evidence", type=Path, required=True)
    parser.add_argument("--arm", choices=sorted(d3e9.ARMS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        a = json.loads(args.d3e9_arm.read_text(encoding="utf-8-sig"))
        b = json.loads(args.d3e10_evidence.read_text(encoding="utf-8-sig"))
        result = validate(a, b, args.arm)
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf8")
        print("D3E10_PROVENANCE_VERDICT=" + result["verdict"])
        print("D3E10_ARM=" + result["arm"])
        print("D3E10_SIZE_TIMESTAMP_CHANGED_COUNT=" + str(result["size_and_timestamp_changed_count"]))
        print("D3E10_OTHER_PROCESS_MATCHED_FILE_COUNT=" + str(result["other_process_4663_matched_file_count"]))
        print("D3E10_AUDIT_EVENT_RECORDS_AVAILABLE=" + str(result["audit_event_records_available"]).lower())
        print("D3E10_AUDIT_QUERY_OUTCOME=" + result["audit_query_outcome"])
        code = 0
    except (ValueError, TypeError, KeyError, UnicodeError, OSError):
        print("D3E10_PROVENANCE_VERDICT=BLOCKED_INVALID_OR_INCOMPLETE_LOCAL_EVIDENCE")
        code = 2
    print("D3E10_CAUSALITY_PROVEN=false")
    print("D3E10_FILE_CONTENT_READ=false")
    print("CLINICAL_EDIT_ALLOWED=false")
    print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
