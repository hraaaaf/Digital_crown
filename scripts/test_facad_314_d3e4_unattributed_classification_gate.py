"""Synthetic D3E4 adversarial tests; no real files, vendor process or OS logs."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("d3e4", HERE/"facad_314_d3e4_unattributed_classification_gate.py")
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
H=lambda c:c*64
SCOPE="facad_ilexis_roaming_settings"
NAMES=("official_examples_tree","disposable_examples_tree","facad_install_tree",
"facad_appdata_roaming",SCOPE,"facad_appdata_local","facad_programdata",
"facad_documents","facad_registry_hkcu","facad_registry_hklm")
def ent(n):return {"sha256":H("e"),"size":n}
def shot(phase, entries):
    scopes={}
    for name in NAMES:
        scopes[name]={"kind":"registry" if name.endswith(("hkcu","hklm")) else "filetree",
                      "root_fingerprint":H("f"),"capture_ok":True,"present":True,
                      "entries":entries if name==SCOPE else {}}
    return {"schema":"facad314_d3_snapshot_v1","phase":phase,
            "session_id":"test-001","scopes":scopes}
def evidence(root=None,other=None,desc=0):
    return {"schema":"facad314_d3e3_event_ids_v1",
            "source":"EPHEMERAL_FACAD_ROOT_PID_4663_KEYS_LOCAL_ONLY",
            "session_id":"test-001","selected_scope":SCOPE,
            "root_pid_relative_key_hashes":list(root if root is not None else [H("a"),H("b")]),
            "other_pid_relative_key_hashes":list(other or []),
            "observed_descendant_pid_count":desc,
            "clinical_edit_allowed":False,"shared_app_storage_isolation_verified":False,
            "complete_descendant_process_coverage":False,"event_delivery_complete":False}

class ClassifierTests(unittest.TestCase):
    def setUp(self):
        self.before=shot("before",{H("a"):ent(1),H("b"):ent(2)})
        self.after=shot("after",{H("a"):ent(4),H("b"):ent(3),H("c"):ent(1)})
        self.events=evidence()
    def go(self):return gate.classify(self.before,self.after,self.events)
    def invalid(self):
        with self.assertRaises(gate.InvalidEvidence):self.go()
    def test_one_unattributed_added(self):
        s=self.go()
        self.assertEqual(s["change_classification"]["added"]["no_4663_event"],1)
        self.assertEqual(s["change_classification"]["modified"]["facad_root_only"],2)
        self.assertEqual(s["changed_identity_without_any_observed_4663_count"],1)
        self.assertFalse(s["specific_process_cause_proven"])
    def test_warm_complete_but_not_isolation(self):
        del self.after["scopes"][SCOPE]["entries"][H("c")]
        s=self.go();self.assertEqual(s["changed_identity_without_any_observed_4663_count"],0)
        self.assertFalse(s["shared_app_storage_isolation_verified"])
    def test_other_pid_is_not_proven_child(self):
        self.events=evidence(other=[H("c")],desc=1)
        s=self.go();self.assertEqual(s["change_classification"]["added"]["other_pid_only"],1)
        self.assertFalse(s["non_root_events_are_proven_descendants"])
    def test_both_pid_classes(self):
        self.events=evidence(other=[H("a")])
        self.assertEqual(self.go()["change_classification"]["modified"]["both_pid_classes"],1)
    def test_deleted_kind(self):
        del self.after["scopes"][SCOPE]["entries"][H("b")]
        self.assertEqual(self.go()["change_classification"]["deleted"]["facad_root_only"],1)
    def test_no_change_no_clearance(self):
        self.after["scopes"][SCOPE]["entries"]=self.before["scopes"][SCOPE]["entries"].copy()
        self.assertFalse(self.go()["all_storage_roots_verified"])
    def test_missing_field(self):
        del self.events["other_pid_relative_key_hashes"];self.invalid()
    def test_unexpected_raw_identifier(self):
        self.events["RawFileName"]="should-not-be-in-manifest";self.invalid()
    def test_wrong_scope(self):
        self.events["selected_scope"]="outside";self.invalid()
    def test_mismatched_session(self):
        self.events["session_id"]="other";self.invalid()
    def test_invalid_hash(self):
        self.events["other_pid_relative_key_hashes"]=["literal-filename"];self.invalid()
    def test_duplicate_hash(self):
        self.events["other_pid_relative_key_hashes"]=[H("a"),H("a")];self.invalid()
    def test_negative_descendants(self):
        self.events["observed_descendant_pid_count"]=-1;self.invalid()
    def test_bool_descendants(self):
        self.events["observed_descendant_pid_count"]=True;self.invalid()
    def test_forged_flags(self):
        for key in ("clinical_edit_allowed","shared_app_storage_isolation_verified",
                    "complete_descendant_process_coverage","event_delivery_complete"):
            self.events=evidence();self.events[key]=True
            with self.subTest(key=key):self.invalid()
    def test_wrong_root(self):
        self.after["scopes"][SCOPE]["root_fingerprint"]=H("d");self.invalid()
    def test_failed_capture(self):
        self.before["scopes"][SCOPE]["capture_ok"]=False;self.invalid()
    def test_cli_only_aggregate(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for name,obj in (("before.json",self.before),("after.json",self.after),("event.json",self.events)):
                (root/name).write_text(json.dumps(obj))
            proc=subprocess.run([sys.executable,str(HERE/"facad_314_d3e4_unattributed_classification_gate.py"),
                 "--before",str(root/"before.json"),"--after",str(root/"after.json"),
                 "--event-keys",str(root/"event.json"),"--output",str(root/"out.json")],
                 capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            output=(root/"out.json").read_text()
            self.assertNotIn(H("a"),output)
            self.assertNotIn("test-001",output)
            self.assertIn("UNVERIFIED",proc.stdout)
if __name__=="__main__":unittest.main()
