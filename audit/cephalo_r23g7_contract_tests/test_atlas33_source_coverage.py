"""R23-G7 fail-closed Atlas source coverage contracts (no patient data)."""
import json
from pathlib import Path

import pytest

from scripts import cephalo_r23g7_source_coverage as ledger


def test_atlas33_exact_published_coverage_never_promotes_values_or_focus():
    result = ledger.build_ledger()
    assert result["protocol_id"] == ledger.PROTOCOL_ID
    assert result["clinical_release"] is False
    assert result["classification_authority"] is False
    assert len(result["rows"]) == 33
    assert result["counts"] == {
        "LOT06_PUBLISHED_SOURCE_DEPENDENCIES": 8,
        "G7_ATLAS_SOURCE_PREVIEW_ONLY": 3,
        "HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES": 22,
    }
    assert all(row["active_runtime_focus_authorized"] is False for row in result["rows"])
    assert all(row["clinical_value_authorized_by_this_ledger"] is False for row in result["rows"])


def test_three_exact_source_dependencies_are_non_aliasing_and_source_locked():
    result = ledger.build_ledger()
    new = {row["measurement_id"]: row for row in result["rows"]
           if row["source_dependency_status"] == "G7_ATLAS_SOURCE_PREVIEW_ONLY"}
    assert set(new) == set(ledger.EXPECTED_NEW)
    for mid, exact in ledger.EXPECTED_NEW.items():
        assert tuple(new[mid]["declared_landmarks"]) == exact
    assert "Pog_hard" in new["M_RICKETTS_U1_APOG_PROTRUSION_MM_V1"]["declared_landmarks"]
    assert "Po_anatomic" in new["M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1"]["declared_landmarks"]


def test_conditional_methods_remain_holds_not_published_focus_contracts():
    result = ledger.build_ledger()
    hold = [row for row in result["rows"]
            if row["source_dependency_status"] == "HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES"]
    assert len(hold) == 22
    assert all(row["atlas_contract_state"] == "CONDITIONAL_EXECUTABLE" for row in hold)
    assert all(row["declared_landmarks"] is None for row in hold)
    assert all(row["active_runtime_focus_authorized"] is False for row in hold)


def test_duplicate_or_non_source_g7_contract_fails_closed(tmp_path, monkeypatch):
    original = json.loads(ledger.G7_PATH.read_text(encoding="utf-8"))
    original["measurements"].append(dict(original["measurements"][0]))
    corrupted = tmp_path / "duplicate.json"
    corrupted.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(ledger, "G7_PATH", corrupted)
    with pytest.raises(ValueError, match="three-row"):
        ledger.build_ledger()


def test_anatomical_alias_or_backend_mismatch_fails_closed(tmp_path, monkeypatch):
    original = json.loads(ledger.G7_PATH.read_text(encoding="utf-8"))
    original["measurements"][0]["required_landmarks"][2] = "Pog"
    corrupted = tmp_path / "alias.json"
    corrupted.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(ledger, "G7_PATH", corrupted)
    with pytest.raises(ValueError, match="anatomical identities"):
        ledger.build_ledger()


def test_atlas_composition_drift_is_a_blocker(tmp_path, monkeypatch):
    original = json.loads(ledger.ATLAS_PATH.read_text(encoding="utf-8"))
    original["measurements"].pop()
    corrupted = tmp_path / "atlas.json"
    corrupted.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(ledger, "ATLAS_PATH", corrupted)
    with pytest.raises(ValueError, match="exact 33"):
        ledger.build_ledger()
