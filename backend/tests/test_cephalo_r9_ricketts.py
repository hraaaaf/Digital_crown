from __future__ import annotations

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_ricketts_evidence import (
    RICKETTS_BLOCKED_CONTRACTS,
    RICKETTS_CONSTRUCTION_DEFINITIONS,
    adapt_ricketts_measurements,
    materialize_ricketts_constructions,
)
from backend.services.cephalo_ricketts_geometry import ricketts_facial_depth_deg_v1


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
        "Po": _landmark("Po", 0.0, 0.0),
        "Or": _landmark("Or", 10.0, 0.0),
        "N": _landmark("N", 4.0, 0.0),
        "Pog": _landmark("Pog", 4.0, 10.0),
    }


def test_ricketts_facial_depth_preserves_posterior_angle_and_mirror_invariance():
    neutral = ricketts_facial_depth_deg_v1((0, 0), (10, 0), (4, 0), (4, 10))
    forward = ricketts_facial_depth_deg_v1((0, 0), (10, 0), (4, 0), (6, 10))
    retrusive = ricketts_facial_depth_deg_v1((0, 0), (10, 0), (4, 0), (2, 10))

    assert neutral == pytest.approx(90.0)
    assert forward is not None and forward > 90.0
    assert retrusive is not None and retrusive < 90.0
    assert ricketts_facial_depth_deg_v1(
        (0, 0), (-10, 0), (-4, 0), (-6, 10)
    ) == pytest.approx(forward)


def test_ricketts_facial_depth_is_not_downs_acute_alias():
    value = ricketts_facial_depth_deg_v1((0, 0), (10, 0), (4, 0), (6, 10))
    assert value == pytest.approx(101.309932474)


def test_ricketts_construction_and_measurement_are_source_bound_and_uncalibrated():
    constructions = materialize_ricketts_constructions(
        _landmarks(), construction_namespace="construction:ricketts:1"
    )

    assert set(constructions) == set(RICKETTS_CONSTRUCTION_DEFINITIONS)
    construction = constructions["RICKETTS_FACIAL_DEPTH_V1"]
    assert construction.availability_status == AvailabilityStatus.AVAILABLE
    assert construction.geometry["analysis"] == "RICKETTS"
    assert construction.geometry["angle_convention"] == "posterior_angle_fh_po_or_to_pog_n_v1"
    assert construction.geometry["mirror_invariant"] is True

    measurements = adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:1",
        constructions=constructions,
    )
    assert len(measurements) == 1
    measurement = measurements[0]
    assert measurement.analysis_id == "RICKETTS"
    assert measurement.method_id == "RICKETTS_FACIAL_DEPTH_DEG_V1"
    assert measurement.requires_calibration is False
    assert measurement.calibration_ref is None
    assert measurement.value == pytest.approx(90.0)


def test_ricketts_missing_cross_image_and_degenerate_geometry_fail_closed():
    missing = _landmarks()
    missing.pop("Pog")
    construction = materialize_ricketts_constructions(
        missing, construction_namespace="construction:ricketts:missing"
    )["RICKETTS_FACIAL_DEPTH_V1"]
    assert construction.availability_status == AvailabilityStatus.NOT_COMPUTABLE

    mixed = _landmarks()
    mixed["Pog"] = _landmark("Pog", 4.0, 10.0, source="source:ceph:other")
    construction = materialize_ricketts_constructions(
        mixed, construction_namespace="construction:ricketts:mixed"
    )["RICKETTS_FACIAL_DEPTH_V1"]
    assert construction.availability_status == AvailabilityStatus.INVALID

    degenerate = _landmarks()
    degenerate["Or"] = _landmark("Or", 0.0, 0.0)
    construction = materialize_ricketts_constructions(
        degenerate, construction_namespace="construction:ricketts:degenerate"
    )["RICKETTS_FACIAL_DEPTH_V1"]
    assert construction.availability_status == AvailabilityStatus.INVALID


def test_ricketts_blocked_contracts_are_explicit_and_not_materialized():
    assert set(RICKETTS_BLOCKED_CONTRACTS) == {
        "RICKETTS_FACIAL_AXIS_DEG_V1",
        "RICKETTS_CONVEXITY_A_NPOG_MM_V1",
        "RICKETTS_E_LINE_LS_MM_V1",
        "RICKETTS_E_LINE_LI_MM_V1",
    }
    constructions = materialize_ricketts_constructions(
        _landmarks(), construction_namespace="construction:ricketts:blocked"
    )
    assert set(constructions) == {"RICKETTS_FACIAL_DEPTH_V1"}


def test_pre_r9_snapshot_and_partial_snapshot_fail_closed():
    assert adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:legacy", constructions={}
    ) == []

    # The current certified set contains one construction. A wrong key therefore
    # remains a pre-R9 snapshot rather than a partial certified R9 snapshot.
    assert adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:wrong",
        constructions={"OTHER": object()},
    ) == []
