from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.schemas.cephalo_evidence import AvailabilityStatus
from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_runtime_evidence import build_cephalo_runtime_evidence_payload
from backend.services.cephalo_steiner_evidence_adapter import (
    adapt_steiner_skeletal_measurements,
    materialize_steiner_skeletal_constructions,
)
from backend.services.cephalo_steiner_geometry import steiner_sn_mp_deg_v1
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 11, 18, 10, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 11, 18, 15, tzinfo=timezone.utc)
CASE_ID = "cephalo:r5-snmp"
METHOD_ID = "STEINER_SN_MP_DEG_V1"


def _raw() -> list[dict[str, float | str]]:
    coords = {
        name: (100.0 + index * 2.0, 120.0 + index * 3.0)
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    }
    coords.update(
        {
            "S": (10.0, 10.0),
            "N": (20.0, 10.0),
            "Po": (0.0, 20.0),
            "Or": (20.0, 20.0),
            "A": (24.0, 28.0),
            "B": (22.0, 38.0),
            "Go": (14.0, 50.0),
            "Gn": (34.0, 62.0),
            "U1_apex": (20.0, 25.0),
            "U1_incisal": (24.0, 35.0),
            "L1_apex": (20.0, 48.0),
            "L1_incisal": (23.0, 38.0),
        }
    )
    return [{"id": key, "x": x, "y": y} for key, (x, y) in coords.items()]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _snmp(payload):
    matches = [item for item in payload["measurements"] if item["method_id"] == METHOD_ID]
    assert len(matches) == 1
    return matches[0]


def test_sn_mp_geometry_is_smallest_orientation_invariant_sn_to_gogn_angle():
    s = (10.0, 10.0)
    n = (20.0, 10.0)
    go = (14.0, 50.0)
    gn = (34.0, 62.0)
    expected = 30.9637565321
    assert steiner_sn_mp_deg_v1(s, n, go, gn) == pytest.approx(expected)
    assert steiner_sn_mp_deg_v1(n, s, go, gn) == pytest.approx(expected)
    assert steiner_sn_mp_deg_v1(s, n, gn, go) == pytest.approx(expected)


def test_sn_mp_typed_evidence_is_source_bound_uncalibrated_and_fail_closed():
    from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin

    def lm(landmark_id, x, y, source="source:ceph:1"):
        return LandmarkEvidence(
            evidence_id=f"landmark:{landmark_id}",
            landmark_id=landmark_id,
            x=x,
            y=y,
            source_image_ref=source,
            origin=LandmarkOrigin.MANUAL,
            evidence_refs=[source],
            evidence_status=EvidenceStatus.OBSERVED,
        )

    landmarks = {
        "S": lm("S", 10.0, 10.0),
        "N": lm("N", 20.0, 10.0),
        "A": lm("A", 24.0, 28.0),
        "B": lm("B", 22.0, 38.0),
        "Go": lm("Go", 14.0, 50.0),
        "Gn": lm("Gn", 34.0, 62.0),
    }
    constructions = materialize_steiner_skeletal_constructions(
        landmarks, construction_namespace="construction:steiner:snmp"
    )
    construction = constructions["STEINER_SN_MP_V1"]
    assert construction.availability_status == AvailabilityStatus.AVAILABLE
    assert construction.geometry["reference_axis"] == "S-N"
    assert construction.geometry["mandibular_plane"] == "Go-Gn"
    assert construction.geometry["axis_orientation_invariant"] is True

    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(
        {key: (item.x, item.y) for key, item in landmarks.items()}
    )
    measurements = adapt_steiner_skeletal_measurements(
        result,
        measurement_namespace="measurement:steiner:snmp",
        constructions=constructions,
    )
    snmp = next(item for item in measurements if item.method_id == METHOD_ID)
    assert snmp.analysis_id == "STEINER"
    assert snmp.unit == "deg"
    assert snmp.requires_calibration is False
    assert snmp.calibration_ref is None
    assert snmp.availability_status == AvailabilityStatus.AVAILABLE

    missing = dict(landmarks)
    missing.pop("Gn")
    assert materialize_steiner_skeletal_constructions(
        missing, construction_namespace="construction:steiner:missing"
    )["STEINER_SN_MP_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE

    mixed = dict(landmarks)
    mixed["Gn"] = lm("Gn", 34.0, 62.0, source="source:other")
    assert materialize_steiner_skeletal_constructions(
        mixed, construction_namespace="construction:steiner:mixed"
    )["STEINER_SN_MP_V1"].availability_status == AvailabilityStatus.INVALID


def test_sn_mp_survives_calibration_and_rematerializes_after_landmark_edit():
    raw = _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    revision1 = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio-r5-snmp.jpg",
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=NOW,
    )
    snmp1 = _snmp(revision1)
    assert snmp1["availability_status"] == AvailabilityStatus.AVAILABLE.value
    assert snmp1["requires_calibration"] is False
    assert snmp1["calibration_ref"] is None

    edited = [dict(item) for item in raw]
    go = next(item for item in edited if item["id"] == "Go")
    go["y"] += 8.0
    edited_result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(edited))
    revision2 = rebuild_evidence_after_landmark_edit(
        previous_payload=revision1,
        patient_id=7,
        image_record_id="radio-r5-snmp.jpg",
        result=edited_result,
        runtime_landmarks=edited,
        clinician_id="clinician-7",
        validated_at=LATER,
    )
    snmp2 = _snmp(revision2)
    assert snmp2["value"] != snmp1["value"]
    assert snmp2["requires_calibration"] is False

    calibrated_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(edited))
    revision3 = rebuild_evidence_after_manual_calibration(
        previous_payload=revision2,
        patient_id=7,
        image_record_id="radio-r5-snmp.jpg",
        result=calibrated_result,
        runtime_landmarks=edited,
        p1={"x": 0.0, "y": 0.0},
        p2={"x": 0.0, "y": 50.0},
        distance_mm=10.0,
        clinician_id="clinician-7",
        calibrated_at=LATER,
    )
    snmp3 = _snmp(revision3)
    assert snmp3["value"] == snmp2["value"]
    assert snmp3["calibration_ref"] is None
    assert snmp3["requires_calibration"] is False
