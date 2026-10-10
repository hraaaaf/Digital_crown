"""D3E.21 two internal adversarial lenses: source truth and no false parity."""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
MOD=ROOT/"scripts/facad_314_d3e21_lab_protocol_gate.py"
MATRIX=ROOT/"docs/audits/FACAD_314_D3E21_ROBERT_DISPLAY_MATRIX.json"
spec=importlib.util.spec_from_file_location("lab",MOD)
lab=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
ORACLE_NAMES=["SNA","SNB","ANB","SNPog","NSBa","ML/NSL","NL/NSL","ML/NL",
              "InterIncisal","ILs/NSL","ILi/ML","Pog-NB"]
ORACLE_VALUES=["67,7","78,4","-10,7","80,8","126,8","33,9","4,5",
               "29,4","140,9","100,1","85,1","4,7"]
ORACLE_FLAGS=set(["license_verified","source_integrity_verified","offline_activation_verified","native_guest_isolation_verified","host_guest_management_isolated_verified","minimal_egress_approved","independent_privacy_review","independent_science_review","same_trace_dc_verified","dc_calibration_verified","construction_equivalence_verified","direct_numeric_export_verified","clinical_edit_allowed","real_ilexis_writer_proven","shared_app_storage_isolation_verified","converged","native_execution_authorized"])

class A_ObservedNotClinical(unittest.TestCase):
    def setUp(self):
        self.m=json.loads(MATRIX.read_text(encoding="utf-8"))
    def blocked(self):
        with self.assertRaises(lab.SourceBlocked):lab.check(self.m)
    def test_static_truth_is_not_parity(self):
        result=lab.check(self.m)
        self.assertEqual(result["count"],12)
        self.assertEqual(result["direct_comparisons"],0)
    def test_oracle_independent_of_mutable_gate(self):
        self.assertEqual([x[0] for x in lab.DISPLAY],ORACLE_NAMES)
        self.assertEqual([x[1] for x in lab.DISPLAY],ORACLE_VALUES)
        self.assertEqual(lab.UNPROVEN,ORACLE_FLAGS)
    def test_forged_value(self):
        self.m["rows"][0]["value"]="82,0"
        self.blocked()
    def test_row_missing(self):
        self.m["rows"].pop()
        self.blocked()
    def test_row_swapped(self):
        self.m["rows"][0],self.m["rows"][1]=self.m["rows"][1],self.m["rows"][0]
        self.blocked()
    def test_unit_mismatch(self):
        self.m["rows"][0]["unit"]="mm"
        self.blocked()
    def test_candidate_forgery(self):
        self.m["rows"][5]["dc_candidate"]="M_IMPA_GOME_DEG_V1"
        self.blocked()
    def test_same_trace_forgery(self):
        self.m["rows"][0]["parity_status"]="OBSERVED_MATCH"
        self.blocked()
    def test_identity_forgery(self):
        self.m["rows"][0]["identity_status"]="PROVEN"
        self.blocked()
    def test_unknown_private_field(self):
        self.m["patient_path"]="hidden"
        self.blocked()
    def test_source_run_forgery(self):
        self.m["source_run_id"]+=1
        self.blocked()
    def test_type_confusion_false_zero(self):
        self.m["clinical_edit_allowed"]=0
        self.blocked()
    def test_duplicate_json_key(self):
        with self.assertRaises(lab.SourceBlocked):
            lab.unique([("case_alias","A"),("case_alias","B")])
    def test_cli_never_leaks_reference_numbers(self):
        p=subprocess.run([sys.executable,str(MOD)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn("D3E21_OBSERVED_UI_ROWS=12",p.stdout)
        self.assertIn("D3E21_SAME_TRACE_COMPARISONS=0",p.stdout)
        self.assertIn("D3E21_DIRECT_PARITY_PROVEN=false",p.stdout)
        self.assertNotIn("67,7",p.stdout)

class B_SyntheticComparatorBoundary(unittest.TestCase):
    def cmp(self,a,b,u1,u2,t,origin="SYNTHETIC_ONLY"):
        return lab.synthetic_compare(a,b,u1,u2,t,origin)
    def test_exact_synthetic_match(self):
        self.assertEqual(self.cmp("32.1","32.1","degree","degree","0"),"SYNTHETIC_MATCH")
    def test_synthetic_tolerance(self):
        self.assertEqual(self.cmp("32.01","32.06","degree","degree","0.05"),"SYNTHETIC_MATCH")
    def test_synthetic_mismatch(self):
        self.assertEqual(self.cmp("32.01","32.07","degree","degree","0.05"),"SYNTHETIC_DIFFERENT")
    def test_unit_mix(self):
        self.assertEqual(self.cmp("1","1","mm","degree","0"),"SYNTHETIC_NOT_COMPARABLE")
    def test_real_facad_origin_blocked(self):
        with self.assertRaises(lab.SourceBlocked):self.cmp("1","1","mm","mm","0",origin="FACAD")
    def test_nan_blocked(self):
        with self.assertRaises(lab.SourceBlocked):self.cmp("NaN","1","mm","mm","0")
    def test_float_blocked(self):
        with self.assertRaises(lab.SourceBlocked):self.cmp(1.0,"1","mm","mm","0")
    def test_negative_tolerance(self):
        with self.assertRaises(lab.SourceBlocked):self.cmp("1","1","mm","mm","-0.5")
    def test_extreme_tolerance(self):
        with self.assertRaises(lab.SourceBlocked):self.cmp("1","1","mm","mm","100")
    def test_flags_are_always_false(self):
        self.assertEqual(set(k for k,v in json.loads(MATRIX.read_text()).items()
                             if type(v) is bool),ORACLE_FLAGS)
def _one(flag):
    def test(self):
        m=json.loads(MATRIX.read_text(encoding="utf-8"))
        m[flag]=True
        with self.assertRaises(lab.SourceBlocked):lab.check(m)
    return test
for flag in sorted(ORACLE_FLAGS):
    setattr(A_ObservedNotClinical,"test_claim_forgery_"+flag,_one(flag))

if __name__=="__main__":
    unittest.main()
