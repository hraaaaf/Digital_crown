"""Repeated calibration must revise, not duplicate, the current calibration source."""
from datetime import datetime, timedelta, timezone

from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING


def test_recalibration_keeps_one_current_calibration_source_and_archives_previous():
    raw = [
        {"id": name, "x": float(100 + i * 2), "y": float(120 + i * 3)}
        for i, name in SOTA_LANDMARKS_MAPPING.items()
    ]
    points = {item["id"]: (item["x"], item["y"]) for item in raw}
    base = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=CephaloEngine(mm_per_pixel=None).calculate_metrics(points),
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id="cephalo:recalibration",
    )
    t1 = datetime(2026, 9, 10, 14, 0, tzinfo=timezone.utc)
    first = rebuild_evidence_after_manual_calibration(
        previous_payload=base,
        patient_id=7,
        image_record_id="radio.jpg",
        result=CephaloEngine(mm_per_pixel=0.2).calculate_metrics(points),
        runtime_landmarks=raw,
        p1={"x": 0.0, "y": 0.0},
        p2={"x": 0.0, "y": 50.0},
        distance_mm=10.0,
        clinician_id="99",
        calibrated_at=t1,
    )
    second = rebuild_evidence_after_manual_calibration(
        previous_payload=first,
        patient_id=7,
        image_record_id="radio.jpg",
        result=CephaloEngine(mm_per_pixel=0.25).calculate_metrics(points),
        runtime_landmarks=raw,
        p1={"x": 0.0, "y": 0.0},
        p2={"x": 0.0, "y": 40.0},
        distance_mm=10.0,
        clinician_id="99",
        calibrated_at=t1 + timedelta(minutes=5),
    )

    assert second["revision"] == 3
    assert len(second["history"]) == 2
    current_calibrations = [source for source in second["sources"] if source["kind"] == "calibration"]
    assert len(current_calibrations) == 1
    assert current_calibrations[0]["metadata"]["mm_per_pixel"] == 0.25
    archived_calibrations = [
        source
        for source in second["history"][-1]["sources"]
        if source["kind"] == "calibration"
    ]
    assert len(archived_calibrations) == 1
    assert archived_calibrations[0]["metadata"]["mm_per_pixel"] == 0.2
