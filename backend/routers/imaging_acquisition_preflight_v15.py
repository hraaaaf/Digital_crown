"""LOT06-B staff-only, read-only acquisition preflight.

DISABLED by default and hard-disabled outside isolated TEST runtime.
No attachment, upload, media creation, server receipt or device credential.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import get_current_user, has_permission
from backend.routers.workstation_mode import _find_workstation
from backend.services.imaging_acquisition_preflight_v15 import (
    PreflightRejected,
    resolve_acquisition_preflight,
)


router = APIRouter(tags=["Imaging Acquisition Preflight"])
_MAX_BYTES = 50 * 1024 * 1024
_ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp", "application/pdf"}
_ALLOWED_CATEGORY = {"PHOTO_CLINICAL", "RVG", "PANORAMIC", "CEPHALOMETRY", "OTHER"}


class AcquisitionPreflightRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    workstation_id: str = Field(min_length=1, max_length=36)
    source_capture_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,128}$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=1, le=_MAX_BYTES)
    mime_type: str = Field(min_length=1, max_length=127)
    category: str = Field(min_length=1, max_length=32)
    patient_id: int | None = Field(default=None, ge=1)
    appointment_id: int | None = Field(default=None, ge=1)


def _isolated_lab_enabled() -> bool:
    # Even setting the feature flag must not activate this in cabinet/production.
    return (
        os.getenv("ENVIRONMENT", "").lower() == "test"
        and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME", "").lower() in {"true", "1"}
        and os.getenv("DC_V15_06_PREFLIGHT_LAB", "") == "1"
    )


@router.post("/preflight")
def preflight(
    data: AcquisitionPreflightRequest,
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Explicit Bearer header avoids cookie-only CSRF exposure for this proposal API.
    if not request.headers.get("authorization", "").startswith("Bearer "):
        raise HTTPException(status_code=401, detail="EXPLICIT_STAFF_BEARER_REQUIRED")
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="PATIENT_PERMISSION_REQUIRED")
    if not _isolated_lab_enabled():
        raise HTTPException(status_code=503, detail="IMAGING_PREFLIGHT_DISABLED")
    if data.mime_type not in _ALLOWED_MIME or data.category not in _ALLOWED_CATEGORY:
        raise HTTPException(status_code=422, detail="UNSUPPORTED_ACQUISITION_FORMAT")
    if data.category != "PHOTO_CLINICAL" and data.mime_type != "application/pdf":
        # Radiographs are not classified by suffix/MIME alone.
        # The future content parser will authorize any broader mapping.
        raise HTTPException(status_code=422, detail="MODALITY_VALIDATION_NOT_AVAILABLE")

    tenant = int(current_user.get_employer_id())
    row = _find_workstation(request, db, tenant)
    if row is None or row.id != data.workstation_id:
        raise HTTPException(status_code=403, detail="WORKSTATION_NOT_AUTHORIZED")
    # Workstation registration is not connector activation or device enrollment.
    # This endpoint is only a guarded staff preview in an isolated laboratory.
    try:
        decision = resolve_acquisition_preflight(
            db,
            employer_id=tenant,
            patient_id=data.patient_id,
            appointment_id=data.appointment_id,
        )
    except PreflightRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return {
        "status": decision.status,
        "reason": decision.reason,
        "patient_id": decision.patient_id,
        "appointment_id": decision.appointment_id,
        "requires_staff_confirmation": True,
        "upload_permitted": False,
        "server_confirmed": False,
        "receipt_id": None,
        "source_capture_id": data.source_capture_id,
        "sha256": data.sha256,
    }
