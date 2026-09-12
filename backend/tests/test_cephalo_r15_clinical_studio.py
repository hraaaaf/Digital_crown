from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.routers import cephalo_clinical_studio as router
from backend.services import cephalo_r15_clinical_studio as studio
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def _empty_registries(monkeypatch):
    monkeypatch.setattr(
        studio,
        "diagnostic_registry",
        SimpleNamespace(diagnostic_rules={}, finding_rules={}),
    )
    monkeypatch.setattr(
        studio,
        "therapeutic_registry",
        SimpleNamespace(option_rules={}, criterion_rules={}),
    )


def test_r15_projection_fails_closed_when_no_analysis(monkeypatch):
    _empty_registries(monkeypatch)

    snapshot = studio.build_r15_clinical_studio_snapshot(
        patient_id=42,
        analysis_id=None,
        angles_data=None,
    )

    assert snapshot["contract_version"] == "R15_CLINICAL_STUDIO_VIEW_V1"
    assert snapshot["clinical_validation_available"] is False
    assert snapshot["active_runtime_chain_verified"] is False
    assert snapshot["evidence_graph_present"] is False
    assert [stage["stage_id"] for stage in snapshot["stages"]] == ["R11", "R12", "R13", "R14"]
    assert "cephalo_analysis_missing" in snapshot["stages"][0]["blocking_gates"]
    assert "r11_authoritative_snapshot_not_persisted" in snapshot["stages"][0]["blocking_gates"]
    assert "r14_authoritative_snapshot_not_persisted" in snapshot["stages"][3]["blocking_gates"]
    assert all(stage["presentation_state"] == "BLOCKED" for stage in snapshot["stages"])
    assert all(stage["missing_data_refs"] == [] for stage in snapshot["stages"])
    assert all(stage["contradictions"] == [] for stage in snapshot["stages"])
    assert all(stage["contraindications"] == [] for stage in snapshot["stages"])
    assert all(stage["clinician_action"]["available"] is False for stage in snapshot["stages"])
    assert all(stage["clinician_action"]["audit_required"] is True for stage in snapshot["stages"])


def test_r15_projection_preserves_verified_measurement_chain_but_never_promotes_clinical_authority(monkeypatch):
    _empty_registries(monkeypatch)
    monkeypatch.setattr(
        studio,
        "project_runtime_chain_read_path",
        lambda payload, patient_id: {
            "scientific_read_path": {
                "active_chain": "VERIFIED",
                "current_measurement_count": 7,
            }
        },
    )

    snapshot = studio.build_r15_clinical_studio_snapshot(
        patient_id=42,
        analysis_id=99,
        angles_data={EVIDENCE_GRAPH_KEY: {"contract": "typed"}},
    )

    r11 = snapshot["stages"][0]
    assert snapshot["evidence_graph_present"] is True
    assert snapshot["active_runtime_chain_verified"] is True
    assert {item["label"]: item["value"] for item in r11["provenance"]}["Mesures typées actives"] == "7"
    assert "diagnostic_rule_registry_empty" in r11["blocking_gates"]
    assert "r11_authoritative_snapshot_not_persisted" in r11["blocking_gates"]
    assert snapshot["clinical_validation_available"] is False
    assert all(stage["clinician_action"]["available"] is False for stage in snapshot["stages"])


def test_r15_projection_marks_incoherent_typed_chain_as_blocked(monkeypatch):
    _empty_registries(monkeypatch)

    def _raise(*args, **kwargs):
        raise ValueError("malformed typed chain")

    monkeypatch.setattr(studio, "project_runtime_chain_read_path", _raise)
    snapshot = studio.build_r15_clinical_studio_snapshot(
        patient_id=42,
        analysis_id=99,
        angles_data={EVIDENCE_GRAPH_KEY: {"contract": "typed"}},
    )

    assert "active_runtime_chain_incoherent" in snapshot["stages"][0]["blocking_gates"]
    assert snapshot["clinical_validation_available"] is False


def test_r15_router_checks_patient_access_before_any_patient_query(monkeypatch):
    calls = []

    def _deny(patient_id, current_user, db):
        calls.append((patient_id, current_user, db))
        raise HTTPException(status_code=403, detail="Accès refusé")

    class QueryMustNotRun:
        def query(self, *args, **kwargs):
            raise AssertionError("DB query executed before patient access guard")

    monkeypatch.setattr(router, "assert_patient_access", _deny)
    fake_db = QueryMustNotRun()
    fake_user = object()

    with pytest.raises(HTTPException) as exc:
        router.get_cephalo_clinical_studio(123, db=fake_db, current_user=fake_user)

    assert exc.value.status_code == 403
    assert calls == [(123, fake_user, fake_db)]
