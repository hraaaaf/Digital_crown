from __future__ import annotations

import pytest

from backend.services.cephalo_measure_registry import (
    CANONICAL_MEASUREMENTS,
    canonical_measurement,
    canonical_unit,
    cephalo_unit,
    is_mm_metric,
)


def test_canonical_ids_resolve_without_aliasing() -> None:
    sna = canonical_measurement("M_SNA_DEG_V1")
    a_nperp = canonical_measurement("M_A_NPERP_MM_V1")

    assert sna is not None
    assert sna.measurement_id == "M_SNA_DEG_V1"
    assert sna.unit == "°"
    assert a_nperp is not None
    assert a_nperp.measurement_id == "M_A_NPERP_MM_V1"
    assert a_nperp.unit == "mm"
    assert canonical_measurement("M_NOT_A_REAL_MEASUREMENT_V1") is None


def test_canonical_unit_is_fail_closed_when_not_source_locked() -> None:
    assert canonical_unit("M_OVERBITE_V1") == "mm"
    assert canonical_unit("M_PA_SKELETAL_SYMMETRY_V1") is None



def test_legacy_public_helpers_remain_compatible() -> None:
    assert is_mm_metric("Situation_A") is True
    assert cephalo_unit("Situation_A") == "mm"
    assert is_mm_metric("SNA") is False
    assert cephalo_unit("SNA") == "°"


def test_canonical_helpers_override_legacy_keyword_guessing() -> None:
    assert is_mm_metric("M_A_NPERP_MM_V1") is True
    assert cephalo_unit("M_A_NPERP_MM_V1") == "mm"
    assert is_mm_metric("M_SNA_DEG_V1") is False
    assert cephalo_unit("M_SNA_DEG_V1") == "°"


def test_prohibited_false_equivalents_remain_distinct() -> None:
    prohibited_pairs = (
        ("M_B_NPERP_MM_V1", "M_POG_NPERP_MM_V1"),
        ("M_U1_FH_DEG_V1", "M_FMIA_L1_FH_DEG_V1"),
        ("M_FACIAL_ANGLE_NPOG_FH_DEG_V1", "M_COM_S_NPERP_DEPTH_MM_V1"),
        ("M_FACIAL_AXIS_RICKETTS_DEG_V1", "M_FACIAL_AXIS_MCNAMARA_DEG_V1"),
        ("M_L1_EDGE_APOG_MM_V1", "M_L1_FACIAL_SURFACE_APOG_MM_V1"),
        ("M_FH_GOME_DEG_V1", "M_FH_SUBGO_M_DEG_V1"),
    )

    for left, right in prohibited_pairs:
        assert left in CANONICAL_MEASUREMENTS
        assert right in CANONICAL_MEASUREMENTS
        assert CANONICAL_MEASUREMENTS[left].measurement_id == left
        assert CANONICAL_MEASUREMENTS[right].measurement_id == right
        assert CANONICAL_MEASUREMENTS[left] != CANONICAL_MEASUREMENTS[right]
