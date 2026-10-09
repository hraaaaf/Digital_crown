"""Synthetic unit tests for D3 offline diff gate; no Facad app launched."""
import importlib.util
import subprocess
import sys
import tempfile
import json
import unittest
from pathlib import Path

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location('gate', HERE / 'facad_314_d3_snapshot_diff_gate.py')
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def fixture(phase):
    return {
        'schema': gate.SCHEMA, 'phase': phase, 'session_id': 'official-demo-session',
        'scopes': {name: {
            'kind': kind, 'root_fingerprint': 'a' * 64,
            'capture_ok': True, 'present': True, 'entries': {}
        } for name, kind in gate.SCOPES.items()},
    }


class D3DiffTests(unittest.TestCase):
    def setUp(self):
        self.before, self.after = fixture('before'), fixture('after')

    def test_unchanged_is_inconclusive_not_isolated(self):
        x = gate.compare(self.before, self.after)
        self.assertEqual(x['verdict'], 'INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT')
        self.assertIs(x['d3_isolation_verified'], False)
        self.assertIs(x['clinical_edit_allowed'], False)

    def test_added_sibling_in_official_examples_blocks(self):
        self.after['scopes']['official_examples_tree']['entries']['image.jpg'] = {'sha256': 'b'*64, 'size': 123}
        x = gate.compare(self.before, self.after)
        self.assertEqual(x['verdict'], 'BLOCKED_OBSERVED_STORAGE_DRIFT')
        self.assertEqual(x['observed_change_count'], 1)
        self.assertNotIn('image.jpg', json.dumps(x))

    def test_changed_registry_blocks(self):
        row = {'sha256': 'b'*64, 'size': 0}
        self.before['scopes']['facad_registry_hkcu']['entries']['MRU'] = row
        self.after['scopes']['facad_registry_hkcu']['entries']['MRU'] = {'sha256': 'c'*64, 'size': 0}
        self.assertEqual(gate.compare(self.before, self.after)['verdict'], 'BLOCKED_OBSERVED_STORAGE_DRIFT')

    def test_deleted_file_blocks(self):
        self.before['scopes']['facad_appdata_local']['entries']['temp'] = {'sha256': 'f'*64, 'size': 1}
        self.assertEqual(gate.compare(self.before, self.after)['observed_changes'][0]['change'], 'DELETED')

    def test_root_appeared_blocks(self):
        self.before['scopes']['facad_programdata']['present'] = False
        self.assertEqual(gate.compare(self.before, self.after)['observed_changes'][0]['change'], 'ROOT_APPEARED_OR_DISAPPEARED')

    def test_missing_scope_rejected(self):
        self.after['scopes'].pop('facad_programdata')
        with self.assertRaises(gate.EvidenceError): gate.compare(self.before, self.after)

    def test_uncaptured_scope_rejected(self):
        self.after['scopes']['facad_install_tree']['capture_ok'] = False
        with self.assertRaises(gate.EvidenceError): gate.compare(self.before, self.after)

    def test_mismatched_session_rejected(self):
        self.after['session_id'] = 'different'
        with self.assertRaises(gate.EvidenceError): gate.compare(self.before, self.after)

    def test_mismatched_root_rejected(self):
        self.after['scopes']['official_examples_tree']['root_fingerprint'] = 'b'*64
        with self.assertRaises(gate.EvidenceError): gate.compare(self.before, self.after)

    def test_bad_entry_hash_rejected(self):
        self.after['scopes']['facad_documents']['entries']['bad'] = {'sha256': 'bad', 'size': 0}
        with self.assertRaises(gate.EvidenceError): gate.compare(self.before, self.after)

    def test_scope_absence_with_entries_rejected(self):
        s=self.after['scopes']['facad_documents'];s['present']=False;s['entries']['foo']={'sha256':'a'*64,'size':1}
        with self.assertRaises(gate.EvidenceError): gate.compare(self.before,self.after)

    def test_reject_extra_fields(self):
        self.after['claim_isolation']=True
        with self.assertRaises(gate.EvidenceError): gate.compare(self.before,self.after)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            def invoke(a,b):
                (d/'before.json').write_text(json.dumps(a))
                (d/'after.json').write_text(json.dumps(b))
                r=subprocess.run([sys.executable,str(HERE/'facad_314_d3_snapshot_diff_gate.py'),'--before',str(d/'before.json'),'--after',str(d/'after.json'),'--output',str(d/'out.json')],capture_output=True,text=True)
                return r.returncode, json.loads((d/'out.json').read_text())
            n,out=invoke(self.before,self.after)
            self.assertEqual(n,3)  # even no drift cannot green-light D3
            self.assertFalse(out['d3_isolation_verified'])
            self.after['scopes']['facad_appdata_roaming']['entries']['change']={'sha256':'b'*64,'size':2}
            self.assertEqual(invoke(self.before,self.after)[0],1)
            self.after['scopes'].pop('facad_appdata_roaming')
            self.assertEqual(invoke(self.before,self.after)[0],2)


if __name__=='__main__': unittest.main()
