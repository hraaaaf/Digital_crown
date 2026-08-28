from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.config import settings
from backend.license_issuer import LicenseIssuerUnavailable, issue_license
from backend.license_security import LicenseSecurityError
from backend.services.license_service import LicenseService
from backend.utils.rate_limit import check_rate_limit


router = APIRouter(tags=["License Control Plane"])


class TrialControlPlaneActivation(BaseModel):
    code: str
    email: EmailStr
    cabinet_id: str


def _require_control_plane() -> None:
    if not settings.PLATFORM_CONTROL_PLANE_ENABLED:
        # Do not expose a dormant administration/signing surface on cabinet installs.
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


def _redemption_payload(data: dict) -> dict:
    return {
        "signed_license": data["signed_license"],
        "expires_at": data["expires_at"],
        "feature_set": data["feature_set"],
        "license_type": data["license_type"],
    }


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


@router.post("/activate-trial", summary="Émettre une Trial signée depuis le control-plane")
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
    if not cabinet_id:
        raise HTTPException(status_code=400, detail="Identifiant cabinet manquant.")

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
        data = existing.to_dict() or {}
        same_redemption = (
            data.get("email") == normalized_email
            and data.get("cabinet_id") == cabinet_id
            and isinstance(data.get("signed_license"), str)
            and data.get("signed_license")
        )
        if not same_redemption:
            raise HTTPException(status_code=400, detail="Ce code d'activation a déjà été utilisé.")
        if trial_code.consumed_at is None:
            trial_code.consumed_at = datetime.utcnow()
            db.commit()
        return _redemption_payload(data)

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
    except (LicenseIssuerUnavailable, LicenseSecurityError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Service de signature de licence non provisionné.",
        ) from exc

    stored = await service.write_signed_license(
        public_id=cabinet_id,
        signed_license=signed_license,
    )
    if not stored:
        raise HTTPException(
            status_code=503,
            detail="Licence signée générée mais non persistée.",
        )

    redemption = {
        "email": normalized_email,
        "cabinet_id": cabinet_id,
        "signed_license": signed_license,
        "expires_at": expiry_utc.isoformat(),
        "feature_set": models.SubscriptionPlan.GOLD.value,
        "license_type": "TRIAL",
        "redeemed_at": now_utc.isoformat(),
        "created_by_user_id": trial_code.created_by_admin_id,
    }
    try:
        redemption_ref.set(redemption)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Journal d'activation control-plane indisponible.",
        ) from exc

    trial_code.consumed_at = datetime.utcnow()
    db.commit()
    return _redemption_payload(redemption)
