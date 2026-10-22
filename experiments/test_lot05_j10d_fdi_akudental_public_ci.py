"""Real-public-dataset runner safety tests: synthetic placeholders, no medical images."""
from pathlib import Path
import tempfile
import unittest

from lot05_j10d_fdi_akudental_public_ci import _safe_filename_resolution
from lot05_j10d_fdi_local_benchmark import BenchmarkError


class TestPublishedDatasetLoader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "nested").mkdir()
        for name in ("one.png", "two.jpg", "three.png"):
            (self.root / "nested" / name).write_bytes(b"synthetic_fake_bytes")
        self.source = {"images": [
            {"id": 9, "file_name": "one.png", "height": 10, "width": 10},
            {"id": 1, "file_name": "two.jpg", "height": 10, "width": 10},
            {"id": 5, "file_name": "three.png", "height": 10, "width": 10},
        ]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_numeric_deterministic_preselection(self):
        updated = _safe_filename_resolution(self.source, self.root, 2)
        by_id = {x["id"]:x["file_name"] for x in updated["images"]}
        self.assertEqual(by_id[9], "one.png")  # outside fixed 2-image selection
        self.assertEqual(by_id[1], "nested/two.jpg")
        self.assertEqual(by_id[5], "nested/three.png")
        self.assertEqual(self.source["images"][0]["file_name"], "one.png")

    def test_missing_sample_fails_closed(self):
        self.source["images"][1]["file_name"] = "absent.png"
        with self.assertRaisesRegex(BenchmarkError,"sample_image_missing_on_publisher_repo"):
            _safe_filename_resolution(self.source,self.root,2)

    def test_duplicate_basename_fails_closed(self):
        (self.root / "one.png").write_bytes(b"synthetic")
        with self.assertRaisesRegex(BenchmarkError,"ambiguous_public_image_basename"):
            _safe_filename_resolution(self.source,self.root,2)

    def test_input_sample_bounds_rejected(self):
        for amount in [0,-1,101]:
            with self.subTest(amount=amount),self.assertRaises(BenchmarkError):
                _safe_filename_resolution(self.source,self.root,amount)

    def test_no_image_files_fails_closed(self):
        for p in (self.root / "nested").iterdir():
            p.unlink()
        with self.assertRaisesRegex(BenchmarkError,"public_image_files_missing"):
            _safe_filename_resolution(self.source,self.root,2)


if __name__ == "__main__":
    unittest.main()
