"""Phase 1 membership contract tests. No patient values or clinical authority."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_v1_only_com_and_steiner_1953_with_explicit_clinical_hold():
    v1 = _read("docs/audits/schemas/cephalo_v1_phase1_protocol_scope_v1.json")
    assert v1["selected_protocol_count"] == 2
    assert [p["id"] for p in v1["selected_protocols"]] == ["COM", "STEINER"]
    assert all(p["automatic_coverage"] == "NOT_YET_CERTIFIED" for p in v1["selected_protocols"])
    assert v1["clinical_authority"] is False
    assert v1["diagnosis_authority"] is False
    assert v1["normative_classification_authority"] is False
    assert v1["rules"]["facad_alias_forbidden"] is True


def test_com_canonical_8_not_silently_promoted_from_legacy_10():
    v1 = _read("docs/audits/schemas/cephalo_v1_phase1_protocol_scope_v1.json")
    packs = _read("docs/audits/schemas/cephalo_vnext_lot06_analysis_pack_registry_v1.json")
    com_pack = next(p for p in packs["analysis_packs"] if p["analysis_id"] == "COM_V1")
    history = _read("backend/data/cephalometry/clinical_reference_profiles_v1.json")["profiles"]["com"]
    com = v1["selected_protocols"][0]
    assert com["measurement_ids"] == com_pack["measurement_ids"]
    assert len(com["measurement_ids"]) == 8
    assert history["protocol_profile_id"] == com["historical_profile"]
    assert len(history["rows"]) == com["historical_row_count"] == 10
    assert com["historical_rows_interchangeable"] is False
    assert com_pack["composition_state"] == "PROVISIONAL_MEMBERSHIP"
    assert com_pack["membership_evidence_refs"] == []


def test_steiner_1953_exact_11_not_1959_four():
    v1 = _read("docs/audits/schemas/cephalo_v1_phase1_protocol_scope_v1.json")
    steiner = v1["selected_protocols"][1]
    source = _read("backend/data/cephalometry/steiner_protocol_profile_v1.json")
    pack = next(p for p in _read("docs/audits/schemas/cephalo_vnext_lot06_analysis_pack_registry_v1.json")["analysis_packs"] if p["analysis_id"] == "STEINER_V1")
    core = source["layers"]["STEINER_1953_BASE"]["required_measurement_ids"]
    extension = source["layers"]["STEINER_1959_EXTENSION"]["required_measurement_ids"]
    assert len(core) == 11 and len(extension) == 4
    assert steiner["measurement_ids"] == core
    assert not set(core) & set(extension)
    assert set(core) <= set(pack["measurement_ids"])
    assert steiner["excluded_extension"] == "STEINER_1959_EXTENSION"
    assert pack["composition_state"] == "PROVISIONAL_MEMBERSHIP"
    assert pack["membership_evidence_refs"] == []
