"""Fictional, path-free D3 cold/warm research verdict tests; no Facad launch."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0,str(HERE))
from facad_314_d3_cold_warm_verdict_gate import (classify, ResearchEvidenceError)


def verdict(session, added=0, modified=0, deleted=0, scope="facad_ilexis_roaming_settings"):
    changes=(
        [{"scope":scope,"change":"ADDED"} for _ in range(added)] +
        [{"scope":scope,"change":"MODIFIED"} for _ in range(modified)] +
        [{"scope":scope,"change":"DELETED"} for _ in range(deleted)]
    )
    return {
        "capture_session_id":session,
        "monitored_scope_count":10,
        "observed_change_count":len(changes),
        "observed_changes":changes,
        "verdict":("BLOCKED_OBSERVED_STORAGE_DRIFT" if changes else
                   "INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT"),
        "d3_isolation_verified":False,
        "clinical_edit_allowed":False,
    }


class D3ColdWarmResearchTests(unittest.TestCase):
    def setUp(self):
        self.cold=verdict("synthetic-cold",added=1,modified=2)
        self.warm=verdict("synthetic-warm")

    def test_cold_only_still_blocked(self):
        result=classify(self.cold,self.warm)
        self.assertEqual(result["classification"],"COLD_ONLY_OBSERVED_DRIFT")
        self.assertEqual(result["verdict"],"BLOCKED_OBSERVED_STORAGE_DRIFT")
        self.assertEqual(result["cold_count"],3)
        self.assertEqual(result["warm_count"],0)
        self.assertIs(result["facad_process_write_path_attribution"],False)
        self.assertIs(result["patient_data_root_verified"],False)
        self.assertIs(result["d3_isolation_verified"],False)

    def test_repeated_drift_requires_block(self):
        self.warm=verdict("synthetic-warm",modified=1)
        r=classify(self.cold,self.warm)
        self.assertEqual(r["classification"],"REPEATED_OBSERVED_DRIFT")
        self.assertEqual(r["verdict"],"BLOCKED_OBSERVED_STORAGE_DRIFT")

    def test_warm_only_drift_requires_block(self):
        r=classify(verdict("synthetic-cold"),verdict("synthetic-warm",added=1))
        self.assertEqual(r["classification"],"WARM_ONLY_OBSERVED_DRIFT")
        self.assertFalse(r["clinical_edit_allowed"])

    def test_both_zero_inconclusive_not_verified(self):
        r=classify(verdict("synthetic-cold"),verdict("synthetic-warm"))
        self.assertEqual(r["verdict"],"INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT")
        self.assertIs(r["d3_isolation_verified"],False)

    def test_same_capture_session_rejected(self):
        self.warm["capture_session_id"]="synthetic-cold"
        with self.assertRaises(ResearchEvidenceError):classify(self.cold,self.warm)

    def test_fake_green_with_drift_rejected(self):
        self.cold["verdict"]="INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT"
        with self.assertRaises(ResearchEvidenceError):classify(self.cold,self.warm)

    def test_missing_scope_rejected(self):
        self.warm["monitored_scope_count"]=9
        with self.assertRaises(ResearchEvidenceError):classify(self.cold,self.warm)

    def test_unknown_scope_rejected(self):
        self.cold["observed_changes"][0]["scope"]="C:\\Sensitive\\Patient"
        with self.assertRaises(ResearchEvidenceError):classify(self.cold,self.warm)

    def test_filename_hash_or_raw_name_fields_rejected(self):
        self.cold["observed_changes"][0]["entry_key_sha256"]="a"*64
        with self.assertRaises(ResearchEvidenceError):classify(self.cold,self.warm)

    def test_forged_clinical_approval_rejected(self):
        self.cold["d3_isolation_verified"]=True
        with self.assertRaises(ResearchEvidenceError):classify(self.cold,self.warm)

    def test_forged_count_rejected(self):
        self.cold["observed_change_count"]=0
        with self.assertRaises(ResearchEvidenceError):classify(self.cold,self.warm)

    def test_invalid_type_and_root_entries_rejected(self):
        self.cold["observed_changes"][0]["change"]="ROOT_APPEARED_OR_DISAPPEARED"
        self.cold["observed_changes"][0]["entries"]=42
        with self.assertRaises(ResearchEvidenceError):classify(self.cold,self.warm)

    def test_cli_cold_drift_never_success_or_path_disclosure(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"cold.json").write_text(json.dumps(self.cold),encoding="utf8")
            (root/"warm.json").write_text(json.dumps(self.warm),encoding="utf8")
            r=subprocess.run([sys.executable,str(HERE/"facad_314_d3_cold_warm_verdict_gate.py"),
                "--cold",str(root/"cold.json"),"--warm",str(root/"warm.json"),
                "--output",str(root/"result.json")],text=True,capture_output=True)
            data=json.loads((root/"result.json").read_text())
        self.assertEqual(r.returncode,1)
        self.assertIn("D3_COLD_OBSERVED_CHANGES=3",r.stdout)
        self.assertIn("D3_WARM_OBSERVED_CHANGES=0",r.stdout)
        self.assertNotIn("synthetic-cold",json.dumps(data)+r.stdout)
        self.assertNotIn("facad_ilexis_roaming_settings",json.dumps(data)+r.stdout)
        self.assertIs(data["clinical_edit_allowed"],False)

    def test_cli_clean_is_exit3_not_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"cold.json").write_text(json.dumps(verdict("cold")),encoding="utf8")
            (root/"warm.json").write_text(json.dumps(verdict("warm")),encoding="utf8")
            r=subprocess.run([sys.executable,str(HERE/"facad_314_d3_cold_warm_verdict_gate.py"),
                "--cold",str(root/"cold.json"),"--warm",str(root/"warm.json"),
                "--output",str(root/"result.json")],text=True,capture_output=True)
        self.assertEqual(r.returncode,3)

    def test_cli_invalid_never_echoes_input(self):
        self.warm["unexpected_patient_path"]="C:\\Sensitive\\Private"
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"cold.json").write_text(json.dumps(self.cold),encoding="utf8")
            (root/"warm.json").write_text(json.dumps(self.warm),encoding="utf8")
            r=subprocess.run([sys.executable,str(HERE/"facad_314_d3_cold_warm_verdict_gate.py"),
                "--cold",str(root/"cold.json"),"--warm",str(root/"warm.json"),
                "--output",str(root/"result.json")],text=True,capture_output=True)
            data=json.loads((root/"result.json").read_text())
        self.assertEqual(r.returncode,2)
        self.assertEqual(data["verdict"],"BLOCKED_INVALID_OR_INCOMPLETE_EVIDENCE")
        self.assertNotIn("Sensitive",json.dumps(data)+r.stdout)


if __name__=="__main__":
    unittest.main()
