"""Calibration timestamps must be auditable across time zones."""
from datetime import datetime

import pytest

from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import CephaloRuntimeEvidenceError, build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING


def test_naive_calibration_timestamp_is_rejected():
    raw = [{"id": name, "x": float(100 + i), "y": float(120 + i)} for i, name in SOTA_LANDMARKS_MAPPING.items()]
    points = {item["id"]: (item["x"], item["y"]) for item in raw}
    previous = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=CephaloEngine(mm_per_pixel=None).calculate_metrics(points),
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id="cephalo:timestamp-required",
    )
    with pytest.raises(CephaloRuntimeEvidenceError, match="timezone-aware"):
        rebuild_evidence_after_manual_calibration(
            previous_payload=previous,
            patient_id=7,
            image_record_id="radio.jpg",
            result=CephaloEngine(mm_per_pixel=0.2).calculate_metrics(points),
            runtime_landmarks=raw,
            p1={"x": 0.0, "y": 0.0},
            p2={"x": 0.0, "y": 50.0},
            distance_mm=10.0,
            clinician_id="99",
            calibrated_at=datetime(2026, 9, 10, 14, 0),
        )
