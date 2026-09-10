"""Canonical cephalometric analysis GET with typed scientific read authority."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.routers.auth import require_permission
from backend.services.cephalo_typed_read import CephaloTypedReadError, project_typed_craniom_read_path
from backend.utils.access_control import assert_patient_access

router = APIRouter()


@router.get("/analyses/{analysis_id}", response_model=schemas.CephaloAnalysisOut)
def get_analysis_with_typed_read_path(
    analysis_id: int,
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

    out = schemas.CephaloAnalysisOut.model_validate(analysis)
    if isinstance(out.angles_data, dict):
        try:
            out.angles_data = project_typed_craniom_read_path(
                out.angles_data,
                patient_id=analysis.patient_id,
            )
        except CephaloTypedReadError as exc:
            # Once typed evidence exists, stale legacy values must never be served as a
            # scientific fallback. Block the read until the persisted evidence is fixed.
            raise HTTPException(
                status_code=409,
                detail="Preuve céphalométrique persistée incohérente; lecture scientifique bloquée.",
            ) from exc

        # Preserve the historical read-only compatibility derivation for legacy rows.
        if "calibration_status" not in out.angles_data:
            out.angles_data = {
                **out.angles_data,
                "calibration_status": "verified" if analysis.is_calibrated else "unverified",
            }
    return out
