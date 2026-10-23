"""J10X structural tests: synthetic TXT labels only, no radiographs/Pillow."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

p = Path(__file__).with_name("lot05_j10x_local_private_fdi_visual_reviewer.py")
spec = importlib.util.spec_from_file_location("j10x", p)
assert spec and spec.loader
j10x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(j10x)


class TestLocalPrivateReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.labels = self.root / "labels"
        self.names = {}
        n = 0
        for split, count in j10x.J10W.SPLITS.items():
            d = self.labels / split
            d.mkdir(parents=True)
            self.names[split] = []
            for _ in range(count):
                n += 1
                p = d / (str(n) + ".txt")
                p.write_text("16 0.3 0.4 0.1 0.1\n17 0.7 0.4 0.1 0.1\n")
                self.names[split].append(p)

    def tearDown(self):
        self.temp.cleanup()

    def test_no_cases_without_duplicate_fdi(self):
        self.assertEqual(j10x.flagged_cases(self.labels), [])

    def test_28_synthetic_flagged_cases_only_private_id_list(self):
        for split, count in (("train", 23), ("val", 3), ("test", 2)):
            for p in self.names[split][:count]:
                p.write_text("16 0.2 0.4 0.1 0.1\n16 0.8 0.4 0.1 0.1\n")
        cases = j10x.flagged_cases(self.labels)
        self.assertEqual(len(cases), 28)
        self.assertEqual(sum(len(x[2]) for x in cases), 28)

    def test_missing_source_split_fails_closed(self):
        self.names["val"][0].unlink()
        with self.assertRaisesRegex(j10x.ReviewError, "source_split_count_mismatch"):
            j10x.flagged_cases(self.labels)

    def test_preexisting_output_refused_without_reading_images(self):
        private = self.root / "private"
        private.mkdir()
        with self.assertRaisesRegex(j10x.ReviewError, "output_already_exists"):
            j10x.private_review(self.root, self.labels, private)


if __name__ == "__main__":
    unittest.main()
