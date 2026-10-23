"""Cabinet-local orthodontic practitioner notes, explicit approval and export read.

Clinical notes approval is NOT R14 diagnostic/therapeutic-scientific validation.
No client payload or historical ai_diagnostic is trusted by the PDF renderer.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend import models
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY

ALLOWED_CASTS = frozenset({
    "classe_molaire_droite", "classe_molaire_gauche",
    "classe_canine_droite", "classe_canine_gauche", "forme_arcade",
    "ddm_maxillaire", "ddm_mandibulaire", "commentaire",
})


def _digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def source_digest(analysis: models.CephaloAnalysis) -> str:
    """Read-only entire persisted scientific source: edits invalidate approval."""
    data = analysis.angles_data
    if not isinstance(data, dict) or not isinstance(data.get(EVIDENCE_GRAPH_KEY), dict):
        raise HTTPException(status_code=409, detail="Étude scientifique active absente")
    return _digest(data)


def _dentist(actor: models.User) -> None:
    role = getattr(actor.role, "value", actor.role)
    if (role != "DENTISTE" or not actor.is_active
        or getattr(actor, "is_suspended", False)
        or getattr(actor, "is_archived", False)):
        raise HTTPException(status_code=403, detail="Validation réservée à un dentiste actif")


def _notes(casts: Mapping[str, Any], summary: str, plan: str) -> dict[str, Any]:
    if not isinstance(casts, dict) or set(casts).difference(ALLOWED_CASTS):
        raise HTTPException(status_code=422, detail="Champs de moulages non reconnus")
    cleaned = {}
    for k, v in casts.items():
        if isinstance(v, str):
            if len(v) > 1500:
                raise HTTPException(status_code=422, detail="Observation trop longue")
            cleaned[k] = v.strip()
        elif k.startswith("ddm_") and isinstance(v, (float,int)) and not isinstance(v, bool):
            from math import isfinite
            if not isfinite(v) or abs(v) > 100:
                raise HTTPException(status_code=422, detail="DDM invalide")
            cleaned[k] = float(v)
        else:
            raise HTTPException(status_code=422, detail="Type d'observation non pris en charge")
    if len(summary) > 10000 or len(plan) > 10000:
        raise HTTPException(status_code=422, detail="Note trop longue")
    return {"moulages": cleaned, "resume_diagnostique": summary.strip(),
            "plan_traitement": plan.strip()}


def _row(db: Session, patient_id: int, analysis_id: int, employer_id: int,
         lock: bool=False):
    q = db.query(models.OrthoBilanPractitionerNote).filter(
        models.OrthoBilanPractitionerNote.patient_id == patient_id,
        models.OrthoBilanPractitionerNote.analysis_id == analysis_id,
        models.OrthoBilanPractitionerNote.employer_id == employer_id)
    if lock:
        q=q.with_for_update()
    return q.first()


def _get_current(db: Session, patient_id: int, analysis_id: int, expected_revision: int,
                 actor: models.User, *, lock=False):
    """Reuse the existing source lock, access check and typed evidence chain."""
    from backend.routers.patients import _bound_cephalo_study
    study, revision = _bound_cephalo_study(
        patient_id, analysis_id, expected_revision, db, actor)
    return study, revision, source_digest(study)


def get_practitioner_note(db: Session, *, patient_id: int, analysis_id: int,
                          expected_revision: int, actor: models.User) -> dict:
    study, revision, digest = _get_current(
        db, patient_id, analysis_id, expected_revision, actor)
    row = _row(db,patient_id,analysis_id,actor.get_employer_id())
    if row is None:
        return {"analysis_id":analysis_id,"analysis_revision":revision,
                "draft_version":0,"notes":_notes({},"",""),
                "approved":False,"stale":False}
    current = row.analysis_revision == revision and row.study_digest == digest
    approved = current and row.approved_by is not None and row.approved_at is not None and (
        row.approved_digest == _digest([row.notes_json,row.study_digest,row.draft_version,row.approved_by]))
    return {"analysis_id":analysis_id,"analysis_revision":revision,
            "draft_version":row.draft_version,"notes":row.notes_json if current else _notes({},"",""),
            "approved":bool(approved),"stale":not current,
            "approved_by":row.approved_by if approved else None,
            "approved_at":row.approved_at.isoformat() if approved else None}


def save_practitioner_draft(db: Session, *, patient_id:int, analysis_id:int,
                            expected_revision:int, expected_draft_version:int,
                            casts:Mapping[str,Any], summary:str, plan:str,
                            actor:models.User) -> dict:
    _dentist(actor)
    # Use the same serialization point as PDF archives and landmark edits:
    # PostgreSQL SELECT FOR UPDATE / SQLite writer intent, then fresh read.
    from backend.services.cephalo_document_lock import lock_selected_cephalo_for_archive
    lock_selected_cephalo_for_archive(db, patient_id=patient_id, analysis_id=analysis_id)
    study, revision, digest=_get_current(db,patient_id,analysis_id,expected_revision,actor)
    notes=_notes(casts,summary,plan)
    row=_row(db,patient_id,analysis_id,actor.get_employer_id(),lock=True)
    current_version=row.draft_version if row else 0
    if current_version != expected_draft_version:
        raise HTTPException(status_code=409,detail="Brouillon modifié : rechargez les notes")
    if row is None:
        row=models.OrthoBilanPractitionerNote(
            employer_id=actor.get_employer_id(),patient_id=patient_id,
            analysis_id=analysis_id,analysis_revision=revision,
            study_digest=digest,draft_version=1,notes_json=notes,drafted_by=actor.id,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None))
        db.add(row)
    else:
        row.analysis_revision=revision
        row.study_digest=digest
        row.notes_json=notes
        row.drafted_by=actor.id
        row.draft_version=current_version+1
        row.approved_by=None
        row.approved_at=None
        row.approved_digest=None
        row.updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    db.flush()
    # Atomic audit: an approval/draft commit must not succeed without the
    # corresponding durable trace. Store IDs only, never patient narrative.
    db.add(models.AuditLog(
        employer_id=actor.get_employer_id(), user_id=actor.id,
        action="ORTHO_BILAN_DRAFT_SAVED", resource_type="CephaloAnalysis",
        resource_id=str(analysis_id),
        severity="INFO", details=f"patient={patient_id};revision={revision};draft={row.draft_version}",
    ))
    # Repeat source check BEFORE commit to reduce stale-scientific-source race.
    _get_current(db,patient_id,analysis_id,expected_revision,actor)
    db.commit()
    return get_practitioner_note(db,patient_id=patient_id,
                                 analysis_id=analysis_id,expected_revision=revision,actor=actor)


def approve_practitioner_draft(db: Session, *, patient_id:int, analysis_id:int,
                               expected_revision:int, expected_draft_version:int,
                               actor:models.User) -> dict:
    _dentist(actor)
    from backend.services.cephalo_document_lock import lock_selected_cephalo_for_archive
    lock_selected_cephalo_for_archive(db, patient_id=patient_id, analysis_id=analysis_id)
    study,revision,digest=_get_current(db,patient_id,analysis_id,expected_revision,actor)
    row=_row(db,patient_id,analysis_id,actor.get_employer_id(),lock=True)
    if row is None or row.draft_version != expected_draft_version or (
        row.analysis_revision != revision or row.study_digest != digest):
        raise HTTPException(status_code=409,detail="Brouillon ou étude périmée")
    if not any(bool(v) for v in (
        row.notes_json.get("moulages"),row.notes_json.get("resume_diagnostique"),
        row.notes_json.get("plan_traitement"))):
        raise HTTPException(status_code=422,detail="Aucune observation à approuver")
    row.approved_by=actor.id
    row.approved_at=datetime.now(timezone.utc).replace(tzinfo=None)
    row.approved_digest=_digest([row.notes_json,digest,row.draft_version,actor.id])
    db.flush()
    db.add(models.AuditLog(
        employer_id=actor.get_employer_id(), user_id=actor.id,
        action="ORTHO_BILAN_NOTES_APPROVED", resource_type="CephaloAnalysis",
        resource_id=str(analysis_id),
        severity="INFO", details=f"patient={patient_id};revision={revision};draft={row.draft_version}",
    ))
    _get_current(db,patient_id,analysis_id,expected_revision,actor)
    db.commit()
    return get_practitioner_note(db,patient_id=patient_id,
                                 analysis_id=analysis_id,expected_revision=revision,actor=actor)


def resolve_approved_practitioner_sections(
    db: Session, *, patient_id:int, analysis_id:int, expected_revision:int,
    study_data: Mapping[str,Any], employer_id:int,
) -> dict[str,Any] | None:
    """Only from a DB row matching authorized study and its persisted digest.

    The caller must have performed _bound_cephalo_study with an authenticated
    actor. This read cannot enable R14 clinical_validation_available.
    """
    from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
    if not isinstance(study_data, dict) or not isinstance(study_data.get(EVIDENCE_GRAPH_KEY),dict):
        return None
    row=_row(db,patient_id,analysis_id,employer_id)
    if row is None or row.approved_by is None or row.approved_at is None:
        return None
    if row.analysis_revision != expected_revision or row.study_digest != _digest(study_data):
        return None
    if row.approved_digest != _digest([row.notes_json,row.study_digest,row.draft_version,row.approved_by]):
        return None
    actor=db.query(models.User).filter(models.User.id==row.approved_by).first()
    if actor is None or actor.get_employer_id()!=employer_id:
        return None
    try:
        _dentist(actor)
    except HTTPException:
        return None
    return {
        "contract_version":"ORTHO_PRACTITIONER_APPROVED_V1",
        "validation_state":"APPROVED",
        "patient_id":patient_id,"analysis_id":analysis_id,
        "analysis_revision":expected_revision,
        "practitioner_id":row.approved_by,
        "validated_at":row.approved_at.isoformat(),
        **dict(row.notes_json or {}),
    }
