"""R23-G8 W1: source parity and fail-closed checks for exactly 4 signed factors."""
import json

import pytest

from scripts import cephalo_r23g8_w1_orientation_coverage as audit


def test_source_coverage_is_exact_8_3_4_18_and_does_not_promote_medical_measurement():
    ledger = audit.build_w1_ledger()
    assert ledger["counts"] == {
        "LOT06_PUBLISHED_SOURCE_DEPENDENCIES": 8,
        "G7_ATLAS_SOURCE_PREVIEW_ONLY": 3,
        "W1_ORIENTATION_OBLIGATION_PREVIEW_ONLY": 4,
        "HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES": 18,
    }
    assert len(ledger["rows"]) == 33
    assert ledger["clinical_release"] is False
    assert ledger["orientation_clinical_evidence_verified"] is False
    assert all(not row["active_runtime_focus_authorized"] and
               not row["clinical_value_authorized_by_this_ledger"]
               for row in ledger["rows"])


def test_exact_w1_landmark_construction_and_image_orientation_gates():
    ledger = audit.build_w1_ledger()
    rows = {r["order"]: r for r in ledger["rows"]}
    assert {i for i, r in rows.items() if r["source_dependency_status"] ==
            "W1_ORIENTATION_OBLIGATION_PREVIEW_ONLY"} == {4, 14, 18, 24}
    for i, (mid, _, ids, _, _, _) in audit.EXPECTED.items():
        assert rows[i]["measurement_id"] == mid
        assert tuple(rows[i]["declared_landmarks"]) == ids
        assert rows[i]["atlas_availability_gate"] == "VERSIONED_IMAGE_ORIENTATION_EVIDENCE_REQUIRED"


@pytest.mark.parametrize("order", [4, 14, 18, 24])
def test_wrong_image_requirement_or_alias_fails_closed(tmp_path, monkeypatch, order):
    c = json.loads(audit.W1_PATH.read_text(encoding="utf-8"))
    row = next(r for r in c["measurements"] if r["source_order"] == order)
    row["requires_same_image_orientation"] = False
    path = tmp_path / "invalid_orientation.json"
    path.write_text(json.dumps(c), encoding="utf-8")
    monkeypatch.setattr(audit, "W1_PATH", path)
    with pytest.raises(ValueError, match="orientation identity drift"):
        audit.build_w1_ledger()


def test_wrong_orientation_source_authority_fails_closed(tmp_path, monkeypatch):
    c = json.loads(audit.W1_PATH.read_text(encoding="utf-8"))
    c["authority"] = "ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1"
    path = tmp_path / "bad_authority.json"
    path.write_text(json.dumps(c), encoding="utf-8")
    monkeypatch.setattr(audit, "W1_PATH", path)
    with pytest.raises(ValueError, match="authority / protocol"):
        audit.build_w1_ledger()


def test_duplicate_signed_measurement_fails_closed(tmp_path, monkeypatch):
    c = json.loads(audit.W1_PATH.read_text(encoding="utf-8"))
    c["measurements"].append(c["measurements"][0].copy())
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(c), encoding="utf-8")
    monkeypatch.setattr(audit, "W1_PATH", path)
    with pytest.raises(ValueError, match="four source"):
        audit.build_w1_ledger()


def test_stale_source_backend_identity_or_mirror_gate_fails_closed(tmp_path, monkeypatch):
    original = audit.BACKEND_PATH.read_text(encoding="utf-8")
    broken = original.replace(
        "image_orientation.source_image_ref != source_ref",
        "image_orientation.source_image_ref == source_ref",
    )
    path = tmp_path / "broken_method.py"
    path.write_text(broken, encoding="utf-8")
    monkeypatch.setattr(audit, "BACKEND_PATH", path)
    with pytest.raises(ValueError, match="fail-closed source gate"):
        audit.build_w1_ledger()


def test_missing_signed_orientation_backend_method_is_detected(tmp_path, monkeypatch):
    original = audit.BACKEND_PATH.read_text(encoding="utf-8")
    broken = original.replace(
        'method="RICKETTS_OVERBITE_FOP_CANONICAL_MM_V2"',
        'method="UNVERIFIED_OVERBITE"',
    )
    path = tmp_path / "method_drift.py"
    path.write_text(broken, encoding="utf-8")
    monkeypatch.setattr(audit, "BACKEND_PATH", path)
    with pytest.raises(ValueError, match="method/canonical"):
        audit.build_w1_ledger()
