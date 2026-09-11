from __future__ import annotations

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_steiner_evidence_adapter import (
    STEINER_SKELETAL_CONSTRUCTION_DEFINITIONS,
    adapt_steiner_skeletal_measurements,
    materialize_steiner_skeletal_constructions,
)
from backend.services.cephalo_steiner_geometry import (
    steiner_anb_deg_v1,
    steiner_sna_deg_v1,
    steiner_snb_deg_v1,
    steiner_sn_mp_deg_v1,
)


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


def _landmarks():
    return {
        "S": _landmark("S", 10.0, 10.0),
        "N": _landmark("N", 20.0, 10.0),
        "A": _landmark("A", 24.0, 28.0),
        "B": _landmark("B", 22.0, 38.0),
        "Go": _landmark("Go", 14.0, 50.0),
        "Gn": _landmark("Gn", 34.0, 62.0),
    }


def _points():
    return {key: (item.x, item.y) for key, item in _landmarks().items()}


def _steiner_constructions(constructions):
    return {
        key: value
        for key, value in constructions.items()
        if key in STEINER_SKELETAL_CONSTRUCTION_DEFINITIONS
    }


def test_steiner_geometry_matches_existing_runtime_sna_snb_anb_and_types_sn_mp():
    points = _points()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(points)

    sna = steiner_sna_deg_v1(points["S"], points["N"], points["A"])
    snb = steiner_snb_deg_v1(points["S"], points["N"], points["B"])
    anb = steiner_anb_deg_v1(points["S"], points["N"], points["A"], points["B"])
    sn_mp = steiner_sn_mp_deg_v1(points["S"], points["N"], points["Go"], points["Gn"])

    assert round(sna, 1) == result.metrics.analyse_osseuse.SNA.valeur
    assert round(snb, 1) == result.metrics.analyse_osseuse.SNB.valeur
    assert round(anb, 1) == result.metrics.analyse_osseuse.ANB.valeur
    assert sn_mp == pytest.approx(30.9637565321)
    assert steiner_sn_mp_deg_v1(points["N"], points["S"], points["Go"], points["Gn"]) == pytest.approx(sn_mp)
    assert steiner_sn_mp_deg_v1(points["S"], points["N"], points["Gn"], points["Go"]) == pytest.approx(sn_mp)


def test_steiner_anb_locks_runtime_round_before_subtraction_order():
    points = {
        "S": (10.0, 10.0),
        "N": (20.0, 10.0),
        "A": (23.927233306464935, 23.036137512059824),
        "B": (25.854326169271445, 31.666251926499946),
    }
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(points)

    sna_raw = steiner_sna_deg_v1(points["S"], points["N"], points["A"])
    snb_raw = steiner_snb_deg_v1(points["S"], points["N"], points["B"])
    anb = steiner_anb_deg_v1(points["S"], points["N"], points["A"], points["B"])

    assert sna_raw is not None and snb_raw is not None and anb is not None
    assert round(sna_raw - snb_raw, 1) == 1.6
    assert round(round(sna_raw, 1) - round(snb_raw, 1), 1) == 1.7
    assert result.metrics.analyse_osseuse.ANB.valeur == 1.7
    assert round(anb, 1) == result.metrics.analyse_osseuse.ANB.valeur


def test_steiner_skeletal_constructions_are_source_bound_and_uncalibrated():
    constructions = materialize_steiner_skeletal_constructions(
        _landmarks(), construction_namespace="construction:steiner:1"
    )
    steiner = _steiner_constructions(constructions)

    assert set(steiner) == set(STEINER_SKELETAL_CONSTRUCTION_DEFINITIONS)
    assert all(
        item.availability_status == AvailabilityStatus.AVAILABLE
        for item in steiner.values()
    )
    assert all(item.geometry["analysis"] == "STEINER" for item in steiner.values())
    assert all(item.geometry["computed_angle_deg"] is not None for item in steiner.values())
    sn_mp = steiner["STEINER_SN_MP_V1"]
    assert sn_mp.geometry["reference_axis"] == "S-N"
    assert sn_mp.geometry["mandibular_plane"] == "Go-Gn"
    assert sn_mp.geometry["axis_orientation_invariant"] is True


def test_steiner_measurements_bind_runtime_values_without_calibration():
    constructions = materialize_steiner_skeletal_constructions(
        _landmarks(), construction_namespace="construction:steiner:2"
    )
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points())
    measurements = adapt_steiner_skeletal_measurements(
        result,
        measurement_namespace="measurement:steiner:2",
        constructions=constructions,
    )
    steiner = [item for item in measurements if item.analysis_id == "STEINER"]

    assert [item.method_id for item in steiner] == [
        "STEINER_SNA_DEG_V1",
        "STEINER_SNB_DEG_V1",
        "STEINER_ANB_DEG_V1",
        "STEINER_SN_MP_DEG_V1",
    ]
    assert all(item.unit == "deg" for item in steiner)
    assert all(item.requires_calibration is False for item in steiner)
    assert all(item.calibration_ref is None for item in steiner)
    assert all(item.availability_status == AvailabilityStatus.AVAILABLE for item in steiner)


def test_missing_a_fails_closed_only_for_sna_and_anb():
    landmarks = _landmarks()
    landmarks.pop("A")
    constructions = _steiner_constructions(materialize_steiner_skeletal_constructions(
        landmarks, construction_namespace="construction:steiner:3"
    ))

    assert constructions["STEINER_SNA_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["STEINER_ANB_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["STEINER_SNB_V1"].availability_status == AvailabilityStatus.AVAILABLE
    assert constructions["STEINER_SN_MP_V1"].availability_status == AvailabilityStatus.AVAILABLE


def test_missing_gn_fails_closed_only_for_sn_mp():
    landmarks = _landmarks()
    landmarks.pop("Gn")
    constructions = _steiner_constructions(materialize_steiner_skeletal_constructions(
        landmarks, construction_namespace="construction:steiner:missing-gn"
    ))
    assert constructions["STEINER_SN_MP_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert all(
        constructions[key].availability_status == AvailabilityStatus.AVAILABLE
        for key in ("STEINER_SNA_V1", "STEINER_SNB_V1", "STEINER_ANB_V1")
    )


def test_cross_image_and_degenerate_geometry_fail_closed():
    mixed = _landmarks()
    mixed["A"] = _landmark("A", 24.0, 28.0, source="source:ceph:other")
    constructions = _steiner_constructions(materialize_steiner_skeletal_constructions(
        mixed, construction_namespace="construction:steiner:4"
    ))
    assert constructions["STEINER_SNA_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["STEINER_ANB_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["STEINER_SN_MP_V1"].availability_status == AvailabilityStatus.AVAILABLE

    mixed_snmp = _landmarks()
    mixed_snmp["Gn"] = _landmark("Gn", 34.0, 62.0, source="source:ceph:other")
    constructions = _steiner_constructions(materialize_steiner_skeletal_constructions(
        mixed_snmp, construction_namespace="construction:steiner:4b"
    ))
    assert constructions["STEINER_SN_MP_V1"].availability_status == AvailabilityStatus.INVALID

    degenerate = _landmarks()
    degenerate["S"] = _landmark("S", 20.0, 10.0)
    constructions = _steiner_constructions(materialize_steiner_skeletal_constructions(
        degenerate, construction_namespace="construction:steiner:5"
    ))
    assert all(item.availability_status == AvailabilityStatus.INVALID for item in constructions.values())


def test_runtime_parity_mismatch_is_rejected():
    constructions = materialize_steiner_skeletal_constructions(
        _landmarks(), construction_namespace="construction:steiner:6"
    )
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points())
    result.metrics.analyse_osseuse.SNA.valeur = 99.9

    with pytest.raises(ValueError, match="Runtime SNA does not match typed Steiner geometry"):
        adapt_steiner_skeletal_measurements(
            result,
            measurement_namespace="measurement:steiner:6",
            constructions=constructions,
        )
