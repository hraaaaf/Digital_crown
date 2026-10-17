"""All test inputs are synthetic: no image, patient or anatomical coordinates."""
import copy
import unittest
from pathlib import Path

from scripts.cephalo_r23g10_annotation_intake import (
    FROZEN_LOT02_SHA, G9_REL, TEMPLATE_REL, load, verify_intake,
)
ROOT = Path(__file__).resolve().parents[2]

def context():
    return load(ROOT / TEMPLATE_REL), load(ROOT / G9_REL)

def planned(template, matrix, split="train"):
    obj = copy.deepcopy(template)
    obj["cases"] = [{
        "case_token": "synthetic-case-a", "lot02_case_id": "syntheticA001",
        "split": split, "source_image_sha256": "a"*64,
        "required_annotation_ids": matrix["identities_without_strict_mapping"],
        "assigned_blinded_experts": ["expert_alpha", "expert_beta"],
        "calibration_status": "PENDING_INDEPENDENT_VERIFICATION",
        "orientation_status": "PENDING_INDEPENDENT_VERIFICATION",
        "annotation_status": "UNANNOTATED",
    }]
    return obj

class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.template, self.matrix = context()

    def reject(self, intake, matrix=None):
        with self.assertRaises(ValueError):
            verify_intake(intake, matrix or self.matrix)

    def test_empty_template_is_not_goldset(self):
        out = verify_intake(self.template, self.matrix)
        self.assertEqual(out["case_assignment_count"], 0)
        self.assertFalse(out["goldset_clinically_verified"])
        self.assertFalse(out["source_manifest_frozen_bytes_checked"])

    def test_two_blinded_assignments_only_count_as_plan(self):
        out = verify_intake(planned(self.template, self.matrix), self.matrix)
        self.assertEqual(out["case_assignment_count"], 1)
        self.assertFalse(out["ready_for_anatomical_measurement_validation"])

    def test_clinical_promotion_and_alias_forbidden(self):
        for field in ["clinical_release", "expert_reference_verified"]:
            obj = copy.deepcopy(self.template)
            obj[field] = True
            self.reject(obj)
        matrix = copy.deepcopy(self.matrix)
        matrix["semantic_aliasing_authorized"] = True
        self.reject(self.template, matrix)

    def test_sensitive_payloads_and_upload_forbidden(self):
        obj = planned(self.template, self.matrix)
        obj["cases"][0]["landmarks"] = {"N": [150, 210]}
        self.reject(obj)
        obj = copy.deepcopy(self.template)
        obj["privacy"]["upload_allowed"] = True
        self.reject(obj)
        obj = planned(self.template, self.matrix)
        obj["cases"][0]["case_token"] = "Patient Jane Doe"
        self.reject(obj)

    def test_untouched_test_split_forbidden(self):
        self.reject(planned(self.template, self.matrix, split="test"))
        obj = copy.deepcopy(self.template)
        obj["protocol"]["allowed_splits"].append("test")
        self.reject(obj)

    def test_no_alias_for_atlas_specific_points(self):
        for old, new in [("Po_anatomic", "Po"), ("Pt_Ricketts", "PTM_McNamara"),
                         ("Pog_hard", "Pog")]:
            obj = planned(self.template, self.matrix)
            obj["cases"][0]["required_annotation_ids"] = [
                new if x == old else x for x in self.matrix["identities_without_strict_mapping"]]
            self.reject(obj)

    def test_two_different_experts_and_unique_case(self):
        obj = planned(self.template, self.matrix)
        obj["cases"][0]["assigned_blinded_experts"] = ["same", "same"]
        self.reject(obj)
        obj = planned(self.template, self.matrix)
        obj["cases"].append(copy.deepcopy(obj["cases"][0]))
        self.reject(obj)

    def test_unverified_orientation_calibration_and_human_annotations(self):
        for field in ["calibration_status", "orientation_status", "annotation_status"]:
            obj = planned(self.template, self.matrix)
            obj["cases"][0][field] = "VERIFIED"
            self.reject(obj)

    def test_only_frozen_source_manifest_and_matching_case(self):
        obj = planned(self.template, self.matrix)
        with self.assertRaises(ValueError):
            verify_intake(obj, self.matrix, source_manifest={},
                          source_manifest_sha="0"*64)
        cases = [{"case_id": f"syntheticA{i:03d}",
                  "split": "train" if i < 700 else "valid" if i < 850 else "test",
                  "image": {"sha256": "a"*64 if i == 1 else "b"*64}}
                 for i in range(1000)]
        src = {"schema": "CEPHALO_LOT02_AARIZ_MANIFEST_V2",
               "source": {"doi": "10.6084/m9.figshare.27986417.v1"},
               "counts": {"train": 700, "valid": 150, "test": 150},
               "cases": cases}
        out = verify_intake(obj, self.matrix, source_manifest=src,
                            source_manifest_sha=FROZEN_LOT02_SHA)
        self.assertTrue(out["source_manifest_frozen_bytes_checked"])
        self.assertFalse(out["clinical_release"])
        obj["cases"][0]["source_image_sha256"] = "c"*64
        with self.assertRaises(ValueError):
            verify_intake(obj, self.matrix, source_manifest=src,
                          source_manifest_sha=FROZEN_LOT02_SHA)

if __name__ == "__main__":
    unittest.main()
