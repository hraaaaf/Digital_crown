"""R13 server decision: synthetic-only audit proof, never R14 signature."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend import models
from backend.routers import cephalo_clinical_studio as router
from backend.services import cephalo_r13_option_decision as decisions
from backend.services import cephalo_r13_decision_authority as authority
from backend.services import cephalo_r11_r13_staging as staging
from backend.services import cephalo_r15_clinical_studio as studio
from backend.services.cephalo_r13_therapeutic_safety import (
    validate_r13_therapeutic_options as real_validate,
)
from backend.tests.test_cephalo_r11_r13_staging import (
    fixture as synthetic_case, approve_test_rules,
)
from backend.tests.test_cephalo_r13_therapeutic_safety import (
    _diagnostic_registry, _therapeutic_registry,
)


def _source_locked_test_validators(monkeypatch):
    approve_test_rules(monkeypatch)
    monkeypatch.setattr(
        authority, "project_runtime_chain_read_path",
        lambda data, patient_id: {"scientific_read_path": {"active_chain": "VERIFIED"}},
    )
    def reviewed_synthetic_rules(snapshot):
        return real_validate(
            snapshot, diagnostic_rule_registry=_diagnostic_registry(),
            therapeutic_rule_registry=_therapeutic_registry(),
        )
    monkeypatch.setattr(authority, "validate_r13_therapeutic_options", reviewed_synthetic_rules)
    monkeypatch.setattr(decisions, "validate_r13_therapeutic_options", reviewed_synthetic_rules)


def _prepared(monkeypatch):
    _source_locked_test_validators(monkeypatch)
    engine, body, actor = synthetic_case()
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        stage = staging.stage_clinical_evidence(
            patient_id=1, analysis=analysis, actor=actor, body=body, db=db,
        )
    request = decisions.R13DecisionRequest(
        expected_revision=2, expected_staging_sha256=stage["content_sha256"],
        action="SELECT_OPTION", option_id=body.options[0].option_id,
    )
    return engine, body, actor, request


def test_r13_request_forbids_forged_actor_validation_timestamp_and_final_plan():
    _engine, _body, _actor, req = _prepared_mock_only()
    for name, value in (
        ("clinician_id", "clinician:forged"),
        ("validation_id", "fake"),
        ("clinician_decided_at", "2026-01-01T00:00:00Z"),
        ("r14_status", "CLINICIAN_VALIDATED"),
    ):
        with pytest.raises(ValidationError):
            decisions.R13DecisionRequest.model_validate({**req.model_dump(), name: value})
    with pytest.raises(ValidationError):
        decisions.R13DecisionRequest.model_validate({**req.model_dump(), "action": "SIGN_R14"})


def _prepared_mock_only():
    obj = SimpleNamespace(option_id="option:r13:synthetic")
    req = decisions.R13DecisionRequest(
        expected_revision=2, expected_staging_sha256="a" * 64,
        action="SELECT_OPTION", option_id=obj.option_id,
    )
    return None, None, None, req


def test_selected_option_persisted_and_audit_record_is_not_R14(monkeypatch):
    engine, body, actor, req = _prepared(monkeypatch)
    with Session(engine) as db:
        response = decisions.decide_r13_option(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=req, db=db,
        )
        assert response["action"] == "SELECT_OPTION"
        assert response["clinical_validation_available"] is False
        assert response["r14_status"] == "NOT_VALIDATED"
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        saved = analysis.angles_data[staging.STAGING_KEY]
        assert staging.read_staged_clinical_evidence(
            patient_id=1, analysis=analysis,
        )["state"] == "CURRENT_NON_FINAL"
        assert saved["r13"]["options"][0]["status"] == "CLINICIAN_SELECTED"
        assert len(saved["r13"]["option_validations"]) == 1
        claim = saved["r13"]["option_validations"][0]
        assert claim["target_id"] == body.options[0].option_id
        assert claim["clinician_id"] == "clinician:1"
        assert claim["action"] == "ACCEPT"
        assert db.query(models.AuditLog).count() == 2
        assert db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).first().action == decisions.DECISION_ACTION
        view = studio.build_r15_clinical_studio_snapshot(
            patient_id=1, analysis_id=101, angles_data=analysis.angles_data,
        )
        assert view["clinical_validation_available"] is False
        assert "r14_authoritative_snapshot_not_persisted" in view["blocking_gates"]


def test_replay_and_restaging_same_revision_are_forbidden(monkeypatch):
    engine, body, actor, req = _prepared(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        decisions.decide_r13_option(
            patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
        )
        with pytest.raises(HTTPException) as err:
            decisions.decide_r13_option(
                patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 409
        with pytest.raises(HTTPException) as err:
            staging.stage_clinical_evidence(
                patient_id=1, analysis=analysis, actor=actor, body=body, db=db,
            )
        assert err.value.status_code == 409
        assert db.query(models.AuditLog).count() == 2


def test_unreviewed_production_registries_block_decision(monkeypatch):
    engine, body, actor, req = _prepared(monkeypatch)
    monkeypatch.setattr(authority, "validate_r13_therapeutic_options", real_validate)
    with Session(engine) as db:
        with pytest.raises(HTTPException) as err:
            decisions.decide_r13_option(
                patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
                actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 409
        assert db.query(models.AuditLog).count() == 1


def test_reject_option_is_a_server_audited_action(monkeypatch):
    engine, _body, actor, req = _prepared(monkeypatch)
    rejection = req.model_copy(update={"action": "REJECT_OPTION"})
    with Session(engine) as db:
        decisions.decide_r13_option(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=rejection, db=db,
        )
        saved = db.get(models.CephaloAnalysis, 101).angles_data[staging.STAGING_KEY]
        assert saved["r13"]["options"][0]["status"] == "CLINICIAN_REJECTED"
        assert saved["r13"]["option_validations"][0]["action"] == "REJECT"


def test_wrong_patient_or_non_clinician_rejected(monkeypatch):
    engine, _body, actor, req = _prepared(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        with pytest.raises(HTTPException) as err:
            decisions.decide_r13_option(
                patient_id=2, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 404
        actor.role = models.UserRole.SECRETAIRE
        with pytest.raises(HTTPException) as err:
            decisions.decide_r13_option(
                patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 403


def test_wrong_version_or_missing_stage_audit_rejected(monkeypatch):
    engine, _body, actor, req = _prepared(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        with pytest.raises(HTTPException) as err:
            decisions.decide_r13_option(
                patient_id=1, analysis=analysis, actor=actor,
                request=req.model_copy(update={"expected_revision": 3}), db=db,
            )
        assert err.value.status_code == 409
        db.query(models.AuditLog).delete()
        db.commit()
        with pytest.raises(HTTPException) as err:
            decisions.decide_r13_option(
                patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 409


def test_router_patient_guard_precedes_study_query(monkeypatch):
    monkeypatch.setattr(router, "assert_patient_access",
                        lambda *args: (_ for _ in ()).throw(HTTPException(status_code=403)))
    class NoQueries:
        def query(self, *_): raise AssertionError("patient guard not invoked")
    _engine, _body, _actor, req = _prepared_mock_only()
    with pytest.raises(HTTPException) as err:
        router.post_r13_clinician_option_decision(
            patient_id=77, analysis_id=8, body=req,
            db=NoQueries(), current_user=object(),
        )
    assert err.value.status_code == 403
