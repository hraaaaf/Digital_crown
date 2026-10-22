"""J10T offline regression tests; no real radiographs, weights or network."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

p = Path(__file__).with_name("lot05_j10t_akudental_torchvision_pilot.py")
spec = importlib.util.spec_from_file_location("j10t", p)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestPilotSafety(unittest.TestCase):
    def test_bbox_iou_identical(self):
        self.assertAlmostEqual(mod._bbox_iou([0, 0, 2, 2], [0, 0, 2, 2]), 1)

    def test_bbox_iou_disjoint(self):
        self.assertEqual(mod._bbox_iou([0, 0, 1, 1], [2, 2, 3, 3]), 0)

    def test_bbox_iou_partial(self):
        self.assertAlmostEqual(mod._bbox_iou([0, 0, 2, 2], [1, 1, 3, 3]), 1 / 7)

    def test_reproducible_fixed_cap_subsampling(self):
        a = [str(i) for i in range(1, 267)]
        self.assertEqual(mod._choose(a, 24), mod._choose(a, 24))
        self.assertEqual(len(mod._choose(a, 24)), 24)
        self.assertEqual(len(set(mod._choose(a, 24))), 24)

    def test_all_splits_required_without_real_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            with self.assertRaisesRegex(ValueError, "missing_split_directory"):
                mod._ids(p, "test")


if __name__ == "__main__":
    unittest.main()
