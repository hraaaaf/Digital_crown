"""Adversarial, synthetic-only Windows 4663 attribution evidence validation."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('gate',HERE/'facad_314_d3e_canary_verdict_gate.py')
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixture():
    return {
        'schema':'facad314_d3e_audit_canary_v1',
        'source':'EPHEMERAL_WINDOWS_RUNNER_SYNTHETIC_CANARY_ONLY',
        'audit_event_id':4663,
        'scoped_sacl_configuration_proven':True,
        'audit_policy_enabled_during_observation':True,
        'matching_4663_write_event_count':2,
        'queried_4663_event_count':4,
        'scoped_4663_event_count':3,
        'scoped_write_mask_event_count':2,
        'scoped_expected_pid_event_count':2,
        'expected_process_pid_matched':True,
        'event_path_scope_matched':True,
        'unexpected_pid_count':0,
        'event_completeness_verified':False,
        'clinical_data_accessed':False,
        'facad_application_launched':False,
        'process_file_write_attribution_proven_for_facad':False,
        'shared_app_storage_isolation_verified':False,
        'clinical_edit_allowed':False,
        'verdict':'SYNTHETIC_CANARY_4663_PID_MATCH_ONLY',
    }

class CanaryTests(unittest.TestCase):
    def setUp(self):
        self.data=fixture()

    def assert_invalid(self):
        with self.assertRaises(gate.InvalidCanary):gate.validate(self.data)

    def test_synthetic_canary_pass_never_clears_facad(self):
        name,code=gate.validate(self.data)
        self.assertEqual(code,0)
        self.assertEqual(name,'CANARY_INSTRUMENTATION_PROVEN_SYNTHETIC_ONLY')
        self.assertFalse(self.data['process_file_write_attribution_proven_for_facad'])

    def test_no_audit_policy(self):
        self.data['audit_policy_enabled_during_observation']=False
        self.assert_invalid()

    def test_no_sacl(self):
        self.data['scoped_sacl_configuration_proven']=False
        self.assert_invalid()

    def test_no_process_pid_match(self):
        self.data['expected_process_pid_matched']=False
        self.assert_invalid()

    def test_no_scoped_path_match(self):
        self.data['event_path_scope_matched']=False
        self.assert_invalid()

    def test_no_4663_events(self):
        self.data['matching_4663_write_event_count']=0
        self.assert_invalid()

    def test_process_or_patient_clearance_forged(self):
        for key in ('facad_application_launched','process_file_write_attribution_proven_for_facad',
                    'clinical_edit_allowed','clinical_data_accessed','shared_app_storage_isolation_verified',
                    'event_completeness_verified'):
            with self.subTest(key=key):
                changed=fixture(); changed[key]=True
                with self.assertRaises(gate.InvalidCanary):gate.validate(changed)

    def test_unknown_event_id(self):
        self.data['audit_event_id']=4656
        self.assert_invalid()

    def test_unknown_source(self):
        self.data['source']='REAL_PATIENT_EVIDENCE'
        self.assert_invalid()

    def test_extra_path_rejected(self):
        self.data['ObjectName']='C:\\Private\\Sensitive'
        self.assert_invalid()

    def test_extra_processname_rejected(self):
        self.data['ProcessName']='C:\\UserName\\Private'
        self.assert_invalid()

    def test_missing_fields_rejected(self):
        self.data.pop('event_path_scope_matched')
        self.assert_invalid()

    def test_bool_derived_from_numeric_rejected(self):
        self.data['expected_process_pid_matched']=1
        self.assert_invalid()

    def test_negative_counter_rejected(self):
        self.data['matching_4663_write_event_count']=-1
        self.assert_invalid()

    def test_inconsistent_write_count_rejected(self):
        self.data['scoped_write_mask_event_count']=1
        self.assert_invalid()

    def test_inconsistent_total_event_count_rejected(self):
        self.data['queried_4663_event_count']=1
        self.assert_invalid()

    def test_bogus_verdict_rejected(self):
        self.data['verdict']='D3_ISOLATION_VERIFIED'
        self.assert_invalid()

    def test_explicit_blocked_report_always_fails(self):
        self.data['verdict']='BLOCKED_NO_MATCHING_CANARY_EVENT'
        _,code=gate.validate(self.data)
        self.assertEqual(code,2)

    def test_cli_no_leak_if_malformed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'input.json'
            self.data['SecretPatientPath']='C:\\Sensitive\\Name'
            path.write_text(json.dumps(self.data))
            done=subprocess.run([sys.executable,str(HERE/'facad_314_d3e_canary_verdict_gate.py'),
                                 '--input',str(path)],capture_output=True,text=True)
        self.assertEqual(done.returncode,2)
        self.assertNotIn('Sensitive',done.stdout+done.stderr)

    def test_cli_good_is_synthetic_only(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'input.json';path.write_text(json.dumps(self.data))
            done=subprocess.run([sys.executable,str(HERE/'facad_314_d3e_canary_verdict_gate.py'),
                                 '--input',str(path)],capture_output=True,text=True)
        self.assertEqual(done.returncode,0)
        self.assertIn('UNVERIFIED',done.stdout)
        self.assertNotIn('C:\\',done.stdout)

if __name__=='__main__':unittest.main()
