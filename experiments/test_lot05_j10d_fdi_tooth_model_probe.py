"""LOT05/J10D FDI-only contract tests; synthetic numbers and boxes, not patient data."""
import unittest
import numpy as np

from lot05_j10d_fdi_tooth_model_probe import (
    CLASS_ORDER, verify_names, validate_detections, FDIProbeError,
)

NAMES = {idx: code for idx, code in enumerate(CLASS_ORDER)}


class TestFDIContract(unittest.TestCase):
    def test_exact_32_labels(self):
        self.assertEqual(verify_names(NAMES), CLASS_ORDER)
        self.assertEqual(CLASS_ORDER[0], "11")
        self.assertEqual(CLASS_ORDER[8], "21")
        self.assertEqual(CLASS_ORDER[16], "31")
        self.assertEqual(CLASS_ORDER[24], "41")
        self.assertEqual(CLASS_ORDER[-1], "48")

    def test_swapped_neighbor_label_rejected(self):
        bad = dict(NAMES); bad[0], bad[1] = bad[1], bad[0]
        with self.assertRaisesRegex(FDIProbeError, "fdi_label_order_mismatch"):
            verify_names(bad)

    def test_bad_count_or_unknown_class_rejected(self):
        for bad in [{}, dict(list(NAMES.items())[:-1]), {**NAMES, 32: "51"}]:
            with self.subTest(bad=bad), self.assertRaises(FDIProbeError):
                verify_names(bad)

    def test_missing_teeth_are_not_auto_numbered(self):
        out = validate_detections(np.array([0., 2.]),
              np.array([[100., 100., 150., 200.],[200., 100., 250., 200.]]),
              np.array([0.9, 0.8]), (512, 1024))
        self.assertEqual(out["proposals"], 2)
        self.assertEqual(out["unique_fdi"], 2)
        self.assertIn("12", out["missing_fdi_do_not_autofill"])

    def test_duplicate_fdi_flagged_not_silently_accepted(self):
        out = validate_detections([0, 0], [[100,100,150,200],[200,100,250,200]],
                                  [0.9,0.8], (512,1024))
        self.assertEqual(out["duplicate_fdi_needs_review"], ["11"])

    def test_empty_is_allowed_with_manual_override(self):
        out = validate_detections([], np.empty((0,4)), [], (512,1024))
        self.assertEqual(out["proposals"], 0)
        self.assertEqual(len(out["missing_fdi_do_not_autofill"]), 32)

    def test_invalid_box_confidence_and_class_fail_closed(self):
        cases = [
            ([32], [[100,100,150,200]], [0.8]),
            ([1.5], [[100,100,150,200]], [0.8]),
            ([1], [[100,100,150,200]], [1.2]),
            ([1], [[100,100,150,200]], [float("nan")]),
            ([1], [[150,100,100,200]], [0.8]),
            ([1], [[150,100,1050,200]], [0.8]),
        ]
        for labels, boxes, conf in cases:
            with self.subTest(labels=labels, boxes=boxes, conf=conf), self.assertRaises(FDIProbeError):
                validate_detections(labels, boxes, conf, (512,1024))

    def test_no_forced_full_dentition(self):
        out = validate_detections([0], [[100,100,140,190]], [0.9], (512,1024))
        self.assertEqual(out["unique_fdi"], 1)
        self.assertEqual(len(out["missing_fdi_do_not_autofill"]), 31)


if __name__ == "__main__":
    unittest.main()
