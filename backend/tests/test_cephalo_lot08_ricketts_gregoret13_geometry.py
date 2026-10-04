import math

import pytest

from backend.services.cephalo_ricketts_geometry import (
    ricketts_l1_apog_inclination_deg_v1,
    ricketts_maxillary_depth_deg_v1,
)


def test_ricketts_maxillary_depth_is_fh_to_na_and_allows_values_above_90():
    assert ricketts_maxillary_depth_deg_v1((0, 0), (10, 0), (0, 0), (0, 10)) == 90.0
    value = ricketts_maxillary_depth_deg_v1((0, 0), (10, 0), (0, 0), (-1, 10))
    assert value is not None and value > 90.0


def test_ricketts_l1_apog_inclination_uses_incisal_to_apex_axis():
    theta = math.radians(22.0)
    l1_incisal = (0.0, 0.0)
    l1_apex = (-math.sin(theta), math.cos(theta))
    a = (0.0, 0.0)
    pog = (0.0, 10.0)
    value = ricketts_l1_apog_inclination_deg_v1(l1_incisal, l1_apex, a, pog)
    assert value is not None
    assert value == pytest.approx(22.0, abs=1e-9)


def test_ricketts_new_angles_fail_closed_on_degenerate_axes():
    assert ricketts_maxillary_depth_deg_v1((0, 0), (0, 0), (0, 0), (0, 10)) is None
    assert ricketts_l1_apog_inclination_deg_v1((0, 0), (0, 0), (0, 0), (0, 10)) is None
