import math

import pytest

from backend.services.cephalo_constructions import (
    craniom_ab_prime_mm_v1,
    craniom_facial_depth_mm_v1,
    nasion_vertical_offset_mm_v1,
    orthogonal_projection_v1,
)


def _rotate(point, degrees):
    angle = math.radians(degrees)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y = point
    return (x * c - y * s, x * s + y * c)


def _translate(point, dx, dy):
    return (point[0] + dx, point[1] + dy)


def test_craniom_ab_prime_positive_when_a_is_anterior_to_b():
    po, orbitale = (0.0, 0.0), (10.0, 0.0)
    a, b = (8.0, 7.0), (3.0, -4.0)

    value = craniom_ab_prime_mm_v1(a, b, po, orbitale, 1.0)

    assert value == pytest.approx(5.0)


def test_craniom_ab_prime_negative_when_a_is_posterior_to_b():
    po, orbitale = (0.0, 0.0), (10.0, 0.0)
    a, b = (2.0, 7.0), (5.0, -4.0)

    value = craniom_ab_prime_mm_v1(a, b, po, orbitale, 1.0)

    assert value == pytest.approx(-3.0)


def test_craniom_ab_prime_is_rotation_invariant():
    points = {
        "po": (0.0, 0.0),
        "or": (10.0, 0.0),
        "a": (8.0, 7.0),
        "b": (3.0, -4.0),
    }
    baseline = craniom_ab_prime_mm_v1(
        points["a"], points["b"], points["po"], points["or"], 0.25
    )
    rotated = {key: _rotate(value, 37.0) for key, value in points.items()}

    actual = craniom_ab_prime_mm_v1(
        rotated["a"], rotated["b"], rotated["po"], rotated["or"], 0.25
    )

    assert actual == pytest.approx(baseline, abs=1e-12)


def test_craniom_ab_prime_is_translation_invariant():
    po, orbitale = (2.0, 1.0), (12.0, 4.0)
    a, b = (9.0, 8.0), (4.0, 2.0)
    baseline = craniom_ab_prime_mm_v1(a, b, po, orbitale, 0.2)

    translated = [
        _translate(point, 150.0, -80.0)
        for point in (a, b, po, orbitale)
    ]
    actual = craniom_ab_prime_mm_v1(*translated, 0.2)

    assert actual == pytest.approx(baseline, abs=1e-12)


def test_calibration_compensates_pixel_scaling():
    po, orbitale = (0.0, 0.0), (10.0, 0.0)
    a, b = (8.0, 7.0), (3.0, -4.0)
    baseline = craniom_ab_prime_mm_v1(a, b, po, orbitale, 0.2)

    scale = 4.0
    scaled = [
        (point[0] * scale, point[1] * scale)
        for point in (a, b, po, orbitale)
    ]
    actual = craniom_ab_prime_mm_v1(*scaled, 0.2 / scale)

    assert actual == pytest.approx(baseline, abs=1e-12)


def test_nasion_vertical_offsets_use_frankfort_axis():
    po, orbitale = (0.0, 0.0), (10.0, 0.0)
    nasion = (4.0, 20.0)

    assert nasion_vertical_offset_mm_v1(
        (7.0, -100.0), nasion, po, orbitale, 0.5
    ) == pytest.approx(1.5)
    assert nasion_vertical_offset_mm_v1(
        (1.0, 999.0), nasion, po, orbitale, 0.5
    ) == pytest.approx(-1.5)


def test_facial_depth_is_unsigned_distance_to_nasion_vertical():
    po, orbitale = (0.0, 0.0), (10.0, 0.0)
    nasion = (10.0, 5.0)
    sella = (2.0, 50.0)

    assert craniom_facial_depth_mm_v1(
        sella, nasion, po, orbitale, 0.25
    ) == pytest.approx(2.0)


def test_orthogonal_projection_hits_frankfort_line():
    projected = orthogonal_projection_v1(
        (0.0, 0.0), (10.0, 0.0), (7.0, 8.0)
    )
    assert projected == pytest.approx((7.0, 0.0))


@pytest.mark.parametrize("ratio", [None, 0.0, -0.1, float("nan"), float("inf")])
def test_linear_constructions_fail_closed_without_valid_calibration(ratio):
    assert craniom_ab_prime_mm_v1(
        (8.0, 7.0), (3.0, -4.0), (0.0, 0.0), (10.0, 0.0), ratio
    ) is None


def test_constructions_fail_closed_on_missing_or_degenerate_landmarks():
    assert craniom_ab_prime_mm_v1(
        None, (3.0, 2.0), (0.0, 0.0), (10.0, 0.0), 0.2
    ) is None
    assert craniom_ab_prime_mm_v1(
        (8.0, 7.0), (3.0, 2.0), (5.0, 5.0), (5.0, 5.0), 0.2
    ) is None
    assert orthogonal_projection_v1(
        (5.0, 5.0), (5.0, 5.0), (8.0, 7.0)
    ) is None
