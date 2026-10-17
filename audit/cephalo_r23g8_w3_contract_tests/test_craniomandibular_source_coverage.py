"""W3 final Atlas33 source descriptions, not clinical release evidence."""
import json
import pytest
from scripts import cephalo_r23g8_w3_cranio_coverage as audit


def test_exact_atlas33_full_description_coverage_never_unlocks_patient_values():
    data=audit.build_w3_ledger()
    assert len(data["rows"]) == 33
    assert data["counts"] == {
        "LOT06_PUBLISHED_SOURCE_DEPENDENCIES": 8,
        "G7_ATLAS_SOURCE_PREVIEW_ONLY": 3,
        "W1_ORIENTATION_OBLIGATION_PREVIEW_ONLY": 4,
        "W2_DENTAL_MANUAL_OBLIGATION_PREVIEW_ONLY": 7,
        "W3_CRANIOMANDIBULAR_OBLIGATION_PREVIEW_ONLY": 11,
        "HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES": 0,
    }
    assert data["clinical_release"] is False
    assert data["clinical_measurements_newly_authorized"] == 0
    assert data["patient_source_goldset_verified"] is False
    assert data["independent_clinical_review"] is False
    assert all(not x["active_runtime_focus_authorized"] and
               not x["clinical_value_authorized_by_this_ledger"]
               for x in data["rows"])


def test_factor29_is_total_facial_height_not_a_second_posterior_facial_height():
    data=audit.build_w3_ledger()
    factors={r["order"]:r for r in data["rows"]}
    assert factors[28]["measurement_id"] == "M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1"
    assert factors[29]["measurement_id"] == "M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1"


@pytest.mark.parametrize("factor",[8,21,23,25,27,28,29,30,31,32,33])
def test_exact_canonical_point_aliases_rejected(tmp_path,monkeypatch,factor):
    source=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    row=next(x for x in source["measurements"] if x["source_order"]==factor)
    row["required_landmarks"][0]="GENERIC_UNVERIFIED_CRANIAL_POINT"
    file=tmp_path/"alias.json"
    file.write_text(json.dumps(source),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",file)
    with pytest.raises(ValueError,match="canonical direct/manual/scale"):
        audit.build_w3_ledger()


def test_cc_pt_and_ptv_pr_are_not_interchangeable(tmp_path,monkeypatch):
    source=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    row=next(x for x in source["measurements"] if x["source_order"]==27)
    row["construction_transitive_landmarks"][audit.CC][2]="PR_Ricketts_PTV"
    file=tmp_path/"wrong_pt.json"
    file.write_text(json.dumps(source),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",file)
    with pytest.raises(ValueError,match="false transitive"):
        audit.build_w3_ledger()


def test_cf_ptv_chain_cannot_be_replaced_by_generic_cf(tmp_path,monkeypatch):
    source=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    row=next(x for x in source["measurements"] if x["source_order"]==23)
    row["construction_dependency_chain"][audit.CF]=[audit.CF]
    file=tmp_path/"wrong_cf.json"
    file.write_text(json.dumps(source),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",file)
    with pytest.raises(ValueError,match="false transitive"):
        audit.build_w3_ledger()


def test_clinical_authority_claim_fails_closed(tmp_path,monkeypatch):
    source=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    source["clinical_release"]=True
    file=tmp_path/"false_go.json"
    file.write_text(json.dumps(source),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",file)
    with pytest.raises(ValueError,match="clinical authority"):
        audit.build_w3_ledger()


def test_duplicate_cranial_source_contract_is_rejected(tmp_path,monkeypatch):
    source=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    source["measurements"].append(source["measurements"][0].copy())
    file=tmp_path/"dup.json"
    file.write_text(json.dumps(source),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",file)
    with pytest.raises(ValueError,match="exactly 11"):
        audit.build_w3_ledger()


def test_backend_method_drift_is_blocker(tmp_path,monkeypatch):
    original=audit.BACKEND.read_text(encoding="utf-8")
    modified=original.replace('method="RICKETTS_TOTAL_FACIAL_HEIGHT_CANONICAL_DEG_V2"',
                              'method="RICKETTS_TOTAL_FACIAL_HEIGHT_UNVERIFIED"')
    file=tmp_path/"changed_backend.py"
    file.write_text(modified,encoding="utf-8")
    monkeypatch.setattr(audit,"BACKEND",file)
    with pytest.raises(ValueError,match="canonical backend method"):
        audit.build_w3_ledger()


def test_indirect_manual_source_cannot_disappear(tmp_path,monkeypatch):
    source=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    row=next(x for x in source["measurements"] if x["source_order"]==27)
    row["construction_manual_landmarks"][audit.CC]=[]
    file=tmp_path/"false_automatic_pt.json"
    file.write_text(json.dumps(source),encoding="utf-8")
    monkeypatch.setattr(audit,"SOURCE",file)
    with pytest.raises(ValueError,match="transitive manual"):
        audit.build_w3_ledger()
