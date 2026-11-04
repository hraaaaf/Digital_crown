"""Numerical contract and negative oracles. Synthetic inputs ONLY; no FACAD same-image claim."""
import math

import pytest

from backend.services.cephalo_facad_wits_candidate import (
    facad_tweed_wits_bisected_ol_mm_candidate_v1 as wits,
)
from backend.services.cephalo_mcnamara_geometry import (
    mcnamara_ans_me_mm_v1, mcnamara_co_a_mm_v1, mcnamara_co_gn_mm_v1,
)
from backend.services.cephalo_tweed_merrifield_geometry import merrifield_z_angle_deg_v1
from backend.services.cephalo_canonical_analysis_v2 import CANONICAL_V2_METHOD_IDS


def _wits(**overrides):
    data = dict(olp=(0, 0), u1_incisal=(10, 2), l1_incisal=(10, -2),
                b=(2, 3), a=(7, 8), mm_per_pixel=0.2)
    data.update(overrides)
    return wits(**data)


def test_facad_candidate_wits_signed_b_to_a_and_mm_scale():
    # OLp=(0,0), OLa=(10,0), (A-B)=(5,5): +5 pixels => +1 mm.
    assert _wits() == pytest.approx(1.0)
    assert _wits(a=(2, 3), b=(7, 8)) == pytest.approx(-1.0)
    assert _wits(a=(2, 8), b=(2, 3)) == pytest.approx(0.0)


def test_facad_candidate_wits_oblique_plane_and_mirror_are_deterministic():
    oblique = dict(olp=(0, 0), u1_incisal=(10, 12), l1_incisal=(10, 8),
                   b=(0, 0), a=(3, 4), mm_per_pixel=0.5)
    expected = (3.0 + 4.0) / math.sqrt(2.0) * 0.5
    assert wits(**oblique) == pytest.approx(expected)
    mirrored = {key: (-value[0], value[1]) if key != "mm_per_pixel" else value
                for key, value in oblique.items()}
    assert wits(**mirrored) == pytest.approx(expected)


def test_facad_candidate_wits_scales_with_calibration_and_coordinate_resize():
    assert _wits(mm_per_pixel=0.1) == pytest.approx(0.5)
    scaled = dict(olp=(0, 0), u1_incisal=(20, 4), l1_incisal=(20, -4),
                  b=(4, 6), a=(14, 16), mm_per_pixel=0.1)
    assert wits(**scaled) == pytest.approx(1.0)


@pytest.mark.parametrize("override", [
    {"olp": None},  # No manual posterior marker => no Wits.
    {"u1_incisal": None},
    {"l1_incisal": None},
    {"a": None},
    {"b": (float("nan"), 2)},
    {"mm_per_pixel": None},
    {"mm_per_pixel": 0},
    {"mm_per_pixel": float("inf")},
    {"olp": (10, 0)},  # OLa == OLp; no axis.
])
def test_facad_candidate_wits_invalid_inputs_refused(override):
    assert _wits(**override) is None


def test_facad_candidate_is_not_registered_as_clinical_measurement():
    assert "M_FACAD_TWEED_WITS_BISECTED_OL_MM_V1" not in CANONICAL_V2_METHOD_IDS


def test_existing_dc_mcnamara_lengths_match_independent_345_oracle():
    # 3-4-5 right triangle => 5 px; 0.2 mm/px => 1.0 mm.
    assert mcnamara_co_a_mm_v1((0, 0), (3, 4), 0.2) == pytest.approx(1.0)
    assert mcnamara_co_gn_mm_v1((0, 0), (6, 8), 0.2) == pytest.approx(2.0)
    assert mcnamara_ans_me_mm_v1((2, 1), (2, 7), 0.2) == pytest.approx(1.2)
    assert mcnamara_co_a_mm_v1((0, 0), (3, 4), None) is None


def test_existing_dc_mcnamara_rotation_and_resize_invariance():
    # R90 rotation changes coordinate representation, not length.
    assert mcnamara_co_a_mm_v1((0, 0), (-4, 3), 0.2) == pytest.approx(1.0)
    # Resizing image x2 requires calibration /2.
    assert mcnamara_co_a_mm_v1((0, 0), (6, 8), 0.1) == pytest.approx(1.0)


def test_existing_dc_z_supplementary_collision_remains_a_hold_not_a_pass():
    po, or_, chin = (0, 0), (10, 0), (2, 20)
    v1_anterior = merrifield_z_angle_deg_v1(po, or_, chin, (7, 10), (6, 12))
    v1_posterior = merrifield_z_angle_deg_v1(po, or_, chin, (-3, 10), (-4, 12))
    # Both give ~63.43 in V1, while oriented inferior-sector rays can give
    # 63.43 versus 116.57. This is NOT FACAD Z numeric parity or an approved fix.
    assert v1_anterior == pytest.approx(63.4349488229)
    assert v1_posterior == pytest.approx(v1_anterior)
    oriented_counterexample = math.degrees(math.acos(-5 / math.sqrt(125)))
    assert oriented_counterexample == pytest.approx(116.5650511771)
    assert v1_posterior != pytest.approx(oriented_counterexample)
