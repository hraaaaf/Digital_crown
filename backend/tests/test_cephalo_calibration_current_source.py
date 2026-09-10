"""Calibration source must remain bound to the current typed case."""
from datetime import datetime, timezone

from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING


def test_calibration_source_carries_same_case_and_patient():
    raw = [
        {"id": name, "x": float(100 + i), "y": float(150 + i * 2)}
        for i, name in SOTA_LANDMARKS_MAPPING.items()
    ]
    points = {item["id"]: (item["x"], item["y"]) for item in raw}
    case_id = "cephalo:source-binding"
    previous = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=CephaloEngine(mm_per_pixel=None).calculate_metrics(points),
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=case_id,
    )
    payload = rebuild_evidence_after_manual_calibration(
        previous_payload=previous,
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
    calibration = next(source for source in payload["sources"] if source["kind"] == "calibration")
    assert calibration["patient_id"] == 7
    assert calibration["metadata"]["case_id"] == case_id
