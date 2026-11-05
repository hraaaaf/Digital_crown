"""R11/R12 authenticated source review gates, with synthetic science only."""
import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend import models
from backend.routers import cephalo_clinical_studio as router
from backend.services import cephalo_r11_r12_attestation as attest
from backend.services import cephalo_r11_r13_staging as staging
from backend.services import cephalo_r13_decision_authority as authority
from backend.services import cephalo_r13_option_decision as decision
from backend.services.cephalo_r13_therapeutic_safety import validate_r13_therapeutic_options as production_validate
from backend.tests.test_cephalo_r11_r13_staging import fixture, approve_test_rules
from backend.tests.test_cephalo_r13_option_decision import _source_locked_test_validators, _complete_r11_reviews


def prepared(monkeypatch):
    _source_locked_test_validators(monkeypatch)
    engine, body, actor = fixture()
    with Session(engine) as db:
        result = staging.stage_clinical_evidence(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, body=body, db=db,
        )
    with Session(engine) as db:
        _complete_r11_reviews(
            db=db, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, stage_sha=result["content_sha256"],
        )
    req = attest.R11R12AttestationRequest(
        expected_revision=2,
        expected_staging_sha256=result["content_sha256"],
        action="ATTEST_R11_R12",
    )
    return engine, actor, body, req


def test_request_is_strict_and_cannot_contain_client_signature():
    _engine, _actor, _body, req = prepared_request_only()
    raw = req.model_dump()
    for field, value in (
        ("clinician_id", "clinician:99"), ("signature", "forged"),
        ("clinical_validation_available", True), ("final_strategy", {}),
    ):
        with pytest.raises(ValidationError):
            attest.R11R12AttestationRequest.model_validate({**raw, field: value})
    with pytest.raises(ValidationError):
        attest.R11R12AttestationRequest.model_validate({**raw, "action": "SIGN_R14"})
    with pytest.raises(ValidationError):
        attest.R11R12AttestationRequest.model_validate({**raw, "expected_revision": True})


def prepared_request_only():
    req = attest.R11R12AttestationRequest(
        expected_revision=2, expected_staging_sha256="a"*64, action="ATTEST_R11_R12",
    )
    return None, None, None, req


def test_doctor_attestation_persisted_in_audit_without_plan(monkeypatch):
    engine, actor, _body, req = prepared(monkeypatch)
    with Session(engine) as db:
        receipt = attest.attest_r11r12(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=req, db=db,
        )
        assert receipt["state"] == "R11_R12_REVIEW_ATTESTED_NON_FINAL"
        assert receipt["clinical_validation_available"] is False
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        view = attest.read_r11r12_attestation(
            patient_id=1, analysis=analysis, tenant_id=actor.get_employer_id(), db=db,
        )
        assert view["state"] == "CURRENT_NON_FINAL_ATTESTED"
        assert db.query(models.AuditLog).count() == 4
        row = db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).first()
        assert row.action == attest.ATTEST_ACTION
        metadata = json.loads(row.details)
        assert metadata["actor_user_id"] == 1
        assert metadata["graph_sha256"]
        assert metadata["staging_sha256"] == req.expected_staging_sha256
        assert "diagnosis" not in metadata
        assert metadata["clinical_validation_available"] is False


def test_same_review_cannot_be_replayed(monkeypatch):
    engine, actor, _body, req = prepared(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        attest.attest_r11r12(patient_id=1, analysis=analysis, actor=actor, request=req, db=db)
        with pytest.raises(HTTPException) as err:
            attest.attest_r11r12(patient_id=1, analysis=analysis, actor=actor, request=req, db=db)
        assert err.value.status_code == 409
        assert db.query(models.AuditLog).count() == 4


def test_r13_rejects_unattested_staging_even_with_test_rules(monkeypatch):
    engine, actor, body, req = prepared(monkeypatch)
    selection = decision.R13DecisionRequest(
        expected_revision=2, expected_staging_sha256=req.expected_staging_sha256,
        option_id=body.options[0].option_id, action="SELECT_OPTION",
    )
    with Session(engine) as db:
        with pytest.raises(HTTPException) as err:
            decision.decide_r13_option(
                patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
                actor=actor, request=selection, db=db,
            )
        assert err.value.status_code == 409
        assert db.query(models.AuditLog).count() == 3


def test_review_invalidated_when_graph_revision_changes(monkeypatch):
    engine, actor, _body, req = prepared(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        attest.attest_r11r12(patient_id=1, analysis=analysis, actor=actor, request=req, db=db)
        angles = dict(analysis.angles_data)
        angles["_evidence_graph_v1"] = {
            **angles["_evidence_graph_v1"], "revision": 3,
        }
        analysis.angles_data = angles
        db.commit()
        view = attest.read_r11r12_attestation(
            patient_id=1, analysis=analysis, tenant_id=actor.get_employer_id(), db=db,
        )
        assert view["state"] == "STALE_OR_UNVERIFIED"


def test_wrong_patient_role_or_stage_sha_are_refused(monkeypatch):
    engine, actor, _body, req = prepared(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        with pytest.raises(HTTPException) as err:
            attest.attest_r11r12(patient_id=2, analysis=analysis, actor=actor, request=req, db=db)
        assert err.value.status_code == 404
        with pytest.raises(HTTPException) as err:
            attest.attest_r11r12(
                patient_id=1, analysis=analysis, actor=actor,
                request=req.model_copy(update={"expected_staging_sha256": "0"*64}), db=db,
            )
        assert err.value.status_code == 409
        actor.role = models.UserRole.SECRETAIRE
        with pytest.raises(HTTPException) as err:
            attest.attest_r11r12(patient_id=1, analysis=analysis, actor=actor, request=req, db=db)
        assert err.value.status_code == 403


def test_unreviewed_production_registry_prevents_attestation(monkeypatch):
    engine, actor, _body, req = prepared(monkeypatch)
    monkeypatch.setattr(authority, "validate_r13_therapeutic_options", production_validate)
    with Session(engine) as db:
        with pytest.raises(HTTPException) as err:
            attest.attest_r11r12(
                patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
                actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 409
        assert db.query(models.AuditLog).count() == 3


def test_router_checks_patient_boundary_before_study_query(monkeypatch):
    monkeypatch.setattr(router, "assert_patient_access",
                        lambda *args: (_ for _ in ()).throw(HTTPException(status_code=403)))
    class ForbidQuery:
        def query(self, *_): raise AssertionError("Patient checked after reading the study")
    _engine, _actor, _body, req = prepared_request_only()
    with pytest.raises(HTTPException) as err:
        router.post_r11_r12_clinician_attestation(
            patient_id=7, analysis_id=101, body=req,
            db=ForbidQuery(), current_user=object(),
        )
    assert err.value.status_code == 403


def test_r11_validation_legacy_actor_cannot_impersonate_authenticated_doctor(monkeypatch):
    _source_locked_test_validators(monkeypatch)
    engine, body, actor = fixture()
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        angles = dict(analysis.angles_data)
        graph = dict(angles["_evidence_graph_v1"])
        validations = list(graph["validations"])
        validations[0] = {**validations[0], "clinician_id": "clinician:999"}
        graph["validations"] = validations
        analysis.angles_data = {**angles, "_evidence_graph_v1": graph}
        db.commit()
        result = staging.stage_clinical_evidence(
            patient_id=1, analysis=analysis, actor=actor, body=body, db=db,
        )
        forged = attest.R11R12AttestationRequest(
            expected_revision=2,
            expected_staging_sha256=result["content_sha256"],
            action="ATTEST_R11_R12",
        )
        with pytest.raises(HTTPException) as err:
            attest.attest_r11r12(
                patient_id=1, analysis=analysis, actor=actor, request=forged, db=db,
            )
        assert err.value.status_code == 403
        assert db.query(models.AuditLog).count() == 1


def test_deleted_attestation_audit_cannot_authorize_r13(monkeypatch):
    engine, actor, body, req = prepared(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        attest.attest_r11r12(
            patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
        )
        db.query(models.AuditLog).filter(
            models.AuditLog.action == attest.ATTEST_ACTION
        ).delete()
        db.commit()
        requested = decision.R13DecisionRequest(
            expected_revision=2, expected_staging_sha256=req.expected_staging_sha256,
            option_id=body.options[0].option_id, action="SELECT_OPTION",
        )
        with pytest.raises(HTTPException) as err:
            decision.decide_r13_option(
                patient_id=1, analysis=analysis, actor=actor, request=requested, db=db,
            )
        assert err.value.status_code == 409
        assert db.query(models.AuditLog).count() == 3
