"""Delegated license/device controls for platform operators."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.superadmin_admins import _audit, _require
from backend.services.license_service import LicenseService

router = APIRouter(prefix="/clients", tags=["SuperAdmin License Controls"])


def _client(db: Session, user_id: int) -> models.User:
    user = db.query(models.User).filter(
        models.User.id == int(user_id),
        models.User.employer_id.is_(None),
    ).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Client plateforme introuvable.")
    return user


def _cabinet(db: Session, user_id: int) -> models.CabinetConfig:
    cabinet = db.query(models.CabinetConfig).filter(
        models.CabinetConfig.owner_id == int(user_id)
    ).first()
    if cabinet is None:
        raise HTTPException(status_code=404, detail="Cabinet client introuvable.")
    return cabinet


def _serialize_device(device: models.MobilePairedDevice) -> dict:
    return {
        "device_id": device.device_id,
        "user_id": device.user_id,
        "created_at": device.created_at,
        "last_seen_at": device.last_seen_at,
        "revoked_at": device.revoked_at,
        "active": device.revoked_at is None,
    }


@router.get("/{user_id}/devices")
async def list_client_devices(
    user_id: int,
    db: Session = Depends(database.get_db),
    actor: models.User = Depends(_require("license.manage_devices")),
):
    _client(db, user_id)
    cabinet = _cabinet(db, user_id)
    clinic_id = str(cabinet.clinic_id or cabinet.public_id)
    effective = await LicenseService().get_effective_license(clinic_id)
    devices = (
        db.query(models.MobilePairedDevice)
        .filter(models.MobilePairedDevice.employer_id == int(user_id))
        .order_by(models.MobilePairedDevice.created_at.desc())
        .all()
    )
    active_count = sum(1 for device in devices if device.revoked_at is None)
    return {
        "client_id": int(user_id),
        "license": {
            "active": effective.get("active") is True,
            "license_type": effective.get("license_type"),
            "max_devices": effective.get("max_devices"),
            "active_devices": active_count,
            "release_channel": effective.get("release_channel"),
        },
        "devices": [_serialize_device(device) for device in devices],
    }


@router.post("/{user_id}/devices/{device_id}/revoke")
def revoke_client_device(
    user_id: int,
    device_id: str,
    db: Session = Depends(database.get_db),
    actor: models.User = Depends(_require("license.manage_devices")),
):
    _client(db, user_id)
    _cabinet(db, user_id)
    device = db.query(models.MobilePairedDevice).filter(
        models.MobilePairedDevice.device_id == device_id,
        models.MobilePairedDevice.employer_id == int(user_id),
    ).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Appareil client introuvable.")

    if device.revoked_at is None:
        device.revoked_at = datetime.utcnow()
        _audit(
            db,
            actor_id=actor.id,
            action="SUPERADMIN_DEVICE_REVOKE",
            target_id=device.device_id,
            resource_type="MobilePairedDevice",
            details=f"client_id={int(user_id)}",
            severity="CRITICAL",
        )
        # Mobile access and refresh decoders both require revoked_at IS NULL.
        # No separate mutable entitlement is introduced here.
        db.commit()
        db.refresh(device)

    return {
        "status": "revoked",
        "client_id": int(user_id),
        "device": _serialize_device(device),
    }
