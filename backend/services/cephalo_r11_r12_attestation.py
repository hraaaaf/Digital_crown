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
from backend.services.cephalo_r11_r13_staging import _json_hash
from backend.services.cephalo_r14_review_receipt import _current_graph, _graph_digest, _require_clinician
from backend.services.cephalo_r13_decision_authority import resolve_r13_staging, require_committed_staging_audit

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
            return True
    return False
