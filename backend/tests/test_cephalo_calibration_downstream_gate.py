"""Fail-closed guard against silently retaining stale downstream clinical evidence."""
from datetime import datetime, timezone

import pytest

from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import CephaloRuntimeEvidenceError, build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING


def test_nonempty_downstream_payload_blocks_calibration_revision():
    raw = [
        {"id": name, "x": float(100 + i * 2), "y": float(120 + i * 3)}
        for i, name in SOTA_LANDMARKS_MAPPING.items()
    ]
    points = {item["id"]: (item["x"], item["y"]) for item in raw}
    first = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=CephaloEngine(mm_per_pixel=None).calculate_metrics(points),
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id="cephalo:downstream-gate",
    )
    first["diagnoses"] = [{"diagnosis_id": "stale-diagnosis"}]

    with pytest.raises(CephaloRuntimeEvidenceError, match="downstream clinical evidence"):
        rebuild_evidence_after_manual_calibration(
            previous_payload=first,
            patient_id=7,
            image_record_id="radio.jpg",
            result=CephaloEngine(mm_per_pixel=0.2).calculate_metrics(points),
            runtime_landmarks=raw,
            p1={"x": 0.0, "y": 0.0},
            p2={"x": 0.0, "y": 50.0},
            distance_mm=10.0,
            clinician_id="99",
            calibrated_at=datetime.now(timezone.utc),
        )
