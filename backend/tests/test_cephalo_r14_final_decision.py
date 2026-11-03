"""R14 backend gate tests use SYNTHETIC clinical rules, never patient authority."""
import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend import models
from backend.routers import cephalo_clinical_studio as router
from backend.services import cephalo_r14_final_decision as final
from backend.services import cephalo_r14_final_read as final_read
from backend.services import cephalo_r13_option_decision as r13_decision
from backend.services import cephalo_r11_r13_staging as staging
from backend.services import cephalo_r15_clinical_studio as studio
from backend.services.cephalo_r14_final_validation_safety import (
    validate_r14_final_clinical_validation as real_r14_validator,
)
from backend.tests.test_cephalo_r13_option_decision import _prepared
from backend.tests.test_cephalo_r13_therapeutic_safety import (
    _diagnostic_registry, _therapeutic_registry,
)


def _synthetic_r14(monkeypatch):
    """Run the real R14→R13→R12→R11 validator with test-only rule registries."""
    def validate(snapshot):
        return real_r14_validator(
            snapshot,
            diagnostic_rule_registry=_diagnostic_registry(),
            therapeutic_rule_registry=_therapeutic_registry(),
        )
    monkeypatch.setattr(final, "validate_r14_final_clinical_validation", validate)
    monkeypatch.setattr(final_read, "validate_r14_final_clinical_validation", validate)


def _selected_study(monkeypatch, *, trusted_r14=True):
    engine, body, actor, request = _prepared(monkeypatch)
    with Session(engine) as db:
        decision = r13_decision.decide_r13_option(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=request, db=db,
        )
    if trusted_r14:
        _synthetic_r14(monkeypatch)
    req = final.R14FinalDecisionRequest(
        expected_revision=2, expected_staging_sha256=decision["staging_sha256"],
        action="VALIDATE_FINAL_R14", option_id=body.options[0].option_id,
    )
    return engine, actor, req


def test_r14_request_cannot_supply_signature_diagnosis_or_clinician():
    raw = {
        "expected_revision": 2, "expected_staging_sha256": "a" * 64,
        "option_id": "option:r13:synthetic", "action": "VALIDATE_FINAL_R14",
    }
    for name, value in (
        ("signature", "FORGED"),
        ("clinician_id", "clinician:99"),
        ("diagnosis", "made up"),
        ("strategy", {}),
        ("validation_id", "client-id"),
        ("clinical_validation_available", True),
    ):
        with pytest.raises(ValidationError):
            final.R14FinalDecisionRequest.model_validate({**raw, name: value})
    with pytest.raises(ValidationError):
        final.R14FinalDecisionRequest.model_validate({**raw, "expected_revision": True})
    with pytest.raises(ValidationError):
        final.R14FinalDecisionRequest.model_validate({**raw, "action": "AUTO_APPROVE"})


def test_server_final_decision_roundtrip_still_pdf_hold(monkeypatch):
    engine, actor, req = _selected_study(monkeypatch)
    with Session(engine) as db:
        response = final.decide_r14_final(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=req, db=db,
        )
        assert response["status"] == "CLINICIAN_VALIDATED"
        assert response["clinical_validation_available"] is False
        assert response["pdf_complete"] is False
        assert len(response["r14_sha256"]) == 64
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        saved = analysis.angles_data[final.R14_KEY]
        assert saved["strategy"]["status"] == "CLINICIAN_VALIDATED"
        assert saved["validation"]["clinician_id"] == "clinician:1"
        assert saved["validation"]["target_type"] == "final_clinical_strategy"
        assert saved["clinical_validation_available"] is False
        assert db.query(models.AuditLog).count() == 4
        row = db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).first()
        assert row.action == final.R14_AUDIT_ACTION
        audit_details = json.loads(row.details)
        assert audit_details["validation_id"] == saved["validation"]["validation_id"]
        assert "Synthetic test option" not in row.details
        read = final_read.read_r14_final(
            patient_id=1, analysis=analysis,
            tenant_id=actor.get_employer_id(), db=db,
        )
        assert read["state"] == "CURRENT_R14_DECISION_NON_RELEASED"
        assert read["clinical_validation_available"] is False
        assert read["pdf_complete"] is False
        r15 = studio.build_r15_clinical_studio_snapshot(
            patient_id=1, analysis_id=101, angles_data=analysis.angles_data,
        )
        assert r15["clinical_validation_available"] is False
        assert "r14_authoritative_snapshot_not_persisted" in r15["blocking_gates"]


def test_production_empty_rule_registries_deny_final(monkeypatch):
    engine, actor, req = _selected_study(monkeypatch, trusted_r14=False)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        with pytest.raises(HTTPException) as error:
            final.decide_r14_final(
                patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert error.value.status_code == 409
        assert final.R14_KEY not in analysis.angles_data
        assert db.query(models.AuditLog).count() == 3


def test_r14_duplicate_decision_is_denied(monkeypatch):
    engine, actor, req = _selected_study(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        final.decide_r14_final(
            patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
        )
        with pytest.raises(HTTPException) as error:
            final.decide_r14_final(
                patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert error.value.status_code == 409
        assert db.query(models.AuditLog).count() == 4


def test_rejected_R14_is_tracked_not_released(monkeypatch):
    engine, actor, req = _selected_study(monkeypatch)
    rejection = req.model_copy(update={"action": "REJECT_FINAL_R14"})
    with Session(engine) as db:
        final.decide_r14_final(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=rejection, db=db,
        )
    with Session(engine) as db:
        result = final_read.read_r14_final(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            tenant_id=actor.get_employer_id(), db=db,
        )
        assert result["status"] == "CLINICIAN_REJECTED"
        assert result["clinical_validation_available"] is False


def test_r14_wrong_patient_doctor_and_option_refused(monkeypatch):
    engine, actor, req = _selected_study(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        with pytest.raises(HTTPException) as err:
            final.decide_r14_final(
                patient_id=2, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 404
        with pytest.raises(HTTPException) as err:
            final.decide_r14_final(
                patient_id=1, analysis=analysis, actor=actor,
                request=req.model_copy(update={"option_id": "wrong-option"}), db=db,
            )
        assert err.value.status_code == 409
        actor.role = models.UserRole.SECRETAIRE
        with pytest.raises(HTTPException) as err:
            final.decide_r14_final(
                patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
            )
        assert err.value.status_code == 403
        assert db.query(models.AuditLog).count() == 3


def test_r14_stale_expected_sha_and_revision_are_rejected(monkeypatch):
    engine, actor, req = _selected_study(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        for changed in [
            req.model_copy(update={"expected_revision": 3}),
            req.model_copy(update={"expected_staging_sha256": "f" * 64}),
        ]:
            with pytest.raises(HTTPException) as err:
                final.decide_r14_final(
                    patient_id=1, analysis=analysis, actor=actor, request=changed, db=db,
                )
            assert err.value.status_code == 409


def test_change_graph_after_final_makes_it_stale(monkeypatch):
    engine, actor, req = _selected_study(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        final.decide_r14_final(
            patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
        )
        data = dict(analysis.angles_data)
        graph = dict(data["_evidence_graph_v1"])
        graph["revision"] = 3
        analysis.angles_data = {**data, "_evidence_graph_v1": graph}
        db.commit()
    with Session(engine) as db:
        assert final_read.read_r14_final(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            tenant_id=actor.get_employer_id(), db=db,
        )["state"] == "STALE_OR_UNVERIFIED"


def test_missing_r14_audit_or_other_tenant_fails_read(monkeypatch):
    engine, actor, req = _selected_study(monkeypatch)
    with Session(engine) as db:
        final.decide_r14_final(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=req, db=db,
        )
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        assert final_read.read_r14_final(
            patient_id=1, analysis=analysis, tenant_id=999, db=db,
        )["state"] == "STALE_OR_UNVERIFIED"
        db.query(models.AuditLog).filter(
            models.AuditLog.action == final.R14_AUDIT_ACTION,
        ).delete()
        db.commit()
        assert final_read.read_r14_final(
            patient_id=1, analysis=analysis,
            tenant_id=actor.get_employer_id(), db=db,
        )["state"] == "STALE_OR_UNVERIFIED"


def test_router_checks_patient_access_before_analysis(monkeypatch):
    monkeypatch.setattr(router, "assert_patient_access",
                        lambda *args: (_ for _ in ()).throw(HTTPException(status_code=403)))
    class NoQuery:
        def query(self, *_):
            raise AssertionError("Study accessed before patient check")
    raw = final.R14FinalDecisionRequest(
        expected_revision=2, expected_staging_sha256="f" * 64,
        option_id="some-option", action="VALIDATE_FINAL_R14",
    )
    with pytest.raises(HTTPException) as err:
        router.post_r14_final_clinician_decision(
            patient_id=1, analysis_id=101, body=raw,
            db=NoQuery(), current_user=object(),
        )
    assert err.value.status_code == 403
