"""Canonical cephalometric refinement route with clinician-bound landmark audit."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.routers.auth import require_permission
from backend.services.cephalo_service import CephaloService
from backend.utils.access_control import assert_patient_access

router = APIRouter()


@router.put("/analyses/{analysis_id}")
def update_analysis_with_landmark_audit(
    analysis_id: int,
    req: schemas.AnalysisUpdate,
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
        return CephaloService(db).refine_analysis(
            analysis_id=analysis_id,
            landmarks=req.landmarks,
            clinical_data=req.clinical_data,
            ai_diagnostic=req.ai_diagnostic,
            mm_per_pixel=req.mm_per_pixel,
            mcnamara_projections=(
                req.mcnamara_projections.model_dump()
                if req.mcnamara_projections
                else None
            ),
            # Identity is server-authenticated, never accepted from request payload.
            clinician_id=str(current_user.id),
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Échec du raffinement céphalométrique") from exc
