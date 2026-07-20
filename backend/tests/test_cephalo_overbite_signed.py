import math

import pytest

from backend.services.cephalo_engine import CephaloEngine


def _points(upper=(50.0, 30.0), lower=(50.0, 20.0), po=(0.0, 0.0), or_=(100.0, 0.0)):
    return {"Po": po, "Or": or_, "U1i": upper, "L1i": lower}


def _overbite(points):
    result = CephaloEngine(mm_per_pixel=1.0).calculate_metrics(points)
    return result.metrics.analyse_dentaire.Recouvrement.valeur


def _rotate(point, degrees=30.0):
    radians = math.radians(degrees)
    x, y = point
    return (
        x * math.cos(radians) - y * math.sin(radians),
        x * math.sin(radians) + y * math.cos(radians),
    )


def test_recouvrement_preserves_positive_zero_and_negative_values():
    assert _overbite(_points()) == pytest.approx(10.0)
    assert _overbite(_points(upper=(50.0, 30.0), lower=(50.0, 30.0))) == pytest.approx(0.0)
    assert _overbite(_points(upper=(50.0, 30.0), lower=(50.0, 40.0))) == pytest.approx(-10.0)


def test_recouvrement_is_invariant_under_rotation():
    points = _points()
    rotated = {name: _rotate(point) for name, point in points.items()}

    assert _overbite(rotated) == pytest.approx(_overbite(points), abs=0.1)


def test_recouvrement_is_invariant_under_horizontal_mirror():
    points = _points()
    mirrored = {name: (100.0 - point[0], point[1]) for name, point in points.items()}

    assert _overbite(mirrored) == pytest.approx(_overbite(points), abs=0.1)
