"""J10P local-only COCO intake regression tests. All fixtures are synthetic."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).with_name("lot05_j10p_roboflow_coco_offline_intake.py")
spec = importlib.util.spec_from_file_location("j10p", MODULE_PATH)
assert spec and spec.loader
j10p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(j10p)


class TestRoboflowCOCOIntake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.base = {}
        categories = [{"id": i, "name": label}
                      for i, label in enumerate(sorted(j10p.FDI))]
        for split, count in j10p.SPLITS.items():
            folder = cls.root / split
            folder.mkdir()
            images = []
            annotations = []
            for index in range(count):
                name = f"synthetic_{split}_{index:05d}.jpg"
                (folder / name).touch()
                images.append({"id": index, "file_name": name,
                               "width": 1280, "height": 1280})
                annotations.append({"id": index, "image_id": index,
                                    "category_id": index % 32,
                                    "bbox": [20, 35, 40, 60]})
            cls.base[split] = {"images": images, "categories": categories,
                               "annotations": annotations}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        for split in j10p.SPLITS:
            self.write(split, self.base[split])

    def write(self, split, data):
        (self.root / split / "_annotations.coco.json").write_text(
            json.dumps(data), encoding="utf-8")

    def changed(self, split):
        return json.loads(json.dumps(self.base[split]))

    def test_valid_synthetic_publisher_v1_passes_without_clearance(self):
        result = j10p.inspect(self.root)
        self.assertEqual(result["images_total"], 3503)
        self.assertEqual(result["splits"]["train"]["fdi_class_count"], 32)
        self.assertEqual(result["possible_cross_split_source_stem_collisions"],
                         {"train_valid": 0, "train_test": 0, "valid_test": 0})
        for flag in ("patient_level_split_independence_proven",
                     "source_patient_rights_verified",
                     "commercial_training_authorized",
                     "clinical_fdi_accuracy_measured",
                     "clinical_use_authorized",
                     "image_pixels_read_or_uploaded"):
            self.assertFalse(result[flag])

    def test_missing_fdi_category_is_blocked(self):
        d = self.changed("train")
        d["categories"].pop()
        self.write("train", d)
        with self.assertRaisesRegex(j10p.IntakeError, "class_map_mismatch"):
            j10p.inspect(self.root)

    def test_duplicate_fdi_category_is_blocked(self):
        d = self.changed("test")
        d["categories"][0]["name"] = d["categories"][1]["name"]
        self.write("test", d)
        with self.assertRaisesRegex(j10p.IntakeError, "duplicate_category"):
            j10p.inspect(self.root)

    def test_dangling_image_reference_is_blocked(self):
        d = self.changed("valid")
        d["annotations"][0]["image_id"] = 99999
        self.write("valid", d)
        with self.assertRaisesRegex(j10p.IntakeError, "dangling_annotation_reference"):
            j10p.inspect(self.root)

    def test_bbox_outside_image_is_blocked(self):
        d = self.changed("train")
        d["annotations"][0]["bbox"] = [1279, 30, 40, 30]
        self.write("train", d)
        with self.assertRaisesRegex(j10p.IntakeError, "bbox_out_of_image_bounds"):
            j10p.inspect(self.root)

    def test_fractional_or_unknown_category_reference_is_blocked(self):
        d = self.changed("train")
        d["annotations"][0]["category_id"] = 99
        self.write("train", d)
        with self.assertRaisesRegex(j10p.IntakeError, "dangling_annotation_reference"):
            j10p.inspect(self.root)

    def test_missing_image_is_blocked(self):
        d = self.changed("valid")
        d["images"][0]["file_name"] = "missing_synthetic.jpg"
        self.write("valid", d)
        with self.assertRaisesRegex(j10p.IntakeError, "image_missing_or_symlink"):
            j10p.inspect(self.root)

    def test_parent_directory_file_reference_is_blocked(self):
        d = self.changed("train")
        d["images"][0]["file_name"] = "../sensitive_patient.jpg"
        self.write("train", d)
        with self.assertRaisesRegex(j10p.IntakeError, "unsafe_image_name"):
            j10p.inspect(self.root)

    def test_missing_split_sample_blocks_published_count(self):
        d = self.changed("valid")
        d["images"].pop()
        self.write("valid", d)
        with self.assertRaisesRegex(j10p.IntakeError, "count_mismatch"):
            j10p.inspect(self.root)

    def test_source_name_overlap_only_generates_heuristic_not_proof(self):
        d = self.changed("valid")
        shared = "synthetic_train_00000.rf.abcdef123456.jpg"
        (self.root / "valid" / shared).touch()
        # Publisher .rf. prefix strips the hash; original train name retained.
        d["images"][0]["file_name"] = shared
        self.write("valid", d)
        result = j10p.inspect(self.root)
        self.assertEqual(
            result["possible_cross_split_source_stem_collisions"]["train_valid"], 1)
        self.assertFalse(result["patient_level_split_independence_proven"])

    def test_annotation_json_symlink_refused(self):
        self.assertFalse(j10p._safe_image_name("x.jpg") is None)
        with self.assertRaises(j10p.IntakeError):
            j10p._safe_image_name("x\\y.jpg")

    def test_bbox_nan_rejected(self):
        d = self.changed("test")
        d["annotations"][0]["bbox"] = [float("nan"), 20, 40, 50]
        self.write("test", d)
        with self.assertRaisesRegex(j10p.IntakeError, "invalid_bbox"):
            j10p.inspect(self.root)


if __name__ == "__main__":
    unittest.main()
