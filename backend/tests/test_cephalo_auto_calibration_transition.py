"""Safety proofs for AUTO_VERIFIED calibration-only evidence revisions."""
from datetime import datetime, timezone

import pytest

from backend.services.cephalo_auto_calibration_gate import (
    AutoCalibrationDecision,
    AutoCalibrationState,
    ValidatedFiducialProfile,
    evaluate_auto_calibration,
)
from backend.services.cephalo_auto_calibration_transition import (
    AutoCalibrationTransitionError,
    auto_calibration_data_from_decision,
    rebuild_evidence_after_auto_calibration,
)
from backend.services.cephalo_calibration_candidate import CalibrationCandidate
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_runtime_evidence import build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 10, 20, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 10, 20, 5, tzinfo=timezone.utc)
CASE_ID = "cephalo:auto-calibration-test"


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _initial(raw=None):
    raw = raw or _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    return build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=NOW,
    )


def _decision():
    candidate = CalibrationCandidate.from_ticks(axis_x_px=40, tick_positions_y_px=[10, 35, 60, 85, 110])
    profile = ValidatedFiducialProfile(
        profile_id="TEST_RULER", version="1", known_tick_spacing_mm=5.0, min_ticks=5,
        max_spacing_deviation_ratio=0.05,
        validation_reference="test-fixture://validated-ruler-profile-v1",
    )
    decision = evaluate_auto_calibration(candidate, profile=profile)
    assert decision.state is AutoCalibrationState.AUTO_VERIFIED
    assert decision.mm_per_pixel == pytest.approx(0.2)
    return decision


def _auto(previous=None, raw=None, *, at=NOW, image_record_id="radio.jpg"):
    previous = previous or _initial()
    raw = raw or _raw()
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(raw))
    return rebuild_evidence_after_auto_calibration(
        previous_payload=previous, patient_id=7, image_record_id=image_record_id,
        result=result, runtime_landmarks=raw, decision=_decision(), calibrated_at=at,
    )


def test_auto_calibration_creates_revision_and_unlocks_measurements_without_clinician_confirmation():
    previous = _initial()
    payload = _auto(previous)
    assert payload["revision"] == 2
    assert payload["revision_reason"] == "AUTO_CALIBRATION"
    assert payload["history"][-1]["revision"] == 1
    assert payload["landmarks"] == previous["landmarks"]
    assert payload["constructions"] == previous["constructions"]
    calibration = [source for source in payload["sources"] if source["kind"] == "calibration"]
    assert len(calibration) == 1
    source = calibration[0]
    assert source["operator_id"] is None
    assert source["quality_status"] == "AUTO_VERIFIED_FIDUCIAL_PROFILE"
    assert source["metadata"]["method"] == "AUTO_FIDUCIAL_PROFILE"
    assert source["metadata"]["clinician_confirmed"] is False
    assert source["metadata"]["profile_id"] == "TEST_RULER"
    measurements = payload["measurements"]
    assert all(item["availability_status"] == "AVAILABLE" for item in measurements)
    craniom = [item for item in measurements if item["analysis_id"] == "CRANIOM"]
    steiner = [item for item in measurements if item["analysis_id"] == "STEINER"]
    calibrated = [item for item in craniom if item["requires_calibration"]]
    craniom_angular = [item for item in craniom if not item["requires_calibration"]]
    assert len(calibrated) == 4
    assert all(item["calibration_ref"] == source["evidence_id"] for item in calibrated)
    assert {item["method_id"] for item in craniom_angular} == {
        "CRANIOM_U1_FRANKFORT_DEG_V1", "CRANIOM_L1_DOWNS_DEG_V1", "CRANIOM_INTERINCISAL_DEG_V1",
    }
    assert all(item["unit"] == "deg" for item in craniom_angular)
    assert all(item["calibration_ref"] is None for item in craniom_angular)
    assert all(source["evidence_id"] not in item["evidence_refs"] for item in craniom_angular)
    assert {item["method_id"] for item in steiner} == {
        "STEINER_SNA_DEG_V1", "STEINER_SNB_DEG_V1", "STEINER_ANB_DEG_V1",
        "STEINER_U1_NA_DEG_V1", "STEINER_L1_NB_DEG_V1", "STEINER_SN_MP_DEG_V1",
    }
    assert all(item["requires_calibration"] is False for item in steiner)
    assert all(item["calibration_ref"] is None for item in steiner)


def test_auto_calibration_preserves_corrected_landmark_and_current_refs_exactly():
    raw = _raw()
    edited = [dict(item) for item in raw]
    target = next(item for item in edited if item["id"] == "A")
    target["x"] += 4.0
    edit_result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(edited))
    corrected = rebuild_evidence_after_landmark_edit(
        previous_payload=_initial(raw), patient_id=7, image_record_id="radio.jpg",
        result=edit_result, runtime_landmarks=edited, clinician_id="99", validated_at=NOW,
    )
    corrected_a_before = next(item for item in corrected["landmarks"] if item["landmark_id"] == "A" and item["origin"] == "MANUAL_CORRECTED")
    calibrated = _auto(corrected, edited, at=LATER)
    corrected_a_after = next(item for item in calibrated["landmarks"] if item["landmark_id"] == "A" and item["origin"] == "MANUAL_CORRECTED")
    assert calibrated["revision"] == corrected["revision"] + 1
    assert calibrated["landmarks"] == corrected["landmarks"]
    assert calibrated["constructions"] == corrected["constructions"]
    assert calibrated["current_landmark_refs"] == corrected["current_landmark_refs"]
    assert corrected_a_after == corrected_a_before
    assert corrected_a_after["validated_by"] == "99"


def test_auto_calibration_rejects_runtime_landmarks_different_from_current_evidence():
    previous = _initial()
    changed = _raw()
    changed[4] = {**changed[4], "x": changed[4]["x"] + 1.0}
    with pytest.raises(AutoCalibrationTransitionError, match="differs from persisted evidence"):
        _auto(previous, changed)


@pytest.mark.parametrize("key", ["normative_evaluations", "findings", "diagnoses", "problems", "objectives", "treatment_options", "validations", "final_plans"])
def test_auto_calibration_blocks_existing_downstream_clinical_evidence(key):
    previous = {**_initial(), key: [{"existing": True}]}
    with pytest.raises(AutoCalibrationTransitionError, match=key):
        _auto(previous)


def test_auto_calibration_rejects_wrong_cephalogram_identity():
    with pytest.raises(AutoCalibrationTransitionError, match="source record mismatch"):
        _auto(_initial(), image_record_id="other-radio.jpg")


def test_candidate_only_decision_cannot_enter_transition():
    candidate = AutoCalibrationDecision(state=AutoCalibrationState.CANDIDATE_UNVERIFIED, reason="NO_VALIDATED_PHYSICAL_SCALE_SOURCE")
    with pytest.raises(AutoCalibrationTransitionError, match="AUTO_VERIFIED"):
        auto_calibration_data_from_decision(candidate)


def test_auto_calibration_rejects_naive_timestamp():
    with pytest.raises(AutoCalibrationTransitionError, match="timezone-aware"):
        _auto(at=datetime(2026, 9, 10, 20, 0))
