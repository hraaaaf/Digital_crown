"""J10Q synthetic regression tests. No actual images or third-party annotations."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).with_name("lot05_j10q_akudental_fdi_yolo_text_only.py")
spec = importlib.util.spec_from_file_location("j10q", MODULE)
assert spec and spec.loader
j10q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(j10q)


class TestAKUDENTALYOLO(unittest.TestCase):
    def test_fdi_mapping_is_exact(self):
        self.assertEqual(len(j10q.FDI), 32)
        self.assertEqual(j10q.FDI[0], "11")
        self.assertEqual(j10q.FDI[31], "48")
        self.assertEqual(j10q.RESTORATIONS, ("bridge", "filling_crown", "implant"))

    def test_valid_text_with_restorations(self):
        result = j10q.audit_label_text("0 0.5 0.5 0.2 0.3\n31 0.6 0.4 0.2 0.3\n32 0.5 0.5 0.8 0.6\n34 0.4 0.5 0.2 0.3\n")
        self.assertEqual(result["instance_count"], 4)
        self.assertEqual(result["tooth_instances"], 2)
        self.assertEqual(result["distinct_tooth_positions"], 2)
        self.assertEqual(result["extra_restoration_instances"]["bridge"], 1)
        self.assertFalse(result["commercial_training_authorized"])
        self.assertFalse(result["pixels_read"])

    def test_missing_tooth_is_not_error(self):
        result = j10q.audit_label_text("14 0.5 0.5 0.2 0.4\n")
        self.assertEqual(result["distinct_tooth_positions"], 1)

    def test_duplicate_tooth_is_flagged_not_silenced(self):
        result = j10q.audit_label_text("1 0.5 0.5 0.2 0.2\n1 0.6 0.7 0.1 0.1\n")
        self.assertEqual(result["duplicate_fdi_instances"], 1)

    def test_incompatible_yolo_segmentation_rows_are_refused(self):
        with self.assertRaisesRegex(j10q.LabelAuditError, "five_yolo_columns"):
            j10q.audit_label_text("0 0.1 0.1 0.4 0.4 0.5 0.5\n")

    def test_non_finite_geometry_is_refused(self):
        for token in ("NaN", "inf", "-inf"):
            with self.subTest(token=token):
                with self.assertRaises(j10q.LabelAuditError):
                    j10q.audit_label_text("2 0.3 0.4 " + token + " 0.2\n")

    def test_box_extending_off_image_is_refused(self):
        with self.assertRaisesRegex(j10q.LabelAuditError, "bbox_outside_image_frame"):
            j10q.audit_label_text("0 0.99 0.5 0.20 0.4\n")

    def test_unknown_class_is_refused(self):
        for cls in ("35", "99", "-1", "0.0"):
            with self.subTest(cls=cls):
                with self.assertRaises(j10q.LabelAuditError):
                    j10q.audit_label_text(cls + " 0.4 0.5 0.2 0.3")

    def test_no_image_or_labelme_json_can_be_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "label.json").write_text('{"imageData":"pixels"}')
            (root / "x.jpg").write_bytes(b"pixels")
            for item in ("label.json", "x.jpg"):
                with self.subTest(item=item):
                    with self.assertRaisesRegex(j10q.LabelAuditError, "unsafe_or_missing_label_file"):
                        j10q.inspect_files([root / item])

    def test_valid_local_text_aggregates_no_file_names_or_coordinates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p1, p2 = root / "patient_alpha.txt", root / "patient_beta.txt"
            p1.write_text("0 0.51 0.51 0.20 0.3\n32 0.3 0.4 0.2 0.2\n")
            p2.write_text("31 0.4 0.5 0.3 0.3\n")
            report = j10q.inspect_files([p1, p2])
            self.assertEqual(report["files_checked"], 2)
            self.assertEqual(report["instances"], 3)
            self.assertEqual(report["tooth_instances"], 2)
            self.assertNotIn("alpha", str(report))
            self.assertNotIn("0.51", str(report))
            self.assertFalse(report["patient_level_independence_proven"])

    def test_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            safe = folder / "safe.txt"
            safe.write_text("0 0.5 0.5 0.2 0.2")
            link = folder / "link.txt"
            link.symlink_to(safe)
            with self.assertRaisesRegex(j10q.LabelAuditError, "unsafe_or_missing_label_file"):
                j10q.inspect_files([link])

    def test_duplicate_file_input_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "a.txt"
            path.write_text("0 0.5 0.5 0.2 0.2")
            with self.assertRaisesRegex(j10q.LabelAuditError, "unsafe_or_missing_label_file"):
                j10q.inspect_files([path, path])


if __name__ == "__main__":
    unittest.main()
