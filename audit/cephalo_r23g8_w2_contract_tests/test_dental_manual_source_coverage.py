"""W2 dental/manual source contract refuses misleading dependencies and Focus."""
import json

import pytest

from scripts import cephalo_r23g8_w2_dental_coverage as audit


def test_complete_atlas33_only_source_descriptions():
    d=audit.build_w2_ledger()
    assert len(d["rows"]) == 33
    assert d["counts"] == {
        "LOT06_PUBLISHED_SOURCE_DEPENDENCIES": 8,
        "G7_ATLAS_SOURCE_PREVIEW_ONLY": 3,
        "W1_ORIENTATION_OBLIGATION_PREVIEW_ONLY": 4,
        "W2_DENTAL_MANUAL_OBLIGATION_PREVIEW_ONLY": 7,
        "HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES": 11,
    }
    assert d["clinical_release"] is False
    assert d["manual_patient_evidence_verified"] is False
    assert all(not row["active_runtime_focus_authorized"] and
               not row["clinical_value_authorized_by_this_ledger"]
               for row in d["rows"])


def test_exact_manual_and_dental_source_identities():
    data=audit.build_w2_ledger()
    by_order={row["order"]:row for row in data["rows"]}
    assert {order for order,row in by_order.items()
            if row["source_dependency_status"]=="W2_DENTAL_MANUAL_OBLIGATION_PREVIEW_ONLY"} == set(audit.EXPECTED)
    for order,spec in audit.EXPECTED.items():
        assert tuple(by_order[order]["declared_landmarks"]) == spec[2]
        assert by_order[order]["atlas_contract_state"] == "CONDITIONAL_EXECUTABLE"


@pytest.mark.parametrize("order", [1,2,3,5,9,15,17])
def test_alias_or_wrong_calibration_fails_closed(tmp_path,monkeypatch,order):
    data=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    row=next(row for row in data["measurements"] if row["source_order"]==order)
    row["required_landmarks"][0] = "GENERIC_ALIAS"
    target=tmp_path/"alias.json"
    target.write_text(json.dumps(data),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",target)
    with pytest.raises(ValueError,match="manual/dental identities"):
        audit.build_w2_ledger()


def test_duplicate_w2_row_never_expands_33_atlas_factors(tmp_path,monkeypatch):
    data=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    data["measurements"].append(data["measurements"][0].copy())
    target=tmp_path/"duplicate.json"
    target.write_text(json.dumps(data),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",target)
    with pytest.raises(ValueError,match="exact seven"):
        audit.build_w2_ledger()


def test_w2_manual_source_authority_cannot_be_clinical(tmp_path,monkeypatch):
    data=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    data["authority"]="ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1"
    target=tmp_path/"forged_authority.json"
    target.write_text(json.dumps(data),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",target)
    with pytest.raises(ValueError,match="authority"):
        audit.build_w2_ledger()


def test_source_method_change_is_refused(tmp_path,monkeypatch):
    text=audit.BACKEND.read_text(encoding="utf-8").replace(
        'method="RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2"',
        'method="RICKETTS_UNKNOWN_UPPER_LIP"',
    )
    target=tmp_path/"method_drift.py"
    target.write_text(text,encoding="utf-8")
    monkeypatch.setattr(audit,"BACKEND",target)
    with pytest.raises(ValueError,match="method bridge"):
        audit.build_w2_ledger()


def test_generic_fop_upstream_alias_is_forbidden(tmp_path, monkeypatch):
    data=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    row=next(row for row in data["measurements"] if row["source_order"]==3)
    fop=audit.FOP
    row["construction_upstream_landmarks"][fop]=["GENERIC_OCCLUSAL_POINT", "FOP_MOLAR_Ricketts"]
    target=tmp_path/"false_fop.json"
    target.write_text(json.dumps(data),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",target)
    with pytest.raises(ValueError, match="upstream identity"):
        audit.build_w2_ledger()
