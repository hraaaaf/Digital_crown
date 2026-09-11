"""Proofs that clinician confirmation is optional and never alters calibrated values."""
from datetime import datetime, timezone

import pytest

from backend.services.cephalo_auto_calibration_confirmation import (
    AutoCalibrationConfirmationError,
    confirm_auto_calibration,
)
from backend.services.cephalo_auto_calibration_gate import (
    ValidatedFiducialProfile,
    evaluate_auto_calibration,
)
from backend.services.cephalo_auto_calibration_transition import rebuild_evidence_after_auto_calibration
from backend.services.cephalo_calibration_candidate import CalibrationCandidate
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 10, 20, 0, tzinfo=timezone.utc)
CONFIRMED = datetime(2026, 9, 10, 20, 10, tzinfo=timezone.utc)
CASE_ID = "cephalo:auto-confirm-test"


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _auto_verified_payload():
    raw = _raw()
    initial_result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    initial = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=initial_result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=NOW,
    )
    candidate = CalibrationCandidate.from_ticks(
        axis_x_px=40,
        tick_positions_y_px=[10, 35, 60, 85, 110],
    )
    profile = ValidatedFiducialProfile(
        profile_id="TEST_RULER",
        version="1",
        known_tick_spacing_mm=5.0,
        min_ticks=5,
        max_spacing_deviation_ratio=0.05,
        validation_reference="test-fixture://validated-ruler-profile-v1",
    )
    decision = evaluate_auto_calibration(candidate, profile=profile)
    calibrated_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(raw))
    return rebuild_evidence_after_auto_calibration(
        previous_payload=initial,
        patient_id=7,
        image_record_id="radio.jpg",
        result=calibrated_result,
        runtime_landmarks=raw,
        decision=decision,
        calibrated_at=NOW,
    )


def test_confirmation_is_audit_only_and_preserves_values_and_geometry():
    previous = _auto_verified_payload()
    payload = confirm_auto_calibration(
        previous_payload=previous,
        patient_id=7,
        clinician_id="99",
        confirmed_at=CONFIRMED,
    )

    assert payload["revision"] == previous["revision"] + 1
    assert payload["revision_reason"] == "CLINICIAN_CALIBRATION_CONFIRMATION"
    assert payload["landmarks"] == previous["landmarks"]
    assert payload["constructions"] == previous["constructions"]
    assert [item["value"] for item in payload["measurements"]] == [
        item["value"] for item in previous["measurements"]
    ]

    source = next(item for item in payload["sources"] if item["kind"] == "calibration")
    assert source["operator_id"] == "99"
    assert source["evidence_status"] == "CLINICIAN_VALIDATED"
    assert source["quality_status"] == "CLINICIAN_CONFIRMED_AUTO_FIDUCIAL_PROFILE"
    assert source["metadata"]["auto_gate_state"] == "AUTO_VERIFIED"
    assert source["metadata"]["clinician_confirmed"] is True
    assert source["metadata"]["confirmed_by"] == "99"
    assert source["metadata"]["profile_id"] == "TEST_RULER"
    assert all(item["calibration_ref"] == source["evidence_id"] for item in payload["measurements"])


def test_confirmation_preserves_current_landmark_refs_when_present():
    previous = _auto_verified_payload()
    refs = [item["evidence_id"] for item in previous["landmarks"]]
    previous = {**previous, "current_landmark_refs": refs}

    payload = confirm_auto_calibration(
        previous_payload=previous,
        patient_id=7,
        clinician_id="99",
        confirmed_at=CONFIRMED,
    )

    assert payload["current_landmark_refs"] == refs


def test_confirmation_rejects_non_auto_calibration_source():
    previous = _auto_verified_payload()
    calibration = next(item for item in previous["sources"] if item["kind"] == "calibration")
    calibration["quality_status"] = "VERIFIED_MANUAL_TWO_POINT"
    calibration["metadata"]["method"] = "MANUAL_TWO_POINT"

    with pytest.raises(AutoCalibrationConfirmationError, match="AUTO_VERIFIED"):
        confirm_auto_calibration(
            previous_payload=previous,
            patient_id=7,
            clinician_id="99",
            confirmed_at=CONFIRMED,
        )


def test_confirmation_rejects_second_confirmation():
    previous = _auto_verified_payload()
    first = confirm_auto_calibration(
        previous_payload=previous,
        patient_id=7,
        clinician_id="99",
        confirmed_at=CONFIRMED,
    )

    with pytest.raises(AutoCalibrationConfirmationError, match="AUTO_VERIFIED|already"):
        confirm_auto_calibration(
            previous_payload=first,
            patient_id=7,
            clinician_id="99",
            confirmed_at=CONFIRMED,
        )


def test_confirmation_rejects_naive_timestamp():
    with pytest.raises(AutoCalibrationConfirmationError, match="timezone-aware"):
        confirm_auto_calibration(
            previous_payload=_auto_verified_payload(),
            patient_id=7,
            clinician_id="99",
            confirmed_at=datetime(2026, 9, 10, 20, 10),
        )


def test_confirmation_blocks_downstream_clinical_evidence():
    previous = {**_auto_verified_payload(), "findings": [{"existing": True}]}
    with pytest.raises(AutoCalibrationConfirmationError, match="findings"):
        confirm_auto_calibration(
            previous_payload=previous,
            patient_id=7,
            clinician_id="99",
            confirmed_at=CONFIRMED,
        )
