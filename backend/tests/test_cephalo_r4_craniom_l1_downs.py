"""R4 contract for typed CRANIOM lower-incisor / Downs geometry."""

import math

from backend.services.cephalo_craniom_angular import craniom_l1_downs_deg_v1
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_geometric_conventions import get_active_craniom_convention


def _points():
    return {
        "S": (10.0, 10.0),
        "N": (20.0, 10.0),
        "Po": (0.0, 20.0),
        "Or": (20.0, 20.0),
        "A": (24.0, 28.0),
        "B": (22.0, 38.0),
        "Go": (5.0, 50.0),
        "Me": (25.0, 55.0),
        "U1_apex": (20.0, 25.0),
        "U1_incisal": (24.0, 35.0),
        "L1_apex": (20.0, 48.0),
        "L1_incisal": (23.0, 38.0),
    }


def test_downs_convention_is_explicit_go_me_and_primary_sourced():
    spec = get_active_craniom_convention("CRANIOM_L1_TO_DOWNS_MP_V1")
    assert spec.reference_frame_id == "DOWNS_MP_GO_ME_V1"
    assert spec.required_landmark_ids == ("L1_apex", "L1_incisal", "Go", "Me")
    assert "doi:10.1016/0002-9416(48)90015-3" in spec.source_references
    assert "doi:10.1051/odfen/2011104" in spec.source_references


def test_versioned_l1_downs_geometry_matches_existing_runtime_impa():
    points = _points()
    expected = craniom_l1_downs_deg_v1(
        points["L1_apex"], points["L1_incisal"], points["Go"], points["Me"]
    )
    runtime = CephaloEngine(mm_per_pixel=None).calculate_metrics(points)
    actual = runtime.metrics.analyse_dentaire.IMPA.valeur

    assert expected is not None
    assert actual is not None
    assert math.isclose(actual, round(expected, 1), rel_tol=0.0, abs_tol=1e-12)


def test_l1_downs_geometry_does_not_require_linear_calibration():
    value = craniom_l1_downs_deg_v1(
        (20.0, 48.0), (23.0, 38.0), (5.0, 50.0), (25.0, 55.0)
    )
    assert value is not None
    assert math.isfinite(value)


def test_l1_downs_geometry_fails_closed_on_missing_or_degenerate_axis():
    assert craniom_l1_downs_deg_v1(None, (23.0, 38.0), (5.0, 50.0), (25.0, 55.0)) is None
    assert craniom_l1_downs_deg_v1((20.0, 48.0), (20.0, 48.0), (5.0, 50.0), (25.0, 55.0)) is None
    assert craniom_l1_downs_deg_v1((20.0, 48.0), (23.0, 38.0), (5.0, 50.0), (5.0, 50.0)) is None
