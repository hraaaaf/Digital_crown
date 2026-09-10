import datetime as dt
from types import SimpleNamespace

import pytest

import backend.services.cephalo_auto_calibration_transition as transition
from backend.services.cephalo_auto_calibration_gate import (
    AutoCalibrationDecision,
    AutoCalibrationState,
)
from backend.services.cephalo_runtime_evidence import EVIDENCE_SCHEMA_VERSION


def _decision():
    return AutoCalibrationDecision(
        state=AutoCalibrationState.AUTO_VERIFIED,
        reason="VALIDATED_PROFILE_AND_GEOMETRY_GATES_PASSED",
        mm_per_pixel=0.2,
        provenance={
            "schema_version": "CEPHALO_AUTO_CALIBRATION_V1",
            "state": "AUTO_VERIFIED",
            "detector_method": "CLASSICAL_RULER_GEOMETRY_V1",
            "profile_id": "TEST_RULER",
            "profile_version": "1",
            "validation_reference": "test-fixture://validated-ruler-profile-v1",
            "known_tick_spacing_mm": 5.0,
            "candidate_tick_count": 5,
            "median_tick_spacing_px": 25.0,
            "max_spacing_deviation_ratio": 0.0,
            "profile_max_spacing_deviation_ratio": 0.05,
            "mm_per_pixel": 0.2,
            "clinician_confirmed": False,
        },
    )


def _previous(**overrides):
    payload = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "case_id": "cephalo:case-12",
        "revision": 1,
        "history": [],
        "sources": [],
        "landmarks": [],
        "constructions": [],
        "measurements": [],
        "normative_evaluations": [],
        "findings": [],
        "diagnoses": [],
        "problems": [],
        "objectives": [],
        "treatment_options": [],
        "validations": [],
        "final_plans": [],
    }
    payload.update(overrides)
    return payload


def test_transition_builds_new_runtime_revision_with_auto_calibration(monkeypatch):
    captured = {}

    def fake_build(**kwargs):
        captured.update(kwargs)
        return {"revision": 2, "sources": [{"quality_status": "AUTO_VERIFIED_FIDUCIAL_PROFILE"}]}

    monkeypatch.setattr(transition, "build_cephalo_runtime_evidence_payload", fake_build)
    result = transition.rebuild_evidence_after_auto_calibration(
        previous_payload=_previous(),
        patient_id=12,
        image_record_id="radio-12.png",
        result=SimpleNamespace(),
        runtime_landmarks=[],
        inference_mode="SOTA_ONNX_38",
        decision=_decision(),
        calibrated_at=dt.datetime(2026, 9, 10, 20, 0, tzinfo=dt.timezone.utc),
    )

    assert result["revision"] == 2
    assert captured["previous_payload"]["revision"] == 1
    assert captured["is_calibrated"] is True
    assert captured["manual_revision"] is False
    assert captured["calibration_data"]["method"] == "AUTO_FIDUCIAL_PROFILE"
    assert captured["calibration_data"]["state"] == "AUTO_VERIFIED"
    assert captured["case_id"] == "cephalo:case-12"


def test_transition_rejects_candidate_only_decision():
    candidate = AutoCalibrationDecision(
        state=AutoCalibrationState.CANDIDATE_UNVERIFIED,
        reason="NO_VALIDATED_PHYSICAL_SCALE_SOURCE",
    )
    with pytest.raises(transition.AutoCalibrationTransitionError, match="AUTO_VERIFIED"):
        transition.auto_calibration_data_from_decision(candidate)


@pytest.mark.parametrize(
    "key",
    [
        "normative_evaluations",
        "findings",
        "diagnoses",
        "problems",
        "objectives",
        "treatment_options",
        "validations",
        "final_plans",
    ],
)
def test_transition_blocks_existing_downstream_clinical_evidence(key):
    payload = _previous(**{key: [{"existing": True}]})
    with pytest.raises(transition.AutoCalibrationTransitionError, match=key):
        transition.rebuild_evidence_after_auto_calibration(
            previous_payload=payload,
            patient_id=12,
            image_record_id="radio-12.png",
            result=SimpleNamespace(),
            runtime_landmarks=[],
            inference_mode="SOTA_ONNX_38",
            decision=_decision(),
            calibrated_at=dt.datetime(2026, 9, 10, 20, 0, tzinfo=dt.timezone.utc),
        )


def test_transition_rejects_naive_timestamp():
    with pytest.raises(transition.AutoCalibrationTransitionError, match="timezone-aware"):
        transition.rebuild_evidence_after_auto_calibration(
            previous_payload=_previous(),
            patient_id=12,
            image_record_id="radio-12.png",
            result=SimpleNamespace(),
            runtime_landmarks=[],
            inference_mode="SOTA_ONNX_38",
            decision=_decision(),
            calibrated_at=dt.datetime(2026, 9, 10, 20, 0),
        )
