from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.config import settings
from backend.device_security import DeviceSecurityError
from backend.license_issuer import (
    LicenseIssuerUnavailable,
    issue_device_certificate,
    issue_license,
)
from backend.license_security import LicenseSecurityError
from backend.services.license_service import LicenseService
from backend.utils.rate_limit import check_rate_limit


router = APIRouter(tags=["License Control Plane"])


class TrialControlPlaneActivation(BaseModel):
    code: str
    email: EmailStr
    cabinet_id: str
    device_id: str
    device_public_key: str
    platform: str


def _require_control_plane() -> None:
    if not settings.PLATFORM_CONTROL_PLANE_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")


def _get_trial_code(db: Session, code_value: str) -> models.TrialActivationCode:
    normalized = code_value.strip().upper()
    code = db.query(models.TrialActivationCode).filter(
        models.TrialActivationCode.code == normalized
    ).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code d'activation introuvable.")
    if code.revoked_at:
        raise HTTPException(status_code=400, detail="Ce code d'activation a été révoqué.")
    if code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Ce code d'activation a expiré.")
    return code


def _redemption_id(code_value: str) -> str:
    return hashlib.sha256(code_value.strip().upper().encode("utf-8")).hexdigest()


def _device_binding_id(license_id: str, device_id: str) -> str:
    material = f"{license_id}|{device_id}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _redemption_payload(data: dict) -> dict:
    return {
        "signed_license": data["signed_license"],
        "signed_device_certificate": data["signed_device_certificate"],
        "device_id": data["device_id"],
        "expires_at": data["expires_at"],
        "feature_set": data["feature_set"],
        "license_type": data["license_type"],
    }


def _is_same_redemption(
    data: dict,
    *,
    email: str,
    cabinet_id: str,
    device_id: str,
) -> bool:
    return bool(
        data.get("email") == email
        and data.get("cabinet_id") == cabinet_id
        and data.get("device_id") == device_id
        and isinstance(data.get("signed_license"), str)
        and data.get("signed_license")
        and isinstance(data.get("signed_device_certificate"), str)
        and data.get("signed_device_certificate")
    )


def _consume_trial_marker(db: Session, trial_code: models.TrialActivationCode) -> None:
    """Best-effort SQL mirror after the authoritative Firestore redemption exists."""
    if trial_code.consumed_at is None:
        trial_code.consumed_at = datetime.utcnow()
        db.commit()


def _existing_redemption_or_conflict(
    *,
    snapshot,
    email: str,
    cabinet_id: str,
    device_id: str,
    trial_code: models.TrialActivationCode,
    db: Session,
) -> dict:
    data = snapshot.to_dict() or {}
    if not _is_same_redemption(
        data,
        email=email,
        cabinet_id=cabinet_id,
        device_id=device_id,
    ):
        raise HTTPException(
            status_code=400,
            detail="Ce code d'activation est déjà lié à une autre installation.",
        )
    _consume_trial_marker(db, trial_code)
    return _redemption_payload(data)


@router.get(
    "/trial-code/{code}",
    response_model=schemas.TrialActivationPreview,
    summary="Prévisualiser un code Trial depuis le control-plane",
)
def preview_trial_code(
    code: str,
    request: Request,
    db: Session = Depends(database.get_db),
):
    _require_control_plane()
    check_rate_limit(request, scope="license-trial-preview")
    trial_code = _get_trial_code(db, code)
    if trial_code.consumed_at:
        raise HTTPException(status_code=400, detail="Ce code d'activation a déjà été utilisé.")
    return schemas.TrialActivationPreview(
        email=trial_code.email,
        nom_complet=trial_code.nom_complet,
        cabinet_name=trial_code.cabinet_name,
        trial_days=trial_code.trial_days,
        expires_at=trial_code.expires_at,
    )


@router.post("/activate-trial", summary="Émettre une Trial signée liée à une machine")
async def activate_trial(
    payload: TrialControlPlaneActivation,
    request: Request,
    db: Session = Depends(database.get_db),
):
    _require_control_plane()
    check_rate_limit(request, scope="license-trial-activate")

    normalized_code = payload.code.strip().upper()
    normalized_email = payload.email.lower().strip()
    cabinet_id = payload.cabinet_id.strip()
    device_id = payload.device_id.strip()
    device_public_key = payload.device_public_key.strip()
    platform = payload.platform.strip().lower()
    if not cabinet_id or not device_id or not device_public_key:
        raise HTTPException(status_code=400, detail="Identité cabinet/machine incomplète.")

    trial_code = _get_trial_code(db, normalized_code)
    if normalized_email != trial_code.email.lower().strip():
        raise HTTPException(status_code=400, detail="Ce code est lié à une autre adresse email.")
    if trial_code.created_by_admin_id is None:
        raise HTTPException(
            status_code=409,
            detail="Code d'activation legacy non attribué : émission signée impossible.",
        )

    service = LicenseService()
    if not service._db:
        raise HTTPException(
            status_code=503,
            detail="Stockage licence control-plane indisponible.",
        )

    redemption_ref = service._db.collection("trial_redemptions").document(
        _redemption_id(normalized_code)
    )
    existing = redemption_ref.get()
    if existing.exists:
        return _existing_redemption_or_conflict(
            snapshot=existing,
            email=normalized_email,
            cabinet_id=cabinet_id,
            device_id=device_id,
            trial_code=trial_code,
            db=db,
        )

    if trial_code.consumed_at:
        raise HTTPException(status_code=400, detail="Ce code d'activation a déjà été utilisé.")

    now_utc = datetime.now(timezone.utc)
    expiry_utc = now_utc + timedelta(days=trial_code.trial_days)
    try:
        signed_license = issue_license(
            cabinet_id=cabinet_id,
            license_type="TRIAL",
            created_by_user_id=trial_code.created_by_admin_id,
            expires_at=expiry_utc,
            release_channel="stable",
            feature_set=models.SubscriptionPlan.GOLD.value,
            max_devices=1,
            issued_at=now_utc,
            not_before=now_utc,
        )
        verified = service._verify_signed_license(
            signed_license,
            cabinet_id,
            now_utc,
            allow_inactive=True,
        )
        signed_device_certificate = issue_device_certificate(
            cabinet_id=cabinet_id,
            license_id=verified.license_id,
            device_id=device_id,
            device_public_key=device_public_key,
            platform=platform,
            created_by_user_id=trial_code.created_by_admin_id,
            expires_at=expiry_utc,
            issued_at=now_utc,
            not_before=now_utc,
        )
    except (LicenseIssuerUnavailable, LicenseSecurityError, DeviceSecurityError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Service de signature licence/machine non provisionné ou identité machine invalide.",
        ) from exc

    if verified.status != "ACTIVE" or verified.license_type != "TRIAL":
        raise HTTPException(status_code=503, detail="Entitlement Trial émis invalide.")

    redemption = {
        "email": normalized_email,
        "cabinet_id": cabinet_id,
        "device_id": device_id,
        "device_public_key": device_public_key,
        "platform": platform,
        "signed_license": signed_license,
        "signed_device_certificate": signed_device_certificate,
        "expires_at": expiry_utc.isoformat(),
        "feature_set": models.SubscriptionPlan.GOLD.value,
        "license_type": "TRIAL",
        "redeemed_at": now_utc.isoformat(),
        "created_by_user_id": trial_code.created_by_admin_id,
    }
    license_document = {
        "signed_license": signed_license,
        "active": True,
        "expiration_date": verified.expires_at,
        "license_type": verified.license_type,
        "feature_set": verified.claims.get("feature_set"),
        "release_channel": verified.claims.get("release_channel"),
        "license_id": verified.license_id,
        "key_id": verified.key_id,
        "max_devices": 1,
    }
    device_document = {
        "cabinet_id": cabinet_id,
        "license_id": verified.license_id,
        "device_id": device_id,
        "device_public_key": device_public_key,
        "platform": platform,
        "status": "ACTIVE",
        "signed_device_certificate": signed_device_certificate,
        "activated_at": now_utc.isoformat(),
    }

    # One atomic authority boundary: commercial license, first allowed device and
    # one-time redemption either all exist or none exists. `create` on both
    # one-time records also makes concurrent double activation fail closed.
    license_ref = service._db.collection("licenses").document(cabinet_id)
    device_ref = service._db.collection("license_devices").document(
        _device_binding_id(verified.license_id, device_id)
    )
    batch = service._db.batch()
    batch.set(license_ref, license_document, merge=True)
    batch.create(device_ref, device_document)
    batch.create(redemption_ref, redemption)
    try:
        batch.commit()
    except Exception as exc:
        try:
            recovered = redemption_ref.get()
        except Exception as read_exc:
            raise HTTPException(
                status_code=503,
                detail="Journal d'activation control-plane indisponible.",
            ) from read_exc
        if recovered.exists:
            return _existing_redemption_or_conflict(
                snapshot=recovered,
                email=normalized_email,
                cabinet_id=cabinet_id,
                device_id=device_id,
                trial_code=trial_code,
                db=db,
            )
        raise HTTPException(
            status_code=503,
            detail="Persistance atomique licence/machine impossible.",
        ) from exc

    _consume_trial_marker(db, trial_code)
    return _redemption_payload(redemption)
