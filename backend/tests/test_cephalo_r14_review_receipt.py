"""R11–R14 clinician blocker-review receipts: source-bound, audited, never signed.

Synthetic-only tests. This does NOT certify a clinical diagnosis or an R14
final validation; production scientific registries remain intentionally empty.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend import models
from backend.routers import cephalo_clinical_studio as router
from backend.services import cephalo_r14_review_receipt as service
from backend.services import cephalo_r15_clinical_studio as studio
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def _actor(*, role=models.UserRole.DENTISTE, active=True, employee=False):
    return SimpleNamespace(
        id=24,
        role=role,
        is_active=active,
        employer_id=7 if employee else None,
        approval_status="approved",
        get_employer_id=lambda: 7,
    )


def _analysis(graph=None):
    if graph is None:
        graph = {"revision": 3, "case_id": "synthetic:case:A"}
    return SimpleNamespace(
        id=96, patient_id=41, angles_data={EVIDENCE_GRAPH_KEY: graph}
    )


def _request(revision=3):
    return service.CephaloBlockerReviewRequest(
        expected_revision=revision, action="ACKNOWLEDGE_BLOCKERS"
    )


def _studio(**_kwargs):
    return {
        "blocking_gates": [
            "r11_authoritative_snapshot_not_persisted",
            "r13_authoritative_snapshot_not_persisted",
            "r14_authoritative_snapshot_not_persisted",
        ],
        "clinical_validation_available": False,
    }


def _db():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    # The existing AuditLog table is enough: no new schema or clinic migration.
    models.AuditLog.__table__.create(engine)
    return engine


def test_acknowledgement_contract_rejects_forged_validation_and_boolean_revision():
    with pytest.raises(ValidationError):
        service.CephaloBlockerReviewRequest(
            expected_revision=3, action="VALIDATE_CLINICALLY"
        )
    with pytest.raises(ValidationError):
        service.CephaloBlockerReviewRequest(
            expected_revision=3, action="ACKNOWLEDGE_BLOCKERS", signature="FORGED"
        )
    with pytest.raises(ValidationError):
        service.CephaloBlockerReviewRequest(
            expected_revision=True, action="ACKNOWLEDGE_BLOCKERS"
        )


@pytest.mark.parametrize("actor", [
    _actor(role=models.UserRole.ADMIN),
    _actor(role=models.UserRole.SECRETAIRE),
    _actor(active=False),
    SimpleNamespace(id=24, role=models.UserRole.DENTISTE, is_active=True,
                    employer_id=7, approval_status="pending", get_employer_id=lambda: 7),
])
def test_blocker_receipts_reject_non_dentist_inactive_and_unapproved_actor(actor):
    class ForbiddenDb:
        def add(self, *_): raise AssertionError("no write allowed")
    with pytest.raises(HTTPException) as exc:
        service.save_blocker_review_receipt(
            patient_id=41, analysis=_analysis(), actor=actor,
            request=_request(), db=ForbiddenDb()
        )
    assert exc.value.status_code == 403


def test_revision_mismatch_fails_before_any_write():
    class ForbiddenDb:
        def add(self, *_): raise AssertionError("no write allowed")
    with pytest.raises(HTTPException) as exc:
        service.save_blocker_review_receipt(
            patient_id=41, analysis=_analysis(), actor=_actor(),
            request=_request(revision=2), db=ForbiddenDb()
        )
    assert exc.value.status_code == 409


@pytest.mark.parametrize("graph", [{}, {"revision": None}, {"revision": True}, {"revision": "3"}, {"revision": 0}])
def test_missing_or_invalid_graph_revision_fails_closed(graph):
    class ForbiddenDb:
        def add(self, *_): raise AssertionError("no write allowed")
    with pytest.raises(HTTPException) as exc:
        service.save_blocker_review_receipt(
            patient_id=41, analysis=_analysis(graph), actor=_actor(),
            request=_request(), db=ForbiddenDb()
        )
    assert exc.value.status_code == 409


def test_review_writes_real_audit_row_and_reads_back_without_clinical_promotion(monkeypatch):
    monkeypatch.setattr(service, "build_r15_clinical_studio_snapshot", _studio)
    engine = _db()
    with Session(engine) as db:
        before = _analysis()
        receipt = service.save_blocker_review_receipt(
            patient_id=41, analysis=before, actor=_actor(), request=_request(), db=db
        )
        assert receipt["contract"] == "CEPH_R14_REVIEW_RECEIPT_V1"
        assert receipt["status"] == "REVIEWED_BUT_CLINICALLY_BLOCKED"
        assert receipt["clinical_validation_available"] is False
        assert receipt["actor_user_id"] == 24
        assert receipt["analysis_revision"] == 3
        assert receipt["receipt_id"] > 0
        assert before.angles_data == {EVIDENCE_GRAPH_KEY: {"revision": 3, "case_id": "synthetic:case:A"}}
    with Session(engine) as db:
        audit = db.query(models.AuditLog).one()
        assert audit.user_id == 24
        assert audit.employer_id == 7
        assert audit.action == "CEPH_R14_BLOCKERS_ACKNOWLEDGED"
        rows = service.read_blocker_review_receipts(
            patient_id=41, analysis=_analysis(), tenant_id=_actor().get_employer_id(), db=db
        )
        assert len(rows) == 1
        assert rows[0]["currency"] == "CURRENT_BLOCKED"
        assert rows[0]["clinical_validation_available"] is False


def test_evidence_edit_or_same_revision_graph_tamper_invalidates_prior_review(monkeypatch):
    monkeypatch.setattr(service, "build_r15_clinical_studio_snapshot", _studio)
    engine = _db()
    with Session(engine) as db:
        service.save_blocker_review_receipt(
            patient_id=41, analysis=_analysis(), actor=_actor(), request=_request(), db=db
        )
        changed = _analysis({"revision": 4, "case_id": "synthetic:case:A"})
        rows = service.read_blocker_review_receipts(patient_id=41, analysis=changed, tenant_id=_actor().get_employer_id(), db=db)
        assert rows[0]["currency"] == "STALE"
        tampered = _analysis({"revision": 3, "case_id": "synthetic:case:B"})
        rows = service.read_blocker_review_receipts(patient_id=41, analysis=tampered, tenant_id=_actor().get_employer_id(), db=db)
        assert rows[0]["currency"] == "STALE"


def test_cross_patient_binding_refused_before_clinical_audit(monkeypatch):
    monkeypatch.setattr(service, "build_r15_clinical_studio_snapshot", _studio)
    class ForbiddenDb:
        def add(self, *_): raise AssertionError("no write allowed")
    with pytest.raises(HTTPException) as exc:
        service.save_blocker_review_receipt(
            patient_id=42, analysis=_analysis(), actor=_actor(), request=_request(),
            db=ForbiddenDb()
        )
    assert exc.value.status_code == 404


def test_http_boundary_checks_patient_access_before_any_analysis_query(monkeypatch):
    calls = []
    def deny(patient_id, user, db):
        calls.append(patient_id)
        raise HTTPException(status_code=403, detail="forbidden")
    monkeypatch.setattr(router, "assert_patient_access", deny)
    class ForbiddenDb:
        def query(self, *_):
            raise AssertionError("query executed before ownership guard")
    with pytest.raises(HTTPException) as exc:
        router.acknowledge_r14_blockers(
            41, 96, _request(), db=ForbiddenDb(), current_user=_actor()
        )
    assert exc.value.status_code == 403
    assert calls == [41]


def test_studio_and_pdf_are_not_promoted_from_review_receipt(monkeypatch):
    # Real R15 projection is intentionally fail-closed with empty source registries;
    # no review receipt is an R14 ClinicianValidationEvidence.
    monkeypatch.setattr(studio, "project_runtime_chain_read_path",
        lambda payload, patient_id: {"scientific_read_path": {
            "active_chain": "VERIFIED", "current_measurement_count": 1}})
    snapshot = studio.build_r15_clinical_studio_snapshot(
        patient_id=41, analysis_id=96,
        angles_data={EVIDENCE_GRAPH_KEY: {"revision": 3},
                     "clinical_review_receipt": {"clinical_validation_available": True}}
    )
    assert snapshot["clinical_validation_available"] is False
    assert "r14_authoritative_snapshot_not_persisted" in snapshot["blocking_gates"]
    assert all(stage["clinician_action"]["available"] is False for stage in snapshot["stages"])


def test_receipt_studio_must_have_real_blockers_and_never_appear_signed(monkeypatch):
    monkeypatch.setattr(service, "build_r15_clinical_studio_snapshot", lambda **_:
                        {"blocking_gates": [], "clinical_validation_available": True})
    class ForbiddenDb:
        def add(self, *_): raise AssertionError("no write allowed")
    with pytest.raises(HTTPException) as exc:
        service.save_blocker_review_receipt(
            patient_id=41, analysis=_analysis(), actor=_actor(), request=_request(),
            db=ForbiddenDb()
        )
    assert exc.value.status_code == 409

def test_blocker_review_receipts_enforce_tenant_boundary_on_same_study(monkeypatch):
    """A same-resource audit from another employer must never leak into this cabinet."""
    monkeypatch.setattr(service, "build_r15_clinical_studio_snapshot", _studio)
    engine = _db()
    with Session(engine) as db:
        service.save_blocker_review_receipt(
            patient_id=41, analysis=_analysis(), actor=_actor(),
            request=_request(), db=db,
        )
        original = db.query(models.AuditLog).one()
        foreign = models.AuditLog(
            user_id=original.user_id,
            employer_id=8,
            action=original.action,
            resource_type=original.resource_type,
            resource_id=original.resource_id,
            severity=original.severity,
            details=original.details,
        )
        db.add(foreign)
        db.commit()
        rows = service.read_blocker_review_receipts(
            patient_id=41, analysis=_analysis(), tenant_id=7, db=db,
        )
        assert [r["receipt_id"] for r in rows] == [original.id]
        assert all(r["currency"] == "CURRENT_BLOCKED" for r in rows)
        assert service.read_blocker_review_receipts(
            patient_id=41, analysis=_analysis(), tenant_id=9, db=db,
        ) == []
