"""A removed SRPose point must never return without an audited correction event."""
from datetime import datetime, timezone

from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_runtime_evidence import build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 10, 15, 30, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 10, 15, 35, tzinfo=timezone.utc)


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _edit(previous, raw, at):
    return rebuild_evidence_after_landmark_edit(
        previous_payload=previous,
        patient_id=7,
        image_record_id="radio.jpg",
        result=CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw)),
        runtime_landmarks=raw,
        clinician_id="99",
        validated_at=at,
    )


def test_reintroduced_srpose_point_is_manual_corrected_even_at_original_coordinates():
    original = _raw()
    original_a = next(item for item in original if item["id"] == "A")
    base = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(original)),
        landmarks=original,
        inference_mode="SOTA_ONNX_38",
        case_id="cephalo:reintroduction",
        recorded_at=NOW,
    )

    without_a = [item for item in original if item["id"] != "A"]
    omitted = _edit(base, without_a, NOW)
    assert all(not ref.endswith(":A") for ref in omitted["current_landmark_refs"])

    # The practitioner re-adds A at exactly the old machine coordinates. The point-set
    # transition itself is an edit and must not silently reactivate SRPose evidence.
    reintroduced = _edit(omitted, original, LATER)
    current_refs = set(reintroduced["current_landmark_refs"])
    candidates = [
        item
        for item in reintroduced["landmarks"]
        if item["landmark_id"] == "A" and item["evidence_id"] in current_refs
    ]
    assert len(candidates) == 1
    current_a = candidates[0]
    assert current_a["origin"] == "MANUAL_CORRECTED"
    assert current_a["original_auto_x"] == original_a["x"]
    assert current_a["original_auto_y"] == original_a["y"]
    assert current_a["validated_by"] == "99"
    assert current_a["evidence_id"].endswith(":r3:A")
