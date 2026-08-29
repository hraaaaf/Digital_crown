from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend import database
from backend.routers.auth import require_permission
from backend.services.audit_service import audit_service
from backend.services.update_dispatch import UpdateApplyDispatchService
from backend.services.update_engine import UpdatePreparationError, UpdateSecurityError
from backend.services.update_prepare import UpdatePrepareService


router = APIRouter()


class UpdatePrepareRequest(BaseModel):
    manifest: dict[str, Any]


class UpdateApplyRequest(BaseModel):
    confirmation: str


@router.post("/update/prepare")
def update_prepare(
    payload: UpdatePrepareRequest,
    db=Depends(database.get_db),
    current_user=Depends(require_permission("admin")),
):
    try:
        # Log only the administrative intent. Never persist the signed envelope:
        # target URLs may be short-lived bearer URLs.
        audit_service.log(
            db=db,
            user_id=current_user.id,
            employer_id=current_user.get_employer_id(),
            action="UPDATE_PREPARE_REQUESTED",
            resource_type="UpdateJob",
            resource_id="pending",
            severity="CRITICAL",
            details=(
                "Préparation update demandée; manifeste vérifié uniquement par les clés "
                "Ed25519 pinnées du runtime, cible HTTPS re-hashée et rescue backup requis."
            ),
        )
        return UpdatePrepareService.prepare_from_manifest(payload.manifest)
    except (UpdatePreparationError, UpdateSecurityError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Impossible de préparer la mise à jour.") from exc


@router.get("/update/{job_id}/status")
def update_status(
    job_id: str,
    current_user=Depends(require_permission("admin")),
):
    try:
        return UpdateApplyDispatchService.get_public_job(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Mise à jour introuvable.") from exc
    except (UpdatePreparationError, UpdateSecurityError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/update/{job_id}/apply")
def update_apply(
    job_id: str,
    payload: UpdateApplyRequest,
    db=Depends(database.get_db),
    current_user=Depends(require_permission("admin")),
):
    try:
        audit_service.log(
            db=db,
            user_id=current_user.id,
            employer_id=current_user.get_employer_id(),
            action="UPDATE_APPLY_REQUESTED",
            resource_type="UpdateJob",
            resource_id=job_id,
            severity="CRITICAL",
            details=(
                "Apply update explicitement confirmé; artifact/rescue revalidés, "
                "signature de distribution plateforme requise, mutation hors-processus et rollback obligatoires."
            ),
        )
        result = UpdateApplyDispatchService.request_apply(job_id, payload.confirmation)
        return JSONResponse(status_code=202, content=result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Mise à jour introuvable.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (UpdatePreparationError, UpdateSecurityError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Impossible d'engager la mise à jour.") from exc
