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

    def test_facad_ilexis_settings_metadata_drift_blocks(self):
        name = 'facad_ilexis_roaming_settings'
        item = 'hashed-Facad-settings-path'
        self.before['scopes'][name]['entries'][item] = {'sha256': 'a'*64, 'size': 123}
        self.after['scopes'][name]['entries'][item] = {'sha256': 'b'*64, 'size': 123}
        result = gate.compare(self.before, self.after)
        self.assertEqual(result['verdict'], 'BLOCKED_OBSERVED_STORAGE_DRIFT')
        self.assertEqual(result['observed_changes'][0]['scope'], name)
        self.assertNotIn(item, json.dumps(result))
        self.assertFalse(result['d3_isolation_verified'])

    def test_missing_ilexis_scope_rejected(self):
        self.after['scopes'].pop('facad_ilexis_roaming_settings')
        with self.assertRaises(gate.EvidenceError):
            gate.compare(self.before, self.after)

    def test_ilexis_absent_does_not_certify_isolation(self):
        for obj in (self.before, self.after):
            obj['scopes']['facad_ilexis_roaming_settings']['present'] = False
        result = gate.compare(self.before, self.after)
        self.assertEqual(result['verdict'], 'INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT')
        self.assertFalse(result['d3_isolation_verified'])
        self.assertFalse(result['clinical_edit_allowed'])

    def test_verdict_does_not_expose_hashed_file_identity(self):
        # A predictable filename is recoverable by guessing against an unsalted hash.
        path_key = 'patient-looking-file-name'
        self.after['scopes']['facad_ilexis_roaming_settings']['entries'][path_key] = {
            'sha256': 'e'*64, 'size': 3
        }
        result = gate.compare(self.before, self.after)
        self.assertEqual(result['observed_change_count'], 1)
        self.assertEqual(
            result['observed_changes'][0],
            {'scope': 'facad_ilexis_roaming_settings', 'change': 'ADDED'}
        )
        self.assertNotIn(path_key, json.dumps(result))
        self.assertNotIn('entry_key_sha256', json.dumps(result))
        self.assertIs(result['d3_isolation_verified'], False)

    def test_windows_bootstrap_ilexis_three_changes_remains_red_with_safe_counts(self):
        # Structural reproduction of Windows run 38006857529 verdict: 1 add, 2
        # changes in Ilexis metadata only. Never ingest original private manifests.
        name = 'facad_ilexis_roaming_settings'
        for n in ('existing_settings_a', 'existing_settings_b'):
            self.before['scopes'][name]['entries'][n] = {
                'sha256': 'a'*64, 'size': 10
            }
            self.after['scopes'][name]['entries'][n] = {
                'sha256': 'b'*64, 'size': 10
            }
        self.after['scopes'][name]['entries']['created_settings'] = {
            'sha256': 'c'*64, 'size': 15
        }
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            before_file, after_file, verdict_file = (
                directory/'before.json', directory/'after.json', directory/'verdict.json'
            )
            before_file.write_text(json.dumps(self.before), encoding='utf-8')
            after_file.write_text(json.dumps(self.after), encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(HERE/'facad_314_d3_snapshot_diff_gate.py'),
                 '--before', str(before_file), '--after', str(after_file),
                 '--output', str(verdict_file)],
                capture_output=True, text=True
            )
            verdict = json.loads(verdict_file.read_text(encoding='utf-8'))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(verdict['verdict'], 'BLOCKED_OBSERVED_STORAGE_DRIFT')
        self.assertEqual(verdict['observed_change_count'], 3)
        self.assertEqual(result.stdout.count('D3_OBSERVED_DRIFT_SCOPE='), 1)
        self.assertIn(
            'D3_OBSERVED_DRIFT_SCOPE=facad_ilexis_roaming_settings;ADDED=1;MODIFIED=2;DELETED=0;ROOT_CHANGED=0',
            result.stdout
        )
        for private_name in ('existing_settings_a', 'existing_settings_b', 'created_settings'):
            self.assertNotIn(private_name, result.stdout)
            self.assertNotIn(private_name, json.dumps(verdict))
        self.assertNotIn('entry_key_sha256', result.stdout)
        self.assertIs(verdict['d3_isolation_verified'], False)
        self.assertIs(verdict['clinical_edit_allowed'], False)

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
