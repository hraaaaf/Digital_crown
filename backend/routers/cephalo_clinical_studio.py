from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.services.cephalo_r15_clinical_studio import build_r15_clinical_studio_snapshot
from backend.services.cephalo_r11_r13_staging import (
    R11R13StagingRequest,
    read_staged_clinical_evidence,
    stage_clinical_evidence,
)
from backend.services.cephalo_r14_review_receipt import (
    CephaloBlockerReviewRequest,
    read_blocker_review_receipts,
    save_blocker_review_receipt,
)
from backend.utils.access_control import assert_patient_access

router = APIRouter()


@router.get("/{patient_id}/cephalo-clinical-studio")
def get_cephalo_clinical_studio(
    patient_id: int,
    analysis_id: int | None = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")

    analysis_query = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id)
    if analysis_id is not None:
        analysis = analysis_query.filter(models.CephaloAnalysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse céphalométrique introuvable pour ce patient")
    else:
        analysis = (
            analysis_query
            .order_by(models.CephaloAnalysis.created_at.desc(), models.CephaloAnalysis.id.desc())
            .first()
        )

    return build_r15_clinical_studio_snapshot(
        patient_id=patient_id,
        analysis_id=analysis.id if analysis else None,
        angles_data=analysis.angles_data if analysis else None,
    )


def _bound_review_analysis(patient_id: int, analysis_id: int, current_user: models.User, db: Session, *, lock: bool = False):
    # Patient ownership must be checked BEFORE an analysis query, including GET.
    assert_patient_access(patient_id, current_user, db)
    query = (
        db.query(models.CephaloAnalysis)
        .filter(models.CephaloAnalysis.patient_id == patient_id, models.CephaloAnalysis.id == analysis_id)
    )
    # The staged scientific JSON must not overwrite a concurrent revision.
    analysis = (query.with_for_update() if lock else query).first()
    if not analysis or analysis.patient_id != patient_id or analysis.id != analysis_id:
        raise HTTPException(status_code=404, detail="Analyse céphalométrique introuvable pour ce patient")
    return analysis


@router.post("/{patient_id}/cephalo-clinical-studio/{analysis_id}/blocker-reviews", status_code=201)
def acknowledge_r14_blockers(
    patient_id: int,
    analysis_id: int,
    body: CephaloBlockerReviewRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Audit a dentist reading the R11–R14 clinical blockers. Never sign a case."""
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db)
    return save_blocker_review_receipt(
        patient_id=patient_id, analysis=analysis, actor=current_user, request=body, db=db
    )


@router.get("/{patient_id}/cephalo-clinical-studio/{analysis_id}/blocker-reviews")
def get_r14_blocker_receipts(
    patient_id: int,
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db)
    return read_blocker_review_receipts(patient_id=patient_id, analysis=analysis, db=db)


@router.post("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r11-r13-staging", status_code=201)
def stage_r11_r13_clinical_snapshot(
    patient_id: int,
    analysis_id: int,
    body: R11R13StagingRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Store non-final source-validated data; never select R13 or sign R14."""
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db, lock=True)
    return stage_clinical_evidence(
        patient_id=patient_id, analysis=analysis, actor=current_user, body=body, db=db,
    )


@router.get("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r11-r13-staging")
def get_r11_r13_clinical_snapshot(
    patient_id: int,
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db)
    return read_staged_clinical_evidence(patient_id=patient_id, analysis=analysis)
