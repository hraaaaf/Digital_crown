"""R13 decision reopen uses audited receipt, never a treatment plan."""
from sqlalchemy.orm import Session

from backend import models
from backend.services import cephalo_r13_option_decision as decisions
from backend.services import cephalo_r13_option_read as read
from backend.services import cephalo_r11_r12_attestation as attest
from backend.services import cephalo_r11_r13_staging as staging
from backend.tests.test_cephalo_r13_option_decision import _prepared


def test_current_selection_survives_database_reopen(monkeypatch):
    engine, _body, actor, req = _prepared(monkeypatch)
    with Session(engine) as db:
        decisions.decide_r13_option(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=req, db=db,
        )
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        actual = read.read_r13_decision(
            patient_id=1, analysis=analysis,
            tenant_id=actor.get_employer_id(), db=db,
        )
        assert actual["state"] == "CURRENT_R13_DECISION"
        assert actual["option_id"] == req.option_id
        assert actual["action"] == "SELECT_OPTION"
        assert actual["clinical_validation_available"] is False
        assert actual["r14_status"] == "NOT_VALIDATED"
        attested = attest.read_r11r12_attestation(
            patient_id=1, analysis=analysis, tenant_id=actor.get_employer_id(), db=db,
        )
        assert attested["state"] == "CURRENT_NON_FINAL_ATTESTED"


def test_selection_becomes_stale_when_science_changes(monkeypatch):
    engine, _body, actor, req = _prepared(monkeypatch)
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 101)
        decisions.decide_r13_option(
            patient_id=1, analysis=analysis, actor=actor, request=req, db=db,
        )
        payload = dict(analysis.angles_data)
        graph = dict(payload["_evidence_graph_v1"])
        graph["revision"] += 1
        analysis.angles_data = {**payload, "_evidence_graph_v1": graph}
        db.commit()
    with Session(engine) as db:
        result = read.read_r13_decision(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            tenant_id=actor.get_employer_id(), db=db,
        )
        assert result == {"state": "STALE", "clinical_validation_available": False}


def test_deleted_audit_is_not_trusted_on_reopen(monkeypatch):
    engine, _body, actor, req = _prepared(monkeypatch)
    with Session(engine) as db:
        decisions.decide_r13_option(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=req, db=db,
        )
        db.query(models.AuditLog).filter(
            models.AuditLog.action == decisions.DECISION_ACTION
        ).delete()
        db.commit()
    with Session(engine) as db:
        result = read.read_r13_decision(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            tenant_id=actor.get_employer_id(), db=db,
        )
        assert result["state"] == "UNVERIFIED"
        assert result["clinical_validation_available"] is False


def test_other_tenant_cannot_claim_a_valid_decision(monkeypatch):
    engine, _body, actor, req = _prepared(monkeypatch)
    with Session(engine) as db:
        decisions.decide_r13_option(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            actor=actor, request=req, db=db,
        )
    with Session(engine) as db:
        result = read.read_r13_decision(
            patient_id=1, analysis=db.get(models.CephaloAnalysis, 101),
            tenant_id=999, db=db,
        )
        assert result["state"] == "UNVERIFIED"
