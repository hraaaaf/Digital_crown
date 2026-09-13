from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.services.cephalo_r15_clinical_studio import build_r15_clinical_studio_snapshot
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
