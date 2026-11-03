"""Audited *non-final* clinician review receipts for the Céphalo R11–R14 hold.

This is NOT a substitute for scientific R11–R13 snapshots or for an R14
ClinicianValidationEvidence. The source registries are empty in production.
Receipts record that the authenticated dentist inspected the current blockers;
they never confer diagnostic, therapeutic, PDF COMPLETE or SIGNED authority.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any, Literal, Mapping

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from sqlalchemy.orm import Session

from backend import models
from backend.services.cephalo_r15_clinical_studio import build_r15_clinical_studio_snapshot
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


REVIEW_ACTION = "CEPH_R14_BLOCKERS_ACKNOWLEDGED"
REVIEW_CONTRACT = "CEPH_R14_REVIEW_RECEIPT_V1"


class CephaloBlockerReviewRequest(BaseModel):
    """No client-supplied clinician, diagnosis, option, signature or approval."""
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: StrictInt = Field(gt=0)
    action: Literal["ACKNOWLEDGE_BLOCKERS"]


def _current_graph(analysis: models.CephaloAnalysis) -> tuple[dict[str, Any], int]:
    data = analysis.angles_data if isinstance(analysis.angles_data, dict) else {}
    graph = data.get(EVIDENCE_GRAPH_KEY)
    if not isinstance(graph, dict):
        raise HTTPException(status_code=409, detail="Graphe scientifique typé absent.")
    revision = graph.get("revision")
    if type(revision) is not int or revision <= 0:
        raise HTTPException(status_code=409, detail="Révision scientifique non vérifiée.")
    return graph, revision


def _graph_digest(graph: Mapping[str, Any]) -> str:
    canonical = json.dumps(graph, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_clinician(actor: models.User) -> int:
    role = getattr(actor, "role", None)
    role = getattr(role, "value", role)
    actor_id = getattr(actor, "id", None)
    if (
        role != models.UserRole.DENTISTE.value
        or getattr(actor, "is_active", False) is not True
        or type(actor_id) is not int or actor_id <= 0
        or (getattr(actor, "employer_id", None) is not None
            and getattr(actor, "approval_status", None) != "approved")
    ):
        raise HTTPException(status_code=403, detail="Praticien authentifié et actif requis.")
    return actor_id


def save_blocker_review_receipt(
    *,
    patient_id: int,
    analysis: models.CephaloAnalysis,
    actor: models.User,
    request: CephaloBlockerReviewRequest,
    db: Session,
) -> dict[str, Any]:
    """Persist an informational clinician receipt, never an R14 approval."""
    actor_id = _require_clinician(actor)
    if analysis.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Analyse absente pour ce patient.")

    graph, revision = _current_graph(analysis)
    if request.expected_revision != revision:
        raise HTTPException(status_code=409, detail="Révision de l'analyse périmée.")

    try:
        fingerprint = _graph_digest(graph)
    except (TypeError, ValueError, OverflowError) as exc:
        raise HTTPException(status_code=409, detail="Preuve scientifique incohérente.") from exc

    studio = build_r15_clinical_studio_snapshot(
        patient_id=patient_id, analysis_id=analysis.id, angles_data=analysis.angles_data
    )
    blockers = studio.get("blocking_gates")
    if (
        not isinstance(blockers, list)
        or not blockers
        or any(not isinstance(item, str) or not item for item in blockers)
        or studio.get("clinical_validation_available") is not False
    ):
        raise HTTPException(status_code=409, detail="État clinique incompatible avec un accusé de blocage.")

    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    details = {
        "contract": REVIEW_CONTRACT,
        "status": "REVIEWED_BUT_CLINICALLY_BLOCKED",
        "patient_id": patient_id,
        "analysis_id": analysis.id,
        "analysis_revision": revision,
        "graph_sha256": fingerprint,
        "actor_user_id": actor_id,
        "reviewed_at": timestamp,
        "blocking_gates": sorted(set(blockers)),
        "clinical_validation_available": False,
    }
    entry = models.AuditLog(
        user_id=actor_id,
        employer_id=actor.get_employer_id(),
        action=REVIEW_ACTION,
        resource_type="CephaloAnalysis",
        resource_id=str(analysis.id),
        severity="INFO",
        details=json.dumps(details, sort_keys=True, ensure_ascii=True),
    )
    db.add(entry)
    try:
        db.commit()
        db.refresh(entry)
    except Exception:
        db.rollback()
        raise
    return {"receipt_id": entry.id, **details}


def project_receipt_currency(receipt: Mapping[str, Any], *, graph: Mapping[str, Any]) -> str:
    """Read-time invalidation; no stale receipt can be treated as a current signoff."""
    try:
        expected_hash = receipt.get("graph_sha256")
        if (
            receipt.get("contract") != REVIEW_CONTRACT
            or receipt.get("status") != "REVIEWED_BUT_CLINICALLY_BLOCKED"
            or receipt.get("clinical_validation_available") is not False
            or type(receipt.get("analysis_revision")) is not int
            or type(graph.get("revision")) is not int
            or receipt["analysis_revision"] != graph["revision"]
            or not isinstance(expected_hash, str)
            or expected_hash != _graph_digest(graph)
        ):
            return "STALE"
    except (TypeError, ValueError, OverflowError, KeyError):
        return "STALE"
    return "CURRENT_BLOCKED"


def read_blocker_review_receipts(
    *,
    patient_id: int,
    analysis: models.CephaloAnalysis,
    db: Session,
) -> list[dict[str, Any]]:
    """Read only tenant-/patient-bound audit rows; never infer clinical authority."""
    graph, _revision = _current_graph(analysis)
    rows = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.resource_type == "CephaloAnalysis",
            models.AuditLog.resource_id == str(analysis.id),
            models.AuditLog.action == REVIEW_ACTION,
        )
        .order_by(models.AuditLog.id.desc())
        .limit(20)
        .all()
    )
    out = []
    for row in rows:
        try:
            receipt = json.loads(row.details)
            if not isinstance(receipt, dict):
                continue
            if (receipt.get("patient_id") != patient_id
                or receipt.get("analysis_id") != analysis.id
                or receipt.get("actor_user_id") != row.user_id
                or receipt.get("contract") != REVIEW_CONTRACT):
                continue
            out.append({
                "receipt_id": row.id,
                "status": receipt["status"],
                "currency": project_receipt_currency(receipt, graph=graph),
                "analysis_revision": receipt["analysis_revision"],
                "reviewed_at": receipt["reviewed_at"],
                "actor_user_id": row.user_id,
                "blocking_gates": receipt["blocking_gates"],
                "clinical_validation_available": False,
            })
        except (TypeError, ValueError, KeyError):
            continue
    return out
