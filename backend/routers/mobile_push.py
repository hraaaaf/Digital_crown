"""M6-D2 — standards-based Web Push bound to the authenticated paired mobile device."""
from dataclasses import dataclass
import os
import re
from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_mobile_push import MobilePushSubscription
from backend.routers import mobile_legacy as _legacy
from backend.routers.auth import has_permission
from backend.services.mobile_push_service import get_or_create_vapid_keypair

router = APIRouter(tags=["Mobile Web Push"])
_B64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class MobilePushIdentity:
    user: models.User
    tenant_id: int
    device_id: str


class PushSubscriptionKeys(BaseModel):
    model_config = ConfigDict(extra="forbid")
    p256dh: str = Field(min_length=32, max_length=255)
    auth: str = Field(min_length=8, max_length=255)


class PushSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint: str = Field(min_length=16, max_length=2048)
    keys: PushSubscriptionKeys
    platform: Literal["ios", "android", "web"] = "web"


class PushUnsubscribeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint: str = Field(min_length=16, max_length=2048)


def _mobile_push_identity(
    authorization: str = Header(...),
    db: Session = Depends(database.get_db),
) -> MobilePushIdentity:
    user, tenant_id, payload = _legacy._decode_mobile_identity(authorization, db)
    if not has_permission(user, "patients"):
        raise HTTPException(status_code=403, detail="Accès mobile refusé pour les notifications.")
    device_id = str(payload.get("device_id") or "")
    if not device_id:
        raise HTTPException(status_code=401, detail="Session mobile non appairée.")
    return MobilePushIdentity(user=user, tenant_id=int(tenant_id), device_id=device_id)


def _validate_subscription_payload(body: PushSubscriptionRequest) -> None:
    parsed = urlparse(body.endpoint)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise HTTPException(status_code=422, detail="Endpoint Web Push invalide.")
    if not _B64URL_RE.fullmatch(body.keys.p256dh) or not _B64URL_RE.fullmatch(body.keys.auth):
        raise HTTPException(status_code=422, detail="Clés Web Push invalides.")


def _secure_lan_enabled() -> bool:
    return os.getenv("DIGITALCROWN_ENABLE_HTTPS", "false").strip().lower() in {"1", "true", "yes", "on"}


def install_secure_lan_url_overrides() -> None:
    """Keep QR/API discovery aligned with the HTTPS runtime selected by the launcher."""
    def lan_backend_url() -> str:
        scheme = "https" if _secure_lan_enabled() else "http"
        return f"{scheme}://{_legacy._detect_lan_ip()}:{os.getenv('PORT', '8005')}"

    def lan_frontend_url() -> str:
        scheme = "https" if _secure_lan_enabled() else "http"
        return f"{scheme}://{_legacy._detect_lan_ip()}:5173"

    _legacy.get_lan_base_url = lan_backend_url
    _legacy.get_lan_frontend_url = lan_frontend_url


@router.get("/push/config", summary="Clé publique Web Push de cette installation")
def get_mobile_push_config(
    _identity: MobilePushIdentity = Depends(_mobile_push_identity),
):
    try:
        _private_key, public_key = get_or_create_vapid_keypair()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Web Push indisponible sur cette installation.") from exc
    return {"public_key": public_key, "payload_contains_patient_data": False}


@router.get("/push/subscription", summary="État Web Push de l'appareil appairé")
def get_mobile_push_subscription_status(
    identity: MobilePushIdentity = Depends(_mobile_push_identity),
    db: Session = Depends(database.get_db),
):
    try:
        _private_key, current_public_key = get_or_create_vapid_keypair()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Web Push indisponible sur cette installation.") from exc
    active = db.query(MobilePushSubscription.id).filter(
        MobilePushSubscription.device_id == identity.device_id,
        MobilePushSubscription.user_id == identity.user.id,
        MobilePushSubscription.employer_id == identity.tenant_id,
        MobilePushSubscription.vapid_public_key == current_public_key,
    ).first() is not None
    return {"active": active}


@router.post("/push/subscription", summary="Lier Web Push à l'appareil mobile appairé")
def register_mobile_push_subscription(
    body: PushSubscriptionRequest,
    identity: MobilePushIdentity = Depends(_mobile_push_identity),
    db: Session = Depends(database.get_db),
):
    _validate_subscription_payload(body)
    try:
        _private_key, current_public_key = get_or_create_vapid_keypair()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Web Push indisponible sur cette installation.") from exc

    endpoint_row = db.query(MobilePushSubscription).filter(
        MobilePushSubscription.endpoint == body.endpoint
    ).first()
    if endpoint_row and endpoint_row.device_id != identity.device_id:
        previous_device = db.query(models.MobilePairedDevice).filter(
            models.MobilePairedDevice.device_id == endpoint_row.device_id
        ).first()
        if previous_device and previous_device.revoked_at is None:
            raise HTTPException(status_code=409, detail="Cette souscription appartient à un autre appareil actif.")
        db.delete(endpoint_row)
        db.flush()

    current = db.query(MobilePushSubscription).filter(
        or_(
            MobilePushSubscription.device_id == identity.device_id,
            MobilePushSubscription.endpoint == body.endpoint,
        )
    ).first()
    if current is None:
        current = MobilePushSubscription(
            device_id=identity.device_id,
            user_id=identity.user.id,
            employer_id=identity.tenant_id,
            endpoint=body.endpoint,
            p256dh=body.keys.p256dh,
            auth=body.keys.auth,
            platform=body.platform,
            vapid_public_key=current_public_key,
        )
        db.add(current)
    else:
        current.device_id = identity.device_id
        current.user_id = identity.user.id
        current.employer_id = identity.tenant_id
        current.endpoint = body.endpoint
        current.p256dh = body.keys.p256dh
        current.auth = body.keys.auth
        current.platform = body.platform
        current.vapid_public_key = current_public_key

    db.commit()
    return {
        "status": "registered",
        "device_bound": True,
        "user_bound": True,
        "payload_contains_patient_data": False,
    }


@router.delete("/push/subscription", summary="Délier Web Push de l'appareil mobile appairé")
def unregister_mobile_push_subscription(
    body: PushUnsubscribeRequest,
    identity: MobilePushIdentity = Depends(_mobile_push_identity),
    db: Session = Depends(database.get_db),
):
    deleted = db.query(MobilePushSubscription).filter(
        MobilePushSubscription.device_id == identity.device_id,
        MobilePushSubscription.user_id == identity.user.id,
        MobilePushSubscription.employer_id == identity.tenant_id,
        MobilePushSubscription.endpoint == body.endpoint,
    ).delete(synchronize_session=False)
    db.commit()
    return {"status": "unregistered" if deleted else "absent"}
