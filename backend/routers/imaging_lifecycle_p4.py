from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_imaging_p4 import ImagingTrashRecord
from backend.routers.auth import require_permission
from backend.services.audit_service import audit_service
from backend.utils.access_control import assert_patient_access


router = APIRouter()


def _trash_record(db: Session, modality: str, analysis_id: int):
    return (
        db.query(ImagingTrashRecord)
        .filter(
            ImagingTrashRecord.modality == modality,
            ImagingTrashRecord.analysis_id == analysis_id,
        )
        .first()
    )


def _move_to_trash(db: Session, current_user: models.User, modality: str, analysis):
    assert_patient_access(analysis.patient_id, current_user, db)
    record = _trash_record(db, modality, analysis.id)
    if record is None:
        record = ImagingTrashRecord(
            modality=modality,
            analysis_id=analysis.id,
            patient_id=analysis.patient_id,
            deleted_by=current_user.id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        audit_service.log(
            db=db,
            user_id=current_user.id,
            employer_id=current_user.get_employer_id(),
            action="TRASH",
            resource_type="PanoramicAnalysis" if modality == "panoramic" else "CephaloAnalysis",
            resource_id=str(analysis.id),
            details=f"patient_id={analysis.patient_id} recoverable=true file_preserved=true",
        )
    return {"status": "trashed", "id": analysis.id, "recoverable": True}


def _restore(db: Session, current_user: models.User, modality: str, analysis):
    assert_patient_access(analysis.patient_id, current_user, db)
    record = _trash_record(db, modality, analysis.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analyse absente de la corbeille.")
    db.delete(record)
    db.commit()
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="RESTORE",
        resource_type="PanoramicAnalysis" if modality == "panoramic" else "CephaloAnalysis",
        resource_id=str(analysis.id),
        details=f"patient_id={analysis.patient_id} restored=true",
    )
    return {"status": "restored", "id": analysis.id}


@router.delete("/panoramic/{analysis_id}")
def trash_panoramic(
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("panoramic")),
):
    analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analyse panoramique introuvable.")
    return _move_to_trash(db, current_user, "panoramic", analysis)


@router.post("/panoramic/{analysis_id}/restore")
def restore_panoramic(
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("panoramic")),
):
    analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analyse panoramique introuvable.")
    return _restore(db, current_user, "panoramic", analysis)


@router.get("/patients/{patient_id}/panoramic-trash")
def list_panoramic_trash(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("panoramic")),
):
    assert_patient_access(patient_id, current_user, db)
    records = (
        db.query(ImagingTrashRecord)
        .filter(
            ImagingTrashRecord.modality == "panoramic",
            ImagingTrashRecord.patient_id == patient_id,
        )
        .order_by(ImagingTrashRecord.deleted_at.desc(), ImagingTrashRecord.id.desc())
        .all()
    )
    ids = [record.analysis_id for record in records]
    analyses = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id.in_(ids)).all() if ids else []
    by_id = {analysis.id: analysis for analysis in analyses}
    rows = []
    for record in records:
        analysis = by_id.get(record.analysis_id)
        if analysis is None:
            continue
        rows.append({
            "id": analysis.id,
            "image_path": analysis.image_path,
            "detections_data": analysis.detections_data,
            "report_narrative": analysis.report_narrative,
            "created_at": analysis.created_at,
            "deleted_at": record.deleted_at,
        })
    return rows


@router.delete("/cephalo/{analysis_id}")
def trash_cephalo(
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analyse céphalométrique introuvable.")
    return _move_to_trash(db, current_user, "cephalo", analysis)


@router.post("/cephalo/{analysis_id}/restore")
def restore_cephalo(
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analyse céphalométrique introuvable.")
    return _restore(db, current_user, "cephalo", analysis)


@router.get("/patients/{patient_id}/cephalo-trash")
def list_cephalo_trash(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    assert_patient_access(patient_id, current_user, db)
    records = (
        db.query(ImagingTrashRecord)
        .filter(
            ImagingTrashRecord.modality == "cephalo",
            ImagingTrashRecord.patient_id == patient_id,
        )
        .order_by(ImagingTrashRecord.deleted_at.desc(), ImagingTrashRecord.id.desc())
        .all()
    )
    ids = [record.analysis_id for record in records]
    analyses = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id.in_(ids)).all() if ids else []
    by_id = {analysis.id: analysis for analysis in analyses}
    rows = []
    for record in records:
        analysis = by_id.get(record.analysis_id)
        if analysis is None:
            continue
        rows.append({
            "id": analysis.id,
            "image_original_path": analysis.image_original_path,
            "angles_data": analysis.angles_data,
            "created_at": analysis.created_at,
            "deleted_at": record.deleted_at,
        })
    return rows
