"""TOP10-D4: parallel McNamara 1984 / Ricketts 1981-2009-1997 hard gates.

Only provisional executable pack membership is changed. No new formulas, norms,
universal classifications, or frontal-PA inference from a lateral image.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from backend.services.cephalo_dependency_graph import build_analysis_pack_dependency_graph
from backend.services.cephalo_protocol_projection import (
    project_mcnamara_reference_protocol,
    project_ricketts_atlas2009_protocol,
    project_ricketts_gregoret13_protocol,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "docs" / "audits" / "schemas"
DATA = ROOT / "backend" / "data" / "cephalometry"


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _packs():
    registry = _read(SCHEMAS / "cephalo_vnext_lot06_analysis_pack_registry_v1.json")
    return {pack["analysis_id"]: pack for pack in registry["analysis_packs"]}


def _contracts():
    data = _read(SCHEMAS / "cephalo_vnext_lot06_executable_measurement_contract_v1.json")
    return {row["measurement_id"]: row for row in data["measurements"]}


def _mcnamara_rows():
    profile = _read(DATA / "clinical_reference_profiles_v1.json")
    assert profile["status"] == "WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL"
    assert profile["rules"]["normative_classification"] is False
    assert profile["rules"]["candidate_alias_projection_forbidden"] is True
    assert profile["profiles"]["mcnamara"]["protocol_profile_id"] == "MCNAMARA_1984_SINGLE_FILM_V1"
    return profile["profiles"]["mcnamara"]["rows"]


def _ricketts1981_ids():
    text = (ROOT / "docs" / "audits" / "CEPHALO_ANALYSIS_MEASUREMENT_PROFILES.md").read_text(
        encoding="utf-8"
    )
    heading = "## `RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1` — Profil : 11 facteurs"
    pa_heading = "## `RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1` — PA/frontale : 12 facteurs"
    # Avoid treating the optional upper E-line as a core 1981 factor.
    lateral = text.split(heading, 1)[1].split(pa_heading, 1)[0]
    frontal = text.split(pa_heading, 1)[1].split("\n# COM", 1)[0]
    pattern = r"^\|\s*\d+\s*\|\s*`(M_[A-Z0-9_]+)`\s*\|"
    return re.findall(pattern, lateral, re.M), re.findall(pattern, frontal, re.M)


def test_mcnamara_1984_has_thirteen_independent_core_rows_and_eight_executable():
    rows = _mcnamara_rows()
    ids = [row["measurement_id"] for row in rows]
    assert [row["order"] for row in rows] == list(range(1, 14))
    assert len(ids) == len(set(ids)) == 13
    available = {cid for cid in ids if cid in _contracts()}
    assert len(available) == 8
    pack = _packs()["MCNAMARA_V1"]
    assert set(pack["measurement_ids"]) == available
    assert {"M_SNA_DEG_V1", "M_FH_GOME_DEG_V1"} <= set(pack["measurement_ids"])
    assert pack["composition_state"] == "PROVISIONAL_MEMBERSHIP"
    assert pack["membership_evidence_refs"] == []
    graph = build_analysis_pack_dependency_graph("MCNAMARA_V1")
    assert set(graph["measurement_ids"]) == available
    assert graph["scientific_state"] == "PROVISIONAL_MEMBERSHIP_FAIL_CLOSED"


def test_mcnamara_five_missing_contracts_are_not_silently_replaced_or_promoted():
    ids = {row["measurement_id"] for row in _mcnamara_rows()}
    missing = ids - set(_contracts())
    assert missing == {
        "M_FACIAL_AXIS_MCNAMARA_DEG_V1",
        "M_U1_A_VERTICAL_MM_V1",
        "M_L1_FACIAL_SURFACE_APOG_MM_V1",
        "M_UPPER_PHARYNX_MM_V1",
        "M_LOWER_PHARYNX_MM_V1",
    }
    assert missing.isdisjoint(_packs()["MCNAMARA_V1"]["measurement_ids"])
    assert "M_FACIAL_AXIS_RICKETTS_DEG_V1" not in _packs()["MCNAMARA_V1"]["measurement_ids"]
    assert "M_B_NPERP_MM_V1" not in _packs()["MCNAMARA_V1"]["measurement_ids"]


def test_mcnamara_exact_fh_and_calibration_requirements_are_executable_gates():
    contracts = _contracts()
    fh = contracts["M_FH_GOME_DEG_V1"]
    assert fh["required_landmarks"] == ["Po_anatomic", "Or", "Go", "Me"]
    assert fh["requires_calibration"] is False
    linear_ids = {
        "M_A_NPERP_MM_V1", "M_POG_NPERP_MM_V1",
        "M_CO_A_MM_V1", "M_CO_GN_ANATOMIC_MM_V1", "M_ANS_ME_MM_V1",
    }
    assert linear_ids <= set(_packs()["MCNAMARA_V1"]["measurement_ids"])
    assert all(contracts[cid]["requires_calibration"] is True for cid in linear_ids)
    assert "Gn_anatomic" in contracts["M_CO_GN_ANATOMIC_MM_V1"]["required_landmarks"]
    assert "Co_anatomic" in contracts["M_CO_A_MM_V1"]["required_landmarks"]


def test_ricketts_1981_lateral_and_frontal_cardinality_remain_separate():
    lateral, frontal = _ricketts1981_ids()
    assert len(lateral) == len(set(lateral)) == 11
    assert len(frontal) == len(set(frontal)) == 12
    assert all(cid.startswith("M_PA_") for cid in frontal)
    assert not set(lateral) & set(frontal)
    assert "M_LI_EPLANE_MM_V1" in lateral
    assert "M_LS_EPLANE_MM_V1" not in lateral


def test_ricketts_1981_pack_adds_only_proven_lateral_executable_measurements():
    lateral, frontal = _ricketts1981_ids()
    pack = _packs()["RICKETTS_V1"]
    assert len(pack["measurement_ids"]) == 7
    assert {"M_L1_EDGE_APOG_MM_V1", "M_INTERINCISAL_DEG_V1"} <= set(pack["measurement_ids"])
    assert set(pack["measurement_ids"]).isdisjoint(frontal)
    assert "M_LS_EPLANE_MM_V1" in pack["measurement_ids"]  # source-documented optional extension
    assert "M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1" in pack["measurement_ids"]
    assert pack["composition_state"] == "PROVISIONAL_MEMBERSHIP"
    assert pack["membership_evidence_refs"] == []
    graph = build_analysis_pack_dependency_graph("RICKETTS_V1")
    assert graph["scientific_state"] == "PROVISIONAL_MEMBERSHIP_FAIL_CLOSED"
    assert "L1_incisal" in graph["landmark_ids"]


def test_ricketts_1981_pa_is_never_fabricated_from_a_lateral_contract():
    _, frontal = _ricketts1981_ids()
    pack = _packs()["RICKETTS_V1"]
    assert not set(frontal) & set(_contracts())
    assert not set(frontal) & set(pack["measurement_ids"])
    assert "M_FH_SUBGO_M_DEG_V1" not in pack["measurement_ids"]
    assert "M_FH_GOME_DEG_V1" not in pack["measurement_ids"]


def test_ricketts_1997_and_2009_have_distinct_immutable_profile_versions():
    atlas = _read(DATA / "ricketts_atlas2009_complete33_protocol_profile_v1.json")
    gregoret = _read(DATA / "ricketts_gregoret13_protocol_profile_v1.json")
    assert atlas["protocol_id"] == "RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1"
    assert gregoret["protocol_id"] == "RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1"
    for profile, count in ((atlas, 33), (gregoret, 13)):
        ids = [x["measurement_id"] for x in profile["measurements"]]
        assert len(ids) == len(set(ids)) == count
        assert [x["order"] for x in profile["measurements"]] == list(range(1, count + 1))
        assert profile["normative_state"]["universal_classification"] is False
        assert profile["normative_state"]["vert_enabled"] is False
    assert atlas["protocol_id"] != gregoret["protocol_id"]
    assert set(_packs()["RICKETTS_V1"]["measurement_ids"]) != set(
        row["measurement_id"] for row in atlas["measurements"]
    )


def test_ricketts_atlas_and_gregoret_source_projections_fail_closed_when_missing():
    atl = project_ricketts_atlas2009_protocol([])
    gr = project_ricketts_gregoret13_protocol([])
    assert len(atl["rows"]) == 33
    assert len(gr["rows"]) == 13
    for profile in (atl, gr):
        assert profile["classification_authority"] is False
        assert all(row["value"] is None for row in profile["rows"])
        assert all(row["availability_status"] == "NOT_COMPUTABLE" for row in profile["rows"])


def test_mcnamara_display_reference_is_not_executable_or_clinically_authoritative():
    profile = project_mcnamara_reference_protocol([])
    assert profile["protocol_profile_id"] == "MCNAMARA_1984_SINGLE_FILM_V1"
    assert profile["source_lock_gate"] == "HISTORICAL_WORKING_REFERENCE_ONLY"
    assert profile["classification_authority"] is False
    assert len(profile["rows"]) == 13
    assert all(row["value"] is None and row["availability_status"] == "NOT_COMPUTABLE"
               for row in profile["rows"])


def test_all_seven_lot06_packs_remain_non_authoritative():
    packs = _packs()
    assert len(packs) == 7
    for item in packs.values():
        assert item["composition_state"] == "PROVISIONAL_MEMBERSHIP"
        assert item["membership_evidence_refs"] == []
        assert build_analysis_pack_dependency_graph(item["analysis_id"])[
            "scientific_state"
        ] == "PROVISIONAL_MEMBERSHIP_FAIL_CLOSED"
