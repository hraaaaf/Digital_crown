"""J10W geometry triage tests use 333 synthetic small text records, never pixels."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

p = Path(__file__).with_name("lot05_j10w_akudental_duplicate_fdi_root_cause.py")
spec = importlib.util.spec_from_file_location("j10w", p)
assert spec and spec.loader
j10w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(j10w)


class TestResearchTriage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.labels = self.root / "labels"
        self.files = {}
        counter = 0
        for split, size in j10w.SPLITS.items():
            folder = self.labels / split
            folder.mkdir(parents=True)
            self.files[split] = []
            for _ in range(size):
                counter += 1
                name = folder / f"{counter}.txt"
                name.write_text("16 .40 .4 .1 .2\n17 .55 .4 .1 .2\n11 .3 .5 .2 .2\n", encoding="utf-8")
                self.files[split].append(name)

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_synthetic_audit_without_images(self):
        r = j10w.audit_labels(self.labels)
        self.assertEqual(r["source_labels_examined"], 333)
        self.assertEqual(r["duplicate_qa"]["images_flagged_total"], 0)
        self.assertEqual(r["per_fdi"]["31"]["total_instances"], 333)
        self.assertEqual(r["per_fdi"]["32"]["total_instances"], 333)
        self.assertEqual(r["per_fdi"]["24"]["total_instances"], 333)
        self.assertFalse(r["images_read"])
        self.assertFalse(r["expert_visual_review_performed"])
        self.assertFalse(r["source_rights_commercial_verified"])

    def test_duplicate_overlapping_box_and_separated_pair(self):
        self.files["val"][0].write_text(
            "16 .4 .4 .1 .2\n16 .4 .4 .1 .2\n17 .55 .4 .1 .2\n", encoding="utf-8")
        self.files["test"][0].write_text(
            "17 .2 .2 .1 .1\n17 .8 .8 .1 .1\n16 .5 .5 .1 .2\n", encoding="utf-8")
        r = j10w.audit_labels(self.labels)
        d = r["duplicate_qa"]
        self.assertEqual(d["images_flagged_total"], 2)
        self.assertEqual(d["extra_same_fdi_records_total"], 2)
        self.assertEqual(d["pairs_iou_gt_070"], 1)
        self.assertEqual(d["pairs_iou_lt_030"], 1)
        self.assertEqual(d["duplicates_by_fdi"], {"31": 1, "32": 1})

    def test_different_labels_do_not_count_as_duplicate(self):
        r = j10w.audit_labels(self.labels)
        self.assertEqual(r["duplicate_qa"]["pairs_examined"], 0)

    def test_private_manifest_never_printed_in_aggregate(self):
        self.files["train"][1].write_text(
            "16 .2 .3 .1 .1\n16 .6 .7 .1 .1\n", encoding="utf-8")
        manifest = self.root / "approved_private_review.json"
        r = j10w.audit_labels(self.labels, private_manifest=manifest)
        self.assertTrue(manifest.exists())
        self.assertIn('"source_image_basename"', manifest.read_text())
        self.assertNotIn("source_image_basename", str(r))
        self.assertEqual(r["duplicate_qa"]["images_flagged_total"], 1)

    def test_missing_split_count_fails_closed(self):
        self.files["train"][0].unlink()
        with self.assertRaisesRegex(j10w.TriageError, "source_split_file_count_mismatch"):
            j10w.audit_labels(self.labels)

    def test_existing_private_manifest_refused(self):
        existing = self.root / "existing.json"
        existing.write_text("{}")
        with self.assertRaisesRegex(j10w.TriageError, "private_manifest_output_must_not_exist"):
            j10w.audit_labels(self.labels, private_manifest=existing)


if __name__ == "__main__":
    unittest.main()
