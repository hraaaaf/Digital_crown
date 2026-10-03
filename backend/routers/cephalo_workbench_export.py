"""LOT07-G Orthodontic Workbench canonical export route."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.services.ortho_workbench_export import (
    OrthoWorkbenchExportError,
    OrthoWorkbenchExportRequest,
    build_ortho_workbench_export,
)
from backend.utils.access_control import assert_patient_access


router = APIRouter()


@router.post("/analyses/{analysis_id}/ortho-workbench-export")
def export_ortho_workbench(
    analysis_id: int,
    request: OrthoWorkbenchExportRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = (
        db.query(models.CephaloAnalysis)
        .filter(models.CephaloAnalysis.id == analysis_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)

    try:
        return build_ortho_workbench_export(
            db,
            analysis=analysis,
            employer_id=current_user.get_employer_id(),
            request=request,
        )
    except OrthoWorkbenchExportError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Export orthodontique bloqué: {exc}",
        ) from exc
