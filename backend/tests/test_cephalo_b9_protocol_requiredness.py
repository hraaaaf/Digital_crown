"""B9 source-lock contracts: no FACAD requiredness may be guessed."""
import json

import pytest

from backend.services import cephalo_protocol_requiredness as requiredness

STEINER = "STEINER_STATIC_PROTOCOL_PROFILE_V1"
TWEED = "TWEED_MERRIFIELD_DC_PROTOCOL_PROFILE_V1"
BASE = "STEINER_1953_BASE"
EXT = "STEINER_1959_EXTENSION"
TRIANGLE = "TWEED_1954_TRIANGLE_DC_PO_OR_V1"


def _available(cid):
    return {
        "canonical_measurement_id": cid,
        "availability_status": "AVAILABLE",
        "value": 1.0,
        "measurement_refs": [f"measurement:{cid}"],
        "value_authority_method_id": "test:source-locked-method",
    }


def test_explicit_steiner_sections_do_not_inherit_one_another():
    base = requiredness.read_required_measurement_contract(STEINER, BASE)
    extension = requiredness.read_required_measurement_contract(STEINER, EXT)
    assert base["source_locked"] is True
    assert base["protocol_final_gate_satisfied"] is True
    assert len(base["required_measurement_ids"]) == 11
    assert len(extension["required_measurement_ids"]) == 4
    assert set(base["required_measurement_ids"]).isdisjoint(extension["required_measurement_ids"])
    assert len(base["source_sha256"]) == 64


def test_tweed_open_final_gate_remains_blocked_even_with_complete_inputs():
    contract = requiredness.read_required_measurement_contract(TWEED, TRIANGLE)
    assert len(contract["required_measurement_ids"]) == 3
    assert contract["source_locked"] is True
    assert contract["protocol_final_gate_satisfied"] is False
    rows = [_available(cid) for cid in contract["required_measurement_ids"]]
    result = requiredness.evaluate_required_measurements(TWEED, TRIANGLE, rows)
    assert not result["required_measurements_satisfied"]
    assert "protocol_final_gate_not_satisfied" in result["blocking_gates"]


@pytest.mark.parametrize("profile,section", [
    ("BERGEN_SHORT_FACAD_V1", BASE),
    ("FACAD_MINI_V1", BASE),
    (STEINER, None),
    (STEINER, "DOES_NOT_EXIST"),
    (None, BASE),
])
def test_missing_or_uncertified_contract_cannot_pass(profile, section):
    result = requiredness.evaluate_required_measurements(profile, section, [])
    assert result["required_measurement_ids"] == []
    assert result["required_measurements_satisfied"] is False
    assert "protocol_requiredness_contract_unavailable" in result["blocking_gates"]


def test_missing_required_row_fails_but_invalid_unrelated_row_is_not_required():
    ids = requiredness.read_required_measurement_contract(STEINER, BASE)["required_measurement_ids"]
    inputs = [_available(cid) for cid in ids[:-1]]
    inputs.append({"canonical_measurement_id": "OTHER", "availability_status": "INVALID"})
    result = requiredness.evaluate_required_measurements(STEINER, BASE, inputs)
    assert result["blocking_gates"] == [f"required_measurement_missing:{ids[-1]}"]


@pytest.mark.parametrize("replacement", [
    {"availability_status": "NOT_COMPUTABLE", "value": None},
    {"availability_status": "INVALID"},
    {"value": None},
    {"value": float("nan")},
    {"value": float("inf")},
    {"value": True},
    {"measurement_refs": []},
    {"value_authority_method_id": None},
])
def test_required_invalid_measurement_never_passes(replacement):
    ids = requiredness.read_required_measurement_contract(STEINER, BASE)["required_measurement_ids"]
    inputs = [_available(cid) for cid in ids]
    inputs[0].update(replacement)
    result = requiredness.evaluate_required_measurements(STEINER, BASE, inputs)
    assert result["required_measurements_satisfied"] is False
    assert f"required_measurement_invalid:{ids[0]}" in result["blocking_gates"]


def test_duplicate_required_identity_fails_closed():
    ids = requiredness.read_required_measurement_contract(STEINER, BASE)["required_measurement_ids"]
    inputs = [_available(cid) for cid in ids]
    result = requiredness.evaluate_required_measurements(STEINER, BASE, inputs + [inputs[0]])
    assert not result["required_measurements_satisfied"]
    assert f"required_measurement_duplicate:{ids[0]}" in result["blocking_gates"]


def test_complete_synthetic_section_does_not_confer_clinical_pdf_authority():
    ids = requiredness.read_required_measurement_contract(STEINER, BASE)["required_measurement_ids"]
    result = requiredness.evaluate_required_measurements(STEINER, BASE, [_available(cid) for cid in ids])
    assert result["required_measurements_satisfied"] is True
    assert "document_state" not in result
    assert "clinical_validation_available" not in result


def test_tampered_source_lock_cannot_be_trusted(tmp_path, monkeypatch):
    filename = tmp_path / "profile.json"
    filename.write_text(json.dumps({
        "protocol_profile_id": STEINER,
        "status": "UNREVIEWED",
        "pre_code_gate": {"status": "SATISFIED", "scope": STEINER},
        "final_gate": {"status": "SATISFIED"},
        "layers": {BASE: {"required_measurement_ids": ["M_SNA_DEG_V1"]}},
    }))
    monkeypatch.setitem(requiredness._PROFILE_SOURCES, STEINER, (filename, "layers"))
    result = requiredness.evaluate_required_measurements(STEINER, BASE, [_available("M_SNA_DEG_V1")])
    assert not result["required_measurements_satisfied"]
    assert "protocol_requiredness_contract_unavailable" in result["blocking_gates"]
