#!/usr/bin/env python3
"""Strict, fail-closed validator of synthetic Windows Security 4663 canary results.

Never certifies Facad writes or actual D3 isolation. No user path ingestion.
"""
import argparse
import json
from pathlib import Path

REQUIRED = {
    "schema", "source", "audit_event_id", "scoped_sacl_configuration_proven",
    "audit_policy_enabled_during_observation", "matching_4663_write_event_count",
    "expected_process_pid_matched", "event_path_scope_matched",
    "queried_4663_event_count", "scoped_4663_event_count",
    "parsed_file_object_event_count", "nonempty_object_name_event_count",
    "canary_file_inherited_audit_rule_present",
    "scoped_write_mask_event_count", "scoped_expected_pid_event_count",
    "unexpected_pid_count", "event_completeness_verified",
    "clinical_data_accessed", "facad_application_launched",
    "process_file_write_attribution_proven_for_facad",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed", "verdict",
}
ALLOWED = {
    "SYNTHETIC_CANARY_4663_PID_MATCH_ONLY",
    "BLOCKED_AUDIT_UNAVAILABLE",
    "BLOCKED_AUDIT_UNAVAILABLE_OR_INCOMPLETE",
    "BLOCKED_NO_MATCHING_CANARY_EVENT",
    "BLOCKED_CLEANUP_FAILED", "BLOCKED_POLICY_RESTORE_FAILED",
}

class InvalidCanary(ValueError):
    pass


def validate(r):
    if not isinstance(r, dict) or set(r) != REQUIRED:
        raise InvalidCanary('INVALID_SCHEMA')
    if r['schema'] != 'facad314_d3e_audit_canary_v1' or r['source'] != 'EPHEMERAL_WINDOWS_RUNNER_SYNTHETIC_CANARY_ONLY':
        raise InvalidCanary('INVALID_SOURCE')
    if type(r['audit_event_id']) is not int or r['audit_event_id'] != 4663:
        raise InvalidCanary('INVALID_EVENT')
    for key in ("clinical_data_accessed", "facad_application_launched",
                "process_file_write_attribution_proven_for_facad",
                "shared_app_storage_isolation_verified", "clinical_edit_allowed",
                "event_completeness_verified"):
        if r[key] is not False:
            raise InvalidCanary('FORGED_CLEARANCE')
    for key in ('scoped_sacl_configuration_proven', 'audit_policy_enabled_during_observation',
                'expected_process_pid_matched', 'event_path_scope_matched',
                'canary_file_inherited_audit_rule_present'):
        if type(r[key]) is not bool:
            raise InvalidCanary('BAD_BOOL')
    for key in ('matching_4663_write_event_count', 'unexpected_pid_count',
                'queried_4663_event_count', 'scoped_4663_event_count',
                'parsed_file_object_event_count', 'nonempty_object_name_event_count',
                'scoped_write_mask_event_count', 'scoped_expected_pid_event_count'):
        if type(r[key]) is not int or r[key] < 0 or r[key] > 500:
            raise InvalidCanary('BAD_COUNTER')
    if not (r['queried_4663_event_count'] >= r['parsed_file_object_event_count'] >=
            r['nonempty_object_name_event_count'] >= r['scoped_4663_event_count'] >=
            r['scoped_write_mask_event_count'] >= r['matching_4663_write_event_count']):
        raise InvalidCanary('COUNTS_INCONSISTENT')
    if not (r['queried_4663_event_count'] >= r['scoped_4663_event_count'] >=
            r['scoped_write_mask_event_count'] >= r['matching_4663_write_event_count']):
        raise InvalidCanary('COUNTS_INCONSISTENT')
    if r['scoped_4663_event_count'] < r['scoped_expected_pid_event_count']:
        raise InvalidCanary('PID_COUNTS_INCONSISTENT')
    if r['matching_4663_write_event_count'] > r['scoped_expected_pid_event_count']:
        raise InvalidCanary('MATCHED_COUNTS_INCONSISTENT')
    if r['verdict'] not in ALLOWED:
        raise InvalidCanary('UNKNOWN_VERDICT')
    evidence = (r['canary_file_inherited_audit_rule_present'] and
                r['scoped_sacl_configuration_proven'] and
                r['audit_policy_enabled_during_observation'] and
                r['expected_process_pid_matched'] and
                r['event_path_scope_matched'] and
                r['matching_4663_write_event_count'] > 0)
    if (r['expected_process_pid_matched'] or r['event_path_scope_matched']) and not r['matching_4663_write_event_count']:
        raise InvalidCanary('CONTRADICTORY_COUNTER')
    if r['verdict'] == 'SYNTHETIC_CANARY_4663_PID_MATCH_ONLY':
        if not evidence:
            raise InvalidCanary('CANARY_NOT_PROVEN')
        return 'CANARY_INSTRUMENTATION_PROVEN_SYNTHETIC_ONLY', 0
    return 'BLOCKED_UNAVAILABLE_OR_UNPROVEN', 2


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--input', required=True, type=Path)
    args = a.parse_args()
    try:
        raw = json.loads(args.input.read_text(encoding='utf-8-sig'))
        statement, code = validate(raw)
    except (ValueError, OSError, UnicodeError):
        statement, code = 'BLOCKED_INVALID_EVIDENCE', 2
    print('D3E_SYNTHETIC_INSTRUMENTATION=' + statement)
    print('SHARED_APP_STORAGE_ISOLATION=UNVERIFIED')
    print('CLINICAL_EDIT_ALLOWED=false')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
