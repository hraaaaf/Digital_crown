"""Content-addressed identity of a persisted cephalometric study; not a clinical revision."""
from __future__ import annotations
import hashlib
import hmac
import json
from pathlib import PurePath
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend import models
from backend.utils.access_control import assert_patient_access

def analysis_source_revision(analysis: models.CephaloAnalysis) -> str:
    state = {
        "patient_id": analysis.patient_id, "analysis_id": analysis.id,
        "image_original_path": analysis.image_original_path,
        "landmarks_data": analysis.landmarks_data, "angles_data": analysis.angles_data,
        "is_calibrated": analysis.is_calibrated, "mm_per_pixel": analysis.mm_per_pixel,
        "calibration_data": analysis.calibration_data,
    }
    value = json.dumps(state, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(value).hexdigest()

def resolve_document_analysis(db: Session, *, patient_id: int, analysis_id: int,
                              source_revision: str, current_user: models.User) -> models.CephaloAnalysis:
    assert_patient_access(patient_id, current_user, db)
    analysis = (db.query(models.CephaloAnalysis)
                .filter(models.CephaloAnalysis.id == analysis_id,
                        models.CephaloAnalysis.patient_id == patient_id)
                .with_for_update().first())
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analyse introuvable dans ce dossier")
    if not hmac.compare_digest(analysis_source_revision(analysis), source_revision):
        raise HTTPException(status_code=409, detail="Révision céphalométrique périmée : rechargez l'étude avant export")
    return analysis

def cephalo_document_identity(analysis: models.CephaloAnalysis) -> dict:
    ref = str(analysis.image_original_path or "")
    return {
        "patient_id": analysis.patient_id, "analysis_id": analysis.id,
        "source_revision": analysis_source_revision(analysis),
        "study_reference_sha256": hashlib.sha256(ref.encode("utf-8")).hexdigest(),
        "study_filename": PurePath(ref.replace("\\", "/")).name,
    }
