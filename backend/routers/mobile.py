"""Canonical mobile auth wrapper: user identity + tenant scope + rotating device refresh + contextual bridge."""
from datetime import datetime, timedelta, timezone
import base64
import logging
import os
import secrets
import uuid

from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session, contains_eager

from backend import database, models
from backend.routers.auth import has_permission, require_permission
from backend.security import ALGORITHM, SECRET_KEY, token_blacklist
from . import admin_legacy as _admin_legacy
from . import mobile_legacy as _legacy
from .mobile_legacy import *  # noqa: F401,F403

logger = logging.getLogger(__name__)
MOBILE_REFRESH_TTL = timedelta(days=30)

_BRIDGE_DESTINATION_CODES = {
    "agenda": "a",
    "finance": "f",
    "lab": "l",
    "assistant": "b",
    "security": "s",
    "dentists": "d",
}
_BRIDGE_CODE_DESTINATIONS = {code: destination for destination, code in _BRIDGE_DESTINATION_CODES.items()}
_BRIDGE_LABELS = {
    "agenda": "Agenda",
    "finance": "Finance",
    "lab": "Labo",
    "assistant": "Assistant",
    "security": "Sécurité",
    "dentists": "Équipe praticiens",
}


def _mobile_jti(employer_id: int, now: datetime) -> str:
    issued_us = int(now.timestamp() * 1_000_000)
    return f"mobile:{int(employer_id)}:{issued_us}:{uuid.uuid4().hex}"


def _create_mobile_jwt(
    user_id: int,
    role: str,
    employer_id: int | None = None,
    device_id: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    tenant_id = int(employer_id if employer_id is not None else user_id)
    payload = {
        "sub": str(user_id),
        "tenant_id": tenant_id,
        "device_id": device_id,
        "type": "mobile",
        "role": role,
        "jti": _mobile_jti(tenant_id, now),
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _create_mobile_refresh_jwt(
    user_id: int,
    role: str,
    employer_id: int,
    device_id: str,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tenant_id": int(employer_id),
        "device_id": device_id,
        "type": "mobile_refresh",
        "role": role,
        "jti": _mobile_jti(int(employer_id), now),
        "iat": now,
        "exp": now + MOBILE_REFRESH_TTL,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


_legacy._create_mobile_jwt = _create_mobile_jwt
_legacy._create_mobile_refresh_jwt = _create_mobile_refresh_jwt
router = _legacy.router


def _remove_legacy_creation_route(path: str) -> None:
    """Remove only legacy POST creators while preserving mobile GET/status/delete routes."""
    for route in list(router.routes):
        methods = getattr(route, "methods", set()) or set()
        if getattr(route, "path", None) == path and "POST" in methods:
            router.routes.remove(route)


_remove_legacy_creation_route('/appointments')
_remove_legacy_creation_route('/patients')


def _role_name(user: models.User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _approval_value(user: models.User) -> str:
    value = getattr(user, "approval_status", None)
    return getattr(value, "value", value) or "approved"


def _allowed_bridge_destinations(user: models.User) -> list[str]:
    """Server-side bridge allowlist. UI filtering never grants permissions.

    Platform administration is deliberately absent: a paired mobile session may
    provide WebAuthn step-up proof, but it never becomes a Superadmin console.
    """
    if not has_permission(user, "agenda"):
        return []

    destinations = ["agenda", "assistant", "security", "dentists"]
    if has_permission(user, ["accounting", "payments"]):
        destinations.append("finance")
    if has_permission(user, "patients"):
        destinations.append("lab")
    return destinations


def _create_bridge_token(destination: str) -> str:
    code = _BRIDGE_DESTINATION_CODES.get(destination)
    if code is None:
        raise ValueError("Destination mobile non reconnue")
    return f"{code}.{secrets.token_urlsafe(24)}"


def _bridge_destination_from_token(token: str | None) -> str:
    if not token or "." not in token:
        return "agenda"
    code = token.split(".", 1)[0]
    return _BRIDGE_CODE_DESTINATIONS.get(code, "agenda")


def _bridge_target_users(db: Session, current_user: models.User) -> list[models.User]:
    employer_id = current_user.get_employer_id()
    users = db.query(models.User).filter(
        or_(models.User.id == employer_id, models.User.employer_id == employer_id)
    ).order_by(models.User.id.asc()).all()
    result = []
    for user in users:
        if not user.is_active:
            continue
        if user.id != employer_id and _approval_value(user) != "approved":
            continue
        if not _allowed_bridge_destinations(user):
            continue
        result.append(user)
    return result


def _resolve_bridge_target(db: Session, current_user: models.User, target_user_id: int) -> models.User:
    employer_id = current_user.get_employer_id()
    target = db.query(models.User).filter(models.User.id == target_user_id).first()
    if not target or target.get_employer_id() != employer_id:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable dans ce cabinet.")
    if not target.is_active or (target.id != employer_id and _approval_value(target) != "approved"):
        raise HTTPException(status_code=403, detail="Utilisateur inactif ou non approuvé.")
    if not _allowed_bridge_destinations(target):
        raise HTTPException(status_code=403, detail="Cet utilisateur ne peut pas ouvrir l'expérience mobile.")
    return target


class BridgePairingRequest(BaseModel):
    target_user_id: int
    destination: str = "agenda"


class BridgeDestinationRequest(BaseModel):
    credential: str


@router.get('/bridge-options', summary='Options autorisées du pont mobile contextuel')
def get_mobile_bridge_options(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("admin")),
):
    targets = []
    for user in _bridge_target_users(db, current_user):
        destinations = _allowed_bridge_destinations(user)
        targets.append({
            "id": user.id,
            "name": user.nom_complet or user.email,
            "email": user.email,
            "role": _role_name(user),
            "is_current_user": user.id == current_user.id,
            "destinations": [
                {"id": destination, "label": _BRIDGE_LABELS[destination]}
                for destination in destinations
            ],
        })
    return {"targets": targets, "expires_in": 300}


@router.post('/bridge-pairing', summary='Générer un pont mobile ciblé et éphémère')
def create_mobile_bridge_pairing(
    body: BridgePairingRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("admin")),
):
    destination = body.destination.strip().lower()
    target = _resolve_bridge_target(db, current_user, body.target_user_id)
    allowed = _allowed_bridge_destinations(target)
    if destination not in allowed:
        raise HTTPException(status_code=403, detail="Destination mobile non autorisée pour cet utilisateur.")

    employer_id = current_user.get_employer_id()
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()
    master_key = os.getenv("CABINET_MASTER_KEY_HEX")
    if not config or not master_key:
        raise HTTPException(status_code=404, detail="Configuration ZKA incomplète.")

    now = datetime.utcnow()
    db.query(models.ZKAPairingToken).filter(
        models.ZKAPairingToken.employer_id == employer_id,
        models.ZKAPairingToken.expires_at < now,
    ).delete()

    pairing_token = _create_bridge_token(destination)
    manual_code = None
    for _ in range(20):
        candidate = f"{secrets.randbelow(900000) + 100000:06d}"
        collision = db.query(models.ZKAPairingToken).filter(
            models.ZKAPairingToken.manual_code == candidate,
            models.ZKAPairingToken.used_at.is_(None),
            models.ZKAPairingToken.expires_at > now,
        ).first()
        if collision is None:
            manual_code = candidate
            break
    if manual_code is None:
        raise HTTPException(status_code=503, detail="Impossible de générer un code mobile unique.")

    record = models.ZKAPairingToken(
        token=pairing_token,
        manual_code=manual_code,
        employer_id=employer_id,
        user_id=target.id,
        public_id=config.public_id,
        master_key=master_key,
        role=_role_name(target),
        expires_at=now + timedelta(minutes=5),
    )

    base_url = _legacy.get_lan_base_url()
    qr_payload = f"{base_url}/mobile/onboarding?token={pairing_token}"
    try:
        qr_bytes = _admin_legacy.QRService.generate_qr_bytes(
            qr_payload,
            color="#4F46E5",
            box_size=10,
            add_logo=False,
            qr_style="classic",
        )
        img_str = base64.b64encode(qr_bytes.getvalue()).decode()
    except Exception as exc:
        db.rollback()
        logger.error("Contextual mobile QR generation failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Échec de génération du QR Code.") from exc

    db.add(record)
    db.commit()
    db.refresh(record)

    _admin_legacy.audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="MOBILE_CONTEXTUAL_BRIDGE_ISSUED",
        resource_type="ZKAPairingToken",
        resource_id=str(record.id),
        severity="WARNING",
        details=(
            f"Pont mobile généré pour user_id={target.id}; destination={destination}; "
            "aucune donnée patient encodée."
        ),
    )

    return {
        "qr_code": f"data:image/png;base64,{img_str}",
        "expires_in": 300,
        "lan_url": base_url,
        "token_code": manual_code,
        "target_user_id": target.id,
        "target_user_name": target.nom_complet or target.email,
        "target_role": _role_name(target),
        "destination": destination,
        "destination_label": _BRIDGE_LABELS[destination],
        "contains_patient_data": False,
    }


@router.post('/bridge-destination', summary='Résoudre la destination serveur après appairage')
def resolve_mobile_bridge_destination(
    body: BridgeDestinationRequest,
    mobile_user: models.User = Depends(_legacy.get_mobile_user),
    db: Session = Depends(database.get_db),
):
    credential = body.credential.strip()
    if not credential:
        return {"destination": "agenda", "label": _BRIDGE_LABELS["agenda"], "fallback": True}

    record = db.query(models.ZKAPairingToken).filter(
        or_(models.ZKAPairingToken.token == credential, models.ZKAPairingToken.manual_code == credential)
    ).order_by(models.ZKAPairingToken.id.desc()).first()
    if not record or record.used_at is None:
        raise HTTPException(status_code=404, detail="Pont mobile introuvable ou non consommé.")
    if record.user_id != mobile_user.id or record.employer_id != mobile_user.get_employer_id():
        raise HTTPException(status_code=403, detail="Pont mobile incompatible avec cette session.")

    requested = _bridge_destination_from_token(record.token)
    allowed = _allowed_bridge_destinations(mobile_user)
    destination = requested if requested in allowed else "agenda"
    return {
        "destination": destination,
        "label": _BRIDGE_LABELS[destination],
        "fallback": destination != requested,
    }


@router.post('/appointments', include_in_schema=False)
def legacy_mobile_appointment_create_disabled(
    _mobile_user: models.User = Depends(require_mobile_permission("agenda")),
):
    raise HTTPException(
        status_code=410,
        detail="Création RDV mobile legacy désactivée. Utilisez /api/appointments/ avec patient_id.",
    )


@router.post('/patients', include_in_schema=False)
def legacy_mobile_patient_create_disabled(
    _mobile_user: models.User = Depends(require_mobile_permission("patients")),
):
    raise HTTPException(
        status_code=410,
        detail="Création patient mobile legacy désactivée. Utilisez /api/patients/ avec date de naissance et sexe explicite.",
    )


_FINANCIAL_NOTIFICATION_PREFIXES = (
    "OVERDUE_PAYMENT",
    "HIGH_VALUE_RISK",
    "ORTHO_SEMESTER_",
)


def _mobile_notification_allowed(user: models.User, alert) -> bool:
    alert_type = str(getattr(alert, "alert_type", "") or "")
    if alert_type.startswith(_FINANCIAL_NOTIFICATION_PREFIXES):
        return has_permission(user, ["accounting", "payments"])
    return True


def _serialize_mobile_notification(alert) -> dict:
    patient = getattr(alert, "patient", None)
    priority = getattr(alert, "priority", None)
    priority = getattr(priority, "value", priority)
    patient_name = None
    if patient is not None:
        patient_name = f"{getattr(patient, 'prenom', '') or ''} {getattr(patient, 'nom', '') or ''}".strip() or None
    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "patient_name": patient_name,
        "type": alert.alert_type,
        "title": alert.title,
        "message": alert.message,
        "priority": priority,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


@router.get('/notifications', summary='Notifications mobiles non lues du cabinet')
def get_mobile_notifications(
    db: Session = Depends(database.get_db),
    mobile_user: models.User = Depends(_legacy.require_mobile_permission("patients")),
):
    employer_id = mobile_user.get_employer_id()
    now = datetime.now()
    query = (
        db.query(models.ProactiveAlert)
        .outerjoin(models.Patient, models.ProactiveAlert.patient_id == models.Patient.id)
        .options(contains_eager(models.ProactiveAlert.patient))
        .filter(
            models.ProactiveAlert.employer_id == employer_id,
            models.ProactiveAlert.is_read == False,  # noqa: E712
            or_(models.ProactiveAlert.expires_at.is_(None), models.ProactiveAlert.expires_at > now),
            or_(models.ProactiveAlert.patient_id.is_(None), models.Patient.deleted_at.is_(None)),
            or_(models.ProactiveAlert.snoozed_until.is_(None), models.ProactiveAlert.snoozed_until <= now),
        )
    )
    if not has_permission(mobile_user, ["accounting", "payments"]):
        query = query.filter(
            ~or_(*[
                models.ProactiveAlert.alert_type.like(f"{prefix}%")
                for prefix in _FINANCIAL_NOTIFICATION_PREFIXES
            ])
        )
    alerts = (
        query
        .order_by(models.ProactiveAlert.priority, models.ProactiveAlert.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "total": len(alerts),
        "alerts": [_serialize_mobile_notification(alert) for alert in alerts],
    }


@router.patch('/notifications/{alert_id}/read', summary='Marquer une notification mobile comme lue')
def mark_mobile_notification_read(
    alert_id: int,
    db: Session = Depends(database.get_db),
    mobile_user: models.User = Depends(_legacy.require_mobile_permission("patients")),
):
    employer_id = mobile_user.get_employer_id()
    alert = db.query(models.ProactiveAlert).filter(
        models.ProactiveAlert.id == alert_id,
        models.ProactiveAlert.employer_id == employer_id,
    ).first()
    if not alert or not _mobile_notification_allowed(mobile_user, alert):
        raise HTTPException(status_code=404, detail='Notification introuvable')
    alert.is_read = True
    db.commit()
    return {"status": "ok"}


@router.patch('/notifications/{alert_id}/snooze', summary='Reporter une notification mobile de 24 heures')
def snooze_mobile_notification(
    alert_id: int,
    db: Session = Depends(database.get_db),
    mobile_user: models.User = Depends(_legacy.require_mobile_permission("patients")),
):
    employer_id = mobile_user.get_employer_id()
    alert = db.query(models.ProactiveAlert).filter(
        models.ProactiveAlert.id == alert_id,
        models.ProactiveAlert.employer_id == employer_id,
    ).first()
    if not alert or not _mobile_notification_allowed(mobile_user, alert):
        raise HTTPException(status_code=404, detail='Notification introuvable')
    now = datetime.now()
    alert.snoozed_until = now + timedelta(hours=24)
    if not alert.expires_at or alert.expires_at < alert.snoozed_until + timedelta(days=1):
        alert.expires_at = alert.snoozed_until + timedelta(days=1)
    db.commit()
    return {"status": "ok", "snoozed_until": alert.snoozed_until.isoformat()}


class MobileRefreshRequest(BaseModel):
    refresh_token: str


@router.post('/refresh-token', summary='Renouveler la session mobile appairée')
def refresh_mobile_credentials(
    body: MobileRefreshRequest,
    db: Session = Depends(database.get_db),
):
    err = HTTPException(status_code=401, detail='Session mobile expirée ou révoquée.')
    try:
        payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get('type') != 'mobile_refresh':
            raise err
        jti = payload.get('jti')
        device_id = payload.get('device_id')
        if not jti or not device_id or token_blacklist.is_revoked(jti, db):
            raise err
        user_id = int(payload['sub'])
        tenant_id = int(payload['tenant_id'])
    except HTTPException:
        raise
    except (JWTError, ValueError, KeyError, TypeError):
        raise err

    device = db.query(models.MobilePairedDevice).filter(
        models.MobilePairedDevice.device_id == device_id,
        models.MobilePairedDevice.user_id == user_id,
        models.MobilePairedDevice.employer_id == tenant_id,
        models.MobilePairedDevice.revoked_at.is_(None),
    ).first()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not device or not user or not user.is_active or user.get_employer_id() != tenant_id:
        raise err
    if device.refresh_jti != jti:
        device.revoked_at = datetime.utcnow()
        db.commit()
        raise err

    role = _role_name(user)
    access_token = _create_mobile_jwt(user.id, role, tenant_id, device_id)
    refresh_token = _create_mobile_refresh_jwt(user.id, role, tenant_id, device_id)
    refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    device.refresh_jti = refresh_payload['jti']
    device.last_seen_at = datetime.utcnow()
    db.commit()
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'device_id': device_id,
        'user_id': user.id,
        'tenant_id': tenant_id,
        'role': role,
    }
