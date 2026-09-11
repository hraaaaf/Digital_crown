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
from backend.services.cephalo_ricketts_geometry import (
    ricketts_e_line_signed_distance_px_v1,
    ricketts_facial_depth_deg_v1,
)


def _landmark(landmark_id: str, x: float, y: float, *, source: str = "source:ceph:1"):
    return LandmarkEvidence(
        evidence_id=f"landmark:{landmark_id}", landmark_id=landmark_id,
        x=x, y=y, source_image_ref=source, origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source], evidence_status=EvidenceStatus.OBSERVED,
    )


def _landmarks():
    return {
        "Po": _landmark("Po", 0.0, 0.0),
        "Or": _landmark("Or", 10.0, 0.0),
        "N": _landmark("N", 4.0, 0.0),
        "Pog": _landmark("Pog", 4.0, 10.0),
        "Prn": _landmark("Prn", 5.0, -5.0),
        "Pog_soft": _landmark("Pog_soft", 5.0, 10.0),
        "Ls_soft": _landmark("Ls_soft", 7.0, 2.0),
        "Li_soft": _landmark("Li_soft", 3.0, 5.0),
    }


def test_ricketts_facial_depth_preserves_posterior_angle_and_mirror_invariance():
    neutral = ricketts_facial_depth_deg_v1((0, 0), (10, 0), (4, 0), (4, 10))
    forward = ricketts_facial_depth_deg_v1((0, 0), (10, 0), (4, 0), (6, 10))
    retrusive = ricketts_facial_depth_deg_v1((0, 0), (10, 0), (4, 0), (2, 10))
    assert neutral == pytest.approx(90.0)
    assert forward is not None and forward > 90.0
    assert retrusive is not None and retrusive < 90.0
    assert ricketts_facial_depth_deg_v1((0, 0), (-10, 0), (-4, 0), (-6, 10)) == pytest.approx(forward)
    assert forward == pytest.approx(101.309932474)


def test_ricketts_e_line_sign_and_mirror_invariance():
    anterior = ricketts_e_line_signed_distance_px_v1(
        (7, 2), (5, -5), (5, 10), (0, 0), (10, 0)
    )
    posterior = ricketts_e_line_signed_distance_px_v1(
        (3, 2), (5, -5), (5, 10), (0, 0), (10, 0)
    )
    mirrored = ricketts_e_line_signed_distance_px_v1(
        (-7, 2), (-5, -5), (-5, 10), (0, 0), (-10, 0)
    )
    assert anterior == pytest.approx(2.0)
    assert posterior == pytest.approx(-2.0)
    assert mirrored == pytest.approx(anterior)


def test_ricketts_materialization_and_calibration_contract():
    constructions = materialize_ricketts_constructions(
        _landmarks(), construction_namespace="construction:ricketts:1"
    )
    assert set(constructions) == set(RICKETTS_CONSTRUCTION_DEFINITIONS)
    assert all(c.availability_status == AvailabilityStatus.AVAILABLE for c in constructions.values())
    assert constructions["RICKETTS_FACIAL_DEPTH_V1"].geometry["angle_convention"] == "posterior_angle_fh_po_or_to_pog_n_v1"
    assert constructions["RICKETTS_E_LINE_LS_V1"].geometry["sign_convention"] == "positive_anterior_negative_posterior_v1"
    assert constructions["RICKETTS_E_LINE_LS_V1"].geometry["frankfort_role"] == "sign_orientation_only"

    uncalibrated = adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:1", constructions=constructions,
        mm_per_pixel=None, calibration_ref=None,
    )
    by_method = {m.method_id: m for m in uncalibrated}
    assert by_method["RICKETTS_FACIAL_DEPTH_DEG_V1"].availability_status == AvailabilityStatus.AVAILABLE
    assert by_method["RICKETTS_FACIAL_DEPTH_DEG_V1"].value == pytest.approx(90.0)
    for method in ("RICKETTS_E_LINE_LS_MM_V1", "RICKETTS_E_LINE_LI_MM_V1"):
        assert by_method[method].availability_status == AvailabilityStatus.NOT_COMPUTABLE
        assert by_method[method].value is None
        assert by_method[method].requires_calibration is True

    calibrated = adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:2", constructions=constructions,
        mm_per_pixel=0.5, calibration_ref="source:calibration:2",
    )
    by_method = {m.method_id: m for m in calibrated}
    assert by_method["RICKETTS_E_LINE_LS_MM_V1"].value == pytest.approx(1.0)
    assert by_method["RICKETTS_E_LINE_LI_MM_V1"].value == pytest.approx(-1.0)
    assert by_method["RICKETTS_E_LINE_LS_MM_V1"].calibration_ref == "source:calibration:2"
    assert by_method["RICKETTS_FACIAL_DEPTH_DEG_V1"].calibration_ref is None


def test_ricketts_missing_cross_image_and_degenerate_geometry_fail_closed():
    missing = _landmarks()
    missing.pop("Pog_soft")
    constructions = materialize_ricketts_constructions(
        missing, construction_namespace="construction:ricketts:missing"
    )
    assert constructions["RICKETTS_FACIAL_DEPTH_V1"].availability_status == AvailabilityStatus.AVAILABLE
    assert constructions["RICKETTS_E_LINE_LS_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["RICKETTS_E_LINE_LI_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE

    mixed = _landmarks()
    mixed["Ls_soft"] = _landmark("Ls_soft", 7.0, 2.0, source="source:ceph:other")
    constructions = materialize_ricketts_constructions(
        mixed, construction_namespace="construction:ricketts:mixed"
    )
    assert constructions["RICKETTS_E_LINE_LS_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["RICKETTS_E_LINE_LI_V1"].availability_status == AvailabilityStatus.AVAILABLE

    degenerate = _landmarks()
    degenerate["Or"] = _landmark("Or", 0.0, 0.0)
    constructions = materialize_ricketts_constructions(
        degenerate, construction_namespace="construction:ricketts:degenerate"
    )
    assert all(c.availability_status == AvailabilityStatus.INVALID for c in constructions.values())


def test_ricketts_blocked_contracts_are_explicit_and_not_materialized():
    assert set(RICKETTS_BLOCKED_CONTRACTS) == {
        "RICKETTS_FACIAL_AXIS_DEG_V1",
        "RICKETTS_CONVEXITY_A_NPOG_MM_V1",
    }
    constructions = materialize_ricketts_constructions(
        _landmarks(), construction_namespace="construction:ricketts:blocked"
    )
    assert set(constructions) == {
        "RICKETTS_FACIAL_DEPTH_V1", "RICKETTS_E_LINE_LS_V1", "RICKETTS_E_LINE_LI_V1"
    }


def test_pre_r9_and_partial_snapshots_fail_closed():
    assert adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:legacy", constructions={},
        mm_per_pixel=None, calibration_ref=None,
    ) == []
    constructions = materialize_ricketts_constructions(
        _landmarks(), construction_namespace="construction:ricketts:partial"
    )
    constructions.pop("RICKETTS_E_LINE_LI_V1")
    with pytest.raises(ValueError, match="Partial Ricketts"):
        adapt_ricketts_measurements(
            measurement_namespace="measurement:ricketts:partial", constructions=constructions,
            mm_per_pixel=0.5, calibration_ref="source:calibration:partial",
        )
