"""Authenticated R11/R12 review of current study evidence, not an R14 signature.

No diagnosis, source rule or therapy is generated here. The dentist must
explicitly attest source-validated R11 findings/diagnoses and staged R12
problems/objectives. The audit is tied to study, patient, tenant and graph.
"""
import datetime as dt
import json
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from backend import models
from backend.schemas.cephalo_evidence import ReviewState, ValidationAction
from backend.services.cephalo_r14_review_receipt import _current_graph, _graph_digest, _require_clinician
from backend.services.cephalo_r13_decision_authority import resolve_r13_staging, require_committed_staging_audit
from backend.services.cephalo_r11_target_reviews import verified_target_review_receipts

ATTEST_ACTION = "CEPH_R11_R12_CLINICIAN_ATTESTED"
ATTEST_CONTRACT = "CEPH_R11_R12_REVIEW_ATTESTATION_V1"


class R11R12AttestationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: StrictInt = Field(gt=0)
    expected_staging_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    action: Literal["ATTEST_R11_R12"]


def _actor_owns_review(r13, actor_id):
    expected = f"clinician:{actor_id}"
    r12 = r13.r12_snapshot
    graph = r12.diagnostic_graph
    if not graph.findings or not graph.diagnoses or not r12.problems or not r12.objectives:
        return False
    if any(
        item.state not in {ReviewState.ACCEPTED, ReviewState.EDITED}
        or item.clinician_id != expected
        or not item.clinician_validated_at
        for item in [*graph.diagnoses, *r12.problems, *r12.objectives]
    ):
        return False
    used_finding_ids = {
        ref for diagnosis in graph.diagnoses
        for ref in [*diagnosis.supporting_finding_refs, *diagnosis.opposing_finding_refs]
    }
    if not used_finding_ids:
        return False
    latest = {}
    for validation in graph.validations:
        if validation.target_type != "finding" or validation.target_id not in used_finding_ids:
            continue
        old = latest.get(validation.target_id)
        if old is None or validation.validated_at > old.validated_at:
            latest[validation.target_id] = validation
        elif old.validated_at == validation.validated_at and validation.validation_id != old.validation_id:
            return False
    return all(
        ref in latest and latest[ref].clinician_id == expected
        and latest[ref].action in {ValidationAction.ACCEPT, ValidationAction.EDIT}
        for ref in used_finding_ids
    )


def _latest_audit(*, patient_id, analysis, tenant_id, db):
    rows = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.action == ATTEST_ACTION,
            models.AuditLog.resource_type == "CephaloAnalysis",
            models.AuditLog.resource_id == str(analysis.id),
            models.AuditLog.employer_id == tenant_id,
        )
        .order_by(models.AuditLog.id.desc()).limit(30).all()
    )
    for row in rows:
        try:
            claim = json.loads(row.details)
            if (
                isinstance(claim, dict)
                and claim.get("contract") == ATTEST_CONTRACT
                and claim.get("patient_id") == patient_id
                and claim.get("analysis_id") == analysis.id
                and claim.get("actor_user_id") == row.user_id
                and claim.get("clinical_validation_available") is False
            ):
                yield row, claim
        except (TypeError, ValueError):
            continue


def verified_r11r12_attestation(
    *, patient_id, analysis, tenant_id, graph_sha256,
    revision, staging_sha256, db,
) -> bool:
    """Only backend audit binding may authorize the subsequent R13 option action."""
    for _row, claim in _latest_audit(
        patient_id=patient_id, analysis=analysis, tenant_id=tenant_id, db=db,
    ):
        if (
            claim.get("analysis_revision") == revision
            and claim.get("graph_sha256") == graph_sha256
            and claim.get("staging_sha256") == staging_sha256
            and type(claim.get("analysis_revision")) is int
            and isinstance(claim.get("reviewed_at"), str)
            and claim["reviewed_at"]
        ):
            # A legacy JSON clinician_id is not proof of a server-authored
            # R11 review. Each finding and diagnosis must have an independent
            # authenticated, patient/tenant/stage-bound audit, and the EXACT
            # audit identities must be tied to the attestation.
            try:
                _staged, r13 = resolve_r13_staging(
                    patient_id=patient_id, analysis=analysis,
                )
                receipts = verified_target_review_receipts(
                    patient_id=patient_id, analysis=analysis,
                    tenant_id=tenant_id, revision=revision,
                    graph_sha256=graph_sha256, staging_sha256=staging_sha256,
                    actor_id=_row.user_id, r13=r13, db=db,
                )
                if receipts and claim.get("r11_target_reviews") == receipts:
                    return True
            except (HTTPException, ValueError, KeyError, TypeError):
                continue
    return False


def attest_r11r12(*, patient_id, analysis, actor, request: R11R12AttestationRequest, db):
    actor_id = _require_clinician(actor)
    if analysis.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Analyse hors patient.")
    graph, revision = _current_graph(analysis)
    if revision != request.expected_revision:
        raise HTTPException(status_code=409, detail="Révision scientifique périmée.")
    staged, r13 = resolve_r13_staging(patient_id=patient_id, analysis=analysis)
    if staged["content_sha256"] != request.expected_staging_sha256:
        raise HTTPException(status_code=409, detail="Contenu R11–R13 modifié.")
    if r13.option_validations:
        raise HTTPException(status_code=409, detail="L'attestation R11/R12 précède obligatoirement R13.")
    require_committed_staging_audit(db=db, analysis=analysis, staged=staged, actor=actor)
    if staged["actor_user_id"] != actor_id or not _actor_owns_review(r13, actor_id):
        raise HTTPException(status_code=403, detail="Revue clinique R11/R12 non attribuable au praticien.")
    sha = _graph_digest(graph)
    tenant = actor.get_employer_id()
    receipts = verified_target_review_receipts(
        patient_id=patient_id, analysis=analysis, tenant_id=tenant,
        graph_sha256=sha, revision=revision,
        staging_sha256=staged["content_sha256"],
        actor_id=actor_id, r13=r13, db=db,
    )
    if not receipts:
        raise HTTPException(
            status_code=409,
            detail="Revue R11 individuelle authentifiée requise pour chaque constat et diagnostic.",
        )
    if verified_r11r12_attestation(
        patient_id=patient_id, analysis=analysis, tenant_id=tenant,
        graph_sha256=sha, revision=revision,
        staging_sha256=staged["content_sha256"], db=db,
    ):
        raise HTTPException(status_code=409, detail="Attestation déjà enregistrée.")
    current, rev = _current_graph(analysis)
    if rev != revision or _graph_digest(current) != sha:
        raise HTTPException(status_code=409, detail="Graphe modifié pendant la revue.")
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    details = {
        "contract": ATTEST_CONTRACT,
        "patient_id": patient_id,
        "analysis_id": analysis.id,
        "actor_user_id": actor_id,
        "analysis_revision": revision,
        "graph_sha256": sha,
        "staging_sha256": staged["content_sha256"],
        "reviewed_at": now,
        "r11_target_reviews": receipts,
        "clinical_validation_available": False,
        "r14_status": "NOT_VALIDATED",
    }
    db.add(models.AuditLog(
        user_id=actor_id, employer_id=tenant,
        action=ATTEST_ACTION, resource_type="CephaloAnalysis",
        resource_id=str(analysis.id), severity="INFO",
        details=json.dumps(details, sort_keys=True, ensure_ascii=True),
    ))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "state": "R11_R12_REVIEW_ATTESTED_NON_FINAL",
        "analysis_revision": revision,
        "staging_sha256": staged["content_sha256"],
        "clinical_validation_available": False,
        "r14_status": "NOT_VALIDATED",
    }


def read_r11r12_attestation(*, patient_id, analysis, tenant_id, db):
    if analysis.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Analyse hors patient.")
    try:
        graph, revision = _current_graph(analysis)
        staged, _r13 = resolve_r13_staging(patient_id=patient_id, analysis=analysis)
        sha = _graph_digest(graph)
        current = verified_r11r12_attestation(
            patient_id=patient_id, analysis=analysis, tenant_id=tenant_id,
            graph_sha256=sha, revision=revision,
            staging_sha256=staged["content_sha256"], db=db,
        )
        # R13 decision creates a new staging hash, but the prior R11/R12
        # attestation remains verifiable through the server-issued decision audit.
        if not current and _r13.option_validations:
            audit = (
                db.query(models.AuditLog)
                .filter(
                    models.AuditLog.action == "CEPH_R13_OPTION_DECIDED",
                    models.AuditLog.resource_type == "CephaloAnalysis",
                    models.AuditLog.resource_id == str(analysis.id),
                    models.AuditLog.employer_id == tenant_id,
                )
                .order_by(models.AuditLog.id.desc()).first()
            )
            try:
                claim = json.loads(audit.details) if audit else {}
                if (
                    claim.get("patient_id") == patient_id
                    and claim.get("analysis_id") == analysis.id
                    and claim.get("revision") == revision
                    and claim.get("graph_sha256") == sha
                    and claim.get("staging_after") == staged["content_sha256"]
                    and claim.get("validation_id") == _r13.option_validations[0].validation_id
                    and claim.get("actor_user_id") == audit.user_id
                ):
                    current = verified_r11r12_attestation(
                        patient_id=patient_id, analysis=analysis, tenant_id=tenant_id,
                        graph_sha256=sha, revision=revision,
                        staging_sha256=claim["staging_before"], db=db,
                    )
            except (AttributeError, KeyError, TypeError, ValueError):
                current = False
        return {
            "state": "CURRENT_NON_FINAL_ATTESTED" if current else "NOT_ATTESTED",
            "analysis_revision": revision,
            "clinical_validation_available": False,
        }
    except HTTPException:
        return {"state": "STALE_OR_UNVERIFIED", "clinical_validation_available": False}
