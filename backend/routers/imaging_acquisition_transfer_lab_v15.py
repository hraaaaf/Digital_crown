"""LOT06-B HTTP test harness. Every endpoint fails closed outside isolated TEST SQLite."""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import get_current_user, has_permission
from backend.routers.workstation_mode import _find_workstation
from backend.services import imaging_acquisition_transfer_lab_v15 as lab

router = APIRouter()
_MAX_BYTES = 50 * 1024 * 1024


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tenant: int = Field(ge=1)
    device: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    capture: str = Field(pattern=r"^[A-Za-z0-9_-]{8,128}$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=1, le=_MAX_BYTES)


class Approval(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    workstation_id: str = Field(min_length=1, max_length=36)
    device: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    capture: str = Field(pattern=r"^[A-Za-z0-9_-]{8,128}$")
    patient_id: int = Field(ge=1)
    appointment_id: int | None = Field(default=None, ge=1)
    explicit_staff_action: bool


def _token(request: Request) -> str:
    return request.headers.get("x-dc06b-lab-device-token", "")


@router.post("/lab/propose", include_in_schema=False)
def propose(data: Proposal, request: Request, db: Session = Depends(database.get_db)):
    try:
        return lab.propose(
            db, tenant=data.tenant, device=data.device, token=_token(request),
            capture=data.capture, digest=data.sha256, size=data.byte_size,
        )
    except lab.TransferLabRejected as exc:
        db.rollback()
        raise HTTPException(exc.status_code, exc.reason) from exc


@router.post("/lab/approve", include_in_schema=False)
def approve(data: Approval, request: Request, db: Session = Depends(database.get_db),
            user: models.User = Depends(get_current_user)):
    try:
        lab.guard(db)
        bearer = request.headers.get("authorization", "")
        cookie = request.cookies.get("access_token")
        if (not bearer.startswith("Bearer ") or not bearer[7:].strip() or
                (cookie and not secrets.compare_digest(cookie, bearer[7:].strip()))):
            raise HTTPException(401, "EXPLICIT_STAFF_BEARER_REQUIRED")
        if data.explicit_staff_action is not True:
            raise HTTPException(403, "EXPLICIT_STAFF_ACTION_REQUIRED")
        tenant = int(user.get_employer_id())
        if not has_permission(user, "patients"):
            raise HTTPException(403, "PATIENT_PERMISSION_REQUIRED")
        station = _find_workstation(request, db, tenant)
        if station is None or station.id != data.workstation_id:
            raise HTTPException(403, "WORKSTATION_NOT_AUTHORIZED")
        return lab.approve(
            db, staff=user, tenant=tenant, workstation=data.workstation_id,
            device=data.device, capture=data.capture, patient=data.patient_id,
            appointment=data.appointment_id,
        )
    except lab.TransferLabRejected as exc:
        db.rollback()
        raise HTTPException(exc.status_code, exc.reason) from exc


@router.post("/lab/transfer", include_in_schema=False)
async def transfer(request: Request, tenant: int = Form(...), device: str = Form(...),
                   capture: str = Form(...), file: UploadFile = File(...),
                   db: Session = Depends(database.get_db)):
    try:
        lab.guard(db)
        if tenant < 1 or not 0 < len(device) <= 64 or not 8 <= len(capture) <= 128:
            raise HTTPException(422, "INVALID_CAPTURE_SCOPE")
        content = await file.read(_MAX_BYTES + 1)
        if len(content) > _MAX_BYTES:
            raise HTTPException(413, "LAB_CONTENT_TOO_LARGE")
        return lab.transfer(
            db, tenant=tenant, device=device, capture=capture, token=_token(request),
            payload=content, mime=file.content_type or "",
        )
    except lab.TransferLabRejected as exc:
        db.rollback()
        raise HTTPException(exc.status_code, exc.reason) from exc
    except (lab.ClinicalAssetIngestionError, lab.ClinicalAssetStorageError) as exc:
        db.rollback()
        raise HTTPException(422, "LAB_PAYLOAD_REJECTED") from exc
    except (OSError, ValueError) as exc:
        db.rollback()
        raise HTTPException(503, "LAB_STORAGE_UNAVAILABLE") from exc
    finally:
        await file.close()


@router.get("/lab/receipt", include_in_schema=False)
def receipt(tenant: int, device: str, capture: str, request: Request,
            db: Session = Depends(database.get_db)):
    try:
        return lab.lookup(
            db, tenant=tenant, device=device, capture=capture, token=_token(request),
        )
    except lab.TransferLabRejected as exc:
        db.rollback()
        raise HTTPException(exc.status_code, exc.reason) from exc
