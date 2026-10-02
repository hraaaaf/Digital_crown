import copy
import json
from pathlib import Path

import pytest

from backend.services.cephalo_dependency_graph import (
    CephaloDependencyGraphError,
    build_analysis_pack_dependency_graph,
    compose_measurement_dependency_graph,
    list_analysis_packs,
    validate_analysis_pack_registry,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (
    ROOT / "docs" / "audits" / "schemas"
    / "cephalo_vnext_lot06_analysis_pack_registry_v1.json"
)


def _registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_lot06_analysis_pack_registry_is_data_driven_and_valid():
    payload = _registry()
    validate_analysis_pack_registry(payload)
    pack_ids = [item["analysis_id"] for item in payload["analysis_packs"]]
    assert len(pack_ids) == len(set(pack_ids))
    assert {item["analysis_id"] for item in list_analysis_packs()} == set(pack_ids)
    assert payload["rules"]["dependencies_must_be_derived_from_executable_measurement_contract"] is True
    assert payload["rules"]["frontend_scientific_dependency_mapping_forbidden"] is True
    assert payload["rules"]["all_is_display_preset_not_scientific_analysis"] is True
    assert payload["rules"]["pack_membership_requires_explicit_source_lock_before_clinical_authority"] is True
    assert payload["rules"]["source_locked_membership_requires_evidence_refs"] is True


def test_lot06_current_pack_membership_is_explicitly_provisional():
    for pack in list_analysis_packs():
        assert pack["composition_state"] == "PROVISIONAL_MEMBERSHIP"
        assert pack["scientific_contract_refs"]
        assert pack["membership_evidence_refs"] == []
        graph = build_analysis_pack_dependency_graph(pack["analysis_id"])
        assert graph["scientific_state"] == "PROVISIONAL_MEMBERSHIP_FAIL_CLOSED"


def test_lot06_dependency_graph_derives_sna_exactly_from_executable_contract():
    graph = compose_measurement_dependency_graph(["M_SNA_DEG_V1"])
    assert graph["measurement_ids"] == ["M_SNA_DEG_V1"]
    assert graph["landmark_ids"] == ["A", "N", "S"]
    assert graph["construction_ids"] == []
    assert {(edge["to_type"], edge["to_id"]) for edge in graph["edges"]} == {
        ("landmark", "S"),
        ("landmark", "N"),
        ("landmark", "A"),
    }


def test_lot06_dependency_graph_deduplicates_shared_landmarks_and_constructions():
    graph = compose_measurement_dependency_graph(
        ["M_A_NPERP_MM_V1", "M_B_NPERP_MM_V1", "M_AB_PRIME_FH_MM_V1"]
    )
    assert graph["landmark_ids"] == ["A", "B", "N", "Or", "Po_anatomic"]
    assert set(graph["construction_ids"]) == {
        "FH_PO_OR_V1",
        "NASION_VERTICAL_FH_V1",
        "CRANIOM_AB_PRIME_V1",
    }


def test_lot06_analysis_pack_graph_keeps_ricketts_fail_closed():
    graph = build_analysis_pack_dependency_graph("RICKETTS_V1")
    assert graph["measurement_ids"] == []
    assert graph["scientific_state"] == "PROVISIONAL_MEMBERSHIP_FAIL_CLOSED"
    assert "M_FACIAL_ANGLE_NPOG_FH_DEG_V1" in graph["blocked_measurement_ids"]
    assert "M_LS_EPLANE_MM_V1" in graph["blocked_measurement_ids"]


def test_lot06_com_pack_uses_canonical_contract_not_frontend_mapping():
    graph = build_analysis_pack_dependency_graph("COM_V1")
    assert "M_A_NPERP_MM_V1" in graph["measurement_ids"]
    assert "NASION_VERTICAL_FH_V1" in graph["construction_ids"]
    assert "Po_anatomic" in graph["landmark_ids"]
    assert all("points" not in item for item in graph["measurements"])
    assert all("lines" not in item for item in graph["measurements"])


def test_lot06_dependency_graph_fails_closed_for_non_promoted_or_unknown_measurement():
    with pytest.raises(CephaloDependencyGraphError):
        compose_measurement_dependency_graph(["M_LS_EPLANE_MM_V1"])
    with pytest.raises(CephaloDependencyGraphError):
        compose_measurement_dependency_graph(["M_NOT_REAL_V1"])


def test_lot06_registry_rejects_missing_pack_scientific_state_or_contract_refs():
    payload = _registry()
    del payload["analysis_packs"][0]["composition_state"]
    with pytest.raises(CephaloDependencyGraphError):
        validate_analysis_pack_registry(payload)

    payload = _registry()
    payload["analysis_packs"][0]["scientific_contract_refs"] = []
    with pytest.raises(CephaloDependencyGraphError):
        validate_analysis_pack_registry(payload)


def test_lot06_registry_rejects_unknown_contract_ref_and_unproven_source_lock():
    payload = _registry()
    payload["analysis_packs"][0]["scientific_contract_refs"] = ["NOT_A_REAL_CONTRACT"]
    with pytest.raises(CephaloDependencyGraphError):
        validate_analysis_pack_registry(payload)

    payload = _registry()
    payload["analysis_packs"][0]["composition_state"] = "SOURCE_LOCKED_MEMBERSHIP"
    payload["analysis_packs"][0]["membership_evidence_refs"] = []
    with pytest.raises(CephaloDependencyGraphError):
        validate_analysis_pack_registry(payload)


def test_lot06_registry_accepts_source_lock_only_with_explicit_membership_evidence():
    payload = _registry()
    payload["analysis_packs"][0]["composition_state"] = "SOURCE_LOCKED_MEMBERSHIP"
    payload["analysis_packs"][0]["membership_evidence_refs"] = [
        "docs/audits/CEPHALO_VNEXT_LOT01_SCIENTIFIC_CONTRACT.md#steiner-membership-evidence"
    ]
    validate_analysis_pack_registry(payload)


def test_lot06_registry_rejects_duplicate_display_preset_identity():
    payload = _registry()
    payload["display_presets"].append(copy.deepcopy(payload["display_presets"][0]))
    with pytest.raises(CephaloDependencyGraphError):
        validate_analysis_pack_registry(payload)


def test_lot06_registry_architecture_scales_beyond_400_packs_without_code_branching():
    payload = _registry()
    template = {
        "display_name": "Synthetic architecture-only pack",
        "version": 1,
        "composition_state": "PROVISIONAL_MEMBERSHIP",
        "scientific_contract_refs": ["STEINER_1953_CORE_V1"],
        "membership_evidence_refs": [],
        "measurement_ids": ["M_SNA_DEG_V1"],
        "blocked_measurement_ids": [],
    }
    payload["analysis_packs"] = [
        {"analysis_id": f"SYNTHETIC_{index:03d}_V1", **copy.deepcopy(template)}
        for index in range(401)
    ]
    payload["display_presets"] = []
    validate_analysis_pack_registry(payload)
