#!/usr/bin/env python3
"""D3E12: only synthetic ETW feasibility, NEVER Ilexis writer clearance."""
import argparse
import json
from pathlib import Path

FIELDS = {
    "schema", "source", "provider", "provider_discovered", "trace_started",
    "trace_stopped", "synthetic_write_verified", "etl_query_status",
    "etl_decoder", "etl_file_present", "etl_file_nonempty",
    "direct_etl_read_status", "tracerpt_attempted", "tracerpt_exit_zero",
    "tracerpt_output_file_present", "tracerpt_output_file_nonempty",
    "tracerpt_evtx_read_status",
    "etl_events_parsed", "etl_event_count",
    "synthetic_file_matched_write_event_count",
    "synthetic_writer_pid_matched_write_event_count",
    "other_or_unknown_pid_matched_write_event_count",
    "raw_trace_and_worker_deleted", "raw_etl_exported",
    "private_file_identity_exported", "process_pid_exported",
    "clinical_file_touched", "actual_ilexis_writer_identified",
    "file_write_completion_proven", "complete_etw_delivery_proven",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed", "verdict",
}
STATUSES = {"events_returned", "no_matching_events", "query_error",
            "parse_error", "probe_error", "unavailable"}
READ_STATUSES = {"not_attempted", "events_returned", "no_matching_events",
                 "access_denied", "invalid_data", "provider_unavailable",
                 "conversion_failed", "other"}


class InvalidD3E12(ValueError):
    pass


def validate(x):
    if not isinstance(x, dict) or set(x) != FIELDS:
        raise InvalidD3E12("SCHEMA_FIELDS_INVALID")
    if (x["schema"] != "facad314_d3e12_synthetic_kernel_file_etw_v1"
            or x["source"] != "WINDOWS_EPHEMERAL_SYNTHETIC_FILE_ONLY"
            or x["provider"] != "Microsoft-Windows-Kernel-File"
            or x["verdict"] != "SYNTHETIC_ETW_FEASIBILITY_NOT_ILEXIS_CAUSALITY"
            or x["etl_query_status"] not in STATUSES):
        raise InvalidD3E12("PROVENANCE_INVALID")
    for key in ("provider_discovered", "trace_started", "trace_stopped",
                "synthetic_write_verified", "etl_events_parsed",
                "etl_file_present", "etl_file_nonempty", "tracerpt_attempted",
                "tracerpt_exit_zero", "tracerpt_output_file_present",
                "tracerpt_output_file_nonempty"):
        if type(x[key]) is not bool:
            raise InvalidD3E12("BOOLEAN_INVALID")
    for key in ("etl_event_count", "synthetic_file_matched_write_event_count",
                "synthetic_writer_pid_matched_write_event_count",
                "other_or_unknown_pid_matched_write_event_count"):
        if type(x[key]) is not int or not 0 <= x[key] <= 20000:
            raise InvalidD3E12("COUNT_INVALID")
    m = x["synthetic_file_matched_write_event_count"]
    if (x["synthetic_writer_pid_matched_write_event_count"]
            + x["other_or_unknown_pid_matched_write_event_count"] != m
            or m > x["etl_event_count"]):
        raise InvalidD3E12("EVENT_CORRELATION_INVALID")
    if x["trace_started"] and (not x["provider_discovered"] or not x["trace_stopped"]):
        raise InvalidD3E12("TRACE_STARTED_NOT_CLEANLY_STOPPED")
    if x["synthetic_write_verified"] and not x["trace_started"]:
        raise InvalidD3E12("SYNTHETIC_WRITE_OUTSIDE_TRACE")
    if (x["direct_etl_read_status"] not in READ_STATUSES - {"conversion_failed"}
            or x["tracerpt_evtx_read_status"] not in READ_STATUSES):
        raise InvalidD3E12("UNRECOGNIZED_READ_STATUS")
    if x["etl_file_nonempty"] and not x["etl_file_present"]:
        raise InvalidD3E12("NONEMPTY_WITHOUT_ETL_FILE")
    if not x["trace_started"] and (
            x["etl_file_present"] or x["tracerpt_attempted"]
            or x["direct_etl_read_status"] != "not_attempted"):
        raise InvalidD3E12("ETW_ARTIFACT_WITHOUT_TRACE")
    if x["tracerpt_attempted"] and not (
            x["trace_started"] and x["etl_file_present"]
            and x["synthetic_write_verified"]):
        raise InvalidD3E12("TRACERPT_WITHOUT_VALID_SYNTHETIC_TRACE")
    if (x["direct_etl_read_status"] == "events_returned"
            and x["etl_decoder"] != "direct_etl"):
        raise InvalidD3E12("DIRECT_EVENTS_NOT_REFLECTED_IN_DECODER")
    if x["tracerpt_attempted"] and x["direct_etl_read_status"] in {
            "not_attempted", "events_returned"}:
        raise InvalidD3E12("FALLBACK_WAS_NOT_NEEDED")
    if (not x["tracerpt_attempted"] and
            (x["tracerpt_exit_zero"] or x["tracerpt_output_file_present"]
             or x["tracerpt_output_file_nonempty"]
             or x["tracerpt_evtx_read_status"] != "not_attempted")):
        raise InvalidD3E12("FALLBACK_OUTCOME_WITHOUT_ATTEMPT")
    if x["tracerpt_output_file_nonempty"] and not x["tracerpt_output_file_present"]:
        raise InvalidD3E12("OUTPUT_NONEMPTY_WITHOUT_FILE")
    if x["tracerpt_exit_zero"] and not x["tracerpt_attempted"]:
        raise InvalidD3E12("TRACERPT_EXIT_WITHOUT_ATTEMPT")
    if (x["etl_decoder"] == "direct_etl"
            and x["direct_etl_read_status"] != "events_returned"):
        raise InvalidD3E12("DIRECT_DECODER_WITHOUT_EVENTS")
    if (x["etl_decoder"] == "tracerpt_evtx"
            and not (x["tracerpt_attempted"] and x["tracerpt_exit_zero"]
                     and x["tracerpt_output_file_nonempty"]
                     and x["tracerpt_evtx_read_status"] == "events_returned")):
        raise InvalidD3E12("FALLBACK_DECODER_WITHOUT_EVENTS")
    if (x["etl_events_parsed"] and not x["etl_file_nonempty"]):
        raise InvalidD3E12("EVENTS_PARSED_FROM_EMPTY_ETL")
    if x["etl_decoder"] not in {"none", "direct_etl", "tracerpt_evtx"}:
        raise InvalidD3E12("UNKNOWN_ETW_DECODER")
    if (x["etl_events_parsed"] and x["etl_decoder"] == "none") or (
        not x["etl_events_parsed"] and x["etl_decoder"] != "none"
    ):
        raise InvalidD3E12("DECODER_EVIDENCE_MISMATCH")
    if x["etl_events_parsed"] != (x["etl_query_status"] == "events_returned"):
        raise InvalidD3E12("TRACE_QUERY_MISMATCH")
    if m and (not x["synthetic_write_verified"] or not x["etl_events_parsed"]):
        raise InvalidD3E12("MATCH_WITHOUT_SYNTHETIC_WRITE_OR_ETW")
    if x["etl_query_status"] == "no_matching_events" and x["etl_event_count"]:
        raise InvalidD3E12("NO_EVENTS_BUT_COUNT_POSITIVE")
    for key in ("raw_etl_exported", "private_file_identity_exported",
                "process_pid_exported", "clinical_file_touched",
                "actual_ilexis_writer_identified", "file_write_completion_proven",
                "complete_etw_delivery_proven", "shared_app_storage_isolation_verified",
                "clinical_edit_allowed"):
        if x[key] is not False:
            raise InvalidD3E12("FORGED_PRIVATE_CLINICAL_OR_COMPLETION_CLAIM")
    if x["raw_trace_and_worker_deleted"] is not True:
        raise InvalidD3E12("PRIVATE_TRACE_NOT_DELETED")
    feasible = (x["synthetic_writer_pid_matched_write_event_count"] > 0
                and x["etl_events_parsed"] and x["synthetic_write_verified"])
    return {
        "schema": "facad314_d3e12_checked_feasibility_v1",
        "provider_discovered": x["provider_discovered"],
        "synthetic_write_verified": x["synthetic_write_verified"],
        "etl_query_status": x["etl_query_status"],
        "etl_decoder": x["etl_decoder"],
        "etl_file_present": x["etl_file_present"],
        "etl_file_nonempty": x["etl_file_nonempty"],
        "direct_etl_read_status": x["direct_etl_read_status"],
        "tracerpt_attempted": x["tracerpt_attempted"],
        "tracerpt_exit_zero": x["tracerpt_exit_zero"],
        "tracerpt_output_file_nonempty": x["tracerpt_output_file_nonempty"],
        "tracerpt_evtx_read_status": x["tracerpt_evtx_read_status"],
        "matched_synthetic_file_write_event_count": m,
        "matched_synthetic_writer_pid_event_count":
            x["synthetic_writer_pid_matched_write_event_count"],
        "bounded_synthetic_pid_link_observed": feasible,
        "actual_ilexis_writer_identified": False,
        "file_write_completion_proven": False,
        "complete_etw_delivery_proven": False,
        "clinical_edit_allowed": False,
        "shared_app_storage_isolation_verified": False,
        "raw_trace_and_worker_deleted": True,
        "verdict": ("SYNTHETIC_ETW_PID_LINK_OBSERVED_NOT_CLINICAL_CAUSALITY"
                    if feasible else "ETW_SYNTHETIC_PID_FEASIBILITY_UNVERIFIED"),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        result = validate(json.loads(args.input.read_text(encoding="utf-8-sig")))
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("D3E12_FEASIBILITY_VERDICT=" + result["verdict"])
        print("D3E12_ETW_QUERY_STATUS=" + result["etl_query_status"])
        print("D3E12_ETW_DECODER=" + result["etl_decoder"])
        print("D3E12_ETL_FILE_NONEMPTY=" + str(result["etl_file_nonempty"]).lower())
        print("D3E12_DIRECT_ETL_READ_STATUS=" + result["direct_etl_read_status"])
        print("D3E12_TRACERPT_ATTEMPTED=" + str(result["tracerpt_attempted"]).lower())
        print("D3E12_TRACERPT_EXIT_ZERO=" + str(result["tracerpt_exit_zero"]).lower())
        print("D3E12_TRACERPT_OUTPUT_NONEMPTY=" + str(result["tracerpt_output_file_nonempty"]).lower())
        print("D3E12_TRACERPT_EVTX_READ_STATUS=" + result["tracerpt_evtx_read_status"])
        print("D3E12_SYNTHETIC_PID_LINK_OBSERVED=" + str(result["bounded_synthetic_pid_link_observed"]).lower())
        return 0
    except (ValueError, TypeError, OSError, UnicodeError, KeyError):
        print("D3E12_FEASIBILITY_VERDICT=BLOCKED_INVALID_OR_PRIVATE_EVIDENCE")
        return 2
    finally:
        print("D3E12_ACTUAL_ILEXIS_WRITER_IDENTIFIED=false")
        print("D3E12_RAW_ETL_EXPORTED=false")
        print("CLINICAL_EDIT_ALLOWED=false")


if __name__ == "__main__":
    raise SystemExit(main())
