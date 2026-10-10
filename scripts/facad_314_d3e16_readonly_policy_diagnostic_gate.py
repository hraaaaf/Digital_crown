#!/usr/bin/env python3
"""D3E16 strict anonymized validator for read-only per-user policy diagnosis."""
import argparse
import json
from pathlib import Path

FIELDS = {
    "schema", "source", "previous_get_user_unavailable_observed",
    "get_user_sid_syntax", "policy_list_users_verbose_csv_query_result",
    "current_sid_in_policy_listing", "current_sid_subcategory_get_result",
    "current_sid_category_all_get_result",
    "used_only_current_sid_for_get_queries",
    "raw_user_policy_inventory_kept_in_memory_only",
    "auditpol_system_policy_modified", "auditpol_per_user_policy_modified",
    "user_accounts_or_sid_exported", "auditpol_stdout_stderr_exported",
    "security_events_or_files_read", "registry_or_clinical_resources_read",
    "global_kernel_file_etw_used", "file_scoped_policy_proven",
    "user_policy_configurable_proven", "actual_ilexis_writer_proven",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed", "verdict",
}
GET_STATUSES = {"zero", "nonzero", "unavailable"}
MATCH_STATUSES = {"exact_current_sid_seen",
                  "not_seen_in_successful_listing", "undetermined"}
FALSE_KEYS = {
    "auditpol_system_policy_modified", "auditpol_per_user_policy_modified",
    "user_accounts_or_sid_exported", "auditpol_stdout_stderr_exported",
    "security_events_or_files_read", "registry_or_clinical_resources_read",
    "global_kernel_file_etw_used", "file_scoped_policy_proven",
    "user_policy_configurable_proven", "actual_ilexis_writer_proven",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed",
}
TRUE_KEYS = {"previous_get_user_unavailable_observed",
             "used_only_current_sid_for_get_queries",
             "raw_user_policy_inventory_kept_in_memory_only"}


class InvalidD3E16(ValueError):
    pass


def validate(x):
    if not isinstance(x, dict) or set(x) != FIELDS:
        raise InvalidD3E16("FIELDS_INVALID")
    if (x["schema"] != "facad314_d3e16_user_auditpol_presence_diagnostic_v1"
            or x["source"] != "EPHEMERAL_RUNNER_CURRENT_SID_READ_ONLY"
            or x["get_user_sid_syntax"] != "braced_current_sid"
            or x["verdict"] !=
            "PER_USER_POLICY_READONLY_DIAGNOSTIC_NOT_CAPTURE_AUTHORIZATION"):
        raise InvalidD3E16("PROVENANCE_INVALID")
    for k in FALSE_KEYS:
        if x[k] is not False:
            raise InvalidD3E16("FORGED_MODIFICATION_EXFILTRATION_OR_CLINICAL_CLAIM")
    for k in TRUE_KEYS:
        if x[k] is not True:
            raise InvalidD3E16("SCOPE_OR_PROVENANCE_UNVERIFIED")
    for k in ("policy_list_users_verbose_csv_query_result",
              "current_sid_subcategory_get_result",
              "current_sid_category_all_get_result"):
        if x[k] not in GET_STATUSES:
            raise InvalidD3E16("GET_RESULT_ENUM_INVALID")
    match = x["current_sid_in_policy_listing"]
    if match not in MATCH_STATUSES:
        raise InvalidD3E16("LIST_MATCH_ENUM_INVALID")
    if x["policy_list_users_verbose_csv_query_result"] == "zero":
        if match == "undetermined":
            raise InvalidD3E16("SUCCESSFUL_LIST_MISSING_COMPARISON")
    elif match != "undetermined":
        raise InvalidD3E16("SID_MATCH_WITHOUT_SUCCESSFUL_LIST")
    # GET failure may mean no specific per-user policy, privileges, or CLI failure.
    # Neither a GET failure nor an absent listing proves policy unconfigurable.
    return {
        "schema": "facad314_d3e16_checked_readonly_diagnostic_v1",
        "policy_list_query": x["policy_list_users_verbose_csv_query_result"],
        "current_sid_listing_match": match,
        "current_sid_subcategory_get_result":
            x["current_sid_subcategory_get_result"],
        "current_sid_category_all_get_result":
            x["current_sid_category_all_get_result"],
        "no_explicit_current_user_entry_seen_in_successful_listing":
            match == "not_seen_in_successful_listing",
        "missing_per_user_policy_definitively_proven": False,
        "per_user_audit_is_single_file_scoped_proven": False,
        "user_policy_configurable_proven": False,
        "policy_modified": False,
        "raw_user_policy_inventory_exported": False,
        "sid_or_username_exported": False,
        "real_ilexis_writer_proven": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": "READONLY_CURRENT_USER_POLICY_VISIBILITY_NOT_CAPTURE_CLEARANCE",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 16000:
            raise InvalidD3E16("INPUT_TOO_LARGE")
        x = json.loads(args.input.read_text(encoding="utf-8-sig"))
        checked = validate(x)
        args.output.write_text(json.dumps(checked, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
        print("D3E16_VERDICT=" + checked["verdict"])
        print("D3E16_CURRENT_SID_LIST_MATCH=" + checked["current_sid_listing_match"])
        print("D3E16_USER_POLICY_CONFIGURABLE_PROVEN=false")
        print("D3E16_CAPTURE_AUTHORIZED=false")
        return 0
    except (ValueError, TypeError, KeyError, OSError, UnicodeError):
        print("D3E16_VERDICT=BLOCKED_INVALID_OR_PRIVATE_POLICY_EVIDENCE")
        return 2
    finally:
        print("FAC03_D3=OPEN_RED")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_EDIT_ALLOWED=false")


if __name__ == "__main__":
    raise SystemExit(main())
