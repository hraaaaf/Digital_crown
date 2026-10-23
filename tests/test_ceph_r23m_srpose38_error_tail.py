"""R23-M adversarial tests: scientific source locked, aggregate only, NO-GO."""
from __future__ import annotations

import copy
import json
import math
import unittest

from scripts.audit_ceph_r23l_aariz_point_families import (
    EVIDENCE, EvidenceMismatch, read_evidence,
)
from scripts.audit_ceph_r23m_srpose38_error_tail import (
    SCHEMA, inspect_aggregates, to_markdown,
)


class R23MErrorTailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.digests = read_evidence(EVIDENCE)
        cls.report = inspect_aggregates(cls.docs, cls.digests)

    def test_qualified_pairs_and_weighted_mean_not_fake_38(self):
        r = self.report
        self.assertEqual(r["schema"], SCHEMA)
        self.assertEqual(r["aggregate_compatible_landmarks"], 24)
        self.assertEqual(r["qualified_point_comparisons"], 3374)
        self.assertAlmostEqual(r["qualified_point_mean_error_mm"], 1.7701473825424257, places=9)
        self.assertTrue(r["not_comparable_directly_to_miccai38_mre"])
        self.assertEqual(len(r["per_landmark_aggregates"]), 24)

    def test_go_two_independent_device_maxima_and_tail_fraction(self):
        g = self.report["go_tail"]
        self.assertEqual(g["n"], 120)
        self.assertAlmostEqual(g["median_mm"], 1.2565492650734922)
        self.assertAlmostEqual(g["max_mm"], 154.90892736708983)
        self.assertEqual({v["device"] for v in g["two_independent_device_group_maxima_over_100mm"]},
                         {"ART Plus", "Hyperion X5"})
        self.assertAlmostEqual(g["two_observations_share_of_total_absolute_error"], .4388115477163984)
        self.assertAlmostEqual(g["descriptive_leave_two_out_mean_mm_NOT_ACCEPTANCE"], 2.9811835355448566)
        self.assertTrue(g["tail_concentration_is_not_causal_proof"])

    def test_no_false_requalification_or_threshold_tuning(self):
        r = self.report
        self.assertEqual(r["original_frozen_acceptance_decision"], "FAIL")
        self.assertFalse(r["clinical_release"])
        self.assertFalse(r["channel_swap_proven"])
        self.assertFalse(r["new_tuning_or_thresholds_authorized"])
        self.assertFalse(r["individual_expert_gt_available"])
        self.assertEqual(r["landmarks_with_mean_below_2_mm"], 14)
        self.assertEqual(r["landmarks_with_p95_at_most_2_mm"], 3)

    def test_source_byte_binding_warning_is_not_masked(self):
        r = self.report
        self.assertFalse(r["original_results_byte_binding_verified"])
        self.assertNotEqual(r["raw_results_sha256_embedded"],
                            r["raw_results_sha256_committed"])
        self.assertIn("MISMATCH", r["provenance_warning"])

    def test_aggregate_output_never_leaks_per_film_predictions(self):
        text = json.dumps(self.report) + to_markdown(self.report)
        for forbidden in ('"case_id"', '"coordinates"', '"predictions"', '"scores"',
                          '"raw_ann_info"', '"image_path"'):
            self.assertNotIn(forbidden, text)
        self.assertIn("CLINICAL NO-GO", to_markdown(self.report))

    def test_tampered_global_mean_rejected_by_device_crosscheck(self):
        bad = copy.deepcopy(self.docs)
        bad["results"]["landmarks"]["Go"]["error_mm"]["mean"] += 0.4
        with self.assertRaises(EvidenceMismatch):
            inspect_aggregates(bad, self.digests)

    def test_tampered_device_n_rejected(self):
        bad = copy.deepcopy(self.docs)
        bad["results"]["landmarks"]["N"]["by_device"]["ART Plus"]["n"] += 1
        with self.assertRaises(EvidenceMismatch):
            inspect_aggregates(bad, self.digests)

    def test_tampered_device_max_rejected(self):
        bad = copy.deepcopy(self.docs)
        bad["results"]["landmarks"]["Go"]["by_device"]["ART Plus"]["max"] = 10.0
        with self.assertRaises(EvidenceMismatch):
            inspect_aggregates(bad, self.digests)

    def test_non_finite_mean_rejected(self):
        bad = copy.deepcopy(self.docs)
        bad["results"]["landmarks"]["Go"]["error_mm"]["mean"] = math.inf
        with self.assertRaises(EvidenceMismatch):
            inspect_aggregates(bad, self.digests)

    def test_source_decision_change_rejected(self):
        bad = copy.deepcopy(self.docs)
        bad["acceptance"]["landmarks"][0]["decision"] = "PASS"
        with self.assertRaises(EvidenceMismatch):
            inspect_aggregates(bad, self.digests)


if __name__ == "__main__":
    unittest.main()
