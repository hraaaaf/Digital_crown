from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.services.cephalo_constructions import (
    craniom_ab_prime_mm_v1,
    craniom_facial_depth_mm_v1,
    nasion_vertical_offset_mm_v1,
)
from backend.services.cephalo_mcnamara_geometry import (
    mcnamara_ans_me_mm_v1,
    mcnamara_co_a_mm_v1,
    mcnamara_co_gn_mm_v1,
)
from backend.services.cephalo_ricketts_geometry import (
    ricketts_constructed_gn_v1,
    ricketts_convexity_signed_distance_px_v1,
    ricketts_facial_axis_deg_v1,
    ricketts_facial_depth_deg_v1,
)
from backend.services.cephalo_steiner_geometry import (
    steiner_anb_deg_v1,
    steiner_l1_nb_deg_v1,
    steiner_sna_deg_v1,
    steiner_snb_deg_v1,
    steiner_sn_mp_deg_v1,
    steiner_u1_na_deg_v1,
)
from backend.services.cephalo_tweed_merrifield_geometry import (
    tweed_fma_deg_v1,
    tweed_fmia_deg_v1,
    tweed_impa_deg_v1,
)


_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "cephalo" / "source_locked_geometry_v1.json"
)


def _fixture() -> dict[str, object]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _point(points: dict[str, list[float]], landmark_id: str) -> tuple[float, float]:
    value = points[landmark_id]
    return (float(value[0]), float(value[1]))


def test_fixture_is_manual_synthetic_and_norm_free() -> None:
    fixture = _fixture()
    assert fixture["fixture_id"] == "CEPHALO_SOURCE_LOCKED_GEOMETRY_V1"
    purpose = str(fixture["purpose"])
    assert "Manual synthetic geometry" in purpose
    assert "detector" in purpose
    assert "clinical norms" in purpose


def test_steiner_manual_fixture_covers_existing_source_specific_primitives() -> None:
    case = _fixture()["steiner"]
    points = case["points"]
    expected = case["expected"]

    s = _point(points, "S")
    n = _point(points, "N")
    a = _point(points, "A")
    b = _point(points, "B")
    u1_apex = _point(points, "U1_apex")
    u1_incisal = _point(points, "U1_incisal")
    l1_apex = _point(points, "L1_apex")
    l1_incisal = _point(points, "L1_incisal")
    go = _point(points, "Go")
    gn_anatomic = _point(points, "Gn_anatomic")

    assert steiner_sna_deg_v1(s, n, a) == pytest.approx(expected["SNA_deg"])
    assert steiner_snb_deg_v1(s, n, b) == pytest.approx(expected["SNB_deg"])
    assert steiner_anb_deg_v1(s, n, a, b) == pytest.approx(expected["ANB_deg"])
    assert steiner_u1_na_deg_v1(u1_apex, u1_incisal, n, a) == pytest.approx(
        expected["U1_NA_deg"]
    )
    assert steiner_l1_nb_deg_v1(l1_apex, l1_incisal, n, b) == pytest.approx(
        expected["L1_NB_deg"]
    )
    assert steiner_sn_mp_deg_v1(s, n, go, gn_anatomic) == pytest.approx(
        expected["SN_GoGn_deg"]
    )


def test_tweed_dc_po_or_fixture_certifies_selected_triangle_geometry() -> None:
    case = _fixture()["tweed_dc_po_or"]
    points = case["points"]
    expected = case["expected"]

    po = _point(points, "Po_anatomic")
    or_ = _point(points, "Or")
    go = _point(points, "Go")
    me = _point(points, "Me")
    l1_apex = _point(points, "L1_apex")
    l1_incisal = _point(points, "L1_incisal")

    fma = tweed_fma_deg_v1(go, me, po, or_)
    impa = tweed_impa_deg_v1(l1_apex, l1_incisal, go, me)
    fmia = tweed_fmia_deg_v1(l1_apex, l1_incisal, po, or_)

    assert fma == pytest.approx(expected["FMA_deg"])
    assert impa == pytest.approx(expected["IMPA_deg"])
    assert fmia == pytest.approx(expected["FMIA_deg"])
    assert fma is not None and impa is not None and fmia is not None
    assert fma + impa + fmia == pytest.approx(expected["triangle_sum_deg"])


def test_mcnamara_manual_fixture_requires_calibrated_anatomic_lengths() -> None:
    case = _fixture()["mcnamara_1984"]
    points = case["points"]
    expected = case["expected"]
    ratio = float(case["mm_per_pixel"])

    co = _point(points, "Co_anatomic")
    a = _point(points, "A")
    gn_anatomic = _point(points, "Gn_anatomic")
    ans = _point(points, "ANS")
    me = _point(points, "Me")

    co_a = mcnamara_co_a_mm_v1(co, a, ratio)
    co_gn = mcnamara_co_gn_mm_v1(co, gn_anatomic, ratio)
    ans_me = mcnamara_ans_me_mm_v1(ans, me, ratio)

    assert co_a == pytest.approx(expected["Co_A_mm"])
    assert co_gn == pytest.approx(expected["Co_Gn_mm"])
    assert ans_me == pytest.approx(expected["ANS_Me_mm"])
    assert co_a is not None and co_gn is not None
    assert co_gn - co_a == pytest.approx(
        expected["maxillomandibular_differential_mm"]
    )


def test_ricketts_manual_fixture_keeps_hard_pog_pt_and_constructed_gn_distinct() -> None:
    case = _fixture()["ricketts"]
    points = case["points"]
    expected = case["expected"]

    po = _point(points, "Po_anatomic")
    or_ = _point(points, "Or")
    n = _point(points, "N")
    pog_hard = _point(points, "Pog_hard")
    go = _point(points, "Go")
    me = _point(points, "Me")
    ba = _point(points, "Ba")
    pt_ricketts = _point(points, "Pt_Ricketts")
    a = _point(points, "A")

    facial_angle = ricketts_facial_depth_deg_v1(po, or_, n, pog_hard)
    gn_constructed = ricketts_constructed_gn_v1(n, pog_hard, go, me)

    assert facial_angle == pytest.approx(expected["Facial_Angle_deg"])
    assert gn_constructed == pytest.approx(tuple(expected["Gn_constructed"]))
    assert gn_constructed is not None

    facial_axis = ricketts_facial_axis_deg_v1(
        ba, n, pt_ricketts, gn_constructed
    )
    convexity = ricketts_convexity_signed_distance_px_v1(
        a, n, pog_hard, po, or_
    )

    assert facial_axis == pytest.approx(expected["Facial_Axis_deg"])
    assert convexity == pytest.approx(expected["Maxillary_Convexity_px"])


def test_com_manual_fixture_certifies_ap_sign_and_legacy_depth_magnitude() -> None:
    case = _fixture()["com_dc_legacy"]
    points = case["points"]
    expected = case["expected"]
    ratio = float(case["mm_per_pixel"])

    n = _point(points, "N")
    po = _point(points, "Po_anatomic")
    or_ = _point(points, "Or")
    a = _point(points, "A")
    b = _point(points, "B")
    s = _point(points, "S")

    assert nasion_vertical_offset_mm_v1(a, n, po, or_, ratio) == pytest.approx(
        expected["Situation_A_mm"]
    )
    assert nasion_vertical_offset_mm_v1(b, n, po, or_, ratio) == pytest.approx(
        expected["Situation_B_mm"]
    )
    assert craniom_ab_prime_mm_v1(a, b, po, or_, ratio) == pytest.approx(
        expected["AB_prime_mm"]
    )
    assert craniom_facial_depth_mm_v1(s, n, po, or_, ratio) == pytest.approx(
        expected["Facial_Depth_mm"]
    )


def test_manual_fixture_fails_closed_on_degenerate_reference_frames() -> None:
    assert tweed_fma_deg_v1((0.0, 1.0), (1.0, 1.0), (0.0, 0.0), (0.0, 0.0)) is None
    assert mcnamara_co_a_mm_v1((0.0, 0.0), (3.0, 4.0), None) is None
    assert ricketts_constructed_gn_v1(
        (0.0, 0.0), (10.0, 0.0), (0.0, 1.0), (10.0, 1.0)
    ) is None
    assert nasion_vertical_offset_mm_v1(
        (1.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), 0.2
    ) is None
