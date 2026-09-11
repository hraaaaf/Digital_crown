"""R4 contract for the first newly typed CRANIOM angular measurement."""

import math

from backend.services.cephalo_craniom_angular import craniom_u1_frankfort_deg_v1
from backend.services.cephalo_engine import CephaloEngine


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


def test_versioned_u1_frankfort_geometry_matches_existing_runtime_value():
    points = _points()
    expected = craniom_u1_frankfort_deg_v1(
        points["U1_apex"], points["U1_incisal"], points["Po"], points["Or"]
    )
    runtime = CephaloEngine(mm_per_pixel=None).calculate_metrics(points)
    actual = runtime.metrics.analyse_dentaire.I_Francfort.valeur

    assert expected is not None
    assert actual is not None
    assert math.isclose(actual, round(expected, 1), rel_tol=0.0, abs_tol=1e-12)


def test_u1_frankfort_geometry_does_not_require_linear_calibration():
    value = craniom_u1_frankfort_deg_v1(
        (20.0, 25.0), (24.0, 35.0), (0.0, 20.0), (20.0, 20.0)
    )
    assert value is not None
    assert math.isfinite(value)


def test_u1_frankfort_geometry_fails_closed_on_missing_or_degenerate_axis():
    assert craniom_u1_frankfort_deg_v1(None, (24.0, 35.0), (0.0, 20.0), (20.0, 20.0)) is None
    assert craniom_u1_frankfort_deg_v1((20.0, 25.0), (20.0, 25.0), (0.0, 20.0), (20.0, 20.0)) is None
    assert craniom_u1_frankfort_deg_v1((20.0, 25.0), (24.0, 35.0), (0.0, 20.0), (0.0, 20.0)) is None
