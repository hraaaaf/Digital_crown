"""R23-L — no-fabrication and no-causal-overclaim tests on frozen LOT04."""
from __future__ import annotations
from copy import deepcopy
import unittest
from scripts.audit_ceph_r23l_aariz_point_families import (
    FAMILY, MODEL_SHA256, EvidenceMismatch, analyze, read_evidence, EVIDENCE, to_markdown
)


class FrozenAarizFamiliesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs,cls.digests=read_evidence(EVIDENCE)

    def test_exact_hash_locked_150_film_baseline_and_24_landmark_groups(self):
        report=analyze(self.docs,self.digests)
        self.assertEqual(report["model_sha256"],MODEL_SHA256)
        self.assertEqual(report["acceptance_cases"],150)
        self.assertEqual(report["total_pass"],1)
        self.assertEqual(report["total_fail"],23)
        self.assertEqual(report["landmark_counts"]["OSSEOUS"]["pass"],1)
        self.assertEqual(report["landmark_counts"]["OSSEOUS"]["fail"],13)
        self.assertEqual(report["landmark_counts"]["DENTAL"]["fail"],4)
        self.assertEqual(report["landmark_counts"]["SOFT_TISSUE"]["fail"],6)
        self.assertEqual(len(report["landmarks"]),24)
        self.assertEqual({x["id"] for x in report["landmarks"]},set(sum((list(x) for x in FAMILY.values()),[])))

    def test_n_a_pns_skin_breakout_with_pinned_reference_ratios(self):
        report=analyze(self.docs,self.digests)
        indexed={x["id"]:x for x in report["landmarks"]}
        for point,lower in [("N",3.9),("A",3.2),("PNS",5.2),("Pog_soft",6.0)]:
            self.assertGreater(indexed[point]["p95_ratio"],lower)
        self.assertEqual(indexed["Me"]["decision"],"PASS")
        self.assertEqual(indexed["Pog_soft"]["family"],"SOFT_TISSUE")
        self.assertEqual(indexed["L1_apex"]["family"],"DENTAL")
        self.assertTrue(all(x["n_reference_eligible"]<=150 for x in report["landmarks"]))

    def test_never_claim_38_points_or_prove_mapping_swap(self):
        report=analyze(self.docs,self.digests)
        self.assertFalse(report["channel_swap_proven"])
        self.assertFalse(report["channel_relabel_authorized"])
        self.assertFalse(report["has_individual_paired_expert_coordinates"])
        self.assertFalse(report["clinical_release"])
        self.assertEqual(report["acceptance_decision_original"],"FAIL")
        md=to_markdown(report)
        self.assertIn("not establish",md)
        self.assertIn("NO-GO",md)
        self.assertIn("24",md)

    def test_modified_model_sha_is_rejected_not_reinterpreted(self):
        docs=deepcopy(self.docs)
        docs["manifest"]["candidate"]["model_sha256"]="f"*64
        with self.assertRaisesRegex(EvidenceMismatch,"candidate hash drifted"):
            analyze(docs,self.digests)

    def test_source_results_sha_drift_refuses_metrics(self):
        digest={**self.digests,"results":"0"*64}
        with self.assertRaisesRegex(EvidenceMismatch,"not linked"):
            analyze(self.docs,digest)

    def test_coverage_missing_and_permutation_not_implicitly_accepted(self):
        docs=deepcopy(self.docs)
        docs["acceptance"]["landmarks"]=docs["acceptance"]["landmarks"][:-1]
        with self.assertRaisesRegex(EvidenceMismatch,"24-landmark scope"):
            analyze(docs,self.digests)

    def test_source_decision_tamper_is_detected(self):
        docs=deepcopy(self.docs)
        next(x for x in docs["acceptance"]["landmarks"] if x["landmark_id"]=="N")["decision"]="PASS"
        with self.assertRaisesRegex(EvidenceMismatch,"inconsistent"):
            analyze(docs,self.digests)

    def test_device_data_is_descriptive_only(self):
        report=analyze(self.docs,self.digests)
        point=next(x for x in report["landmarks"] if x["id"]=="N")
        self.assertGreaterEqual(len(point["by_device"]),3)
        self.assertTrue(all(x["exploratory_only"] for x in point["by_device"]))
        self.assertTrue(any(x["small_stratum"] for x in point["by_device"]))

    def test_duplicate_or_missing_acceptance_predictions_fails_closed(self):
        docs=deepcopy(self.docs)
        docs["results"]["predictions"].pop()
        with self.assertRaisesRegex(EvidenceMismatch,"predictions not complete"):
            analyze(docs,self.digests)


if __name__=="__main__":
    unittest.main()
