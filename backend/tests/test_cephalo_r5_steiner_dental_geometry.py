from __future__ import annotations

import pytest

from backend.services.cephalo_steiner_geometry import (
    steiner_l1_nb_deg_v1,
    steiner_l1_nb_mm_v1,
    steiner_u1_na_deg_v1,
    steiner_u1_na_mm_v1,
)


def test_steiner_dental_angles_are_calibration_independent():
    n = (20.0, 10.0)
    a = (24.0, 28.0)
    b = (22.0, 38.0)
    u1a = (20.0, 25.0)
    u1i = (24.0, 35.0)
    l1a = (20.0, 48.0)
    l1i = (23.0, 38.0)

    assert steiner_u1_na_deg_v1(u1a, u1i, n, a) == pytest.approx(
        steiner_u1_na_deg_v1(u1a, u1i, n, a)
    )
    assert steiner_l1_nb_deg_v1(l1a, l1i, n, b) == pytest.approx(
        steiner_l1_nb_deg_v1(l1a, l1i, n, b)
    )
    assert steiner_u1_na_deg_v1(u1a, u1a, n, a) is None
    assert steiner_l1_nb_deg_v1(l1a, l1a, n, b) is None


def test_steiner_dental_linear_distances_require_valid_calibration():
    n = (0.0, 0.0)
    a = (0.0, 10.0)
    b = (0.0, 20.0)
    u1i = (5.0, 5.0)
    l1i = (4.0, 15.0)

    assert steiner_u1_na_mm_v1(u1i, n, a, 0.2) == pytest.approx(1.0)
    assert steiner_l1_nb_mm_v1(l1i, n, b, 0.2) == pytest.approx(0.8)
    assert steiner_u1_na_mm_v1(u1i, n, a, None) is None
    assert steiner_l1_nb_mm_v1(l1i, n, b, 0.0) is None


def test_steiner_dental_distance_is_perpendicular_and_orientation_invariant():
    n = (0.0, 0.0)
    a = (10.0, 0.0)
    u1i = (4.0, 3.0)

    forward = steiner_u1_na_mm_v1(u1i, n, a, 0.5)
    reversed_line = steiner_u1_na_mm_v1(u1i, a, n, 0.5)

    assert forward == pytest.approx(1.5)
    assert reversed_line == pytest.approx(forward)


def test_steiner_dental_geometry_fails_closed_on_degenerate_reference_lines():
    n = (1.0, 1.0)
    u1a = (0.0, 0.0)
    u1i = (0.0, 5.0)
    l1a = (3.0, 0.0)
    l1i = (3.0, 5.0)

    assert steiner_u1_na_deg_v1(u1a, u1i, n, n) is None
    assert steiner_l1_nb_deg_v1(l1a, l1i, n, n) is None
    assert steiner_u1_na_mm_v1(u1i, n, n, 0.2) is None
    assert steiner_l1_nb_mm_v1(l1i, n, n, 0.2) is None
