from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_runtime_evidence import build_cephalo_runtime_evidence_payload
from backend.services.cephalo_tweed_merrifield_evidence import (
    adapt_tweed_merrifield_measurements,
    materialize_tweed_merrifield_constructions,
)
from backend.services.cephalo_tweed_merrifield_geometry import (
    merrifield_z_angle_deg_v1,
    tweed_fma_deg_v1,
    tweed_fmia_deg_v1,
    tweed_impa_deg_v1,
)
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 11, 19, 20, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 11, 19, 25, tzinfo=timezone.utc)
LATEST = datetime(2026, 9, 11, 19, 30, tzinfo=timezone.utc)
CASE_ID = "cephalo:r6-tweed-merrifield"


def _landmark(landmark_id: str, x: float, y: float, *, source: str = "source:ceph:1"):
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


def _coords():
    return {
        "Po": (0.0, 0.0),
        "Or": (10.0, 0.0),
        "Go": (0.0, 10.0),
        "Me": (10.0, 15.0),
        "L1_apex": (4.0, 18.0),
        "L1_incisal": (5.0, 8.0),
        "Pog_soft": (2.0, 20.0),
        "Ls_soft": (7.0, 10.0),
        "Li_soft": (6.0, 12.0),
    }


def _landmarks():
    return {key: _landmark(key, *value) for key, value in _coords().items()}


def test_tweed_geometry_matches_runtime_fma_impa_and_types_fmia_directly():
    points = _coords()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(points)

    fma = tweed_fma_deg_v1(points["Go"], points["Me"], points["Po"], points["Or"])
    impa = tweed_impa_deg_v1(
        points["L1_apex"], points["L1_incisal"], points["Go"], points["Me"]
    )
    fmia = tweed_fmia_deg_v1(
        points["L1_apex"], points["L1_incisal"], points["Po"], points["Or"]
    )

    assert fma is not None and impa is not None and fmia is not None
    assert round(fma, 1) == result.metrics.analyse_osseuse.Angle_de_Tweed.valeur
    assert round(impa, 1) == result.metrics.analyse_dentaire.IMPA.valeur
    assert fmia == pytest.approx(84.2894068625)
    assert round(fma + impa + fmia, 1) == pytest.approx(180.0, abs=0.1)


def test_fmia_is_orientation_invariant_but_fma_impa_keep_runtime_semantics():
    p = _coords()
    fmia = tweed_fmia_deg_v1(p["L1_apex"], p["L1_incisal"], p["Po"], p["Or"])
    assert fmia is not None
    assert tweed_fmia_deg_v1(p["L1_incisal"], p["L1_apex"], p["Po"], p["Or"]) == pytest.approx(fmia)
    assert tweed_fmia_deg_v1(p["L1_apex"], p["L1_incisal"], p["Or"], p["Po"]) == pytest.approx(fmia)


def test_merrifield_z_angle_selects_most_protrusive_lip_and_is_mirror_invariant():
    p = _coords()
    z_upper = merrifield_z_angle_deg_v1(
        p["Po"], p["Or"], p["Pog_soft"], p["Ls_soft"], p["Li_soft"]
    )
    assert z_upper == pytest.approx(63.4349488229)

    lower_more_anterior = {**p, "Li_soft": (8.0, 12.0)}
    z_lower = merrifield_z_angle_deg_v1(
        lower_more_anterior["Po"],
        lower_more_anterior["Or"],
        lower_more_anterior["Pog_soft"],
        lower_more_anterior["Ls_soft"],
        lower_more_anterior["Li_soft"],
    )
    assert z_lower is not None
    assert z_lower != pytest.approx(z_upper)

    mirrored = {key: (-value[0], value[1]) for key, value in p.items()}
    z_mirror = merrifield_z_angle_deg_v1(
        mirrored["Po"], mirrored["Or"], mirrored["Pog_soft"],
        mirrored["Ls_soft"], mirrored["Li_soft"],
    )
    assert z_mirror == pytest.approx(z_upper)


def test_r6_constructions_and_measurements_are_source_bound_and_uncalibrated():
    constructions = materialize_tweed_merrifield_constructions(
        _landmarks(), construction_namespace="construction:r6:1"
    )
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_coords())
    measurements = adapt_tweed_merrifield_measurements(
        result,
        measurement_namespace="measurement:r6:1",
        constructions=constructions,
    )

    assert set(constructions) == {
        "TWEED_FMA_V1", "TWEED_IMPA_V1", "TWEED_FMIA_V1", "MERRIFIELD_Z_ANGLE_V1"
    }
    assert all(item.availability_status == AvailabilityStatus.AVAILABLE for item in constructions.values())
    assert {item.analysis_id for item in measurements} == {"TWEED", "MERRIFIELD"}
    assert {item.method_id for item in measurements} == {
        "TWEED_FMA_DEG_V1",
        "TWEED_IMPA_DEG_V1",
        "TWEED_FMIA_DEG_V1",
        "MERRIFIELD_Z_ANGLE_DEG_V1",
    }
    assert all(item.requires_calibration is False for item in measurements)
    assert all(item.calibration_ref is None for item in measurements)


def test_r6_missing_cross_image_and_degenerate_geometry_fail_closed():
    missing = _landmarks()
    missing.pop("Or")
    constructions = materialize_tweed_merrifield_constructions(
        missing, construction_namespace="construction:r6:missing"
    )
    assert constructions["TWEED_FMA_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["TWEED_FMIA_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["MERRIFIELD_Z_ANGLE_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE

    mixed = _landmarks()
    mixed["Me"] = _landmark("Me", 10.0, 15.0, source="source:ceph:other")
    constructions = materialize_tweed_merrifield_constructions(
        mixed, construction_namespace="construction:r6:mixed"
    )
    assert constructions["TWEED_FMA_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["TWEED_IMPA_V1"].availability_status == AvailabilityStatus.INVALID

    degenerate = _landmarks()
    degenerate["Or"] = _landmark("Or", 0.0, 0.0)
    constructions = materialize_tweed_merrifield_constructions(
        degenerate, construction_namespace="construction:r6:degenerate"
    )
    assert constructions["TWEED_FMA_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["TWEED_FMIA_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["MERRIFIELD_Z_ANGLE_V1"].availability_status == AvailabilityStatus.INVALID


def _raw(overrides=None):
    coords = {
        name: (float(100 + index * 2), float(120 + index * 3))
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    }
    coords.update(_coords())
    if overrides:
        coords.update(overrides)
    return [{"id": name, "x": xy[0], "y": xy[1]} for name, xy in coords.items()]


def _point_map(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _r6_measurements(payload):
    return {
        item["method_id"]: item
        for item in payload["measurements"]
        if item["analysis_id"] in {"TWEED", "MERRIFIELD"}
    }


def test_r6_creation_landmark_edit_and_calibration_keep_one_active_behavioral_chain():
    raw = _raw()
    result1 = CephaloEngine(mm_per_pixel=None).calculate_metrics(_point_map(raw))
    revision1 = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio-r6.jpg",
        result=result1,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=NOW,
    )
    r6_1 = _r6_measurements(revision1)
    assert set(r6_1) == {
        "TWEED_FMA_DEG_V1", "TWEED_IMPA_DEG_V1", "TWEED_FMIA_DEG_V1",
        "MERRIFIELD_Z_ANGLE_DEG_V1",
    }
    assert all(item["availability_status"] == "AVAILABLE" for item in r6_1.values())

    edited = _raw({"Me": (12.0, 18.0)})
    result2 = CephaloEngine(mm_per_pixel=None).calculate_metrics(_point_map(edited))
    revision2 = rebuild_evidence_after_landmark_edit(
        previous_payload=revision1,
        patient_id=7,
        image_record_id="radio-r6.jpg",
        result=result2,
        runtime_landmarks=edited,
        clinician_id="clinician-r6",
        validated_at=LATER,
    )
    r6_2 = _r6_measurements(revision2)
    assert r6_2["TWEED_FMA_DEG_V1"]["value"] != r6_1["TWEED_FMA_DEG_V1"]["value"]
    assert r6_2["TWEED_IMPA_DEG_V1"]["value"] != r6_1["TWEED_IMPA_DEG_V1"]["value"]

    calibrated_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_point_map(edited))
    revision3 = rebuild_evidence_after_manual_calibration(
        previous_payload=revision2,
        patient_id=7,
        image_record_id="radio-r6.jpg",
        result=calibrated_result,
        runtime_landmarks=edited,
        p1={"x": 0.0, "y": 0.0},
        p2={"x": 0.0, "y": 50.0},
        distance_mm=10.0,
        clinician_id="clinician-r6",
        calibrated_at=LATEST,
    )
    r6_3 = _r6_measurements(revision3)
    assert {key: value["value"] for key, value in r6_3.items()} == {
        key: value["value"] for key, value in r6_2.items()
    }
    assert all(item["requires_calibration"] is False for item in r6_3.values())
    assert all(item["calibration_ref"] is None for item in r6_3.values())
