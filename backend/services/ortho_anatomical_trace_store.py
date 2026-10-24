"""G5 LAB-only authenticated anatomical tracing draft/approval lifecycle.

This does NOT certify a diagnostic R14 decision. No automatic contours,
no clinical account access, and no client-injected approval/hashed source.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend import models
from backend.services.ortho_anatomical_trace import (
    CONTOUR_CONTRACT, ContourRejected, canonical_digest,
    normalize_manual_contours, verify_approved_anatomical_trace,
)
from backend.services.ortho_bilan_practitioner_notes import source_digest

LAB_IMAGE = Path(__file__).resolve().parents[1] / "static/uploads/radios/t2-cephalo-seeded.png"


def _guard() -> None:
    if not (os.environ.get("ENVIRONMENT") == "test"
            and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
            and os.environ.get("DATABASE_URL") == "sqlite:///./t2-runtime-cert.db"):
        raise HTTPException(status_code=404, detail="Laboratoire G5 indisponible")


def _dentist(actor: models.User) -> None:
    from backend.services.ortho_bilan_practitioner_notes import _dentist as role_guard
    role_guard(actor)


def _source(db: Session, *, patient_id:int, analysis_id:int,
            expected_revision:int, actor:models.User) -> tuple[Any,int,str,str]:
    _guard()
    from backend.routers.patients import _bound_cephalo_study
    from backend.services.ortho_lab_image_integrity import verified_aariz_display_image_pair
    study, revision = _bound_cephalo_study(
        patient_id,analysis_id,expected_revision,db,actor)
    if study.image_original_path != "api/static/uploads/radios/t2-cephalo-seeded.png":
        raise HTTPException(status_code=409,detail="Source G5 non autorisée dans le laboratoire")
    if not verified_aariz_display_image_pair(study.angles_data or {},LAB_IMAGE):
        raise HTTPException(status_code=409,detail="Radio Aariz et annotations non appariées")
    digest = source_digest(study)
    image_sha = sha256(LAB_IMAGE.read_bytes()).hexdigest()
    return study,revision,digest,image_sha


def _row(db:Session, *, patient_id:int,analysis_id:int,actor:models.User,
         lock:bool=False):
    q=db.query(models.OrthoAnatomicalTrace).filter(
        models.OrthoAnatomicalTrace.patient_id == patient_id,
        models.OrthoAnatomicalTrace.analysis_id == analysis_id,
        models.OrthoAnatomicalTrace.employer_id == actor.get_employer_id())
    return (q.with_for_update() if lock else q).first()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _snapshot(row: models.OrthoAnatomicalTrace | None,
              *,patient_id:int,analysis_id:int,revision:int,
              digest:str,image_sha:str) -> dict[str,Any]:
    if row is None:
        return {"draft_version":0,"contours":[],"approved":False,"stale":False,
                "analysis_revision":revision}
    is_current=(row.analysis_revision == revision
        and row.scientific_digest == digest and row.image_sha256 == image_sha)
    approved = False
    if is_current and row.approved_by is not None and row.approved_at is not None:
        metadata=_signed_payload(row,state="APPROVED")
        approved=verify_approved_anatomical_trace(
            metadata,patient_id=patient_id,analysis_id=analysis_id,
            revision=revision,scientific_digest=digest,
            image_sha256=image_sha,image_size=(row.image_width,row.image_height)
        ) is not None
    return {
        "analysis_revision":revision,
        "draft_version":row.draft_version,
        "contours":row.contours_json if is_current else [],
        "approved":approved,"stale":not is_current,
        "approved_by":row.approved_by if approved else None,
        "approved_at":row.approved_at.isoformat() if approved else None,
    }


def _signed_payload(row:models.OrthoAnatomicalTrace,*,state:str="APPROVED") -> dict:
    return {
        "contract":CONTOUR_CONTRACT,
        "state":state,
        "source_mode":"CLINICIAN_MANUAL",
        "patient_id":row.patient_id,"analysis_id":row.analysis_id,
        "analysis_revision":row.analysis_revision,
        "scientific_digest":row.scientific_digest,
        "image_sha256":row.image_sha256,
        "image_size":[row.image_width,row.image_height],
        "version":row.draft_version,
        "contour_digest":row.contour_digest,
        "contours":row.contours_json,
        "approved_by":row.approved_by,
        "approved_at":row.approved_at.isoformat() if row.approved_at else None,
        "approved_digest":row.approved_digest,
    }


def get_g5_trace(db:Session, *, patient_id:int, analysis_id:int,
                 expected_revision:int, actor:models.User) -> dict:
    _,revision,digest,image_sha=_source(
        db,patient_id=patient_id,analysis_id=analysis_id,
        expected_revision=expected_revision,actor=actor)
    row=_row(db,patient_id=patient_id,analysis_id=analysis_id,actor=actor)
    return _snapshot(row,patient_id=patient_id,analysis_id=analysis_id,
                     revision=revision,digest=digest,image_sha=image_sha)


def save_g5_manual_draft(db:Session, *,patient_id:int,analysis_id:int,
                         expected_revision:int,expected_draft_version:int,
                         contours:object,actor:models.User) -> dict:
    _guard(); _dentist(actor)
    _source(db,patient_id=patient_id,analysis_id=analysis_id,
            expected_revision=expected_revision,actor=actor)
    from backend.services.cephalo_document_lock import lock_selected_cephalo_for_archive
    lock_selected_cephalo_for_archive(
        db,patient_id=patient_id,analysis_id=analysis_id)
    _,revision,digest,image_sha=_source(
        db,patient_id=patient_id,analysis_id=analysis_id,
        expected_revision=expected_revision,actor=actor)
    try:
        normalized=normalize_manual_contours(contours,image_size=(1935,2400))
    except ContourRejected as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    row=_row(db,patient_id=patient_id,analysis_id=analysis_id,actor=actor,lock=True)
    if (row.draft_version if row else 0) != expected_draft_version:
        raise HTTPException(status_code=409,detail="Version de tracé modifiée")
    version=expected_draft_version+1
    if row is None:
        row=models.OrthoAnatomicalTrace(
            employer_id=actor.get_employer_id(),patient_id=patient_id,
            analysis_id=analysis_id,analysis_revision=revision,
            scientific_digest=digest,image_sha256=image_sha,
            image_width=1935,image_height=2400,
            draft_version=version,contours_json=[
                {"id":x["id"],"points":x["points"]}
                for x in normalized["contours"]],
            contour_digest=normalized["contour_digest"],
            drafted_by=actor.id,updated_at=_now())
        db.add(row)
    else:
        row.analysis_revision=revision
        row.scientific_digest=digest
        row.image_sha256=image_sha
        row.image_width=1935
        row.image_height=2400
        row.draft_version=version
        row.contours_json=[{"id":x["id"],"points":x["points"]}
                           for x in normalized["contours"]]
        row.contour_digest=normalized["contour_digest"]
        row.drafted_by=actor.id
        row.updated_at=_now()
        row.approved_by=None
        row.approved_at=None
        row.approved_digest=None
    db.flush()
    db.add(models.AuditLog(
        employer_id=actor.get_employer_id(),user_id=actor.id,
        action="ODF_G5_ANATOMY_DRAFT",resource_type="CephaloAnalysis",
        resource_id=str(analysis_id),severity="INFO",
        details=f"patient={patient_id};rev={revision};draft={version}",
    ))
    _source(db,patient_id=patient_id,analysis_id=analysis_id,
            expected_revision=expected_revision,actor=actor)
    db.commit()
    return get_g5_trace(db,patient_id=patient_id,analysis_id=analysis_id,
                        expected_revision=expected_revision,actor=actor)


def approve_g5_manual_trace(db:Session, *,patient_id:int,analysis_id:int,
                            expected_revision:int,expected_draft_version:int,
                            actor:models.User) -> dict:
    _guard(); _dentist(actor)
    _source(db,patient_id=patient_id,analysis_id=analysis_id,
            expected_revision=expected_revision,actor=actor)
    from backend.services.cephalo_document_lock import lock_selected_cephalo_for_archive
    lock_selected_cephalo_for_archive(
        db,patient_id=patient_id,analysis_id=analysis_id)
    _,revision,digest,image_sha=_source(
        db,patient_id=patient_id,analysis_id=analysis_id,
        expected_revision=expected_revision,actor=actor)
    row=_row(db,patient_id=patient_id,analysis_id=analysis_id,actor=actor,lock=True)
    if (row is None or row.draft_version != expected_draft_version
        or row.analysis_revision != revision or row.scientific_digest != digest
        or row.image_sha256 != image_sha):
        raise HTTPException(status_code=409,detail="Courbes ou étude périmées")
    try:
        canonical=normalize_manual_contours(
            row.contours_json,image_size=(row.image_width,row.image_height))
    except ContourRejected as exc:
        raise HTTPException(status_code=409,detail=str(exc)) from exc
    if canonical["contour_digest"]!=row.contour_digest:
        raise HTTPException(status_code=409,detail="Courbes modifiées depuis le brouillon")
    row.approved_by=actor.id
    row.approved_at=_now()
    row.approved_digest=canonical_digest([
        patient_id,analysis_id,revision,digest,image_sha,
        row.draft_version,row.contour_digest,actor.id,
    ])
    db.flush()
    db.add(models.AuditLog(
        employer_id=actor.get_employer_id(),user_id=actor.id,
        action="ODF_G5_ANATOMY_APPROVED",resource_type="CephaloAnalysis",
        resource_id=str(analysis_id),severity="INFO",
        details=f"patient={patient_id};rev={revision};draft={row.draft_version}",
    ))
    _source(db,patient_id=patient_id,analysis_id=analysis_id,
            expected_revision=expected_revision,actor=actor)
    db.commit()
    return get_g5_trace(db,patient_id=patient_id,analysis_id=analysis_id,
                        expected_revision=revision,actor=actor)


def resolve_approved_g5_trace(db:Session, *,
        study:models.CephaloAnalysis, patient_id:int,analysis_id:int,
        expected_revision:int, employer_id:int) -> dict|None:
    _guard()
    row=db.query(models.OrthoAnatomicalTrace).filter(
        models.OrthoAnatomicalTrace.patient_id==patient_id,
        models.OrthoAnatomicalTrace.analysis_id==analysis_id,
        models.OrthoAnatomicalTrace.employer_id==employer_id).first()
    if row is None or row.approved_by is None:
        return None
    dentist=db.query(models.User).filter(models.User.id==row.approved_by).first()
    if dentist is None or dentist.get_employer_id()!=employer_id:
        return None
    try:
        _dentist(dentist)
    except HTTPException:
        return None
    try:
        if not (study.id==analysis_id and study.patient_id==patient_id
                and row.analysis_revision==expected_revision
                and row.scientific_digest==source_digest(study)
                and row.image_sha256==sha256(LAB_IMAGE.read_bytes()).hexdigest()):
            return None
    except (OSError, HTTPException):
        return None
    from backend.services.ortho_lab_image_integrity import verified_aariz_display_image_pair
    if not verified_aariz_display_image_pair(study.angles_data or {},LAB_IMAGE):
        return None
    return _signed_payload(row)
