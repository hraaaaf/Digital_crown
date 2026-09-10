import pytest

from backend.services.cephalo_constructions import (
    craniom_ab_prime_mm_v1,
    craniom_facial_depth_mm_v1,
    nasion_vertical_offset_mm_v1,
    orthogonal_projection_v1,
)
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
        "U1a": (20.0, 25.0),
        "U1i": (24.0, 35.0),
        "L1a": (20.0, 48.0),
        "L1i": (23.0, 38.0),
    }


def test_runtime_matches_versioned_craniom_linear_constructions():
    points = _points()
    ratio = 0.2
    result = CephaloEngine(mm_per_pixel=ratio).calculate_metrics(points)

    expected_a = nasion_vertical_offset_mm_v1(
        points["A"], points["N"], points["Po"], points["Or"], ratio
    )
    expected_b = nasion_vertical_offset_mm_v1(
        points["B"], points["N"], points["Po"], points["Or"], ratio
    )
    expected_ab = craniom_ab_prime_mm_v1(
        points["A"], points["B"], points["Po"], points["Or"], ratio
    )
    expected_depth = craniom_facial_depth_mm_v1(
        points["S"], points["N"], points["Po"], points["Or"], ratio
    )

    assert result.metrics.analyse_osseuse.Situation_A.valeur == pytest.approx(round(expected_a, 1))
    assert result.metrics.analyse_osseuse.Situation_B.valeur == pytest.approx(round(expected_b, 1))
    assert result.metrics.analyse_osseuse.Decalage_A_B.valeur == pytest.approx(round(expected_ab, 1))
    assert result.metrics.analyse_osseuse.Profondeur_Faciale.valeur == pytest.approx(round(expected_depth, 1))


def test_runtime_visual_a_and_b_prime_match_orthogonal_projection_on_frankfort():
    points = _points()
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(points)

    expected_a_prime = orthogonal_projection_v1(
        points["Po"], points["Or"], points["A"]
    )
    expected_b_prime = orthogonal_projection_v1(
        points["Po"], points["Or"], points["B"]
    )

    assert result.visual_debug["A_prime"] == pytest.approx(expected_a_prime)
    assert result.visual_debug["B_prime"] == pytest.approx(expected_b_prime)


def test_runtime_linear_craniom_values_fail_closed_without_calibration():
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points())

    assert result.metrics.analyse_osseuse.Situation_A.valeur is None
    assert result.metrics.analyse_osseuse.Situation_B.valeur is None
    assert result.metrics.analyse_osseuse.Decalage_A_B.valeur is None
    assert result.metrics.analyse_osseuse.Profondeur_Faciale.valeur is None
