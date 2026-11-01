"""TOP10-D3: executable membership reconciliation and adversarial geometry guards.

This is an architecture/geometry test only. No protocol membership is clinically
promoted; the diagnostic interpretation and normative gates remain unchanged.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from backend.services.cephalo_dependency_graph import build_analysis_pack_dependency_graph
from backend.services.cephalo_steiner_geometry import (
    steiner_anb_deg_v1,
    steiner_l1_dline_mm_v1,
    steiner_l1_nb_mm_v1,
    steiner_pog_nb_mm_v1,
    steiner_sna_deg_v1,
    steiner_snb_deg_v1,
    steiner_u1_na_mm_v1,
)
from backend.services.cephalo_tweed_merrifield_geometry import (
    tweed_fma_deg_v1,
    tweed_fmia_deg_v1,
    tweed_impa_deg_v1,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data" / "cephalometry"
SCHEMAS = ROOT / "docs" / "audits" / "schemas"


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _packs():
    data = _read(SCHEMAS / "cephalo_vnext_lot06_analysis_pack_registry_v1.json")
    return {item["analysis_id"]: item for item in data["analysis_packs"]}


def _required_steiner():
    profile = _read(DATA / "steiner_protocol_profile_v1.json")
    base = profile["layers"]["STEINER_1953_BASE"]["required_measurement_ids"]
    extension = profile["layers"]["STEINER_1959_EXTENSION"]["required_measurement_ids"]
    return base, extension


def test_steiner_membership_equals_1953_plus_1959_sections_without_clinical_promotion():
    base, extension = _required_steiner()
    pack = _packs()["STEINER_V1"]
    assert len(base) == 11 and len(extension) == 4
    assert len(set(base + extension)) == 15
    assert pack["measurement_ids"] == base + extension
    assert pack["scientific_contract_refs"] == [
        "STEINER_1953_CORE_V1",
        "STEINER_1959_CLINICAL_EXTENSION_V1",
    ]
    assert pack["composition_state"] == "PROVISIONAL_MEMBERSHIP"
    assert pack["membership_evidence_refs"] == []
    graph = build_analysis_pack_dependency_graph("STEINER_V1")
    assert graph["measurement_ids"] == base + extension
    assert graph["scientific_state"] == "PROVISIONAL_MEMBERSHIP_FAIL_CLOSED"


def test_tweed_triangle_and_merrifield_z_remain_separate_and_fail_closed():
    profile = _read(DATA / "tweed_merrifield_protocol_profile_v1.json")
    triangle = profile["profiles"]["TWEED_1954_TRIANGLE_DC_PO_OR_V1"]["required_measurement_ids"]
    z = profile["profiles"]["MERRIFIELD_1966_Z_ANGLE_V1"]["required_measurement_ids"]
    packs = _packs()
    assert len(triangle) == 3 and len(z) == 1
    assert packs["TWEED_DC_V1"]["measurement_ids"] == triangle
    assert packs["MERRIFIELD_V1"]["measurement_ids"] == z
    assert not set(triangle) & set(z)
    assert profile["final_gate"]["status"] == "OPEN"
    for pack_id in ("TWEED_DC_V1", "MERRIFIELD_V1"):
        assert packs[pack_id]["composition_state"] == "PROVISIONAL_MEMBERSHIP"
        assert packs[pack_id]["membership_evidence_refs"] == []
        assert build_analysis_pack_dependency_graph(pack_id)["scientific_state"] == (
            "PROVISIONAL_MEMBERSHIP_FAIL_CLOSED"
        )


def test_all_nineteen_contract_ids_and_linear_calibration_gates_are_exact():
    base, extension = _required_steiner()
    packs = _packs()
    ids = base + extension + packs["TWEED_DC_V1"]["measurement_ids"] + (
        packs["MERRIFIELD_V1"]["measurement_ids"]
    )
    assert len(ids) == len(set(ids)) == 19
    contracts = _read(SCHEMAS / "cephalo_vnext_lot06_executable_measurement_contract_v1.json")
    by_id = {item["measurement_id"]: item for item in contracts["measurements"]}
    assert set(ids) <= set(by_id)
    distances = [by_id[cid] for cid in ids if by_id[cid]["unit"] == "mm"]
    assert len(distances) == 4
    assert all(item["requires_calibration"] for item in distances)
    assert all(item["availability_gate"] and item["implementation"] for item in (
        by_id[cid] for cid in ids
    ))


def test_steiner_anb_rounding_is_preserved_and_not_confused_with_raw_difference():
    s = (-1.0, 0.0)
    n = (0.0, 0.0)

    def point(angle_deg):
        angle = math.radians(angle_deg)
        return (-math.cos(angle), math.sin(angle))

    a, b = point(82.149), point(78.151)
    sna = steiner_sna_deg_v1(s, n, a)
    snb = steiner_snb_deg_v1(s, n, b)
    assert sna == pytest.approx(82.149, abs=1e-8)
    assert snb == pytest.approx(78.151, abs=1e-8)
    # Current typed contract rounds each component BEFORE subtraction.
    assert steiner_anb_deg_v1(s, n, a, b) == pytest.approx(3.9, abs=1e-8)
    assert sna - snb == pytest.approx(3.998, abs=1e-8)


def test_tweed_triangle_uses_existing_intermediate_impa_rounding_without_faking_180():
    go, me = (0.0, 10.0), (10.0, 15.0)
    po, or_ = (0.0, 0.0), (10.0, 0.0)
    apex, incisal = (4.0, 18.0), (5.0, 8.0)
    fma = tweed_fma_deg_v1(go, me, po, or_)
    impa = tweed_impa_deg_v1(apex, incisal, go, me)
    fmia = tweed_fmia_deg_v1(apex, incisal, po, or_)
    assert fma == pytest.approx(26.5650511771, abs=1e-8)
    assert impa == pytest.approx(69.1, abs=1e-8)
    assert fmia == pytest.approx(84.2894068625, abs=1e-8)
    total = fma + impa + fmia
    assert total == pytest.approx(179.9544580396, abs=1e-8)
    assert round(total, 1) == 180.0
    assert total != pytest.approx(180.0, abs=1e-3)


def test_exact_landmark_identities_and_missing_linear_calibration_fail_closed():
    contracts = _read(SCHEMAS / "cephalo_vnext_lot06_executable_measurement_contract_v1.json")
    by_id = {item["measurement_id"]: item for item in contracts["measurements"]}
    assert "D_Steiner_1959" in by_id["M_SND_DEG_V1"]["required_landmarks"]
    assert "D_point" not in by_id["M_SND_DEG_V1"]["required_landmarks"]
    assert "Gn_anatomic" in by_id["M_L1_GOGN_DEG_V1"]["required_landmarks"]
    for cid in ("M_FH_GOME_DEG_V1", "M_FMIA_L1_FH_DEG_V1", "M_MERRIFIELD_Z_FH_DEG_V1"):
        assert "Po_anatomic" in by_id[cid]["required_landmarks"]
        assert "Po" not in by_id[cid]["required_landmarks"]

    line_start, line_end, point = (0.0, 0.0), (0.0, 10.0), (3.0, 4.0)
    assert steiner_u1_na_mm_v1(point, line_start, line_end, None) is None
    assert steiner_u1_na_mm_v1(None, line_start, line_end, 0.5) is None
    assert steiner_l1_nb_mm_v1(point, line_start, line_end, None) is None
    assert steiner_pog_nb_mm_v1(point, line_start, line_end, None) is None
    assert steiner_l1_dline_mm_v1(point, (0.0, 0.0), (1.0, 0.0), (11.0, 0.0), None) is None
