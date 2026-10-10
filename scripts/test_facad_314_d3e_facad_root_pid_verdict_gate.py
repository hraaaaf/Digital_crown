"""Synthetic-only negative tests; never invoke Facad or read Windows Security log."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('gate',HERE/'facad_314_d3e_facad_root_pid_verdict_gate.py')
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def sample():
    return {
        'schema':'facad314_d3e_root_pid_write_v1',
        'source':'EPHEMERAL_OFFICIAL_ROBERT_STARTUP_ONLY',
        'selected_scope':'facad_ilexis_roaming_settings',
        'windows_event_id':4663,
        'selected_scope_existed_before_start':True,
        'audit_policy_success_enabled':True,
        'scope_sacl_applied':True,
        'scope_sacl_restored':True,
        'audit_policy_restored':True,
        'queried_event_count':5,
        'scoped_file_write_event_count':3,
        'facad_root_pid_write_event_count':2,
        'other_process_pid_write_event_count':1,
        'process_counter_samples':12,
        'process_root_alive_during_observation':True,
        'complete_descendant_process_coverage':False,
        'event_delivery_complete':False,
        'configured_patient_data_root_verified':False,
        'patient_files_or_settings_content_read':False,
        'registry_values_read':False,
        'license_content_read':False,
        'same_landmark_parity_executed':False,
        'shared_app_storage_isolation_verified':False,
        'clinical_edit_allowed':False,
        'verdict':'POSITIVE_FACAD_ROOT_PID_WRITE_USE_EVENTS_NOT_ISOLATION',
    }


class RootPidEvidenceTests(unittest.TestCase):
    def setUp(self): self.a=sample()

    def assert_blocked_schema(self):
        with self.assertRaises(gate.UnsafeEvidence):gate.validate(self.a)

    def test_positive_has_narrow_meaning(self):
        label,code=gate.validate(self.a)
        self.assertEqual((label,code),('POSITIVE_ROOT_PID_EVENTS_ONLY',0))
        self.assertFalse(self.a['event_delivery_complete'])
        self.assertFalse(self.a['complete_descendant_process_coverage'])
        self.assertFalse(self.a['clinical_edit_allowed'])

    def test_zero_root_events_not_positive(self):
        self.a['facad_root_pid_write_event_count']=0
        self.a['other_process_pid_write_event_count']=3
        self.assert_blocked_schema()

    def test_missing_ilexis_scope(self):
        self.a['selected_scope_existed_before_start']=False
        self.assert_blocked_schema()

    def test_missing_audit_policy(self):
        self.a['audit_policy_success_enabled']=False
        self.assert_blocked_schema()

    def test_missing_sacl(self):
        self.a['scope_sacl_applied']=False
        self.assert_blocked_schema()

    def test_sacl_restore_missing(self):
        self.a['scope_sacl_restored']=False
        self.assert_blocked_schema()

    def test_audit_policy_restore_missing(self):
        self.a['audit_policy_restored']=False
        self.assert_blocked_schema()

    def test_bad_process_sampling(self):
        self.a['process_counter_samples']=0
        self.assert_blocked_schema()

    def test_process_not_alive(self):
        self.a['process_root_alive_during_observation']=False
        self.assert_blocked_schema()

    def test_counter_mismatch(self):
        self.a['scoped_file_write_event_count']=4
        self.assert_blocked_schema()

    def test_overstated_count(self):
        self.a['queried_event_count']=1
        self.assert_blocked_schema()

    def test_forged_clinical_clearance(self):
        for k in ('complete_descendant_process_coverage','event_delivery_complete',
                  'configured_patient_data_root_verified','patient_files_or_settings_content_read',
                  'registry_values_read','license_content_read','same_landmark_parity_executed',
                  'shared_app_storage_isolation_verified','clinical_edit_allowed'):
            with self.subTest(k=k):
                a=sample();a[k]=True
                with self.assertRaises(gate.UnsafeEvidence):gate.validate(a)

    def test_wrong_scope(self):
        self.a['selected_scope']='facad_patient_data_root'
        self.assert_blocked_schema()

    def test_unknown_pid_field_rejected(self):
        self.a['raw_process_pid']=123
        self.assert_blocked_schema()

    def test_raw_objectname_rejected(self):
        self.a['ObjectName']='C:\\Users\\private'
        self.assert_blocked_schema()

    def test_unknown_verdict(self):
        self.a['verdict']='D3_ISOLATION_VERIFIED'
        self.assert_blocked_schema()

    def test_reported_block_is_non_green(self):
        self.a['verdict']='BLOCKED_NO_FACAD_ROOT_PID_WRITE_EVENT'
        status,code=gate.validate(self.a)
        self.assertEqual(code,2)
        self.assertIn('BLOCKED',status)

    def test_cli_cannot_expose_sensitive_fields(self):
        self.a['ObjectName']='C:\\Sensitive\\PHI'
        with tempfile.TemporaryDirectory() as tmp:
            inp=Path(tmp)/'evidence.json'
            inp.write_text(json.dumps(self.a),encoding='utf8')
            r=subprocess.run([sys.executable,str(HERE/'facad_314_d3e_facad_root_pid_verdict_gate.py'),
                 '--input',str(inp)],capture_output=True,text=True)
        self.assertEqual(r.returncode,2)
        self.assertNotIn('Sensitive',r.stdout+r.stderr)
        self.assertIn('UNVERIFIED',r.stdout)

    def test_cli_positive_is_not_d3_clearance(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp=Path(tmp)/'evidence.json'
            inp.write_text(json.dumps(self.a),encoding='utf8')
            r=subprocess.run([sys.executable,str(HERE/'facad_314_d3e_facad_root_pid_verdict_gate.py'),
                 '--input',str(inp)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0)
        self.assertIn('POSITIVE_ROOT_PID_EVENTS_ONLY',r.stdout)
        self.assertIn('CLINICAL_EDIT_ALLOWED=false',r.stdout)


if __name__=='__main__': unittest.main()
