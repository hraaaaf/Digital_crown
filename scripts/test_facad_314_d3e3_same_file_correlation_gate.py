"""Purely synthetic tests for D3E.3 local identity overlap; no Facad or real paths."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("gate",HERE/"facad_314_d3e3_same_file_correlation_gate.py")
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
H=lambda ch:ch*64
SCOPE="facad_ilexis_roaming_settings"
def snapshot(phase,entries=None):
    names=["official_examples_tree","disposable_examples_tree","facad_install_tree",
           "facad_appdata_roaming",SCOPE,"facad_appdata_local","facad_programdata",
           "facad_documents","facad_registry_hkcu","facad_registry_hklm"]
    scopes={}
    for name in names:
        kind="registry" if name.endswith(("hkcu","hklm")) else "filetree"
        scopes[name]={"kind":kind,"root_fingerprint":H("e"),
                      "capture_ok":True,"present":True,"entries":(
                      entries if name==SCOPE and entries is not None else {})}
    return {"schema":"facad314_d3_snapshot_v1","phase":phase,
            "session_id":"synthetic-only-001","scopes":scopes}
def entry(size):return {"sha256":H("f"),"size":size}
def event(keys=None):
    return {"schema":"facad314_d3e3_event_ids_v1",
            "source":"EPHEMERAL_FACAD_ROOT_PID_4663_KEYS_LOCAL_ONLY",
            "session_id":"synthetic-only-001","selected_scope":SCOPE,
            "root_pid_relative_key_hashes":list(keys if keys is not None else [H("a")]),
            "other_pid_relative_key_hashes":[],
            "observed_descendant_pid_count":0,
            "clinical_edit_allowed":False,"shared_app_storage_isolation_verified":False,
            "complete_descendant_process_coverage":False,"event_delivery_complete":False}

class TestLocalIdentity(unittest.TestCase):
    def setUp(self):
        self.before=snapshot("before",{H("a"):entry(1)})
        self.after=snapshot("after",{H("a"):entry(2)})
        self.events=event()
    def compute(self):return gate.compute(self.before,self.after,self.events)
    def invalid(self):
        with self.assertRaises(gate.InvalidCorrelation):self.compute()
    def test_one_positive_not_clinical(self):
        x,code=self.compute()
        self.assertEqual(code,0)
        self.assertEqual(x["same_file_metadata_and_4663_count"],1)
        self.assertIs(x["causal_metadata_change_proven"],False)
        self.assertIs(x["clinical_edit_allowed"],False)
        self.assertEqual(set(x),{
            "schema","source","selected_scope","selected_scope_metadata_changed_count",
            "facad_root_pid_unique_written_file_count","same_file_metadata_and_4663_count",
            "changed_files_without_root_pid_event_count",
            "root_pid_event_files_without_metadata_change_count",
            "filename_or_file_hash_exported","complete_descendant_process_coverage",
            "event_delivery_complete","causal_metadata_change_proven",
            "all_storage_roots_verified","shared_app_storage_isolation_verified",
            "clinical_edit_allowed","verdict"})
    def test_no_matching_events_block(self):
        self.events["root_pid_relative_key_hashes"]=[H("b")]
        x,code=self.compute()
        self.assertEqual(code,2);self.assertEqual(x["same_file_metadata_and_4663_count"],0)
    def test_empty_events_block(self):
        self.events["root_pid_relative_key_hashes"]=[]
        self.assertEqual(self.compute()[1],2)
    def test_missing_event_field(self):
        del self.events["source"];self.invalid()
    def test_raw_objectname_rejected(self):
        self.events["ObjectName"]="C:\\Sensitive\\patient";self.invalid()
    def test_extra_raw_pid_rejected(self):
        self.events["ProcessId"]=42;self.invalid()
    def test_wrong_scope_rejected(self):
        self.events["selected_scope"]="facad_patient_files";self.invalid()
    def test_wrong_session_rejected(self):
        self.events["session_id"]="other";self.invalid()
    def test_bad_digest_rejected(self):
        self.events["root_pid_relative_key_hashes"]=["relative\\path"];self.invalid()
    def test_bad_digest_case_rejected(self):
        self.events["root_pid_relative_key_hashes"]=[H("A")];self.invalid()
    def test_duplicate_ids_rejected(self):
        self.events["root_pid_relative_key_hashes"]=[H("a"),H("a")];self.invalid()
    def test_forged_coverage_rejected(self):
        for flag in ("clinical_edit_allowed","shared_app_storage_isolation_verified",
                     "complete_descendant_process_coverage","event_delivery_complete"):
            with self.subTest(flag=flag):
                self.events=event();self.events[flag]=True;self.invalid()
    def test_snapshot_root_changed_rejected(self):
        self.after["scopes"][SCOPE]["root_fingerprint"]=H("b");self.invalid()
    def test_snapshot_absent_rejected(self):
        self.after["scopes"][SCOPE]["present"]=False
        self.after["scopes"][SCOPE]["entries"]={}
        self.invalid()
    def test_snapshot_incomplete_rejected(self):
        self.before["scopes"][SCOPE]["capture_ok"]=False;self.invalid()
    def test_deleted_file_is_change(self):
        self.after["scopes"][SCOPE]["entries"]={}
        x,code=self.compute();self.assertEqual(code,0)
        self.assertEqual(x["same_file_metadata_and_4663_count"],1)
    def test_unchanged_file_not_overlap(self):
        self.after["scopes"][SCOPE]["entries"][H("a")]=entry(1)
        x,code=self.compute();self.assertEqual(code,2)
    def test_multiple_changed_files_partial_match(self):
        self.before["scopes"][SCOPE]["entries"][H("b")]=entry(1)
        self.after["scopes"][SCOPE]["entries"][H("b")]=entry(3)
        x,code=self.compute();self.assertEqual(code,0)
        self.assertEqual(x["changed_files_without_root_pid_event_count"],1)
    def test_cli_does_not_print_raw_path(self):
        self.events["ObjectName"]="C:\\Sensitive\\path"
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name,data in (("b.json",self.before),("a.json",self.after),("e.json",self.events)):
                (root/name).write_text(json.dumps(data))
            run=subprocess.run([sys.executable,str(HERE/"facad_314_d3e3_same_file_correlation_gate.py"),
                 "--before",str(root/"b.json"),"--after",str(root/"a.json"),
                 "--event-keys",str(root/"e.json"),"--output",str(root/"out.json")],
                 text=True,capture_output=True)
            self.assertEqual(run.returncode,2)
            self.assertNotIn("Sensitive",run.stdout+run.stderr)
            self.assertFalse((root/"out.json").exists())
    def test_cli_aggregate_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name,data in (("b.json",self.before),("a.json",self.after),("e.json",self.events)):
                (root/name).write_text(json.dumps(data))
            run=subprocess.run([sys.executable,str(HERE/"facad_314_d3e3_same_file_correlation_gate.py"),
                 "--before",str(root/"b.json"),"--after",str(root/"a.json"),
                 "--event-keys",str(root/"e.json"),"--output",str(root/"out.json")],
                 text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            output=(root/"out.json").read_text()
            self.assertNotIn(H("a"),output)
            self.assertNotIn("synthetic-only-001",output)
            self.assertIn("UNVERIFIED",run.stdout)

if __name__=="__main__": unittest.main()
