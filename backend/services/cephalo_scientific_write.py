"""Guard every typed scientific graph transition before committing study-local JSON.

Only one SQL UPDATE may replace a loaded study when the DB still holds the
same graph revision and clinician stage/final digests. This does not replace
clinical rule review, nor ensure safety from external/legacy SQL writers.
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from backend import models
from backend.services.cephalo_clinical_cas import STAGING_KEY, R14_KEY, _stored_digest
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def _revision(graph: object) -> int:
    value = graph.get("revision") if isinstance(graph, dict) else None
    if type(value) is not int or value <= 0:
        raise HTTPException(status_code=409, detail="Révision scientifique invalide.")
    return value


def guard_scientific_payload(*, previous: dict, updated: dict) -> dict:
    """No dropped clinical receipts or unversioned scientific mutation."""
    prior = previous.get(EVIDENCE_GRAPH_KEY)
    new = updated.get(EVIDENCE_GRAPH_KEY)
    if not isinstance(prior, dict):
        if new is not None and not isinstance(new, dict):
            raise HTTPException(status_code=409, detail="Graphe scientifique non typé.")
        if isinstance(new, dict):
            _revision(new)
        return updated
    old_revision = _revision(prior)
    if not isinstance(new, dict):
        raise HTTPException(status_code=409, detail="Graphe scientifique supprimé.")
    next_revision = _revision(new)
    if prior.get("case_id") != new.get("case_id"):
        raise HTTPException(status_code=409, detail="Identité du cas scientifique modifiée.")
    if new != prior and next_revision != old_revision + 1:
        raise HTTPException(
            status_code=409,
            detail="Toute modification scientifique doit créer exactement la révision suivante.",
        )
    if new == prior and next_revision != old_revision:
        raise HTTPException(status_code=409, detail="Révision scientifique incohérente.")
    protected = dict(updated)
    for key in (STAGING_KEY, R14_KEY):
        if key in previous:
            # Preserve historically signed work even though the next science
            # revision will make it STALE at read time.
            protected[key] = previous[key]
        else:
            protected.pop(key, None)
    return protected


def save_scientific_transition(
    *, db: Session, analysis: models.CephaloAnalysis, updated_angles: dict,
    other_values: dict[str, Any] | None = None,
) -> None:
    previous = analysis.angles_data
    if not isinstance(previous, dict):
        raise HTTPException(status_code=409, detail="Analyse scientifique illisible.")
    updated = guard_scientific_payload(previous=previous, updated=updated_angles)
    old = previous.get(EVIDENCE_GRAPH_KEY)
    if not isinstance(old, dict):
        raise HTTPException(status_code=409, detail="Graphe scientifique initial absent.")
    old_revision = _revision(old)
    stage_sha = _stored_digest(previous, STAGING_KEY)
    r14_sha = _stored_digest(previous, R14_KEY)

    stage_expr = models.CephaloAnalysis.angles_data[STAGING_KEY]["content_sha256"].as_string()
    r14_expr = models.CephaloAnalysis.angles_data[R14_KEY]["content_sha256"].as_string()
    statement = (
        update(models.CephaloAnalysis)
        .where(
            models.CephaloAnalysis.id == analysis.id,
            models.CephaloAnalysis.patient_id == analysis.patient_id,
            models.CephaloAnalysis.angles_data[EVIDENCE_GRAPH_KEY]["revision"].as_integer()
            == old_revision,
        )
        .where(stage_expr.is_(None) if stage_sha is None else stage_expr == stage_sha)
        .where(r14_expr.is_(None) if r14_sha is None else r14_expr == r14_sha)
        .values(angles_data=updated, **(other_values or {}))
        .execution_options(synchronize_session=False)
    )
    result = db.execute(statement)
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflit concurrent sur la révision scientifique ; rechargez l'étude.",
        )
    db.expire(analysis)
