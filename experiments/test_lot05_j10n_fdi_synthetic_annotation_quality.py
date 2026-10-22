"""J10N: deny-by-default synthetic FDI annotation schema, quality and leakage tests."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).with_name("lot05_j10n_fdi_synthetic_annotation_quality.py")
spec = importlib.util.spec_from_file_location("j10n_qa", P)
assert spec and spec.loader
import sys
sys.path.insert(0, str(P.parent))
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)
WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/lot05-j10n-synthetic-annotation-qa.yml"


def generated():
    return qa.synthetic_registry()


class TestSyntheticAnnotationContract(unittest.TestCase):
    def test_fixture_has_four_strict_split_groups_and_one_repeated_subject(self):
        summary = qa.validate_synthetic_registry(generated())
        self.assertEqual(summary["status"], "SYNTHETIC_ANNOTATION_QA_PASS_REAL_DATA_BLOCKED")
        self.assertEqual(summary["synthetic_record_count"], 5)
        self.assertEqual(summary["synthetic_subject_groups"], 4)
        self.assertEqual(summary["split_counts"], {"train": 3, "val": 1, "test_external": 1})
        self.assertEqual(summary["adjudicated_synthetic_cases"], 1)
        self.assertEqual(summary["synthetic_edentulous_cases"], 1)
        self.assertEqual(summary["clinical_radiographs_processed"], 0)

    def test_permanent_fdi32_contract_and_visible_only_missing_teeth_allowed(self):
        data = generated()
        self.assertEqual(data["fdi_labels"], list(qa.FDI_32))
        self.assertEqual(len(data["records"][0]["review_a"]["teeth"]), 4)
        self.assertEqual(len(data["records"][3]["review_a"]["teeth"]), 0)
        data["fdi_labels"] = list(range(32))
        with self.assertRaises(qa.SyntheticAnnotationError):
            qa.validate_synthetic_registry(data)

    def test_real_training_or_patient_data_flags_rejected(self):
        for field in qa.RIGHTS_KEYS:
            with self.subTest(field=field):
                data = generated()
                data["rights"][field] = True
                with self.assertRaises(qa.SyntheticAnnotationError):
                    qa.validate_synthetic_registry(data)

    def test_training_mode_must_be_synthetic_only(self):
        for mode in ("commercial", "real_dataset", None, "SYNTHETIC_ONLY"):
            data = generated()
            data["mode"] = mode
            with self.subTest(mode=mode), self.assertRaises(qa.SyntheticAnnotationError):
                qa.validate_synthetic_registry(data)

    def test_no_extra_clinical_or_free_text_fields_allowed(self):
        for level in ("top", "record", "annotation"):
            data = generated()
            if level == "top":
                data["patient_name"] = "test"
            elif level == "record":
                data["records"][0]["original_dicom_filename"] = "test.dcm"
            else:
                data["records"][0]["review_a"]["teeth"][0]["diagnosis"] = "test"
            with self.subTest(level=level), self.assertRaises(qa.SyntheticAnnotationError):
                qa.validate_synthetic_registry(data)

    def test_bad_patient_group_and_real_site_identifiers_rejected(self):
        for field, value in (
            ("subject_group", "John_Doe"),
            ("source_site", "Clinic Casablanca"),
            ("near_duplicate_group", "real_patient_hash"),
        ):
            data = generated()
            data["records"][0][field] = value
            with self.subTest(field=field), self.assertRaises(qa.SyntheticAnnotationError):
                qa.validate_synthetic_registry(data)

    def test_subject_group_never_crosses_splits(self):
        data = generated()
        data["records"][3]["subject_group"] = "SYN-G001"
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "same_subject"):
            qa.validate_synthetic_registry(data)

    def test_near_duplicate_never_crosses_splits_even_other_subject(self):
        data = generated()
        data["records"][3]["near_duplicate_group"] = "SYN-D001"
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "near_duplicate_leaked"):
            qa.validate_synthetic_registry(data)

    def test_external_site_must_be_independent(self):
        data = generated()
        data["records"][-1]["source_site"] = "SYN-SITE-A"
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "external_test_site_leaks"):
            qa.validate_synthetic_registry(data)

    def test_duplicate_hash_and_record_ids_banned(self):
        for prop in ("image_sha256", "record_id"):
            data = generated()
            data["records"][2][prop] = data["records"][0][prop]
            with self.subTest(prop=prop), self.assertRaises(qa.SyntheticAnnotationError):
                qa.validate_synthetic_registry(data)

    def test_two_distinct_reviewers_required(self):
        data = generated()
        data["records"][0]["review_b"]["reviewer_id"] = "SYN-REV-1"
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "same_person_double_review"):
            qa.validate_synthetic_registry(data)

    def test_unresolved_fdi_label_disagreement_rejected(self):
        data = generated()
        data["records"][2]["adjudication"] = None
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "disagreement_requires"):
            qa.validate_synthetic_registry(data)

    def test_adjudicator_cannot_be_first_or_second_reviewer(self):
        data = generated()
        data["records"][2]["adjudication"]["reviewer_id"] = "SYN-REV-2"
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "adjudicator_must_be_independent"):
            qa.validate_synthetic_registry(data)

    def test_implicit_deletion_of_disputed_tooth_banned(self):
        data = generated()
        data["records"][2]["adjudication"]["teeth"] = []
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "disagreement_cannot_be_dropped"):
            qa.validate_synthetic_registry(data)

    def test_unreviewed_orientation_rejected(self):
        data = generated()
        data["records"][0]["orientation_verified_synthetic"] = False
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "orientation_not_reviewed"):
            qa.validate_synthetic_registry(data)

    def test_explicit_edentulous_confirmation_required(self):
        data = generated()
        data["records"][3]["edentulous_confirmed"] = False
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "edentulous_must_be_explicit"):
            qa.validate_synthetic_registry(data)

    def test_wrong_fdi_missing_box_and_duplicate_fdi_rejected(self):
        for change in ("bad_fdi", "bad_bbox", "duplicate"):
            data = generated()
            teeth = data["records"][0]["review_a"]["teeth"]
            if change == "bad_fdi":
                teeth[0]["fdi"] = 55
            elif change == "bad_bbox":
                teeth[0]["bbox_cxcywh"] = [0.01, 0.2, 0.3, 0.3]
            else:
                teeth[1]["fdi"] = teeth[0]["fdi"]
            with self.subTest(change=change), self.assertRaises(qa.SyntheticAnnotationError):
                qa.validate_synthetic_registry(data)

    def test_second_reviewer_box_shift_requires_adjudication(self):
        data = generated()
        teeth = data["records"][0]["review_b"]["teeth"]
        teeth[0]["bbox_cxcywh"][0] += 0.20
        with self.assertRaisesRegex(qa.SyntheticAnnotationError, "disagreement_requires"):
            qa.validate_synthetic_registry(data)

    def test_nonfinite_and_boolean_boxes_rejected(self):
        for wrong in (float("nan"), float("inf"), True, "0.25"):
            data = generated()
            data["records"][0]["review_a"]["teeth"][0]["bbox_cxcywh"][0] = wrong
            with self.subTest(wrong=str(wrong)), self.assertRaises(qa.SyntheticAnnotationError):
                qa.validate_synthetic_registry(data)

    def test_no_external_image_import_and_no_cli_dataset_input(self):
        source = P.read_text(encoding="utf-8")
        for disallowed in ("Image.open(", "pydicom", "torch.save(", "save_pretrained(",
                           "dataset-path", "input-json", "requests.get(", "cv2.imread("):
            self.assertNotIn(disallowed, source)
        self.assertIn("audit_dataset_manifest", source)
        self.assertIn("check_research_only_mode", source)
        wf = WORKFLOW.read_text(encoding="utf-8")
        for needed in ("ubuntu-24.04", "windows-2025", "actions/upload-artifact@",
                       "reports/j10n-", "commercial_model_release_approved"):
            self.assertIn(needed, wf)
        for disallowed in ("deploy", "datasets download", "patient.zip", "image.png"):
            self.assertNotIn(disallowed, wf.lower())


if __name__ == "__main__":
    unittest.main()
