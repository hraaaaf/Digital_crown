"""Persistence-boundary tests for the cephalometric typed evidence snapshot."""
from datetime import datetime, timezone

from backend.schemas.cephalo_evidence import AvailabilityStatus, LandmarkOrigin
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_SCHEMA_VERSION,
    build_cephalo_runtime_evidence_payload,
)
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot
from backend.schemas.cephalo_evidence import (
    ConstructionEvidence,
    LandmarkEvidence,
    MeasurementEvidence,
    SourceEvidence,
)

NOW = datetime(2026, 9, 10, 13, 0, tzinfo=timezone.utc)
CASE_ID = "cephalo:test-case"


def _points():
    return {
        "S": (10.0, 10.0), "N": (20.0, 10.0), "Po": (0.0, 20.0), "Or": (20.0, 20.0),
        "A": (24.0, 28.0), "B": (22.0, 38.0), "Go": (5.0, 50.0), "Me": (25.0, 55.0),
        "U1a": (20.0, 25.0), "U1i": (24.0, 35.0), "L1a": (20.0, 48.0), "L1i": (23.0, 38.0),
    }


def _raw(offset=0.0):
    return [{"id": key, "x": x + offset, "y": y} for key, (x, y) in _points().items()]


def _result(ratio=0.2):
    return CephaloEngine(mm_per_pixel=ratio).calculate_metrics(_points())


def _graph(payload):
    return EvidenceGraphSnapshot(
        sources=[SourceEvidence.model_validate(x) for x in payload["sources"]],
        landmarks=[LandmarkEvidence.model_validate(x) for x in payload["landmarks"]],
        constructions=[ConstructionEvidence.model_validate(x) for x in payload["constructions"]],
        measurements=[MeasurementEvidence.model_validate(x) for x in payload["measurements"]],
    )


def test_srpose_snapshot_is_persistable_but_auto_calibration_is_not_silently_trusted():
    payload = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="api/static/uploads/radios/test.jpg",
        result=_result(),
        landmarks=_raw(),
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=NOW,
    )

    assert payload["schema_version"] == EVIDENCE_SCHEMA_VERSION
    assert payload["revision"] == 1
    assert len(payload["landmarks"]) == len(_points())
    assert all(x["origin"] == LandmarkOrigin.SRPOSE38_AUTO.value for x in payload["landmarks"])
    assert len(payload["measurements"]) == 4
    assert all(x["value"] is None for x in payload["measurements"])
    assert all(x["availability_status"] == AvailabilityStatus.NOT_COMPUTABLE.value for x in payload["measurements"])
    validate_case_evidence_graph(_graph(payload), patient_id=7, case_id=CASE_ID)


def test_uncertified_automatic_detector_cannot_masquerade_as_srpose_evidence():
    payload = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=_result(),
        landmarks=_raw(),
        inference_mode="PRODUCTION",
        case_id=CASE_ID,
        recorded_at=NOW,
    )
    assert payload["landmarks"] == []
    assert all(x["availability_status"] == AvailabilityStatus.NOT_COMPUTABLE.value for x in payload["constructions"])
    assert all(x["value"] is None for x in payload["measurements"])


def test_manual_revision_preserves_original_srpose_points_and_drives_new_constructions():
    first = build_cephalo_runtime_evidence_payload(
        patient_id=7, image_record_id="radio.jpg", result=_result(), landmarks=_raw(),
        inference_mode="SOTA_ONNX_38", case_id=CASE_ID, recorded_at=NOW,
    )
    second = build_cephalo_runtime_evidence_payload(
        patient_id=7, image_record_id="radio.jpg", result=_result(), landmarks=_raw(offset=1.0),
        inference_mode=None, previous_payload=first, manual_revision=True, recorded_at=NOW,
    )

    assert second["revision"] == 2
    origins = [x["origin"] for x in second["landmarks"]]
    assert origins.count(LandmarkOrigin.SRPOSE38_AUTO.value) == len(_points())
    assert origins.count(LandmarkOrigin.MANUAL.value) == len(_points())
    for construction in second["constructions"]:
        assert all(":r2:" in ref for ref in construction["landmark_refs"])
    validate_case_evidence_graph(_graph(second), patient_id=7, case_id=CASE_ID)


def test_explicit_two_point_calibration_unlocks_only_the_four_versioned_linear_measurements():
    payload = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=_result(0.2),
        landmarks=_raw(),
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        is_calibrated=True,
        calibration_data={"p1": {"x": 0, "y": 0}, "p2": {"x": 0, "y": 50}, "distance_mm": 10},
        recorded_at=NOW,
    )

    calibration = [x for x in payload["sources"] if x["kind"] == "calibration"]
    assert len(calibration) == 1
    assert calibration[0]["quality_status"] == "VERIFIED_MANUAL_TWO_POINT"
    assert len(payload["measurements"]) == 4
    assert all(x["availability_status"] == AvailabilityStatus.AVAILABLE.value for x in payload["measurements"])
    assert all(x["value"] is not None for x in payload["measurements"])
    validate_case_evidence_graph(_graph(payload), patient_id=7, case_id=CASE_ID)
