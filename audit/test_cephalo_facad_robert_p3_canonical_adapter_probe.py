"""Public Robert P3 canonical V2 typed adapter readiness (NOT clinical parity)."""
from __future__ import annotations

import copy
import json
import unittest

from audit import cephalo_facad_robert_p3_canonical_adapter_probe as p3
from audit import cephalo_facad_robert_public_ci as pub

FIXTURE = json.loads(pub.FIXTURE.read_text(encoding="utf-8"))


class CanonicalV2ProvisionalCrosswalkTests(unittest.TestCase):
    def setUp(self):
        self.fixture = copy.deepcopy(FIXTURE)

    def test_real_canonical_v2_typed_adapter_executed_for_two_angles(self):
        result = p3.assess(self.fixture)
        self.assertEqual(result["status"], "P3_TYPED_CANONICAL_V2_TWO_ANGLES_EDUCATIONAL_ONLY")
        self.assertTrue(result["canonical_v2_typed_adapter_executed"])
        self.assertEqual(len(result["rows"]), 2)
        self.assertFalse(result["facad_operator_crosswalk_validated"])
        self.assertFalse(result["complete_analysis_runtime_executed"])
        self.assertEqual(result["clinical_parity_verified"], 0)
        self.assertTrue(result["clinical_no_go"])

    def test_real_v2_results_use_canonical_methods_not_aliases(self):
        rows = p3.assess(self.fixture)["rows"]
        self.assertEqual(
            {x["dc_canonical_method_id"] for x in rows},
            {"RICKETTS_L1_APOG_INCLINATION_CANONICAL_DEG_V2",
             "RICKETTS_U1_APOG_INCLINATION_CANONICAL_DEG_V2"}
        )
        self.assertTrue(all(not x["landmark_identity_proven"] and
                            not x["source_image_orientation_proven"] and
                            x["clinical_parity"] is False for x in rows))

    def test_production_craniom_interincisal_typed_construction_rounds_once(self):
        result = p3.assess(self.fixture)
        self.assertTrue(result["craniom_interincisal_typed_construction_executed"])
        self.assertFalse(result["complete_craniom_measurement_adapter_executed"])
        inter = result["craniom_interincisal_typed_construction"]
        self.assertEqual(inter["dc_versioned_construction_id"],
                         "CRANIOM_U1_L1_INTERINCISAL_V1")
        self.assertEqual(inter["canonical_measurement_id"], "M_INTERINCISAL_DEG_V1")
        self.assertEqual(inter["dc_craniom_typed_construction_deg"], 140.7)
        self.assertEqual(inter["facad_display_deg"], 140.9)
        self.assertAlmostEqual(inter["raw_delta_deg"], -0.2, places=6)
        self.assertFalse(inter["clinical_parity"])

    def test_production_typed_interincisal_does_not_promote_clinical_parity(self):
        result = p3.assess(self.fixture)
        self.assertEqual(result["clinical_parity_verified"], 0)
        self.assertFalse(result["facad_operator_crosswalk_validated"])
        self.assertFalse(result["complete_analysis_runtime_executed"])
        self.assertTrue(result["clinical_no_go"])
        self.assertFalse(result["craniom_interincisal_typed_construction"]["landmark_identity_proven"])

    def test_no_po_or_frankfort_fabricated(self):
        self.assertNotIn("Po", p3.CANDIDATE_CROSSWALK)
        self.assertNotIn("Or", p3.CANDIDATE_CROSSWALK)
        self.assertNotIn("P", p3.CANDIDATE_CROSSWALK)
        self.assertFalse(p3.assess(self.fixture)["clinical_runtime_calibration_proven"])

    def test_do_not_promote_third_interincisal_from_craniom_helper(self):
        methods = p3.assess(self.fixture)["rows"]
        self.assertNotIn("InterIncisal", {m["facad_factor"] for m in methods})

    def test_reject_fabricated_anatomical_frankfort(self):
        del self.fixture["points_mm"]["SN"]
        self.fixture["points_mm"]["Or"] = [1.0, 5.0]
        with self.assertRaisesRegex(ValueError, "review authentic Frankfort"):
            p3.assess(self.fixture)

    def test_reject_modified_coordinate_source_semantics(self):
        self.fixture["coordinate_system"] = "DC_VERIFIED"
        with self.assertRaisesRegex(ValueError, "unverified frame"):
            p3.assess(self.fixture)

    def test_reject_modified_facad_data_asserting_clinical_authority(self):
        self.fixture["clinical_parity_proven"] = True
        with self.assertRaisesRegex(ValueError, "unsafe promotion"):
            p3.assess(self.fixture)

    def test_reject_missing_canonical_crosswalk_anatomy(self):
        del self.fixture["points_mm"]["Iia"]
        with self.assertRaises(ValueError):
            p3.assess(self.fixture)


if __name__ == "__main__":
    unittest.main()
