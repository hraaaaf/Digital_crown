#!/usr/bin/env python3
"""Validate path-free Facad root-PID event 4663 evidence without isolation claims."""
import argparse
import json
from pathlib import Path

FIELDS = {
    'schema','source','selected_scope','windows_event_id',
    'selected_scope_existed_before_start','audit_policy_success_enabled',
    'scope_sacl_applied','scope_sacl_restored','audit_policy_restored',
    'queried_event_count','scoped_file_write_event_count',
    'facad_root_pid_write_event_count','other_process_pid_write_event_count',
    'process_counter_samples','process_root_alive_during_observation',
    'complete_descendant_process_coverage','event_delivery_complete',
    'configured_patient_data_root_verified','patient_files_or_settings_content_read',
    'registry_values_read','license_content_read','same_landmark_parity_executed',
    'shared_app_storage_isolation_verified','clinical_edit_allowed','verdict',
}
PASS='POSITIVE_FACAD_ROOT_PID_WRITE_USE_EVENTS_NOT_ISOLATION'
BLOCKED={
 'BLOCKED_AUDIT_NOT_STARTED','BLOCKED_INCOMPLETE_OR_UNAVAILABLE_4663_EVIDENCE',
 'BLOCKED_NO_FACAD_ROOT_PID_WRITE_EVENT','BLOCKED_PROCESS_STOP_FAILED',
 'BLOCKED_SACL_RESTORE_FAILED','BLOCKED_AUDIT_POLICY_RESTORE_FAILED',
 'BLOCKED_UNKNOWN_INITIAL_POLICY','BLOCKED_RESTORATION_NOT_PROVEN',
}


class UnsafeEvidence(ValueError):
    pass


def validate(r):
    if not isinstance(r,dict) or set(r)!=FIELDS:
        raise UnsafeEvidence('INVALID_FIELDS')
    if (r['schema']!='facad314_d3e_root_pid_write_v1' or
        r['source']!='EPHEMERAL_OFFICIAL_ROBERT_STARTUP_ONLY' or
        r['selected_scope']!='facad_ilexis_roaming_settings' or
        type(r['windows_event_id']) is not int or r['windows_event_id']!=4663):
        raise UnsafeEvidence('SOURCE_OR_SCOPE_UNTRUSTED')
    for key in ('complete_descendant_process_coverage','event_delivery_complete',
                'configured_patient_data_root_verified','patient_files_or_settings_content_read',
                'registry_values_read','license_content_read','same_landmark_parity_executed',
                'shared_app_storage_isolation_verified','clinical_edit_allowed'):
        if r[key] is not False:
            raise UnsafeEvidence('FORGED_CLEARANCE')
    for key in ('selected_scope_existed_before_start','audit_policy_success_enabled',
                'scope_sacl_applied','scope_sacl_restored','audit_policy_restored',
                'process_root_alive_during_observation'):
        if type(r[key]) is not bool:
            raise UnsafeEvidence('INVALID_BOOLEAN')
    for key in ('queried_event_count','scoped_file_write_event_count',
                'facad_root_pid_write_event_count','other_process_pid_write_event_count',
                'process_counter_samples'):
        if type(r[key]) is not int or not (0 <= r[key] <= 4000):
            raise UnsafeEvidence('INVALID_COUNTER')
    if (r['queried_event_count'] < r['scoped_file_write_event_count'] or
        r['scoped_file_write_event_count'] !=
            r['facad_root_pid_write_event_count']+r['other_process_pid_write_event_count']):
        raise UnsafeEvidence('COUNTERS_DO_NOT_BALANCE')
    if r['verdict'] not in BLOCKED | {PASS}:
        raise UnsafeEvidence('UNRECOGNIZED_VERDICT')
    if r['verdict']==PASS:
        if (not all(r[k] is True for k in (
                'selected_scope_existed_before_start','audit_policy_success_enabled',
                'scope_sacl_applied','scope_sacl_restored','audit_policy_restored',
                'process_root_alive_during_observation')) or
            r['facad_root_pid_write_event_count']<1 or
            r['process_counter_samples']!=12):
            raise UnsafeEvidence('POSITIVE_CLAIM_NOT_PROVEN')
        return 'POSITIVE_ROOT_PID_EVENTS_ONLY',0
    return 'BLOCKED_INCOMPLETE_OR_NO_EVENTS',2


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--input',type=Path,required=True)
    args=a.parse_args()
    try:
        status,code=validate(json.loads(args.input.read_text(encoding='utf-8-sig')))
    except (UnsafeEvidence, OSError, ValueError, UnicodeError):
        status,code='BLOCKED_INVALID_EVIDENCE',2
    print('D3E2_EVIDENCE_STATUS='+status)
    print('D3E2_COMPLETE_DESCENDANT_COVERAGE=false')
    print('SHARED_APP_STORAGE_ISOLATION=UNVERIFIED')
    print('CLINICAL_EDIT_ALLOWED=false')
    return code


if __name__=='__main__':
    raise SystemExit(main())
