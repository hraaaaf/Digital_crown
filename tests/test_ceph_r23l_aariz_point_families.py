"""R23-L: strict frozen-evidence audit tests; real archived data, NO model rerun."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_ceph_r23l_aariz_point_families import (
    EVIDENCE, FAMILIES, EXPECTED_MODEL_SHA, ROOT,
    analyze, digest, run, source_mapping, validate_archived_evidence,
)

def sources():
    return (
        json.loads((EVIDENCE/"cephalo_vnext_lot04_acceptance_record.json").read_text()),
        json.loads((EVIDENCE/"cephalo_vnext_lot04_results.json").read_text()),
        json.loads((EVIDENCE/"cephalo_vnext_lot04_acceptance_record_detail.json").read_text()),
        source_mapping(ROOT/"scripts/run_cephalo_vnext_lot04_benchmark.py"),
    )

class FrozenEvidenceTests(unittest.TestCase):
    def test_archived_source_150_cases_has_38_model_predictions_but_no_expert_xy(self):
        a,b,d,m=sources()
        validate_archived_evidence(a,b,d,m)
        self.assertEqual(len(b["predictions"]),150)
        self.assertEqual({len(x["coordinates"]) for x in b["predictions"]},{38})
        self.assertEqual({len(x["scores"]) for x in b["predictions"]},{38})
        self.assertEqual(len(a["landmarks"]),24)
        self.assertEqual(a["overall_decision"],"FAIL")
        self.assertEqual(a["candidate_model_sha256"],EXPECTED_MODEL_SHA)

    def test_clinically_constrained_family_counts_frozen_no_result_promotion(self):
        a,b,d,m=sources()
        report=analyze(a,b,source_digest=d["source_results_sha256"],manifest_sha=a["manifest_sha256"])
        self.assertEqual({k:(v["total"],v["passed"],v["failed"]) for k,v in report["families"].items()},
                         {"osseux":(14,1,13),"dentaire":(4,0,4),"cutane":(6,0,6)})
        self.assertEqual(report["total_fail"],23)
        self.assertEqual(report["total_pass"],1)
        self.assertEqual(len(report["downstream_angle_results_not_detector_outputs"]),9)
        self.assertFalse(report["evidence_limits"]["automated_swap_detection_possible"])
        self.assertFalse(report["evidence_limits"]["clinical_release"])
        self.assertFalse(report["evidence_limits"]["anatomical_channel_identity_source_verified"])
        self.assertEqual(report["verdict"],"TECHNICAL_DIAGNOSTIC__MAPPING_HYPOTHESIS_OPEN__CLINICAL_NO_GO")
        self.assertEqual(report["other_model_channels_without_Aariz_reference"],14)

    def test_audit_generates_aggregate_only_no_case_predictions_or_personal_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=run(Path(tmp))
            a=json.loads((Path(tmp)/"report.json").read_text())
            self.assertEqual(a["total_fail"],23)
            self.assertEqual(r["total_pass"],1)
            self.assertFalse(a["evidence_limits"]["archived_detail_sha256_matches_current_results_bytes"])
            self.assertFalse(a["evidence_limits"]["archival_chain_of_custody_verified"])
            self.assertEqual(a["verdict"],"TECHNICAL_DIAGNOSTIC__ARCHIVE_DIGEST_DRIFT_OPEN__CLINICAL_NO_GO")
            report=(Path(tmp)/"report.json").read_text()
            # Aggregates contain no per-case IDs or original coordinates.
            b=json.loads((EVIDENCE/"cephalo_vnext_lot04_results.json").read_text())
            self.assertNotIn(b["predictions"][0]["case_id"],report)
            self.assertNotIn('"coordinates"',report)
            self.assertIn("Aariz", (Path(tmp)/"README.md").read_text())

    def test_scientific_record_stays_fail_and_code_drift_is_rejected(self):
        a,b,d,m=sources()
        changed=copy.deepcopy(a);changed["overall_decision"]="PASS"
        with self.assertRaisesRegex(ValueError,"Historical FAIL"):
            validate_archived_evidence(changed,b,d,m)
        changed=copy.deepcopy(a);changed["candidate_model_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Candidate/model drift"):
            validate_archived_evidence(changed,b,d,m)
        wrong=dict(m);wrong["A"]="S"
        with self.assertRaisesRegex(ValueError,"Incorrect overlap"):
            validate_archived_evidence(a,b,d,wrong)

    def test_missing_casewise_expert_labels_not_faked(self):
        a,b,d,m=sources()
        changed=copy.deepcopy(b)
        changed["predictions"][0]["reference_coordinates"]={"N":[0,0]}
        with self.assertRaisesRegex(ValueError,"evidence boundary"):
            validate_archived_evidence(a,changed,d,m)
        changed=copy.deepcopy(b);changed["predictions"][0]["coordinates"].pop("S")
        with self.assertRaisesRegex(ValueError,"38 model-output"):
            validate_archived_evidence(a,changed,d,m)

    def test_device_small_sample_flags_and_all_24_are_unique(self):
        a,b,d,m=sources()
        r=analyze(a,b,source_digest=d["source_results_sha256"],manifest_sha=a["manifest_sha256"])
        names=[p["id"] for g in r["families"].values() for p in g["points"]]
        self.assertEqual(len(names),len(set(names)))
        self.assertEqual(len(names),24)
        n=next(x for x in r["families"]["osseux"]["points"] if x["id"]=="N")
        self.assertGreater(n["p95_mm"],7)
        self.assertGreater(n["observed_to_human_p95_ratio"],3)
        self.assertTrue(any(x["small_sample_lt_20"] for x in n["devices"]))

if __name__=="__main__":
    unittest.main()
