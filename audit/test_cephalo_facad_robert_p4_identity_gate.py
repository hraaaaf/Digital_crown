"""P4 public Robert source-lock tests; never assert clinical placement from labels."""
from __future__ import annotations

import copy
import json
import unittest

from audit import cephalo_facad_robert_p4_identity_gate as p4
from audit import cephalo_facad_robert_p3_canonical_adapter_probe as p3

FIXTURE = json.loads(p4.demo.FIXTURE.read_text(encoding="utf-8"))
CONTRACT = json.loads(p4.SOURCE_CONTRACT.read_text(encoding="utf-8"))
DOCS = (p4.SRPOSE_CONTRACT.read_text(encoding="utf-8"),
        p4.CANONICAL_IDENTITY_DOC.read_text(encoding="utf-8"),
        p4.DENTAL_SOURCE_DOC.read_text(encoding="utf-8"))


class SixLandmarkSourceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = copy.deepcopy(FIXTURE)
        self.contract = copy.deepcopy(CONTRACT)

    def test_real_dc_projector_blocks_unproven_facad_hard_pog(self):
        result = p4.assess(self.fixture, self.contract, DOCS)
        self.assertEqual(result["source_terminology_pairs_reviewed"], 6)
        self.assertFalse(result["facad_pog_projected_to_dc_pog_hard"])
        self.assertEqual(len(result["typed_canonical_v2_angles_blocked_by_unverified_identity"]), 2)
        self.assertTrue(result["typed_craniom_interincisal_geometry_available"])
        self.assertEqual(result["landmark_placement_on_ceph_image_independently_verified"], 0)
        self.assertEqual(result["cross_vendor_clinical_parities"], 0)
        self.assertTrue(result["clinical_no_go"])

    def test_p3_educational_direct_injection_differs_from_real_identity_bridge(self):
        # P3 geometry manually assigns Pog_hard for research; production P4
        # projects a generic MANUAL Pog and deliberately withholds that alias.
        p3_result = p3.assess(self.fixture)
        p4_result = p4.assess(self.fixture, self.contract, DOCS)
        self.assertEqual(len(p3_result["rows"]), 2)
        self.assertEqual(len(p4_result["typed_canonical_v2_angles_blocked_by_unverified_identity"]), 2)
        self.assertFalse(p4_result["facad_pog_projected_to_dc_pog_hard"])
        self.assertFalse(p3_result["facad_operator_crosswalk_validated"])

    def test_preserve_six_source_anatomical_terms_not_reverse_incisors(self):
        self.assertEqual(
            [(r["facad_landmark"],r["dc_research_target"])
             for r in self.contract["records"]],
            [("Ii","L1_incisal"), ("Iia","L1_apex"),
             ("Is","U1_incisal"), ("Isa","U1_apex"),
             ("A","A"), ("Pog","Pog_hard")])

    def test_pog_is_not_soft_tissue_pgs(self):
        self.assertIn("PGs", self.fixture["points_mm"])
        self.assertNotIn("PGs", [r["facad_landmark"] for r in self.contract["records"]])
        self.assertEqual(p4.assess(self.fixture, self.contract, DOCS)["cross_vendor_clinical_parities"],0)

    def test_individual_placement_authority_cannot_be_promoted(self):
        self.contract["records"][0]["robert_marker_placement_independently_verified"] = True
        with self.assertRaisesRegex(ValueError, "falsely claims"):
            p4.assess(self.fixture, self.contract, DOCS)

    def test_global_canonical_authority_cannot_be_promoted(self):
        self.contract["facad_to_dc_canonical_identity_bridge_authorized"] = True
        with self.assertRaisesRegex(ValueError,"unsubstantiated"):
            p4.assess(self.fixture, self.contract, DOCS)

    def test_vendor_manual_3_8_is_not_3_14_case_specific_proof(self):
        self.contract["vendor_manual"]["publication_date"] = "2026-10-24"
        with self.assertRaisesRegex(ValueError,"manual/version"):
            p4.assess(self.fixture,self.contract,DOCS)

    def test_reject_canonical_hard_pog_alias_without_certified_predecessor(self):
        self.contract["records"][-1]["facad_landmark"] = "PGs"
        with self.assertRaisesRegex(ValueError,"crosswalk identity"):
            p4.assess(self.fixture,self.contract,DOCS)

    def test_reject_unverified_frankfort_in_facad_fixture(self):
        # Keep cardinality 30 and unit metadata; no invented Or accepted.
        del self.fixture["points_mm"]["SN"]
        self.fixture["points_mm"]["Or"] = [0.0, 0.0]
        with self.assertRaisesRegex(ValueError,"never fake"):
            p4.assess(self.fixture,self.contract,DOCS)

    def test_reject_pog_authority_document_changed(self):
        src, doc, dental = DOCS
        with self.assertRaisesRegex(ValueError,"identity contract changed"):
            p4.assess(self.fixture,self.contract,
                      (src,doc.replace("Pog → Pog_hard","Pog → PGs"),dental))

    def test_reject_facad_upper_lower_incisor_axis_swap(self):
        src, doc, dental = DOCS
        with self.assertRaisesRegex(ValueError,"definitions drifted"):
            p4.assess(self.fixture,self.contract,
                      (src,doc,dental.replace("Angle4p(Pog,A,Iia,Ii)",
                                              "Angle4p(Pog,A,Isa,Is)")))

    def test_missing_facad_incisor_point_not_inferred(self):
        self.fixture["points_mm"].pop("Iia")
        with self.assertRaises(ValueError):
            p4.assess(self.fixture,self.contract,DOCS)


if __name__ == "__main__":
    unittest.main()
