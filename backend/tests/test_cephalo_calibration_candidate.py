import pytest

from backend.services.cephalo_calibration_candidate import (
    CalibrationCandidate,
    CalibrationCandidateError,
)


def test_candidate_is_geometry_only_and_unverified():
    candidate = CalibrationCandidate.from_ticks(
        axis_x_px=42,
        tick_positions_y_px=[10, 22, 34, 46, 58],
    )

    payload = candidate.to_payload()

    assert candidate.median_tick_spacing_px == 12
    assert payload["status"] == "CANDIDATE_UNVERIFIED"
    assert payload["mm_per_pixel"] is None
    assert payload["distance_mm"] is None
    assert payload["clinician_validated"] is False


def test_candidate_uses_median_spacing_without_physical_assumption():
    candidate = CalibrationCandidate.from_ticks(
        axis_x_px=8.5,
        tick_positions_y_px=[10, 20, 31, 41],
    )

    assert candidate.median_tick_spacing_px == 10
    assert "mm" not in candidate.detector_method.lower()


@pytest.mark.parametrize(
    "ticks",
    [[], [10], [10, 10], [20, 10], [10, float("nan")]],
)
def test_candidate_rejects_invalid_tick_geometry(ticks):
    with pytest.raises(CalibrationCandidateError):
        CalibrationCandidate.from_ticks(axis_x_px=12, tick_positions_y_px=ticks)
