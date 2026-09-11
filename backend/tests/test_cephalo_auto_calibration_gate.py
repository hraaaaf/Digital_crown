import pytest

from backend.services.cephalo_auto_calibration_gate import (
    AutoCalibrationState,
    ValidatedFiducialProfile,
    evaluate_auto_calibration,
)
from backend.services.cephalo_calibration_candidate import CalibrationCandidate


def _candidate(ticks):
    return CalibrationCandidate.from_ticks(axis_x_px=40, tick_positions_y_px=ticks)


def _profile(**overrides):
    values = {
        "profile_id": "TEST_RULER",
        "version": "1",
        "known_tick_spacing_mm": 10.0,
        "min_ticks": 5,
        "max_spacing_deviation_ratio": 0.05,
        "validation_reference": "test-fixture://validated-ruler-profile-v1",
    }
    values.update(overrides)
    return ValidatedFiducialProfile(**values)


def test_no_validated_physical_source_never_auto_verifies():
    decision = evaluate_auto_calibration(_candidate([10, 20, 30, 40, 50]), profile=None)

    assert decision.state is AutoCalibrationState.CANDIDATE_UNVERIFIED
    assert decision.reason == "NO_VALIDATED_PHYSICAL_SCALE_SOURCE"
    assert decision.mm_per_pixel is None
    assert decision.provenance is None


def test_validated_profile_and_regular_geometry_can_auto_verify():
    decision = evaluate_auto_calibration(
        _candidate([10, 20, 30, 40, 50]),
        profile=_profile(),
    )

    assert decision.state is AutoCalibrationState.AUTO_VERIFIED
    assert decision.mm_per_pixel == pytest.approx(1.0)
    assert decision.provenance["clinician_confirmed"] is False
    assert decision.provenance["profile_id"] == "TEST_RULER"
    assert decision.provenance["validation_reference"].startswith("test-fixture://")


def test_irregular_geometry_does_not_auto_verify_even_with_profile():
    decision = evaluate_auto_calibration(
        _candidate([10, 20, 30, 43, 53]),
        profile=_profile(),
    )

    assert decision.state is AutoCalibrationState.CANDIDATE_UNVERIFIED
    assert decision.reason == "TICK_GEOMETRY_OUTSIDE_PROFILE_TOLERANCE"
    assert decision.mm_per_pixel is None


def test_profile_minimum_tick_gate_is_profile_owned():
    decision = evaluate_auto_calibration(
        _candidate([10, 20, 30, 40, 50]),
        profile=_profile(min_ticks=6),
    )

    assert decision.state is AutoCalibrationState.CANDIDATE_UNVERIFIED
    assert decision.reason == "INSUFFICIENT_TICKS_FOR_PROFILE"


@pytest.mark.parametrize(
    "overrides",
    [
        {"known_tick_spacing_mm": 0},
        {"min_ticks": 1},
        {"max_spacing_deviation_ratio": -0.1},
        {"max_spacing_deviation_ratio": 1.0},
        {"validation_reference": ""},
    ],
)
def test_profile_rejects_unusable_physical_or_quality_contract(overrides):
    with pytest.raises(ValueError):
        _profile(**overrides)
