"""Tests services/temporal_comparator.py — compare_panoramic_analyses."""
from datetime import datetime
from unittest.mock import MagicMock

from backend.services.temporal_comparator import compare_panoramic_analyses


def _make_analysis(detections):
    """Build a mock PanoramicAnalysis with a given detections_data."""
    mock = MagicMock()
    mock.detections_data = {"detections": detections}
    mock.created_at = datetime(2025, 1, 1)
    return mock


class TestComparePanoramicAnalyses:
    def test_stable_when_identical(self):
        det = [{"class_name": "carie", "tooth_fdi": "36", "confidence": 0.9}]
        older = _make_analysis(det)
        newer = _make_analysis(det)
        result = compare_panoramic_analyses(older, newer)
        assert result["new_findings"] == []
        assert result["resolved_findings"] == []
        assert result["worsened_findings"] == []
        assert len(result["stable_findings"]) == 1
        assert "stable" in result["summary_text"].lower()

    def test_new_finding_detected(self):
        older = _make_analysis([])
        newer = _make_analysis([
            {"class_name": "carie", "tooth_fdi": "36", "confidence": 0.85}
        ])
        result = compare_panoramic_analyses(older, newer)
        assert len(result["new_findings"]) == 1
        assert "carie" in result["new_findings"][0]
        assert "nouvelle" in result["summary_text"]

    def test_resolved_finding_detected(self):
        older = _make_analysis([
            {"class_name": "tartre", "tooth_fdi": "11", "confidence": 0.7}
        ])
        newer = _make_analysis([])
        result = compare_panoramic_analyses(older, newer)
        assert len(result["resolved_findings"]) == 1
        assert "tartre" in result["resolved_findings"][0]
        assert "résolue" in result["summary_text"]

    def test_worsened_finding_detected(self):
        older = _make_analysis([
            {"class_name": "carie", "tooth_fdi": "46", "confidence": 0.5}
        ])
        newer = _make_analysis([
            {"class_name": "carie", "tooth_fdi": "46", "confidence": 0.75}
        ])
        result = compare_panoramic_analyses(older, newer)
        assert len(result["worsened_findings"]) >= 1
        assert "carie" in result["worsened_findings"][0]
        assert "aggravée" in result["worsened_findings"][0]
        assert "Aggravation" in result["summary_text"]

    def test_no_worsening_below_threshold(self):
        older = _make_analysis([
            {"class_name": "carie", "tooth_fdi": "36", "confidence": 0.60}
        ])
        newer = _make_analysis([
            {"class_name": "carie", "tooth_fdi": "36", "confidence": 0.65}
        ])
        result = compare_panoramic_analyses(older, newer)
        assert result["worsened_findings"] == []

    def test_empty_both_analyses_is_stable(self):
        older = _make_analysis([])
        newer = _make_analysis([])
        result = compare_panoramic_analyses(older, newer)
        assert result["new_findings"] == []
        assert result["resolved_findings"] == []
        assert "stable" in result["summary_text"].lower()

    def test_multiple_teeth(self):
        older = _make_analysis([
            {"class_name": "carie", "tooth_fdi": "16", "confidence": 0.8},
            {"class_name": "tartre", "tooth_fdi": "11", "confidence": 0.6},
        ])
        newer = _make_analysis([
            {"class_name": "carie", "tooth_fdi": "16", "confidence": 0.8},
            {"class_name": "implant", "tooth_fdi": "26", "confidence": 0.95},
        ])
        result = compare_panoramic_analyses(older, newer)
        assert len(result["new_findings"]) == 1       # implant
        assert len(result["resolved_findings"]) == 1  # tartre resolved
        assert len(result["stable_findings"]) == 1    # carie stable

    def test_counts_in_result(self):
        older = _make_analysis([
            {"class_name": "a", "tooth_fdi": "11", "confidence": 0.9}
        ])
        newer = _make_analysis([
            {"class_name": "b", "tooth_fdi": "12", "confidence": 0.9}
        ])
        result = compare_panoramic_analyses(older, newer)
        assert result["older_count"] == 1
        assert result["newer_count"] == 1

    def test_dates_in_result(self):
        older = _make_analysis([])
        newer = _make_analysis([])
        older.created_at = datetime(2024, 6, 1)
        newer.created_at = datetime(2025, 1, 15)
        result = compare_panoramic_analyses(older, newer)
        assert result["older_date"] == "2024-06-01"
        assert result["newer_date"] == "2025-01-15"

    def test_unknown_tooth_fdi(self):
        older = _make_analysis([])
        newer = _make_analysis([
            {"class_name": "carie", "confidence": 0.8}  # no tooth_fdi → unknown
        ])
        result = compare_panoramic_analyses(older, newer)
        assert len(result["new_findings"]) == 1
        assert "inconnue" in result["new_findings"][0]
