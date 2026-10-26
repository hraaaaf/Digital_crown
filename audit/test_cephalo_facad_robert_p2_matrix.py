"""Synthetic-only guards for complete FACAD 32F+13F 45-occurrence P2 matrix."""
from __future__ import annotations

import copy
import json
import unittest

from audit import cephalo_facad_robert_p2_geometry_gate as p2
from audit import cephalo_facad_robert_p2_matrix as matrix
from audit import test_cephalo_facad_robert_p2_geometry_gate as synthetic

ATLAS = json.loads(p2.ATLAS.read_text(encoding="utf-8"))
FINAL = p2.FACAD_FINAL_SEVEN.read_text(encoding="utf-8")
ROSTER = json.loads(matrix.ROSTER_PATH.read_text(encoding="utf-8"))


def source():
    fixture = synthetic.synthetic_agreeing_case()
    result = p2.assess_p2(fixture, ATLAS, FINAL)
    return fixture, result


class Full45FactorMatrixTests(unittest.TestCase):
    def test_all_45_factor_occurrences_and_14_observations_accounted(self):
        fixture, p2_result = source()
        x = matrix.matrix(fixture, ROSTER, p2_result)
        self.assertEqual(len(x["rows"]), 45)
        self.assertEqual(x["roster_observed"], 45)
        self.assertEqual(x["facad_numeric_observations"], 14)
        self.assertEqual(x["geometric_candidate_occurrences_non_clinical"], 5)
        self.assertEqual(x["numeric_blocked_occurrences"], 9)
        self.assertEqual(x["numeric_unobserved_occurrences"], 31)
        self.assertEqual(x["cross_product_clinical_parities"], 0)
        self.assertTrue(x["clinical_no_go"])

    def test_vendor_rows_preserve_two_distinct_profiles(self):
        fixture, p2_result = source()
        rows = matrix.matrix(fixture, ROSTER, p2_result)["rows"]
        self.assertEqual([r["order"] for r in rows[:32]], list(range(1,33)))
        self.assertEqual([r["order"] for r in rows[32:]], list(range(1,14)))
        self.assertEqual({r["profile"] for r in rows[:32]}, {"32F"})
        self.assertEqual({r["profile"] for r in rows[32:]}, {"13F"})

    def test_specific_facad_cone_and_upper_lip_never_promoted(self):
        fixture, p2_result = source()
        rows = matrix.matrix(fixture, ROSTER, p2_result)["rows"]
        cone = next(r for r in rows if r["facad_label"] == "Facial cone angle")
        upper = next(r for r in rows if r["facad_label"] == "Upper lip len")
        self.assertEqual(cone["numeric_evidence"], "BLOCKED_VENDOR_GO_ME_VS_DC_RICKETTS_MP")
        self.assertEqual(upper["numeric_evidence"], "BLOCKED_HARD_ANATOMICAL_IDENTITY_MISMATCH")
        self.assertTrue(all(r["vendor_alias_policy"] == "NO_DIRECT_CLINICAL_ALIAS"
                            for r in (cone, upper)))
        self.assertTrue(all(r["clinical_parity_validated"] is False for r in rows))

    def test_all_seven_vendor_variants_protected_even_without_values(self):
        fixture, p2_result = source()
        rows = matrix.matrix(fixture, ROSTER, p2_result)["rows"]
        blocked = [r for r in rows if r["facad_label"] in matrix.CONFLICTING_VENDOR]
        self.assertEqual({r["facad_label"] for r in blocked}, matrix.CONFLICTING_VENDOR)
        self.assertTrue(all(r["vendor_alias_policy"] == "NO_DIRECT_CLINICAL_ALIAS"
                            for r in blocked))

    def test_refuses_deleted_factor_definition(self):
        fixture, p2_result = source()
        roster = copy.deepcopy(ROSTER)
        roster["profile_rosters"][0]["ordered_factor_labels"].pop()
        with self.assertRaisesRegex(ValueError, "expected number"):
            matrix.matrix(fixture, roster, p2_result)

    def test_refuses_reordering_factor_without_identity_proof(self):
        fixture, p2_result = source()
        roster = copy.deepcopy(ROSTER)
        roster["profile_rosters"][0]["ordered_factor_labels"][0]["order"] = 11
        with self.assertRaisesRegex(ValueError, "factor ordering"):
            matrix.matrix(fixture, roster, p2_result)

    def test_refuses_canonical_parity_promotion(self):
        fixture, p2_result = source()
        bad = copy.deepcopy(p2_result)
        bad["cross_product_clinical_parities"] = 1
        with self.assertRaisesRegex(ValueError, "prerequisite"):
            matrix.matrix(fixture, ROSTER, bad)

    def test_refuses_missing_numerically_observed_facad_factor(self):
        fixture, p2_result = source()
        roster = copy.deepcopy(ROSTER)
        roster["profile_rosters"][0]["ordered_factor_labels"][11]["facad_label"] = "Fake Factor"
        with self.assertRaisesRegex(ValueError, "missing in editor roster"):
            matrix.matrix(fixture, roster, p2_result)


if __name__ == "__main__":
    unittest.main()
