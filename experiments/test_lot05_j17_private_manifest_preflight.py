"""J17 synthetic-only tests, no real private manifest."""
import copy,hashlib,importlib.util
from pathlib import Path
import unittest
p=Path(__file__).with_name("lot05_j17_private_manifest_preflight.py")
spec=importlib.util.spec_from_file_location("j17_test",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture():
    return {"schema":m.SCHEMA,"source_commit":m.PIN,"source_reviewed_cases":28,
            "source_reviewed_pairs":6,"source_manifest_sha256":hashlib.sha256(b"synthetic").hexdigest(),
            "active_permanent":[{"dentition":"permanent","clinical_status":"confirmed",
               "staging_status":"PENDING_PRIVATE_GEOMETRY_AND_COLLISION_QA",
               "decision":{"case":1,"split":"train","stem":"1001","from_fdi":"32",
                           "to_fdi":"31","expected_bbox":[.5,.5,.1,.1]}}],
            "primary_out_of_ontology":[{"dentition":"primary","clinical_status":"tentative",
               "decision":{"clinician_fdi":"63"}}],
            **{k:[] for k in m.PERMANENT_KEYS if k not in ("active_permanent","primary_out_of_ontology")},
            "release_gates":{k:False for k in m.GATES},
            "staging_status":"BLOCKED_NO_SOURCE_OR_LABEL_WRITES"}
class SyntheticJ17(unittest.TestCase):
    def test_valid_but_never_staged(self):
        r=m.check(fixture(),b"synthetic");self.assertTrue(r["source_hash_verified"]);self.assertFalse(r["staging_performed"])
    def test_hash_mismatch(self):
        with self.assertRaises(m.PrivatePreflightError):m.check(fixture(),b"wrong")
    def test_no_release_gate_true(self):
        d=fixture();d["release_gates"]["staging_authorized"]=True
        with self.assertRaises(m.PrivatePreflightError):m.check(d)
    def test_primary_never_active(self):
        d=fixture();d["active_permanent"][0]["decision"]["to_fdi"]="63"
        with self.assertRaises(ValueError):m.check(d)
    def test_tentative_never_active(self):
        d=fixture();d["active_permanent"][0]["clinical_status"]="tentative"
        with self.assertRaises(m.PrivatePreflightError):m.check(d)
    def test_no_duplicate_witness(self):
        d=fixture();d["active_permanent"]*=2
        with self.assertRaises(m.PrivatePreflightError):m.check(d)
    def test_no_bad_bbox(self):
        d=fixture();d["active_permanent"][0]["decision"]["expected_bbox"]=[.5,.5,0,.1]
        with self.assertRaises(m.PrivatePreflightError):m.check(d)
    def test_no_staging_status_override(self):
        d=fixture();d["staging_status"]="READY"
        with self.assertRaises(m.PrivatePreflightError):m.check(d)
    def test_primary_code_must_be_primary(self):
        d=fixture();d["primary_out_of_ontology"][0]["decision"]["clinician_fdi"]="23"
        with self.assertRaises(m.PrivatePreflightError):m.check(d)
    def test_bad_source_pin(self):
        d=fixture();d["source_commit"]="other"
        with self.assertRaises(m.PrivatePreflightError):m.check(d)
if __name__=="__main__":unittest.main()
