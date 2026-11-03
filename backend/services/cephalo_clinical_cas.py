"""Compare-and-swap for local Céphalo clinical JSON writes.

Cross-dialect JSON path comparisons (SQLite JSON1 and PostgreSQL JSON).
An old SQLAlchemy Session must not overwrite a newer clinical decision.
This does NOT certify writers that bypass this helper or SQLite/PG races
not exercised by integration tests.
"""
from __future__ import annotations

from typing import Any
from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from backend import models
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.services.cephalo_r11_r13_staging import STAGING_KEY

R14_KEY = "_cephalo_r14_final_decision_v1"


def _stored_digest(angles_data: dict, key: str) -> str | None:
    value = angles_data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise HTTPException(status_code=409, detail="Etat clinique existant non reconnu.")
    digest = value.get("content_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise HTTPException(status_code=409, detail="Empreinte clinique existante invalide.")
    return digest


def cas_replace_clinical_json(
    *, db: Session, analysis: models.CephaloAnalysis, patient_id: int,
    expected_revision: int, expected_stage_sha: str | None,
    replacement: dict[str, Any],
) -> None:
    """Update study JSON only if the currently stored study still has these keys.

    SQL UPDATE checks the current DB row, rather than an ORM-cached object.
    Caller commits the corresponding AuditLog within the SAME transaction.
    """
    old = analysis.angles_data
    if not isinstance(old, dict) or analysis.patient_id != patient_id:
        raise HTTPException(status_code=409, detail="Analyse clinique invalide.")
    expected_r14_sha = _stored_digest(old, R14_KEY)
    stored_stage_sha = _stored_digest(old, STAGING_KEY)
    if stored_stage_sha != expected_stage_sha:
        raise HTTPException(status_code=409, detail="Snapshot clinique périmé.")

    stage_expr = models.CephaloAnalysis.angles_data[STAGING_KEY]["content_sha256"].as_string()
    final_expr = models.CephaloAnalysis.angles_data[R14_KEY]["content_sha256"].as_string()
    statement = (
        update(models.CephaloAnalysis)
        .where(
            models.CephaloAnalysis.id == analysis.id,
            models.CephaloAnalysis.patient_id == patient_id,
            models.CephaloAnalysis.angles_data[EVIDENCE_GRAPH_KEY]["revision"].as_integer()
            == expected_revision,
        )
        .where(
            stage_expr.is_(None) if expected_stage_sha is None
            else stage_expr == expected_stage_sha
        )
        .where(
            final_expr.is_(None) if expected_r14_sha is None
            else final_expr == expected_r14_sha
        )
        .values(angles_data=replacement)
        .execution_options(synchronize_session=False)
    )
    result = db.execute(statement)
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflit concurrent : l'analyse a changé, relire avant de décider.",
        )
    # Avoid later ORM flush of a previously loaded JSON blob.
    db.expire(analysis, ["angles_data"])
