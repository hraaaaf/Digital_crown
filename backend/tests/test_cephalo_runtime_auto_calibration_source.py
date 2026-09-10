import datetime as dt
from types import SimpleNamespace

import pytest

from backend.services.cephalo_auto_calibration_gate import (
    AutoCalibrationState,
    ValidatedFiducialProfile,
    evaluate_auto_calibration,
)
from backend.services.cephalo_calibration_candidate import CalibrationCandidate
from backend.services.cephalo_runtime_evidence import (
    CephaloRuntimeEvidenceError,
    _calibration_source,
)


def _result(ratio=1.0):
    return SimpleNamespace(analysis_metadata=SimpleNamespace(pixel_ratio=ratio))


def _auto_calibration_data():
    candidate = CalibrationCandidate.from_ticks(
        axis_x_px=40,
        tick_positions_y_px=[10, 20, 30, 40, 50],
    )
    profile = ValidatedFiducialProfile(
        profile_id="TEST_RULER",
        version="1",
        known_tick_spacing_mm=10.0,
        min_ticks=5,
        max_spacing_deviation_ratio=0.05,
        validation_reference="test-fixture://validated-ruler-profile-v1",
    )
    decision = evaluate_auto_calibration(candidate, profile=profile)
    return {
        "method": "AUTO_FIDUCIAL_PROFILE",
        "state": decision.state.value,
        "reason": decision.reason,
        "provenance": decision.provenance,
    }


def _source(*, result=None, data=None):
    return _calibration_source(
        patient_id=12,
        case_id="cephalo:case-12",
        image_record_id="radio-12.png",
        result=result or _result(),
        is_calibrated=True,
        calibration_data=data if data is not None else _auto_calibration_data(),
        recorded_at=dt.datetime(2026, 9, 10, 20, 0, tzinfo=dt.timezone.utc),
    )


def test_runtime_accepts_only_gated_auto_verified_source():
    source = _source()

    assert source.evidence_id == "source:cephalo:case-12:calibration"
    assert source.quality_status == "AUTO_VERIFIED_FIDUCIAL_PROFILE"
    assert source.operator_id is None
    assert source.metadata["method"] == "AUTO_FIDUCIAL_PROFILE"
    assert source.metadata["mm_per_pixel"] == pytest.approx(1.0)


def test_runtime_rejects_candidate_state_marked_as_calibrated():
    data = _auto_calibration_data()
    data["state"] = AutoCalibrationState.CANDIDATE_UNVERIFIED.value

    with pytest.raises(CephaloRuntimeEvidenceError, match="AUTO_VERIFIED"):
        _source(data=data)


def test_runtime_rejects_auto_ratio_that_disagrees_with_profile_provenance():
    with pytest.raises(CephaloRuntimeEvidenceError, match="mm_per_pixel|ratio"):
        _source(result=_result(0.9))


def test_runtime_rejects_unknown_calibration_method():
    with pytest.raises(CephaloRuntimeEvidenceError, match="Unsupported calibration method"):
        _source(data={"method": "MAGIC_SCALE_V0"})


def test_manual_two_point_path_remains_unchanged():
    source = _source(
        data={
            "method": "MANUAL_TWO_POINT",
            "p1": {"x": 0.0, "y": 0.0},
            "p2": {"x": 10.0, "y": 0.0},
            "distance_mm": 10.0,
        }
    )

    assert source.quality_status == "VERIFIED_MANUAL_TWO_POINT"
    assert source.metadata["method"] == "MANUAL_TWO_POINT"
    assert source.metadata["mm_per_pixel"] == pytest.approx(1.0)
