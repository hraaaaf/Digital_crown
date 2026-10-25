"""LOT05/J15 synthetic-only safety gate tests. No clinical source or manifests."""
import importlib.util
from pathlib import Path
import unittest

p=Path(__file__).with_name("lot05_j15_private_staging_plan.py")
spec=importlib.util.spec_from_file_location("j15_unit",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def sample():
    return {
        "source_pin":m.EXPECTED_SOURCE_PIN,
        "source_counts":m.EXPECTED_SPLITS.copy(),
        "active_permanent_proposals":4,
        "blocked_clinical_decisions":1,
        "unresolved_clinical_decisions":1,
        "collision_groups_pending":1,
        "exact_dedupe_pending":1,
        "originals_unchanged":True,
        "private_geometry_qa_passed":False,
        "private_staging_engine_integrated":False,
    }

class J15Synthetic(unittest.TestCase):
    def test_blocks_real_staging_by_default(self):
        r=m.plan_synthetic(sample())
        self.assertEqual(r["status"],"BLOCKED_NO_REAL_STAGING")
        self.assertFalse(r["private_corrected_dataset_created"])

    def test_rejects_private_sample_keys(self):
        s=sample();s["sample_id"]="SYNTHETIC"
        with self.assertRaises(m.J15Error):m.plan_synthetic(s)

    def test_rejects_private_bbox(self):
        s=sample();s["bbox"]=[.1,.2,.3,.4]
        with self.assertRaises(m.J15Error):m.plan_synthetic(s)

    def test_rejects_wrong_pin(self):
        s=sample();s["source_pin"]="untrusted"
        with self.assertRaises(m.J15Error):m.plan_synthetic(s)

    def test_rejects_changed_split(self):
        s=sample();s["source_counts"]["val"]=34
        with self.assertRaises(m.J15Error):m.plan_synthetic(s)

    def test_rejects_modified_originals(self):
        s=sample();s["originals_unchanged"]=False
        with self.assertRaises(m.J15Error):m.plan_synthetic(s)

    def test_rejects_negative_count(self):
        s=sample();s["collision_groups_pending"]=-1
        with self.assertRaises(m.J15Error):m.plan_synthetic(s)

    def test_rejects_bool_as_count(self):
        s=sample();s["active_permanent_proposals"]=True
        with self.assertRaises(m.J15Error):m.plan_synthetic(s)

    def test_primary_and_tentative_blockers(self):
        s=sample();s["collision_groups_pending"]=0
        r=m.plan_synthetic(s)
        self.assertIn("blocked_clinical_decisions",r["blockers"])
        self.assertIn("unresolved_clinical_decisions",r["blockers"])

    def test_private_engine_not_integrated(self):
        s=sample();s["blocked_clinical_decisions"]=0
        s["unresolved_clinical_decisions"]=0
        s["collision_groups_pending"]=0
        s["exact_dedupe_pending"]=0
        s["private_geometry_qa_passed"]=True
        r=m.plan_synthetic(s)
        self.assertIn("private_staging_engine_not_integrated",r["blockers"])

    def test_precheck_only_never_stages(self):
        s=sample()
        for k in ("blocked_clinical_decisions","unresolved_clinical_decisions",
                  "collision_groups_pending","exact_dedupe_pending"):
            s[k]=0
        s["private_geometry_qa_passed"]=True
        s["private_staging_engine_integrated"]=True
        r=m.plan_synthetic(s)
        self.assertEqual(r["status"],"PRECHECK_ONLY_NOT_STAGING")
        self.assertFalse(r["private_corrected_dataset_created"])
        self.assertFalse(r["clinical_training_allowed"])

    def test_ontology_gate_primary_stays_blocked(self):
        from lot05_j14_mixed_dentition_ontology_gate import gate_decision
        self.assertNotEqual(gate_decision({"fdi":"63","clinical_status":"confirmed"}),
                            "ELIGIBLE_FOR_LATER_PRIVATE_GEOMETRY_AND_COLLISION_QA")

if __name__=="__main__":
    unittest.main()
