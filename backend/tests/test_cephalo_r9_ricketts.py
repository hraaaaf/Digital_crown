from __future__ import annotations

import pytest

from backend.schemas.cephalo_evidence import AvailabilityStatus, EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_ricketts_evidence import (
    RICKETTS_BLOCKED_CONTRACTS,
    RICKETTS_CONSTRUCTION_DEFINITIONS,
    adapt_ricketts_measurements,
    materialize_ricketts_constructions,
)
from backend.services.cephalo_ricketts_geometry import (
    ricketts_constructed_gn_v1,
    ricketts_convexity_signed_distance_px_v1,
    ricketts_e_line_horizontal_signed_distance_px_v1,
    ricketts_facial_axis_deg_v1,
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
        "Po": _landmark("Po", 0.0, 0.0), "Or": _landmark("Or", 10.0, 0.0),
        "N": _landmark("N", 4.0, 0.0), "Pog": _landmark("Pog", 6.0, 10.0),
        "Go": _landmark("Go", 0.0, 12.0), "Me": _landmark("Me", 10.0, 12.0),
        "Ba": _landmark("Ba", -6.0, 0.0), "PT_point": _landmark("PT_point", 2.0, 4.0),
        "A": _landmark("A", 8.0, 4.0), "Prn": _landmark("Prn", 5.0, -5.0),
        "Pog_soft": _landmark("Pog_soft", 9.0, 10.0),
        "Ls_soft": _landmark("Ls_soft", 10.0, 2.0), "Li_soft": _landmark("Li_soft", 5.0, 5.0),
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


def test_ricketts_constructed_gn_and_facial_axis_are_explicit_and_mirror_invariant():
    gn = ricketts_constructed_gn_v1((4, 0), (6, 10), (0, 12), (10, 12))
    assert gn == pytest.approx((6.4, 12.0))
    angle = ricketts_facial_axis_deg_v1((-6, 0), (4, 0), (2, 4), gn)
    assert angle == pytest.approx(61.189206257)
    mirrored_gn = ricketts_constructed_gn_v1((-4, 0), (-6, 10), (0, 12), (-10, 12))
    assert mirrored_gn == pytest.approx((-6.4, 12.0))
    mirrored = ricketts_facial_axis_deg_v1((6, 0), (-4, 0), (-2, 4), mirrored_gn)
    assert mirrored == pytest.approx(angle)
    assert ricketts_constructed_gn_v1((0, 0), (10, 0), (0, 1), (10, 1)) is None


def test_ricketts_convexity_is_signed_perpendicular_and_mirror_invariant():
    anterior = ricketts_convexity_signed_distance_px_v1((7, 4), (5, 0), (5, 10), (0, 0), (10, 0))
    posterior = ricketts_convexity_signed_distance_px_v1((3, 4), (5, 0), (5, 10), (0, 0), (10, 0))
    mirrored = ricketts_convexity_signed_distance_px_v1((-7, 4), (-5, 0), (-5, 10), (0, 0), (-10, 0))
    assert anterior == pytest.approx(2.0)
    assert posterior == pytest.approx(-2.0)
    assert mirrored == pytest.approx(anterior)


def test_ricketts_e_line_uses_frankfort_parallel_not_perpendicular_distance():
    value = ricketts_e_line_horizontal_signed_distance_px_v1((10, 2), (5, -5), (9, 10), (0, 0), (10, 0))
    mirrored = ricketts_e_line_horizontal_signed_distance_px_v1((-10, 2), (-5, -5), (-9, 10), (0, 0), (-10, 0))
    assert value == pytest.approx(47.0 / 15.0)
    assert mirrored == pytest.approx(value)
    assert ricketts_e_line_horizontal_signed_distance_px_v1((7, 2), (5, -5), (5, 10), (0, 0), (10, 0)) == pytest.approx(2.0)
    assert ricketts_e_line_horizontal_signed_distance_px_v1((3, 2), (5, -5), (5, 10), (0, 0), (10, 0)) == pytest.approx(-2.0)


def test_ricketts_materializes_five_source_locked_constructions():
    constructions = materialize_ricketts_constructions(_landmarks(), construction_namespace="construction:ricketts:1")
    assert set(constructions) == set(RICKETTS_CONSTRUCTION_DEFINITIONS) == {
        "RICKETTS_FACIAL_DEPTH_V1", "RICKETTS_FACIAL_AXIS_V1", "RICKETTS_CONVEXITY_A_NPOG_V1",
        "RICKETTS_E_LINE_LS_V1", "RICKETTS_E_LINE_LI_V1",
    }
    assert all(item.availability_status == AvailabilityStatus.AVAILABLE for item in constructions.values())
    assert constructions["RICKETTS_FACIAL_AXIS_V1"].geometry["gn_construction"] == "intersection_N_Pog_with_Go_Me_v1"
    assert constructions["RICKETTS_FACIAL_AXIS_V1"].geometry["constructed_gn"]["x"] == pytest.approx(6.4)
    assert constructions["RICKETTS_CONVEXITY_A_NPOG_V1"].geometry["distance_convention"] == "perpendicular_shortest_distance_v1"
    assert constructions["RICKETTS_E_LINE_LS_V1"].geometry["distance_convention"] == "parallel_to_frankfort_v1"


def test_ricketts_calibration_contract_unlocks_only_linear_measurements():
    constructions = materialize_ricketts_constructions(_landmarks(), construction_namespace="construction:ricketts:2")
    uncalibrated = adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:uncalibrated", constructions=constructions,
        mm_per_pixel=None, calibration_ref=None,
    )
    by_method = {item.method_id: item for item in uncalibrated}
    assert {method for method, item in by_method.items() if not item.requires_calibration} == {
        "RICKETTS_FACIAL_DEPTH_DEG_V1", "RICKETTS_FACIAL_AXIS_DEG_V1",
    }
    assert all(by_method[m].availability_status == AvailabilityStatus.AVAILABLE for m in (
        "RICKETTS_FACIAL_DEPTH_DEG_V1", "RICKETTS_FACIAL_AXIS_DEG_V1"))
    for method in ("RICKETTS_CONVEXITY_A_NPOG_MM_V1", "RICKETTS_E_LINE_LS_MM_V1", "RICKETTS_E_LINE_LI_MM_V1"):
        assert by_method[method].availability_status == AvailabilityStatus.NOT_COMPUTABLE
        assert by_method[method].value is None
        assert by_method[method].calibration_ref is None

    calibrated = adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:calibrated", constructions=constructions,
        mm_per_pixel=0.5, calibration_ref="source:calibration:r9",
    )
    by_method = {item.method_id: item for item in calibrated}
    assert all(item.availability_status == AvailabilityStatus.AVAILABLE for item in calibrated)
    for method in ("RICKETTS_CONVEXITY_A_NPOG_MM_V1", "RICKETTS_E_LINE_LS_MM_V1", "RICKETTS_E_LINE_LI_MM_V1"):
        assert by_method[method].calibration_ref == "source:calibration:r9"
    assert by_method["RICKETTS_FACIAL_DEPTH_DEG_V1"].calibration_ref is None
    assert by_method["RICKETTS_FACIAL_AXIS_DEG_V1"].calibration_ref is None


@pytest.mark.parametrize(("mm_per_pixel", "calibration_ref"), [
    (0.5, None), (None, "source:calibration:r9"), (float("nan"), "source:calibration:r9"),
])
def test_ricketts_incoherent_calibration_is_invalid(mm_per_pixel, calibration_ref):
    constructions = materialize_ricketts_constructions(_landmarks(), construction_namespace="construction:ricketts:calibration-invalid")
    measurements = adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:calibration-invalid", constructions=constructions,
        mm_per_pixel=mm_per_pixel, calibration_ref=calibration_ref,
    )
    linears = [item for item in measurements if item.requires_calibration]
    assert all(item.availability_status == AvailabilityStatus.INVALID for item in linears)
    assert all(item.value is None for item in linears)


def test_ricketts_fail_closed_is_dependency_scoped():
    missing_go = _landmarks(); missing_go.pop("Go")
    constructions = materialize_ricketts_constructions(missing_go, construction_namespace="construction:ricketts:missing-go")
    assert constructions["RICKETTS_FACIAL_AXIS_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["RICKETTS_FACIAL_DEPTH_V1"].availability_status == AvailabilityStatus.AVAILABLE
    assert constructions["RICKETTS_CONVEXITY_A_NPOG_V1"].availability_status == AvailabilityStatus.AVAILABLE

    mixed_a = _landmarks(); mixed_a["A"] = _landmark("A", 8.0, 4.0, source="source:ceph:other")
    constructions = materialize_ricketts_constructions(mixed_a, construction_namespace="construction:ricketts:mixed-a")
    assert constructions["RICKETTS_CONVEXITY_A_NPOG_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["RICKETTS_FACIAL_DEPTH_V1"].availability_status == AvailabilityStatus.AVAILABLE

    mixed_ls = _landmarks(); mixed_ls["Ls_soft"] = _landmark("Ls_soft", 10.0, 2.0, source="source:ceph:other")
    constructions = materialize_ricketts_constructions(mixed_ls, construction_namespace="construction:ricketts:mixed-ls")
    assert constructions["RICKETTS_E_LINE_LS_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["RICKETTS_E_LINE_LI_V1"].availability_status == AvailabilityStatus.AVAILABLE

    parallel_e = _landmarks(); parallel_e["Prn"] = _landmark("Prn", 0.0, 5.0); parallel_e["Pog_soft"] = _landmark("Pog_soft", 10.0, 5.0)
    constructions = materialize_ricketts_constructions(parallel_e, construction_namespace="construction:ricketts:parallel-e")
    assert constructions["RICKETTS_E_LINE_LS_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["RICKETTS_E_LINE_LI_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["RICKETTS_FACIAL_DEPTH_V1"].availability_status == AvailabilityStatus.AVAILABLE


def test_ricketts_candidates_are_resolved_and_partial_snapshots_fail_closed():
    assert RICKETTS_BLOCKED_CONTRACTS == {}
    assert adapt_ricketts_measurements(
        measurement_namespace="measurement:ricketts:legacy", constructions={}, mm_per_pixel=None, calibration_ref=None,
    ) == []
    constructions = materialize_ricketts_constructions(_landmarks(), construction_namespace="construction:ricketts:partial")
    constructions.pop("RICKETTS_E_LINE_LI_V1")
    with pytest.raises(ValueError, match="Partial Ricketts"):
        adapt_ricketts_measurements(
            measurement_namespace="measurement:ricketts:partial", constructions=constructions,
            mm_per_pixel=0.5, calibration_ref="source:calibration:partial",
        )
