"""Synthetic-only FACAD P2 mathematical robustness and clinical gating tests."""
from __future__ import annotations

import copy
import json
import math
import unittest
from pathlib import Path

from audit import cephalo_facad_robert_p2_geometry_gate as p2
from audit import test_cephalo_facad_robert_public_ci as old_tests

ATLAS = json.loads(p2.ATLAS.read_text(encoding="utf-8"))
FINAL_SEVEN = p2.FACAD_FINAL_SEVEN.read_text(encoding="utf-8")


def synthetic_agreeing_case():
    fixture = old_tests.fake_case()
    points = {key: tuple(v) for key, v in fixture["points_mm"].items()}
    values = p2.public.dc.raw_helpers(points)
    for factor, val in values.items():
        rounded = round(val, 1)
        fixture["facad_values"]["32F"][factor]["value"] = rounded
        if factor in fixture["facad_values"]["13F"]:
            fixture["facad_values"]["13F"][factor]["value"] = rounded
    return fixture


class P2ScientificFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.fixture = synthetic_agreeing_case()

    def test_three_consistent_and_facad_facial_cone_always_forbidden(self):
        result = p2.assess_p2(self.fixture, ATLAS, FINAL_SEVEN)
        self.assertEqual(result["candidate_quantization_consistent"], 3)
        self.assertEqual(result["known_anatomical_alias_conflicts"], 1)
        self.assertEqual(result["cross_product_clinical_parities"], 0)
        self.assertFalse(result["full_runtime_adapter_validated"])
        self.assertTrue(result["clinical_no_go"])
        self.assertEqual(
            [x["factor"] for x in result["rows"][:3]],
            ["ILi/A-Pog", "ILs/A-Pog", "InterIncisal"],
        )
        self.assertEqual(result["rows"][3]["status"],
                         "BLOCKED_VENDOR_GO_ME_VS_DC_RICKETTS_MP")

    def test_synthetic_interincisal_calls_versioned_craniom_function(self):
        p = {name: tuple(v) for name, v in self.fixture["points_mm"].items()}
        expected = p2.public.dc.ca.craniom_interincisal_deg_v1(
            p["Isa"], p["Is"], p["Iia"], p["Ii"])
        self.assertAlmostEqual(p2.public.dc.raw_helpers(p)["InterIncisal"],
                               expected, places=10)

    def test_conservative_error_bound_is_positive_and_metric(self):
        p = {name: tuple(v) for name, v in self.fixture["points_mm"].items()}
        for label in p2.CANDIDATE_METHODS:
            self.assertTrue(0 < p2.angle_rounding_bound_deg(p, label) < 15)

    def test_bound_scales_up_with_coarser_coordinate_precision(self):
        p = {name: tuple(v) for name, v in self.fixture["points_mm"].items()}
        fine = p2.angle_rounding_bound_deg(p, "InterIncisal", 0.01)
        coarse = p2.angle_rounding_bound_deg(p, "InterIncisal", 0.1)
        self.assertGreater(coarse, fine)
        self.assertGreater(fine, 0.05)

    def test_0_1_mm_rounding_error_not_silently_treated_as_pixels(self):
        # The 0.038853-mm/pixel calibration ratio is not the precision
        # of the exported millimetre coordinates.
        self.fixture["coordinate_rounding_mm"] = 0.038853
        with self.assertRaisesRegex(ValueError, "unverified frame"):
            p2.assess_p2(self.fixture, ATLAS, FINAL_SEVEN)

    def test_unknown_geometry_has_no_bound(self):
        with self.assertRaisesRegex(ValueError, "audited vector"):
            p2.angle_rounding_bound_deg({}, "Convexity")

    def test_zero_or_degenerate_segment_fails_closed(self):
        p = {name: tuple(v) for name, v in self.fixture["points_mm"].items()}
        p["Iia"] = p["Ii"]
        with self.assertRaisesRegex(ValueError, "rounding dominates"):
            p2.angle_rounding_bound_deg(p, "ILi/A-Pog")

    def test_candidate_numeric_mismatch_larger_than_bound_rejected(self):
        self.fixture["facad_values"]["32F"]["ILs/A-Pog"]["value"] += 20
        with self.assertRaisesRegex(ValueError, "outside maximal rounding"):
            p2.assess_p2(self.fixture, ATLAS, FINAL_SEVEN)

    def test_identical_generic_facial_cone_still_not_canonical(self):
        p = {name: tuple(v) for name, v in self.fixture["points_mm"].items()}
        actual = p2.public.dc.raw_helpers(p)["Facial cone angle"]
        self.fixture["facad_values"]["32F"]["Facial cone angle"]["value"] = actual
        result = p2.assess_p2(self.fixture, ATLAS, FINAL_SEVEN)
        self.assertEqual(result["rows"][3]["status"],
                         "BLOCKED_VENDOR_GO_ME_VS_DC_RICKETTS_MP")
        self.assertEqual(result["cross_product_clinical_parities"], 0)

    def test_lost_canonical_taper_gate_rejects_source_drift(self):
        atlas = copy.deepcopy(ATLAS)
        for m in atlas["measurements"]:
            if m.get("measurement_id") == "M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1":
                m["gate"] = "ALLOW_GENERIC_GO_ME"
        with self.assertRaisesRegex(ValueError, "taper gate changed"):
            p2.assess_p2(self.fixture, atlas, FINAL_SEVEN)

    def test_lost_source_lock_final_seven_doc_rejects_source_drift(self):
        with self.assertRaisesRegex(ValueError, "conflict unverified"):
            p2.assess_p2(self.fixture, ATLAS, "Facial cone angle looks similar")

    def test_missing_executable_dc_measurement_rejects_source_drift(self):
        atlas = copy.deepcopy(ATLAS)
        for m in atlas["measurements"]:
            if m.get("measurement_id") == "M_INTERINCISAL_DEG_V1":
                m["state"] = "BLOCKED"
        with self.assertRaisesRegex(ValueError, "executable canonical"):
            p2.assess_p2(self.fixture, atlas, FINAL_SEVEN)

    def test_reflection_and_translation_preserve_angles_not_crosswalk(self):
        p = self.fixture["points_mm"]
        moved = copy.deepcopy(self.fixture)
        moved["points_mm"] = {k: [-x+173, y+29] for k, (x, y) in p.items()}
        orig = p2.assess_p2(self.fixture, ATLAS, FINAL_SEVEN)
        mir = p2.assess_p2(moved, ATLAS, FINAL_SEVEN)
        for a, b in zip(orig["rows"], mir["rows"]):
            self.assertAlmostEqual(a["dc_versioned_geometry_deg"],
                                   b["dc_versioned_geometry_deg"], places=5)
        self.assertEqual(mir["cross_product_clinical_parities"], 0)


if __name__ == "__main__":
    unittest.main()
