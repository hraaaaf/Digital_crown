"""Synthetic-only adversarial FDI benchmark tests. No images or patient files."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from lot05_j10d_fdi_local_benchmark import (
    BenchmarkError, _case_metrics, _get_manifest, _read_predictions,
    _trusted_image_path, evaluate,
)

GT36 = {"fdi": "36", "bbox": [10, 10, 60, 60]}
GT37 = {"fdi": "37", "bbox": [70, 10, 120, 60]}
P36 = {**GT36, "confidence": .95}
P37 = {**GT37, "confidence": .90}
P37_AS_36 = {"fdi": "36", "bbox": [70, 10, 120, 60], "confidence": .80}


def case(i, *, gt=None, dentition="permanent"):
    return {"case_id": f"opaque-{i}", "height": 160, "width": 220,
            "dentition": dentition, "gt": [GT36, GT37] if gt is None else gt}


class TestBenchmark(unittest.TestCase):
    def test_all_correct_has_perfect_localization_and_numbering(self):
        result = evaluate([case(0)], {"opaque-0": [P36, P37]})
        self.assertEqual(result["overall"]["correct_number_and_localization_count"], 2)
        self.assertEqual(result["overall"]["fully_correct_films"], 1)
        self.assertEqual(result["overall"]["fdi_correct_recall"], 1)
        self.assertFalse(result["generalization_validated"])
        self.assertFalse(result["independence_proven_by_runner"])

    def test_neighbor_swap_localized_but_wrong_fdi(self):
        swapped = _case_metrics([GT36, GT37], [P36, P37_AS_36], height=160, width=220, iou_threshold=.5)
        self.assertEqual(swapped["localized"], 2)
        self.assertEqual(swapped["correct_fdi"], 1)
        self.assertEqual(swapped["wrong_fdi"], 1)
        self.assertEqual(swapped["neighbor_swaps"], 1)
        self.assertEqual(swapped["missed_teeth"], 0)
        self.assertEqual(swapped["duplicate_fdi_labels"], 1)

    def test_non_neighbor_swap(self):
        wrong = {"fdi": "46", "bbox": GT37["bbox"], "confidence": .9}
        r = _case_metrics([GT37], [wrong], height=160, width=220, iou_threshold=.5)
        self.assertEqual(r["other_swaps"], 1)
        self.assertEqual(r["neighbor_swaps"], 0)

    def test_missing_tooth_stays_missing(self):
        r = _case_metrics([GT36, GT37], [P36], height=160, width=220, iou_threshold=.5)
        self.assertEqual(r["missed_teeth"], 1)
        self.assertEqual(r["correct_fdi"], 1)
        self.assertEqual(r["fully_correct_film"], 0)

    def test_misplaced_box_unmatched(self):
        far = {"fdi": "36", "bbox": [150, 80, 170, 100], "confidence": .8}
        r = _case_metrics([GT36], [far], height=160, width=220, iou_threshold=.5)
        self.assertEqual(r["missed_teeth"], 1)
        self.assertEqual(r["unmatched_predictions"], 1)
        self.assertEqual(r["localized"], 0)

    def test_extra_false_positive(self):
        extra = {"fdi": "48", "bbox": [150, 80, 170, 100], "confidence": .8}
        r = _case_metrics([GT36], [P36, extra], height=160, width=220, iou_threshold=.5)
        self.assertEqual(r["unmatched_predictions"], 1)
        self.assertEqual(r["fully_correct_film"], 0)

    def test_empty_ground_truth_properly_not_infinite(self):
        r = _case_metrics([], [], height=160, width=220, iou_threshold=.5)
        self.assertEqual(r["fully_correct_film"], 1)
        report = evaluate([case(0, gt=[])], {"opaque-0": []})
        self.assertIsNone(report["overall"]["fdi_correct_recall"])
        self.assertEqual(report["overall"]["fully_correct_films"], 1)

    def test_small_groups_suppressed_and_ci_finite(self):
        cases = [case(i, dentition=("mixed" if i == 0 else "permanent")) for i in range(8)]
        predictions = {x["case_id"]: [P36, P37] for x in cases}
        r = evaluate(cases, predictions)
        self.assertEqual(r["by_dentition"]["mixed"]["status"], "SUPPRESSED_SMALL_SUBGROUP")
        self.assertEqual(r["by_dentition"]["permanent"]["films"], 7)
        self.assertEqual(r["bootstrap_95_percent_ci_fdi_recall_by_film"], [1.0, 1.0])

    def test_reject_invalid_iou(self):
        for threshold in [0, -1, 1.2, float("nan")]:
            with self.assertRaises(BenchmarkError):
                evaluate([case(0)], {"opaque-0": []}, iou_threshold=threshold)

    def test_reject_bad_annotations_and_confidence(self):
        base = [GT36]
        bad_guesses = [
            [{"fdi": "35", "bbox": [10, 10, 60, 60], "confidence": float("nan")}],
            [{"fdi": "55", "bbox": [10, 10, 60, 60], "confidence": .9}],
            [{"fdi": "36", "bbox": [10, 10, 260, 60], "confidence": .9}],
            [{"fdi": "36", "bbox": [60, 60, 10, 10], "confidence": .9}],
            [{"fdi": "36", "bbox": [10, 10, 60, 60], "confidence": 2.0}],
        ]
        for guesses in bad_guesses:
            with self.subTest(guesses=guesses), self.assertRaises(BenchmarkError):
                _case_metrics(base, guesses, height=160, width=220, iou_threshold=.5)

    def test_manifest_duplicate_and_malformed_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "manifest.json"
            p.write_text(json.dumps({"schema":"digital-crown-fdi-eval-v1", "cases":[case(0),case(0)]}))
            with self.assertRaisesRegex(BenchmarkError,"duplicate_case_ids"):
                _get_manifest(p)
            p.write_text(json.dumps({"schema":"wrong", "cases":[case(0)]}))
            with self.assertRaisesRegex(BenchmarkError,"wrong_manifest_schema"):
                _get_manifest(p)

    def test_predictions_must_cover_all_cases(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"pred.json"
            p.write_text(json.dumps({"schema":"digital-crown-fdi-predictions-v1", "predictions":{"unrecognized": []}}))
            with self.assertRaisesRegex(BenchmarkError,"missing_or_extra_prediction_cases"):
                _read_predictions(p, {"opaque-0"})

    def test_unsafe_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(BenchmarkError):
                _trusted_image_path(Path(td), "/etc/passwd")
            with self.assertRaises(Exception):
                _trusted_image_path(Path(td), "../etc/passwd")

    def test_complete_cli_round_trip_without_image_or_phi(self):
        # Test CLI via Python subprocess, so this also verifies imports, output schema
        # and report's case-ID/filename non-disclosure.
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "manifest.json"
            predictions = root / "predictions.json"
            output = root / "report.json"
            manifest.write_text(json.dumps({"schema": "digital-crown-fdi-eval-v1", "cases":[case(0)]}))
            predictions.write_text(json.dumps({"schema": "digital-crown-fdi-predictions-v1",
                "predictions":{"opaque-0":[P36,P37_AS_36]}}))
            run = subprocess.run([sys.executable, str(Path(__file__).with_name("lot05_j10d_fdi_local_benchmark.py")),
                    "--manifest", str(manifest), "--predictions", str(predictions),
                    "--report", str(output)], text=True, capture_output=True, check=True)
            report = output.read_text()
            self.assertIn('"wrong_number_on_localized_tooth": 1', report)
            self.assertNotIn("opaque-0", report)
            self.assertNotIn(str(root), report)
            self.assertNotIn("opaque-0", run.stdout)
            self.assertNotIn(str(root), run.stdout)


if __name__ == "__main__":
    unittest.main()
