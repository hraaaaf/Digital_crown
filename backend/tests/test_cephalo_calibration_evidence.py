"""Tests for audited manual-calibration evidence revisions."""
from datetime import datetime, timezone

import pytest

from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import (
    CephaloRuntimeEvidenceError,
    build_cephalo_runtime_evidence_payload,
)
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 10, 14, 30, tzinfo=timezone.utc)
CASE_ID = "cephalo:calibration-test"


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw=None):
    return {item["id"]: (item["x"], item["y"]) for item in (raw or _raw())}


def _initial():
    raw = _raw()
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


def _calibrated(previous=None, raw=None):
    previous = previous or _initial()
    raw = raw or _raw()
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(raw))
    return rebuild_evidence_after_manual_calibration(
        previous_payload=previous,
        patient_id=7,
        image_record_id="radio.jpg",
        result=result,
        runtime_landmarks=raw,
        p1={"x": 0.0, "y": 0.0},
        p2={"x": 0.0, "y": 50.0},
        distance_mm=10.0,
        clinician_id="99",
        calibrated_at=NOW,
    )


def test_manual_calibration_creates_audited_revision_unlocks_linear_and_preserves_u1():
    previous = _initial()
    payload = _calibrated(previous)

    assert payload["revision"] == 2
    assert payload["revision_reason"] == "MANUAL_CALIBRATION"
    assert len(payload["history"]) == 1
    assert payload["history"][0]["revision"] == 1

    calibration = [source for source in payload["sources"] if source["kind"] == "calibration"]
    assert len(calibration) == 1
    assert calibration[0]["operator_id"] == "99"
    assert datetime.fromisoformat(calibration[0]["recorded_at"].replace("Z", "+00:00")) == NOW
    assert calibration[0]["metadata"]["method_version"] == "1"
    assert calibration[0]["metadata"]["calibrated_by"] == "99"

    assert len(payload["measurements"]) == 5
    assert all(item["availability_status"] == "AVAILABLE" for item in payload["measurements"])
    linear = [item for item in payload["measurements"] if item["requires_calibration"]]
    angular = [item for item in payload["measurements"] if not item["requires_calibration"]]
    assert len(linear) == 4
    assert all(item["calibration_ref"] == calibration[0]["evidence_id"] for item in linear)
    assert len(angular) == 1
    assert angular[0]["method_id"] == "CRANIOM_U1_FRANKFORT_DEG_V1"
    assert angular[0]["calibration_ref"] is None


def test_calibration_rejects_runtime_landmarks_different_from_persisted_evidence():
    raw = _raw()
    raw[4] = {**raw[4], "x": raw[4]["x"] + 5.0}
    with pytest.raises(CephaloRuntimeEvidenceError, match="differs from persisted evidence"):
        _calibrated(raw=raw)


def test_calibration_refuses_to_silently_keep_downstream_clinical_objects():
    previous = {**_initial(), "findings": [{"finding_id": "stale"}]}
    with pytest.raises(CephaloRuntimeEvidenceError, match="downstream clinical evidence"):
        _calibrated(previous=previous)


def test_calibration_rejects_wrong_cephalogram_identity():
    previous = _initial()
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    with pytest.raises(CephaloRuntimeEvidenceError, match="source record mismatch"):
        rebuild_evidence_after_manual_calibration(
            previous_payload=previous,
            patient_id=7,
            image_record_id="other-radio.jpg",
            result=result,
            runtime_landmarks=_raw(),
            p1={"x": 0.0, "y": 0.0},
            p2={"x": 0.0, "y": 50.0},
            distance_mm=10.0,
            clinician_id="99",
            calibrated_at=NOW,
        )
