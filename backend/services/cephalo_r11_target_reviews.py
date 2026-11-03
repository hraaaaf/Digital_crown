"""Authenticated, per-target R11 review receipts (non-final).

R11 scientific findings and diagnoses are read exclusively from the current
study-local source-validated graph. This operation does NOT retroactively make
legacy JSON authorship server-authored. It proves the current authenticated
dentist explicitly reviewed each exact target at this graph+stage SHA.

Production clinical registries are still EMPTY, so no real clinical approval.
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from backend import models
from backend.schemas.cephalo_evidence import ReviewState, ValidationAction
from backend.services.cephalo_r11_r13_staging import _json_hash
from backend.services.cephalo_r13_decision_authority import (
    require_committed_staging_audit, resolve_r13_staging,
)
from backend.services.cephalo_r14_review_receipt import (
    _current_graph, _graph_digest, _require_clinician,
)

R11_TARGET_ACTION = "CEPH_R11_TARGET_REVIEWED"
R11_TARGET_CONTRACT = "CEPH_R11_TARGET_REVIEW_V1"


class R11TargetReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: StrictInt = Field(gt=0)
    expected_staging_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_type: Literal["finding", "diagnosis"]
    target_id: str = Field(min_length=1, max_length=255)
    action: Literal["CONFIRM_R11_TARGET_REVIEW"]


def target_bindings(r13, actor_id: int) -> list[dict]:
    """Exact R11 snapshot targets + evidence digests; reject legacy spoofed actor."""
    graph = r13.r12_snapshot.diagnostic_graph
    expected = f"clinician:{actor_id}"
    latest = {}
    for validation in graph.validations:
        if validation.target_type != "finding":
            continue
        prev = latest.get(validation.target_id)
        if prev is None or validation.validated_at > prev.validated_at:
            latest[validation.target_id] = validation
        elif prev.validated_at == validation.validated_at and prev.validation_id != validation.validation_id:
            raise HTTPException(status_code=409, detail="Revue R11 ambiguë.")

    if not graph.findings or not graph.diagnoses:
        raise HTTPException(status_code=409, detail="Preuves R11 absentes.")
    targets = []
    for finding in graph.findings:
        validated = latest.get(finding.finding_id)
        if (validated is None or validated.action not in {ValidationAction.ACCEPT, ValidationAction.EDIT}
                or validated.clinician_id != expected):
            raise HTTPException(status_code=409, detail="Constat R11 non attribuable.")
        targets.append({
            "target_type": "finding",
            "target_id": finding.finding_id,
            "target_sha256": _json_hash(finding.model_dump(mode="json")),
            "upstream_validation_sha256": _json_hash(validated.model_dump(mode="json")),
        })
    for diagnosis in graph.diagnoses:
        if (diagnosis.state not in {ReviewState.ACCEPTED, ReviewState.EDITED}
                or diagnosis.clinician_id != expected
                or diagnosis.clinician_validated_at is None):
            raise HTTPException(status_code=409, detail="Diagnostic R11 non attribuable.")
        targets.append({
            "target_type": "diagnosis",
            "target_id": diagnosis.diagnosis_id,
            "target_sha256": _json_hash(diagnosis.model_dump(mode="json")),
            "upstream_validation_sha256": None,
        })
    keys = [(item["target_type"], item["target_id"]) for item in targets]
    if len(set(keys)) != len(keys):
        raise HTTPException(status_code=409, detail="Cibles R11 dupliquées.")
    return sorted(targets, key=lambda item: (item["target_type"], item["target_id"]))


def _audit_rows(*, db, analysis, tenant_id):
    return (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.action == R11_TARGET_ACTION,
            models.AuditLog.resource_type == "CephaloAnalysis",
            models.AuditLog.resource_id == str(analysis.id),
            models.AuditLog.employer_id == tenant_id,
        )
        .order_by(models.AuditLog.id.asc()).all()
    )


def verified_target_review_receipts(
    *, patient_id, analysis, tenant_id, revision, graph_sha256,
    staging_sha256, actor_id, r13, db,
) -> list[dict] | None:
    """Require exactly one server-authored audit for EVERY R11 target.

    Match the current source snapshot, not a client-provided reviewed flag.
    Duplicate audit rows or missing rows fail closed.
    """
    try:
        bindings = target_bindings(r13, actor_id)
    except (HTTPException, ValueError):
        return None
    expected = {(item["target_type"], item["target_id"]): item for item in bindings}
    claimed = {}
    for row in _audit_rows(db=db, analysis=analysis, tenant_id=tenant_id):
        try:
            data = json.loads(row.details)
            if not isinstance(data, dict):
                continue
            if (
                data.get("contract") != R11_TARGET_CONTRACT
                or data.get("patient_id") != patient_id
                or data.get("analysis_id") != analysis.id
                or type(data.get("analysis_revision")) is not int
                or data.get("analysis_revision") != revision
                or data.get("graph_sha256") != graph_sha256
                or data.get("staging_sha256") != staging_sha256
            ):
                continue
            key = (data.get("target_type"), data.get("target_id"))
            target = expected.get(key)
            if target is None:
                continue
            if key in claimed:
                return None
            if not (
                data.get("action") == "CONFIRM_R11_TARGET_REVIEW"
                and data.get("actor_user_id") == row.user_id == actor_id
                and data.get("target_sha256") == target["target_sha256"]
                and data.get("upstream_validation_sha256") == target["upstream_validation_sha256"]
                and isinstance(data.get("reviewed_at"), str)
                and data["reviewed_at"]
                and data.get("clinical_validation_available") is False
            ):
                return None
            claimed[key] = {"target_type": key[0], "target_id": key[1],
                            "audit_id": row.id, "target_sha256": target["target_sha256"]}
        except (TypeError, ValueError, KeyError):
            return None
    if set(claimed) != set(expected):
        return None
    return [claimed[key] for key in sorted(claimed)]


def record_r11_target_review(*, patient_id, analysis, actor,
                             request: R11TargetReviewRequest, db):
    actor_id = _require_clinician(actor)
    if analysis.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Analyse hors patient.")
    graph, revision = _current_graph(analysis)
    if revision != request.expected_revision:
        raise HTTPException(status_code=409, detail="Révision scientifique périmée.")
    staged, r13 = resolve_r13_staging(patient_id=patient_id, analysis=analysis)
    if staged["content_sha256"] != request.expected_staging_sha256:
        raise HTTPException(status_code=409, detail="Snapshot clinique R11 modifié.")
    if r13.option_validations:
        raise HTTPException(status_code=409, detail="Revue R11 requise avant décision R13.")
    if staged["actor_user_id"] != actor_id:
        raise HTTPException(status_code=403, detail="Staging R11/R12 par un autre praticien.")
    require_committed_staging_audit(db=db, analysis=analysis, staged=staged, actor=actor)
    binding = next(
        (item for item in target_bindings(r13, actor_id)
         if item["target_type"] == request.target_type and item["target_id"] == request.target_id),
        None,
    )
    if binding is None:
        raise HTTPException(status_code=404, detail="Cible R11 absente.")
    tenant = actor.get_employer_id()
    sha = _graph_digest(graph)
    for row in _audit_rows(db=db, analysis=analysis, tenant_id=tenant):
        try:
            claim = json.loads(row.details)
            if (
                claim.get("contract") == R11_TARGET_CONTRACT
                and claim.get("patient_id") == patient_id
                and claim.get("analysis_id") == analysis.id
                and claim.get("analysis_revision") == revision
                and claim.get("graph_sha256") == sha
                and claim.get("staging_sha256") == staged["content_sha256"]
                and claim.get("target_type") == request.target_type
                and claim.get("target_id") == request.target_id
            ):
                raise HTTPException(status_code=409, detail="Revue R11 déjà émise.")
        except (TypeError, ValueError):
            continue
    current_graph, current_revision = _current_graph(analysis)
    if current_revision != revision or _graph_digest(current_graph) != sha:
        raise HTTPException(status_code=409, detail="Graphe scientifique modifié.")
    claim = {
        **binding,
        "contract": R11_TARGET_CONTRACT,
        "patient_id": patient_id,
        "analysis_id": analysis.id,
        "analysis_revision": revision,
        "graph_sha256": sha,
        "staging_sha256": staged["content_sha256"],
        "actor_user_id": actor_id,
        "reviewed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "action": request.action,
        "clinical_validation_available": False,
    }
    entry = models.AuditLog(
        user_id=actor_id, employer_id=tenant,
        action=R11_TARGET_ACTION,
        resource_type="CephaloAnalysis", resource_id=str(analysis.id), severity="INFO",
        details=json.dumps(claim, sort_keys=True, ensure_ascii=True),
    )
    db.add(entry)
    try:
        db.commit()
        db.refresh(entry)
    except Exception:
        db.rollback()
        raise
    return {
        "state": "R11_TARGET_REVIEWED_NON_FINAL",
        "audit_id": entry.id,
        "target_type": request.target_type,
        "target_id": request.target_id,
        "clinical_validation_available": False,
    }
