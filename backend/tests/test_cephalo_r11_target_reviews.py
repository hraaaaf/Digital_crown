"""R11 individual review origin is a server AuditLog, not legacy JSON authorship."""
import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend import models
from backend.routers import cephalo_clinical_studio as router
from backend.services import cephalo_r11_target_reviews as reviews
from backend.services import cephalo_r11_r12_attestation as attest
from backend.services import cephalo_r11_r13_staging as staging
from backend.services import cephalo_r13_option_decision as decision
from backend.tests.test_cephalo_r11_r13_staging import fixture
from backend.tests.test_cephalo_r13_option_decision import (
    _source_locked_test_validators, _complete_r11_reviews,
)


def _case(monkeypatch):
    _source_locked_test_validators(monkeypatch)
    engine, body, actor = fixture()
    with Session(engine) as db:
        saved = staging.stage_clinical_evidence(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, body=body, db=db,
        )
    return engine, body, actor, saved["content_sha256"]


def _request(target_type, target_id, sha):
    return reviews.R11TargetReviewRequest(
        expected_revision=2, expected_staging_sha256=sha,
        target_type=target_type, target_id=target_id,
        action="CONFIRM_R11_TARGET_REVIEW",
    )


def _target_id(analysis, target_type):
    group, key = ("findings", "finding_id") if target_type == "finding" else ("diagnoses", "diagnosis_id")
    return analysis.angles_data["_evidence_graph_v1"][group][0][key]


def _attest(analysis, actor, sha, db):
    return attest.attest_r11r12(
        patient_id=1, analysis=analysis, actor=actor,
        request=attest.R11R12AttestationRequest(
            expected_revision=2, expected_staging_sha256=sha, action="ATTEST_R11_R12",
        ), db=db,
    )


def test_request_does_not_accept_client_authorship_signature_or_evidence():
    raw = _request("finding", "finding:synthetic", "a"*64).model_dump()
    for field, value in (
        ("clinician_id", "clinician:999"),
        ("clinician_validated_at", "2026-11-03T00:00:00Z"),
        ("validation_id", "forged"),
        ("diagnosis", "arbitrary"),
        ("signature", "forged"),
        ("clinical_validation_available", True),
    ):
        with pytest.raises(ValidationError):
            reviews.R11TargetReviewRequest.model_validate({**raw, field:value})
    with pytest.raises(ValidationError):
        reviews.R11TargetReviewRequest.model_validate({**raw, "target_type":"free_text"})
    with pytest.raises(ValidationError):
        reviews.R11TargetReviewRequest.model_validate({**raw, "expected_revision": True})


def test_individual_r11_decisions_are_authenticated_audits_only(monkeypatch):
    engine, _body, actor, sha = _case(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        _complete_r11_reviews(db=db, analysis=analysis, actor=actor, stage_sha=sha)
        rows = db.query(models.AuditLog).filter(
            models.AuditLog.action == reviews.R11_TARGET_ACTION,
        ).order_by(models.AuditLog.id.asc()).all()
        assert len(rows) == 2
        assert {(json.loads(r.details)["target_type"], json.loads(r.details)["target_id"]) for r in rows} == {
            ("finding", _target_id(analysis, "finding")),
            ("diagnosis", _target_id(analysis, "diagnosis")),
        }
        for row in rows:
            claim = json.loads(row.details)
            assert row.user_id == claim["actor_user_id"] == 1
            assert claim["graph_sha256"] and claim["staging_sha256"] == sha
            assert claim["target_sha256"] and claim["reviewed_at"]
            assert claim["clinical_validation_available"] is False
        receipt = _attest(analysis, actor, sha, db)
        assert receipt["clinical_validation_available"] is False
        claim = json.loads(db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).first().details)
        assert len(claim["r11_target_reviews"]) == 2
        assert sorted(x["audit_id"] for x in claim["r11_target_reviews"]) == sorted(r.id for r in rows)


def test_missing_individual_diagnosis_review_denies_global_attestation(monkeypatch):
    engine, _body, actor, sha = _case(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        reviews.record_r11_target_review(
            patient_id=1, analysis=analysis, actor=actor,
            request=_request("finding", _target_id(analysis, "finding"), sha), db=db,
        )
        with pytest.raises(HTTPException) as err:
            _attest(analysis, actor, sha, db)
        assert err.value.status_code == 409


def test_duplicate_review_is_rejected_and_does_not_add_an_audit(monkeypatch):
    engine, _body, actor, sha = _case(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        req = _request("finding", _target_id(analysis, "finding"), sha)
        reviews.record_r11_target_review(
            patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
        )
        with pytest.raises(HTTPException) as err:
            reviews.record_r11_target_review(
                patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 409
        assert db.query(models.AuditLog).count() == 2


def test_deleted_target_review_revokes_attestation_and_r13(monkeypatch):
    engine, body, actor, sha = _case(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        _complete_r11_reviews(db=db, analysis=analysis, actor=actor, stage_sha=sha)
        _attest(analysis, actor, sha, db)
        assert attest.verified_r11r12_attestation(
            patient_id=1, analysis=analysis, tenant_id=actor.get_employer_id(),
            graph_sha256=staging._graph_digest(analysis.angles_data["_evidence_graph_v1"]),
            revision=2, staging_sha256=sha, db=db,
        )
        db.query(models.AuditLog).filter(
            models.AuditLog.action == reviews.R11_TARGET_ACTION,
            models.AuditLog.details.like('%"target_type": "diagnosis"%'),
        ).delete()
        db.commit()
        assert not attest.verified_r11r12_attestation(
            patient_id=1, analysis=analysis, tenant_id=actor.get_employer_id(),
            graph_sha256=staging._graph_digest(analysis.angles_data["_evidence_graph_v1"]),
            revision=2, staging_sha256=sha, db=db,
        )
        req = decision.R13DecisionRequest(
            expected_revision=2, expected_staging_sha256=sha,
            option_id=body.options[0].option_id, action="SELECT_OPTION",
        )
        with pytest.raises(HTTPException) as err:
            decision.decide_r13_option(
                patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 409


def test_wrong_role_patient_hash_and_target_are_rejected(monkeypatch):
    engine, _body, actor, sha = _case(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        valid = _request("finding", _target_id(analysis, "finding"), sha)
        for args, status in [
            ({"patient_id": 99, "request": valid}, 404),
            ({"patient_id": 1, "request": valid.model_copy(update={"expected_staging_sha256":"f"*64})}, 409),
            ({"patient_id": 1, "request": valid.model_copy(update={"target_id":"unknown"})}, 404),
        ]:
            with pytest.raises(HTTPException) as err:
                reviews.record_r11_target_review(
                    analysis=analysis, actor=actor, db=db, **args,
                )
            assert err.value.status_code == status
        actor.role = models.UserRole.SECRETAIRE
        with pytest.raises(HTTPException) as err:
            reviews.record_r11_target_review(
                patient_id=1, analysis=analysis, actor=actor, request=valid, db=db,
            )
        assert err.value.status_code == 403
        assert db.query(models.AuditLog).count() == 1


def test_router_checks_patient_access_before_study_query(monkeypatch):
    monkeypatch.setattr(router, "assert_patient_access",
                        lambda *args: (_ for _ in ()).throw(HTTPException(status_code=403)))
    class NoRead:
        def query(self, *_):
            raise AssertionError("Patient access must be checked first")
    with pytest.raises(HTTPException) as err:
        router.post_r11_individual_review(
            patient_id=1, analysis_id=101,
            body=_request("finding", "finding:synthetic", "f"*64),
            db=NoRead(), current_user=object(),
        )
    assert err.value.status_code == 403


def test_stale_sqlite_session_cannot_duplicate_confirmed_target(monkeypatch):
    """A second loaded Session sees the committed audit after the write lock."""
    engine, _body, actor, sha = _case(monkeypatch)
    with Session(engine) as stale:
        loaded = stale.get(models.CephaloAnalysis, 101)
        request = _request("finding", _target_id(loaded, "finding"), sha)
        with Session(engine) as winner:
            reviews.record_r11_target_review(
                patient_id=1, analysis=winner.get(models.CephaloAnalysis, 101),
                actor=actor, request=request, db=winner,
            )
        with pytest.raises(HTTPException) as err:
            reviews.record_r11_target_review(
                patient_id=1, analysis=loaded,
                actor=actor, request=request, db=stale,
            )
        assert err.value.status_code == 409
    with Session(engine) as db:
        assert db.query(models.AuditLog).filter(
            models.AuditLog.action == reviews.R11_TARGET_ACTION,
        ).count() == 1
        assert db.get(models.CephaloAnalysis, 101).angles_data[staging.STAGING_KEY]["content_sha256"] == sha
