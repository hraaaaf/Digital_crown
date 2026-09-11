from __future__ import annotations

import pytest

from backend.services.cephalo_steiner_geometry import (
    steiner_l1_nb_deg_v1,
    steiner_u1_na_deg_v1,
)


def test_steiner_dental_angles_return_smallest_axis_angle():
    n = (20.0, 10.0)
    a = (24.0, 28.0)
    b = (22.0, 38.0)
    u1a = (20.0, 25.0)
    u1i = (24.0, 35.0)
    l1a = (20.0, 48.0)
    l1i = (23.0, 38.0)

    assert steiner_u1_na_deg_v1(u1a, u1i, n, a) == pytest.approx(9.2726017772)
    assert steiner_l1_nb_deg_v1(l1a, l1i, n, b) == pytest.approx(20.7848610140)


def test_steiner_dental_angles_are_axis_orientation_invariant():
    n = (20.0, 10.0)
    a = (24.0, 28.0)
    b = (22.0, 38.0)
    u1a = (20.0, 25.0)
    u1i = (24.0, 35.0)
    l1a = (20.0, 48.0)
    l1i = (23.0, 38.0)

    upper = steiner_u1_na_deg_v1(u1a, u1i, n, a)
    lower = steiner_l1_nb_deg_v1(l1a, l1i, n, b)

    assert steiner_u1_na_deg_v1(u1i, u1a, n, a) == pytest.approx(upper)
    assert steiner_u1_na_deg_v1(u1a, u1i, a, n) == pytest.approx(upper)
    assert steiner_l1_nb_deg_v1(l1i, l1a, n, b) == pytest.approx(lower)
    assert steiner_l1_nb_deg_v1(l1a, l1i, b, n) == pytest.approx(lower)


def test_steiner_dental_angles_fail_closed_on_degenerate_axes_or_reference_lines():
    n = (1.0, 1.0)
    a = (2.0, 3.0)
    b = (4.0, 5.0)
    u1a = (0.0, 0.0)
    u1i = (0.0, 5.0)
    l1a = (3.0, 0.0)
    l1i = (3.0, 5.0)

    assert steiner_u1_na_deg_v1(u1a, u1a, n, a) is None
    assert steiner_l1_nb_deg_v1(l1a, l1a, n, b) is None
    assert steiner_u1_na_deg_v1(u1a, u1i, n, n) is None
    assert steiner_l1_nb_deg_v1(l1a, l1i, n, n) is None
