"""J10R synthetic staging QA only. No real radiographs, datasets or internet."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

module = Path(__file__).with_name("lot05_j10r_akudental_private_research_workspace.py")
spec = importlib.util.spec_from_file_location("j10r", module)
assert spec and spec.loader
j10r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(j10r)


class TestPrivateWorkspace(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "synthetic_source"
        images = self.source / "AKUDENTAL" / "images"
        images.mkdir(parents=True)
        self.labels = self.source / "AKUDENTAL" / "folds" / "fold_0" / "labels"
        counter = 0
        for split, total in zip(j10r.SPLITS, j10r.EXPECTED["fold_0"]):
            folder = self.labels / split
            folder.mkdir(parents=True)
            for _ in range(total):
                counter += 1
                (folder / f"{counter}.txt").write_text("0 0.5 0.5 0.2 0.4\n")
                (images / f"{counter}.jpg").write_bytes(b"synthetic-placeholder-not-an-image")
        self.destination = self.root / "stage"

    def tearDown(self):
        self.temp.cleanup()

    def test_workspace_uses_only_symlinks_for_images(self):
        result = j10r.stage(self.source, "fold_0", self.destination)
        self.assertEqual(result["image_symlinks"], 333)
        self.assertEqual(result["split_counts"], {"train": 266, "val": 33, "test": 34})
        self.assertEqual(result["status"], "PILOT_WORKSPACE_STAGED_NO_TRAINING")
        self.assertEqual(result["annotations_qa"]["tooth_instances"], 333)
        self.assertTrue((self.destination / "images" / "train" / "1.jpg").is_symlink())
        self.assertEqual((self.destination / "labels" / "train" / "1.txt").read_text(),
                         "0 0.5 0.5 0.2 0.4\n")
        yaml = (self.destination / "data.yaml").read_text()
        self.assertIn("nc: 35", yaml)
        self.assertIn("  0: '11'", yaml)
        self.assertIn("  31: '48'", yaml)
        self.assertIn("  34: 'Implant'", yaml)
        self.assertFalse(result["commercial_rights_verified"])
        self.assertFalse(result["training_performed"])

    def test_bbox_corruption_rejected_before_writing_workspace(self):
        (self.labels / "train" / "1.txt").write_text("0 0.9 0.9 0.4 0.4")
        with self.assertRaisesRegex(j10r._J10Q.LabelAuditError,
                                    "bbox_outside_image_frame"):
            j10r.stage(self.source, "fold_0", self.destination)
        self.assertFalse(self.destination.exists())

    def test_duplicate_fdi_kept_and_reported_without_silent_edits(self):
        (self.labels / "val" / "267.txt").write_text(
            "23 0.2 0.5 0.1 0.2\n23 0.6 0.5 0.1 0.2\n")
        result = j10r.stage(self.source, "fold_0", self.destination)
        self.assertEqual(result["annotations_qa"]["duplicate_fdi_instances_to_review"], 1)
        self.assertEqual((self.destination / "labels" / "val" / "267.txt").read_text(),
                         (self.labels / "val" / "267.txt").read_text())

    def test_missing_source_image_is_fail_closed(self):
        (self.source / "AKUDENTAL" / "images" / "267.jpg").unlink()
        with self.assertRaisesRegex(j10r.StageError, "source_image_missing_or_symlink"):
            j10r.stage(self.source, "fold_0", self.destination)
        self.assertFalse(self.destination.exists())

    def test_no_output_inside_source_tree(self):
        with self.assertRaisesRegex(j10r.StageError, "output_overlap"):
            j10r.stage(self.source, "fold_0", self.source / "working_copy")
        self.assertFalse((self.source / "working_copy").exists())

    def test_source_label_symlinks_are_refused(self):
        label = self.labels / "train" / "1.txt"
        label.unlink()
        label.symlink_to(self.labels / "train" / "2.txt")
        with self.assertRaisesRegex(j10r.StageError, "unsafe_source_label_file"):
            j10r.stage(self.source, "fold_0", self.destination)


if __name__ == "__main__":
    unittest.main()
