"""M4-A resource-bound mobile bridge. Keeps M6.4 destination bridge unchanged."""
from datetime import datetime, timedelta
import base64
import logging
import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, delete, insert, or_, select
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import has_permission, require_permission
from . import admin_legacy as _admin_legacy
from . import mobile_legacy as _legacy
from .mobile import _allowed_bridge_destinations, _bridge_target_users, _resolve_bridge_target, _role_name

logger = logging.getLogger(__name__)
router = APIRouter()

# Server-side context. Neither resource id nor PHI is encoded in QR or mobile URL.
BRIDGE_CONTEXT_TABLE = Table(
    "mobile_bridge_contexts",
    models.Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("context_key", String(64), unique=True, index=True, nullable=False),
    Column("pairing_id", Integer, ForeignKey("zka_pairing_tokens.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
    Column("employer_id", Integer, index=True, nullable=False),
    Column("target_user_id", Integer, index=True, nullable=False),
    Column("device_id", String(64), index=True, nullable=True),
    Column("resource_type", String(32), nullable=False),
    Column("resource_id", Integer, nullable=False),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    extend_existing=True,
)


class ResourceBridgePairingRequest(BaseModel):
    resource_type: str
    resource_id: int
    target_user_id: int | None = None


class ResourceBridgeDestinationRequest(BaseModel):
    credential: str


class ResourceContextRequest(BaseModel):
    context_key: str


def _resource_token() -> str:
    # Same 192-bit secret budget as M6.4, still within ZKAPairingToken.token VARCHAR(36).
    return f"c.{secrets.token_urlsafe(24)}"


def _patient_resource(db: Session, user: models.User, resource_id: int) -> models.Patient:
    if not has_permission(user, "patients"):
        raise HTTPException(status_code=403, detail="Accès patient mobile refusé.")
    patient = db.query(models.Patient).filter(
        models.Patient.id == int(resource_id),
        models.Patient.employer_id == user.get_employer_id(),
        models.Patient.deleted_at.is_(None),
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Dossier patient introuvable dans ce cabinet.")
    return patient


def _resource_bridge_target_users(db: Session, current_user: models.User) -> list[models.User]:
    candidates = _bridge_target_users(db, current_user) if has_permission(current_user, "admin") else [current_user]
    return [user for user in candidates if has_permission(user, "patients") and _allowed_bridge_destinations(user)]


def _resolve_resource_bridge_target(db: Session, current_user: models.User, target_user_id: int | None) -> models.User:
    requested_id = int(target_user_id or current_user.id)
    if requested_id != current_user.id and not has_permission(current_user, "admin"):
        raise HTTPException(status_code=403, detail="Seul un administrateur peut cibler un autre utilisateur mobile.")
    target = _resolve_bridge_target(db, current_user, requested_id)
    if not has_permission(target, "patients"):
        raise HTTPException(status_code=403, detail="Utilisateur cible sans permission Patients.")
    return target


def _context_for_pairing(db: Session, pairing_id: int):
    return db.execute(select(BRIDGE_CONTEXT_TABLE).where(BRIDGE_CONTEXT_TABLE.c.pairing_id == int(pairing_id))).mappings().first()


def _context_by_key(db: Session, context_key: str):
    return db.execute(select(BRIDGE_CONTEXT_TABLE).where(BRIDGE_CONTEXT_TABLE.c.context_key == context_key)).mappings().first()


def _purge_expired(db: Session, employer_id: int, now: datetime) -> None:
    expired_ids = [row[0] for row in db.query(models.ZKAPairingToken.id).filter(
        models.ZKAPairingToken.employer_id == employer_id,
        models.ZKAPairingToken.expires_at < now,
    ).all()]
    if expired_ids:
        db.execute(delete(BRIDGE_CONTEXT_TABLE).where(BRIDGE_CONTEXT_TABLE.c.pairing_id.in_(expired_ids)))
        db.query(models.ZKAPairingToken).filter(models.ZKAPairingToken.id.in_(expired_ids)).delete(synchronize_session=False)


def _context_state(db: Session, mobile_user: models.User, context) -> tuple[str, str | None]:
    if context["employer_id"] != mobile_user.get_employer_id() or context["target_user_id"] != mobile_user.id:
        raise HTTPException(status_code=403, detail="Contexte mobile incompatible avec cette session.")
    if str(context["resource_type"]).lower() != "patient":
        return "unavailable", "Type de ressource mobile non pris en charge."
    if not has_permission(mobile_user, "patients"):
        return "unavailable", "La permission Patients n'est plus disponible pour cette session."
    patient = db.query(models.Patient.id).filter(
        models.Patient.id == int(context["resource_id"]),
        models.Patient.employer_id == mobile_user.get_employer_id(),
        models.Patient.deleted_at.is_(None),
    ).first()
    if not patient:
        return "unavailable", "Le dossier patient n'est plus disponible."
    return "ready", None


@router.get('/resource-bridge-options', summary='Cibles autorisées pour un pont mobile de ressource')
def get_resource_bridge_options(
    resource_type: str,
    resource_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    if resource_type.strip().lower() != "patient":
        raise HTTPException(status_code=422, detail="Type de ressource mobile non pris en charge.")
    _patient_resource(db, current_user, resource_id)
    targets = _resource_bridge_target_users(db, current_user)
    return {
        "resource_type": "patient",
        "resource_label": "Dossier patient",
        "targets": [{
            "id": user.id,
            "name": user.nom_complet or user.email,
            "email": user.email,
            "role": _role_name(user),
            "is_current_user": user.id == current_user.id,
        } for user in targets],
        "expires_in": 300,
        "contains_patient_data": False,
    }


@router.post('/resource-bridge-pairing', summary='Générer un pont opaque vers une ressource mobile')
def create_resource_bridge_pairing(
    body: ResourceBridgePairingRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    if body.resource_type.strip().lower() != "patient":
        raise HTTPException(status_code=422, detail="Type de ressource mobile non pris en charge.")
    patient = _patient_resource(db, current_user, body.resource_id)
    target = _resolve_resource_bridge_target(db, current_user, body.target_user_id)
    _patient_resource(db, target, patient.id)

    employer_id = current_user.get_employer_id()
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()
    master_key = os.getenv("CABINET_MASTER_KEY_HEX")
    if not config or not master_key:
        raise HTTPException(status_code=404, detail="Configuration ZKA incomplète.")

    now = datetime.utcnow()
    _purge_expired(db, employer_id, now)
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
        token=_resource_token(), manual_code=manual_code, employer_id=employer_id,
        user_id=target.id, public_id=config.public_id, master_key=master_key,
        role=_role_name(target), expires_at=now + timedelta(minutes=5),
    )
    db.add(record)
    db.flush()
    db.execute(insert(BRIDGE_CONTEXT_TABLE).values(
        context_key=secrets.token_urlsafe(24), pairing_id=record.id, employer_id=employer_id,
        target_user_id=target.id, device_id=None, resource_type="patient",
        resource_id=patient.id, created_at=now,
    ))

    base_url = _legacy.get_lan_base_url()
    qr_payload = f"{base_url}/mobile/onboarding?token={record.token}"
    try:
        qr_bytes = _admin_legacy.QRService.generate_qr_bytes(
            qr_payload, color="#4F46E5", box_size=10, add_logo=False, qr_style="classic",
        )
        img_str = base64.b64encode(qr_bytes.getvalue()).decode()
    except Exception as exc:
        db.rollback()
        logger.error("Patient resource QR generation failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Échec de génération du QR Code.") from exc

    db.commit()
    db.refresh(record)
    _admin_legacy.audit_service.log(
        db=db, user_id=current_user.id, employer_id=employer_id,
        action="MOBILE_RESOURCE_BRIDGE_ISSUED", resource_type="Patient",
        resource_id=str(patient.id), severity="WARNING",
        details=f"Pont mobile patient généré pour user_id={target.id}; QR opaque sans donnée patient.",
    )
    return {
        "qr_code": f"data:image/png;base64,{img_str}", "expires_in": 300,
        "lan_url": base_url, "token_code": manual_code, "target_user_id": target.id,
        "target_user_name": target.nom_complet or target.email, "target_role": _role_name(target),
        "resource_type": "patient", "resource_label": "Dossier patient", "contains_patient_data": False,
    }


@router.post('/resource-bridge-destination', summary='Résoudre un contexte ressource après appairage')
def resolve_resource_bridge_destination(
    body: ResourceBridgeDestinationRequest,
    authorization: str = Header(...),
    db: Session = Depends(database.get_db),
):
    mobile_user, tenant_id, mobile_payload = _legacy._decode_mobile_identity(authorization, db)
    credential = body.credential.strip()
    if not credential:
        raise HTTPException(status_code=404, detail="Contexte ressource absent.")
    record = db.query(models.ZKAPairingToken).filter(
        or_(models.ZKAPairingToken.token == credential, models.ZKAPairingToken.manual_code == credential)
    ).order_by(models.ZKAPairingToken.id.desc()).first()
    if not record or record.used_at is None:
        raise HTTPException(status_code=404, detail="Pont ressource introuvable ou non consommé.")
    if record.user_id != mobile_user.id or record.employer_id != tenant_id:
        raise HTTPException(status_code=403, detail="Pont ressource incompatible avec cette session.")
    context = _context_for_pairing(db, record.id)
    if not context:
        raise HTTPException(status_code=404, detail="Ce pont ne contient pas de contexte ressource.")

    device_id = str(mobile_payload.get("device_id") or "")
    if not device_id:
        raise HTTPException(status_code=401, detail="Session mobile sans appareil associé.")
    if context["device_id"] and context["device_id"] != device_id:
        raise HTTPException(status_code=403, detail="Contexte mobile lié à un autre appareil.")
    if not context["device_id"]:
        db.execute(BRIDGE_CONTEXT_TABLE.update().where(BRIDGE_CONTEXT_TABLE.c.id == context["id"]).values(device_id=device_id))
        db.commit()
        context = _context_for_pairing(db, record.id)

    state, reason = _context_state(db, mobile_user, context)
    return {
        "destination": "context", "label": "Dossier patient", "fallback": False,
        "context": {"type": context["resource_type"], "key": context["context_key"], "state": state, "reason": reason},
    }


@router.post('/resource-context', summary='Relire une ressource mobile contextuelle autorisée')
def get_resource_context(
    body: ResourceContextRequest,
    authorization: str = Header(...),
    db: Session = Depends(database.get_db),
):
    mobile_user, tenant_id, mobile_payload = _legacy._decode_mobile_identity(authorization, db)
    context = _context_by_key(db, body.context_key.strip()) if body.context_key.strip() else None
    if not context:
        raise HTTPException(status_code=404, detail="Contexte mobile introuvable.")
    if context["target_user_id"] != mobile_user.id or context["employer_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Contexte mobile incompatible avec cette session.")
    device_id = str(mobile_payload.get("device_id") or "")
    if not device_id or context["device_id"] != device_id:
        raise HTTPException(status_code=403, detail="Contexte mobile lié à un autre appareil.")

    state, reason = _context_state(db, mobile_user, context)
    if state != "ready":
        raise HTTPException(status_code=403 if not has_permission(mobile_user, "patients") else 404, detail=reason or "Dossier patient indisponible.")

    patient = _patient_resource(db, mobile_user, int(context["resource_id"]))
    assurance = getattr(patient.assurance, "value", patient.assurance)
    return {
        "type": "patient", "label": "Dossier patient",
        "patient": {
            "id": patient.id, "numero_dossier": patient.numero_dossier,
            "nom": patient.nom, "prenom": patient.prenom,
            "date_naissance": patient.date_naissance.isoformat() if patient.date_naissance else None,
            "telephone": patient.telephone, "assurance": assurance,
            "has_medical_alert": bool(patient.antecedents_medicaux),
            "motif_consultation": patient.motif_consultation,
        },
    }
