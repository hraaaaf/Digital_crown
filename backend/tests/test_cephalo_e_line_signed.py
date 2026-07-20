import math

import pytest

from backend.services.cephalo_engine import CephaloEngine


def _points(ls=(2.0, 5.0), li=(3.0, 5.0)):
    return {
        "Prn": (0.0, 0.0),
        "Pog_soft": (0.0, 10.0),
        "Po": (-10.0, 0.0),
        "Or": (10.0, 0.0),
        "Ls": ls,
        "Li": li,
    }


def _values(points, ratio=1.0):
    result = CephaloEngine(mm_per_pixel=ratio).calculate_metrics(points)
    esthetic = result.metrics.analyse_esthetique
    return esthetic.Ligne_E_Ls.valeur, esthetic.Ligne_E_Li.valeur


def _rotate(point, degrees):
    radians = math.radians(degrees)
    x, y = point
    return (
        x * math.cos(radians) - y * math.sin(radians),
        x * math.sin(radians) + y * math.cos(radians),
    )


@pytest.mark.parametrize("lip", ["Ls", "Li"])
@pytest.mark.parametrize("coordinate, expected", [((2.0, 5.0), 2.0), ((-2.0, 5.0), -2.0), ((0.0, 5.0), 0.0)])
def test_e_line_preserves_anterior_posterior_and_on_line_values(lip, coordinate, expected):
    points = _points()
    points[lip] = coordinate

    assert _values(points)[0 if lip == "Ls" else 1] == pytest.approx(expected)


def test_e_line_is_invariant_under_mirror_rotation_and_endpoint_reversal():
    points = _points()
    baseline = _values(points)

    mirrored = {name: (-x, y) for name, (x, y) in points.items()}
    assert _values(mirrored) == pytest.approx(baseline)

    for degrees in (30.0, -45.0, 90.0):
        rotated = {name: _rotate(point, degrees) for name, point in points.items()}
        assert _values(rotated) == pytest.approx(baseline, abs=1e-6)

    reversed_endpoints = dict(points)
    reversed_endpoints["Prn"], reversed_endpoints["Pog_soft"] = points["Pog_soft"], points["Prn"]
    assert _values(reversed_endpoints) == pytest.approx(baseline)


@pytest.mark.parametrize("missing", ["Po", "Or", "Prn", "Pog_soft", "Ls", "Li"])
def test_e_line_is_unavailable_when_a_required_landmark_is_missing(missing):
    points = _points()
    points.pop(missing)
    ls_value, li_value = _values(points)

    if missing == "Li":
        assert ls_value is not None
        assert li_value is None
    elif missing == "Ls":
        assert ls_value is None
        assert li_value is not None
    else:
        assert ls_value is None
        assert li_value is None


def test_e_line_is_unavailable_without_calibration_or_with_degenerate_geometry():
    assert _values(_points(), ratio=None) == (None, None)

    degenerate_e_line = _points()
    degenerate_e_line["Pog_soft"] = degenerate_e_line["Prn"]
    assert _values(degenerate_e_line) == (None, None)

    degenerate_frankfort = _points()
    degenerate_frankfort["Or"] = degenerate_frankfort["Po"]
    assert _values(degenerate_frankfort) == (None, None)


def test_e_line_is_unavailable_when_anterior_side_is_indeterminate():
    points = _points()
    points["Prn"] = (0.0, 0.0)
    points["Pog_soft"] = (10.0, 0.0)
    points["Po"] = (0.0, -10.0)
    points["Or"] = (10.0, -10.0)

    assert _values(points) == (None, None)


def test_e_line_does_not_auto_alias_refined_lip_points():
    points = _points()
    points.pop("Ls")
    points.pop("Li")
    points["Ls2"] = (2.0, 5.0)
    points["Li2"] = (3.0, 5.0)

    assert _values(points) == (None, None)
