"""FUE-0 pure synthetic AKUDENTAL 35-class COCO adapter tests; no real radiographs."""
import json
from pathlib import Path
import tempfile
import unittest

from lot05_j10d_fdi_akudental_coco_adapter import category_map, coco_to_manifest
from lot05_j10d_fdi_tooth_model_probe import CLASS_ORDER
from lot05_j10d_fdi_local_benchmark import BenchmarkError, evaluate

EXTRA = ("Bridge", "Filling - Crown", "Implant")


def categories():
    return [{"id": idx, "name": f"{code} - Sample tooth"} for idx, code in enumerate(CLASS_ORDER)] + [
        {"id": idx, "name": name} for idx, name in enumerate(EXTRA, start=32)
    ]


def fixture(root: Path):
    (root / "one.jpg").write_bytes(b"fake_not_a_patient")
    (root / "two.jpg").write_bytes(b"fake_not_a_patient")
    return {
        "images": [{"id": 1, "file_name": "one.jpg", "height": 200, "width": 400},
                   {"id": 2, "file_name": "two.jpg", "height": 200, "width": 400}],
        "categories": categories(),
        "annotations": [
            {"id": 1, "image_id": 1, "category_id": 21, "iscrowd": 0, "bbox": [10, 30, 90, 70]},
            {"id": 2, "image_id": 1, "category_id": 22, "iscrowd": 0, "bbox": [120, 30, 90, 70]},
            {"id": 3, "image_id": 1, "category_id": 34, "iscrowd": 0, "bbox": [0, 0, 15, 15]},
            {"id": 4, "image_id": 2, "category_id": 0, "iscrowd": 0, "bbox": [30, 20, 60, 90]},
        ],
    }


class TestAkudentalConverter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.coco = fixture(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def convert(self, **kwargs):
        return coco_to_manifest(self.coco, images_root=self.root, **kwargs)

    def test_all_32_fdi_and_3_non_tooth_classes(self):
        mapping = category_map(categories())
        self.assertEqual(mapping[21], "36")
        self.assertEqual(mapping[22], "37")
        self.assertEqual(mapping[0], "11")
        self.assertEqual(mapping[31], "48")
        self.assertIsNone(mapping[34])
        self.assertEqual(len(mapping), 35)

    def test_convert_xywh_to_xyxy_and_skip_implant_without_shifting(self):
        manifest, audit = self.convert()
        self.assertEqual([a["fdi"] for a in manifest["cases"][0]["gt"]], ["36", "37"])
        self.assertEqual(manifest["cases"][0]["gt"][0]["bbox"], [10.,30.,100.,100.])
        self.assertEqual(audit["images_selected"], 2)
        self.assertEqual(audit["ground_truth_teeth_selected"], 3)
        self.assertEqual(audit["ignored_non_tooth_annotations_total"], 1)
        self.assertFalse(audit["patient_and_DENTEX_overlap_checked"])
        self.assertNotIn("one.jpg", json.dumps(audit))

    def test_manifest_accepted_by_existing_evaluator_and_swaps_counted(self):
        manifest, _ = self.convert()
        cases = manifest["cases"]
        predictions = {}
        for case in cases:
            predictions[case["case_id"]] = [
                {**ann, "confidence": .9} for ann in case["gt"]
            ]
        predictions[cases[0]["case_id"]][1]["fdi"] = "36"
        result = evaluate(cases, predictions)
        self.assertEqual(result["overall"]["ground_truth_teeth"], 3)
        self.assertEqual(result["overall"]["wrong_number_on_localized_tooth"], 1)
        self.assertEqual(result["overall"]["adjacent_fdi_swaps"], 1)
        self.assertEqual(result["overall"]["correct_number_and_localization_count"], 2)

    def test_fixed_sampling_order_and_site_group(self):
        manifest, audit = self.convert(max_images=1, site_group=5, device_group=7)
        self.assertEqual(audit["images_selected"], 1)
        self.assertEqual(manifest["cases"][0]["site_group"], 5)
        self.assertEqual(manifest["cases"][0]["device_group"], 7)
        self.assertEqual(manifest["cases"][0]["case_id"], "source-1")

    def test_missing_tooth_annotations_not_fabricated(self):
        self.coco["annotations"] = []
        manifest, audit = self.convert()
        self.assertEqual(len(manifest["cases"]), 2)
        self.assertEqual(audit["image_with_no_fdi_annotation"], 2)
        self.assertEqual(manifest["cases"][0]["gt"], [])

    def test_permuted_coco_numeric_ids_map_by_names(self):
        for i, row in enumerate(self.coco["categories"]):
            row["id"] = 100 + i
        for ann in self.coco["annotations"]:
            ann["category_id"] += 100
        manifest, _ = self.convert()
        self.assertEqual([a["fdi"] for a in manifest["cases"][0]["gt"]], ["36","37"])

    def test_missing_or_duplicate_fdi_category_fails(self):
        broken = categories()
        broken[0]["name"] = "12 - Duplicate instead of 11"
        with self.assertRaises(BenchmarkError):
            category_map(broken)
        broken = categories()
        broken[-1]["name"] = "Unrecognised anomaly"
        with self.assertRaises(BenchmarkError):
            category_map(broken)

    def test_box_bounds_must_be_valid(self):
        for bbox in [[10, 10, 500, 20], [10, 10, -2, 30], [10, 10, float("nan"), 10]]:
            self.coco["annotations"][0]["bbox"] = bbox
            with self.subTest(bbox=bbox), self.assertRaises(BenchmarkError):
                self.convert()

    def test_missing_image_is_error(self):
        self.coco["images"][0]["file_name"] = "missing.jpg"
        with self.assertRaises((BenchmarkError, FileNotFoundError)):
            self.convert()

    def test_path_traversal_and_unsupported_ext_rejected(self):
        for value in ["../one.jpg", "/etc/passwd", "one.exe"]:
            self.coco["images"][0]["file_name"] = value
            with self.subTest(value=value), self.assertRaises((BenchmarkError, FileNotFoundError)):
                self.convert()

    def test_duplicate_image_and_annotation_fails(self):
        self.coco["images"][1]["id"] = 1
        with self.assertRaises(BenchmarkError):
            self.convert()
        self.coco = fixture(self.root)
        self.coco["annotations"][1]["id"] = 1
        with self.assertRaises(BenchmarkError):
            self.convert()

    def test_bad_iscrowd_rejected(self):
        self.coco["annotations"][0]["iscrowd"] = 1
        with self.assertRaisesRegex(BenchmarkError,"crowd_fdi_gt_not_supported"):
            self.convert()

    def test_no_silent_non_fdi_substitution(self):
        self.coco["categories"][34]["name"] = "supernumerary 49"
        with self.assertRaises(BenchmarkError):
            self.convert()

    def test_audit_no_patient_name_id_path(self):
        _, audit = self.convert()
        body = json.dumps(audit)
        for forbidden in ("one.jpg", "two.jpg", "source-1", str(self.root)):
            self.assertNotIn(forbidden, body)
        self.assertEqual(audit["clinical_fdi_labels_adjudicated_by_this_project"], False)


if __name__ == "__main__":
    unittest.main()
