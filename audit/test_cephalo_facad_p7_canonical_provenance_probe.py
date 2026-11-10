"""P7 actual production bridge safety regression on synthetic evidence."""
import unittest
from audit.cephalo_facad_p6_identity_review_gate import REQUIRED
from audit.cephalo_facad_p7_canonical_provenance_probe import probe

def review(all_true=False):
    return {
      "schema": "FACAD_P6_INDEPENDENT_IDENTITY_REVIEW_V1",
      "source_unannotated_full_resolution": all_true,
      "source_rights_confirmed": all_true,
      "independent_reviewer": all_true,
      "same_trace_verified": all_true,
      "landmarks": {k: {
        "independent_image_identification": all_true,
        "selected_tooth_confirmed": all_true,
        "anatomical_definition_confirmed": all_true,
        "reviewer_signed": all_true,
      } for k in REQUIRED},
    }

class P7Tests(unittest.TestCase):
    def test_missing_real_source_uses_production_bridge_without_promotion(self):
        result = probe(review())
        self.assertTrue(result["production_bridge_exercised"])
        self.assertFalse(result["p6_independent_review_complete"])
        self.assertFalse(result["manual_pog_promoted_to_pog_hard"])
        self.assertTrue(result["clinical_no_go"])

    def test_even_synthetic_fully_signed_review_cannot_forge_srpose(self):
        result = probe(review(True))
        self.assertTrue(result["p6_independent_review_complete"])
        self.assertFalse(result["certified_srpose_evidence_available"])
        self.assertEqual(result["clinical_parity_count"], 0)
        self.assertFalse(result["manual_pog_promoted_to_pog_hard"])

    def test_unexpected_private_payload_fails_closed(self):
        doc = review()
        doc["screenshot"] = "private"
        with self.assertRaises(ValueError):
            probe(doc)
