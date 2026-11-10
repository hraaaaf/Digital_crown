"""Synthetic P6 gate tests. No private images, PHI or vendor data."""
import unittest
from audit.cephalo_facad_p6_identity_review_gate import REQUIRED, validate_review

def make_review():
    return {"schema": "FACAD_P6_INDEPENDENT_IDENTITY_REVIEW_V1",
            "source_unannotated_full_resolution": False,
            "source_rights_confirmed": False,
            "independent_reviewer": False,
            "same_trace_verified": False,
            "landmarks": {name: {"independent_image_identification": False,
                                 "selected_tooth_confirmed": False,
                                 "anatomical_definition_confirmed": False,
                                 "reviewer_signed": False} for name in REQUIRED}}

class GateTests(unittest.TestCase):
    def test_missing_source_fail_closed(self):
        result = validate_review(make_review())
        self.assertFalse(result["independent_review_complete"])
        self.assertEqual(result["priority_landmarks_review_supported"], 0)
        self.assertTrue(result["clinical_no_go"])

    def test_all_reviewed_is_not_canonical_authorization(self):
        review = make_review()
        for name in ("source_unannotated_full_resolution",
                     "source_rights_confirmed", "independent_reviewer",
                     "same_trace_verified"):
            review[name] = True
        for record in review["landmarks"].values():
            for name in record: record[name] = True
        result = validate_review(review)
        self.assertTrue(result["independent_review_complete"])
        self.assertEqual(result["priority_landmarks_review_supported"], 7)
        self.assertFalse(result["raw_facad_pog_promotable_to_dc_pog_hard"])
        self.assertFalse(result["canonical_bridge_executed"])
        self.assertEqual(result["clinical_parity_count"], 0)

    def test_missing_tooth_confirmation_blocks_full_review(self):
        review = make_review()
        for k in ("source_unannotated_full_resolution", "source_rights_confirmed",
                  "independent_reviewer", "same_trace_verified"):
            review[k] = True
        for v in review["landmarks"].values():
            for k in v: v[k] = True
        review["landmarks"]["Iia"]["selected_tooth_confirmed"] = False
        self.assertFalse(validate_review(review)["independent_review_complete"])

    def test_extraneous_sensitive_payload_rejected(self):
        review = make_review()
        review["patient"] = "test"
        with self.assertRaisesRegex(ValueError,"unexpected"):
            validate_review(review)

    def test_missing_label_and_nonboolean_rejected(self):
        review = make_review()
        del review["landmarks"]["PGs"]
        with self.assertRaisesRegex(ValueError,"roster"):
            validate_review(review)
        review = make_review()
        review["same_trace_verified"] = "yes"
        with self.assertRaisesRegex(ValueError,"boolean"):
            validate_review(review)

if __name__ == "__main__":
    unittest.main()
