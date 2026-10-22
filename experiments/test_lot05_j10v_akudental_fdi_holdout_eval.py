"""J10V pure-geometry unit tests. No academic images, patient pixels or ML weights."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).with_name("lot05_j10v_akudental_fdi_holdout_eval.py")
spec = importlib.util.spec_from_file_location("j10v", path)
assert spec and spec.loader
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def record(pred_boxes, pred_cls, scores, gt_boxes, gt_cls):
    return ({"boxes": pred_boxes, "labels": pred_cls, "scores": scores},
            {"boxes": gt_boxes, "labels": gt_cls})


BOX = [0.1, 0.2, 0.7, 0.8]


class TestFDIEvaluation(unittest.TestCase):
    def test_perfect_tooth_match(self):
        result = v._exact([record([BOX], [1], [.9], [BOX], [1])], range(1, 33))
        self.assertEqual((result["tp"], result["fp"], result["fn"]), (1, 0, 0))
        self.assertEqual(result["precision"], 1.0)

    def test_wrong_tooth_fails_exact_but_appears_in_spatial_confusion(self):
        docs = [record([BOX], [2], [.8], [BOX], [1])]
        exact = v._exact(docs, range(1, 33))
        self.assertEqual((exact["tp"], exact["fp"], exact["fn"]), (0, 1, 1))
        matrix = v._spatial_confusion(docs)
        self.assertEqual(matrix["matrix_32x32"][0][1], 1)
        self.assertEqual(matrix["wrong_fdi_with_spatial_match"], 1)
        self.assertEqual(matrix["correct_fdi_with_spatial_match"], 0)

    def test_restoration_not_counted_as_tooth_tp(self):
        docs = [record([BOX], [33], [.9], [BOX], [33])]
        self.assertEqual(v._exact(docs, range(1, 33))["tp"], 0)
        self.assertEqual(v._exact(docs, range(33, 36))["tp"], 1)

    def test_spurious_prediction_counted_fp(self):
        docs = [record([[0, 0, .1, .1]], [1], [.9], [BOX], [1])]
        self.assertEqual(v._exact(docs, range(1, 33))["fp"], 1)
        self.assertEqual(v._exact(docs, range(1, 33))["fn"], 1)

    def test_score_threshold_is_fixed(self):
        docs = [record([BOX], [1], [.12], [BOX], [1])]
        self.assertEqual(v._exact(docs, range(1, 33), threshold=.25)["tp"], 0)
        self.assertEqual(v._exact(docs, range(1, 33), threshold=.05)["tp"], 1)

    def test_perfect_ap50(self):
        docs = [record([BOX], [1], [.99], [BOX], [1])]
        self.assertAlmostEqual(v._ap50_per_class(docs, range(1, 33))[1], 1, places=4)

    def test_no_gt_class_ap_is_null(self):
        docs = [record([BOX], [1], [.99], [BOX], [1])]
        self.assertIsNone(v._ap50_per_class(docs, range(1, 33))[2])

    def test_ap_has_penalty_for_initial_false_positive(self):
        docs = [record([[0, 0, .1, .1], BOX], [1, 1], [.99, .70], [BOX], [1])]
        ap = v._ap50_per_class(docs, range(1, 33))[1]
        self.assertTrue(0 < ap < 1)

    def test_duplicate_source_labels_are_aggregate_only(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            for split in ("train", "val", "test"):
                folder = root / "labels" / split
                folder.mkdir(parents=True)
                (folder / "fake-patient-identifier.txt").write_text(
                    "23 .4 .4 .2 .2\n23 .7 .7 .1 .1\n33 .5 .5 .1 .1\n")
            result = v._duplicates(root)
            self.assertEqual(result["val"]["extra_duplicate_fdi_instances"], 1)
            self.assertEqual(result["val"]["duplicates_by_fdi"], {"38": 1})
            self.assertNotIn("fake-patient-identifier", str(result))


if __name__ == "__main__":
    unittest.main()
