"""Bergen B4 safety regression: geometry validity, NOT FACAD clinical parity."""

import math

import pytest

from audit.facad_bergen_geometry_guard import (
    angle3p_unsigned_deg, angle4p_unsigned_deg, point_line_distance_px,
)


def test_b4_angle3_zero_first_ray_never_becomes_signed_zero():
    assert angle3p_unsigned_deg((0, 0), (0, 0), (1, 0)) is None


def test_b4_angle3_zero_second_ray_never_becomes_signed_zero():
    assert angle3p_unsigned_deg((1, 0), (0, 0), (0, 0)) is None


def test_b4_angle4_zero_first_line_has_no_angle():
    assert angle4p_unsigned_deg((0, 0), (0, 0), (0, 0), (1, 0)) is None


def test_b4_angle4_zero_second_line_has_no_angle():
    assert angle4p_unsigned_deg((0, 0), (1, 0), (0, 0), (0, 0)) is None


def test_b4_point_line_zero_line_never_divides_by_zero():
    assert point_line_distance_px((3, 5), (1, 1), (1, 1)) is None


@pytest.mark.parametrize('invalid', [None, (), (0,), (1, 2, 3), (math.nan, 1), (math.inf, 0), (True, 0), (10**1000, 2)])
def test_bad_point_is_never_a_valid_angle_or_distance(invalid):
    assert angle3p_unsigned_deg(invalid, (0, 0), (0, 1)) is None
    assert angle4p_unsigned_deg(invalid, (0, 0), (1, 0), (0, 0)) is None
    assert point_line_distance_px(invalid, (0, 0), (1, 0)) is None


def test_genuine_zero_angle_is_valid_and_distinct_from_undefined():
    assert angle3p_unsigned_deg((1, 0), (0, 0), (2, 0)) == pytest.approx(0)
    assert angle4p_unsigned_deg((0, 0), (1, 0), (0, 5), (4, 5)) == pytest.approx(0)


def test_right_and_straight_angles_and_distance():
    assert angle3p_unsigned_deg((1, 0), (0, 0), (0, 1)) == pytest.approx(90)
    assert angle3p_unsigned_deg((1, 0), (0, 0), (-1, 0)) == pytest.approx(180)
    assert angle4p_unsigned_deg((0, 0), (1, 0), (0, 0), (0, -1)) == pytest.approx(90)
    assert point_line_distance_px((4, 3), (0, 0), (8, 0)) == pytest.approx(3)


def test_translation_rotation_mirror_and_scaling_metamorphic():
    baseline = angle3p_unsigned_deg((2, 0), (0, 0), (1, 1))
    assert baseline == pytest.approx(45)
    assert angle3p_unsigned_deg((12, 5), (10, 5), (11, 6)) == pytest.approx(baseline)
    assert angle3p_unsigned_deg((0, 2), (0, 0), (-1, 1)) == pytest.approx(baseline)
    assert angle3p_unsigned_deg((-2, 0), (0, 0), (-1, 1)) == pytest.approx(baseline)
    assert angle3p_unsigned_deg((20, 0), (0, 0), (10, 10)) == pytest.approx(baseline)
    for factor in [0.5, 1, 10]:
        result = point_line_distance_px((4 * factor, 3 * factor), (0, 0), (8 * factor, 0))
        assert result == pytest.approx(3 * factor)


def test_near_degenerate_vector_is_non_computable():
    assert angle3p_unsigned_deg((1e-15, 0), (0, 0), (1, 0)) is None
    assert point_line_distance_px((0, 1), (0, 0), (1e-15, 0)) is None
