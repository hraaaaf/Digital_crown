"""Contextual mobile resource bridge: patient, panoramic, document and appointment resources."""
from datetime import datetime, timedelta
from pathlib import Path
import base64
import logging
import mimetypes
import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, delete, insert, or_, select
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers import documents as _documents
from backend.routers.auth import get_current_user, has_permission
from backend.utils.access_control import assert_patient_access
from . import admin_legacy as _admin_legacy
from . import mobile_legacy as _legacy
from .mobile import _approval_value, _role_name

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

_RESOURCE_SPECS = {
    "patient": {"permission": "patients", "label": "Dossier patient"},
    "panoramic": {"permission": "panoramic", "label": "Radio panoramique"},
    "document": {"permission": None, "label": "Document"},
    "appointment": {"permission": "agenda", "label": "Rendez-vous"},
}


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


def _resource_type(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in _RESOURCE_SPECS:
        raise HTTPException(status_code=422, detail="Type de ressource mobile non pris en charge.")
    return normalized


def _document_type_value(document: models.DocumentArchive) -> str:
    value = getattr(document.document_type, "value", document.document_type)
    return str(value or "").strip().lower()


def _document_permission(document: models.DocumentArchive) -> str:
    # Same source of truth as document generation/download. Unknown historical
    # types stay conservative instead of becoming permission-free on mobile.
    return str(_documents.DOCUMENT_TYPE_PERMISSIONS.get(_document_type_value(document), "patients"))


def _resource_permission(resource_type: str, resource=None) -> str:
    resource_type = _resource_type(resource_type)
    if resource_type == "document":
        if not isinstance(resource, models.DocumentArchive):
            raise HTTPException(status_code=422, detail="Document mobile non résolu.")
        return _document_permission(resource)
    return str(_RESOURCE_SPECS[resource_type]["permission"])


def _resource_label(resource_type: str) -> str:
    return str(_RESOURCE_SPECS[_resource_type(resource_type)]["label"])


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


def _panoramic_resource(db: Session, user: models.User, resource_id: int) -> models.PanoramicAnalysis:
    if not has_permission(user, "panoramic"):
        raise HTTPException(status_code=403, detail="Accès panoramique mobile refusé.")
    analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == int(resource_id)).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Radio panoramique introuvable.")
    assert_patient_access(analysis.patient_id, user, db)
    patient = db.query(models.Patient.id).filter(
        models.Patient.id == analysis.patient_id,
        models.Patient.employer_id == user.get_employer_id(),
        models.Patient.deleted_at.is_(None),
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient de la radio panoramique indisponible.")
    return analysis


def _document_resource(db: Session, user: models.User, resource_id: int) -> models.DocumentArchive:
    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == int(resource_id),
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document actif introuvable.")
    permission = _document_permission(document)
    if not has_permission(user, permission):
        raise HTTPException(status_code=403, detail=f"Accès document mobile refusé. Permission requise : {permission}.")
    assert_patient_access(document.patient_id, user, db)
    patient = db.query(models.Patient.id).filter(
        models.Patient.id == document.patient_id,
        models.Patient.employer_id == user.get_employer_id(),
        models.Patient.deleted_at.is_(None),
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient du document indisponible.")
    return document


def _appointment_resource(db: Session, user: models.User, resource_id: int) -> models.Appointment:
    if not has_permission(user, "agenda"):
        raise HTTPException(status_code=403, detail="Accès rendez-vous mobile refusé.")
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == int(resource_id),
        models.Appointment.employer_id == user.get_employer_id(),
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable dans ce cabinet.")
    if appointment.patient_id:
        assert_patient_access(appointment.patient_id, user, db)
        patient = db.query(models.Patient.id).filter(
            models.Patient.id == appointment.patient_id,
            models.Patient.employer_id == user.get_employer_id(),
            models.Patient.deleted_at.is_(None),
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient du rendez-vous indisponible.")
    return appointment


def _resource_entity(db: Session, user: models.User, resource_type: str, resource_id: int):
    resource_type = _resource_type(resource_type)
    if resource_type == "patient":
        return _patient_resource(db, user, resource_id)
    if resource_type == "panoramic":
        return _panoramic_resource(db, user, resource_id)
    if resource_type == "document":
        return _document_resource(db, user, resource_id)
    if resource_type == "appointment":
        return _appointment_resource(db, user, resource_id)
    raise HTTPException(status_code=422, detail="Type de ressource mobile non pris en charge.")


def _resource_bridge_target_users(
    db: Session,
    current_user: models.User,
    resource_type: str,
    resource,
) -> list[models.User]:
    permission = _resource_permission(resource_type, resource)
    if not has_permission(current_user, "admin"):
        return [current_user] if current_user.is_active and has_permission(current_user, permission) else []

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
        if not has_permission(user, permission):
            continue
        result.append(user)
    return result


def _resolve_resource_bridge_target(
    db: Session,
    current_user: models.User,
    target_user_id: int | None,
    resource_type: str,
    resource,
) -> models.User:
    requested_id = int(target_user_id or current_user.id)
    if requested_id != current_user.id and not has_permission(current_user, "admin"):
        raise HTTPException(status_code=403, detail="Seul un administrateur peut cibler un autre utilisateur mobile.")

    employer_id = current_user.get_employer_id()
    target = db.query(models.User).filter(models.User.id == requested_id).first()
    if not target or target.get_employer_id() != employer_id:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable dans ce cabinet.")
    if not target.is_active or (target.id != employer_id and _approval_value(target) != "approved"):
        raise HTTPException(status_code=403, detail="Utilisateur inactif ou non approuvé.")

    permission = _resource_permission(resource_type, resource)
    if not has_permission(target, permission):
        raise HTTPException(status_code=403, detail=f"Utilisateur cible sans permission {permission}.")
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


def _context_state(db: Session, mobile_user: models.User, context) -> tuple[str, str | None, int | None]:
    if context["employer_id"] != mobile_user.get_employer_id() or context["target_user_id"] != mobile_user.id:
        raise HTTPException(status_code=403, detail="Contexte mobile incompatible avec cette session.")

    resource_type = str(context["resource_type"]).lower()
    if resource_type not in _RESOURCE_SPECS:
        return "unavailable", "Type de ressource mobile non pris en charge.", 404

    try:
        _resource_entity(db, mobile_user, resource_type, int(context["resource_id"]))
    except HTTPException as exc:
        if exc.status_code in (403, 404):
            return "unavailable", str(exc.detail), int(exc.status_code)
        raise
    return "ready", None, None


def _validated_mobile_context(
    db: Session,
    authorization: str,
    context_key: str,
):
    mobile_user, tenant_id, mobile_payload = _legacy._decode_mobile_identity(authorization, db)
    context = _context_by_key(db, context_key.strip()) if context_key.strip() else None
    if not context:
        raise HTTPException(status_code=404, detail="Contexte mobile introuvable.")
    if context["target_user_id"] != mobile_user.id or context["employer_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Contexte mobile incompatible avec cette session.")
    device_id = str(mobile_payload.get("device_id") or "")
    if not device_id or context["device_id"] != device_id:
        raise HTTPException(status_code=403, detail="Contexte mobile lié à un autre appareil.")

    state, reason, error_status = _context_state(db, mobile_user, context)
    if state != "ready":
        raise HTTPException(status_code=error_status or 404, detail=reason or "Ressource mobile indisponible.")
    return mobile_user, context


def _document_file(document: models.DocumentArchive) -> Path:
    raw_path = str(document.file_path or "").strip()
    if not raw_path:
        raise HTTPException(status_code=404, detail="Fichier du document introuvable.")

    if raw_path.startswith("static/archives/") or raw_path.startswith("static/documents/"):
        candidate = (Path(_documents.MEDIA_DIR) / raw_path.replace("static/", "", 1)).resolve()
        allowed_root = Path(_documents.MEDIA_DIR).resolve()
    else:
        candidate = (Path(_documents.BASE_DIR) / raw_path).resolve()
        allowed_root = Path(_documents.BASE_DIR).resolve()

    if candidate != allowed_root and allowed_root not in candidate.parents:
        raise HTTPException(status_code=404, detail="Chemin du document invalide.")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Fichier du document introuvable sur ce serveur.")
    return candidate


@router.get('/resource-bridge-options', summary='Cibles autorisées pour un pont mobile de ressource')
def get_resource_bridge_options(
    resource_type: str,
    resource_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    resource_type = _resource_type(resource_type)
    resource = _resource_entity(db, current_user, resource_type, resource_id)
    targets = _resource_bridge_target_users(db, current_user, resource_type, resource)
    return {
        "resource_type": resource_type,
        "resource_label": _resource_label(resource_type),
        "targets": [{
            "id": user.id,
            "name": user.nom_complet or user.email,
            "email": user.email,
            "role": _role_name(user),
            "is_current_user": user.id == current_user.id,
        } for user in targets],
        "expires_in": 300,
        "contains_patient_data": False,
        "contains_resource_data": False,
    }


@router.post('/resource-bridge-pairing', summary='Générer un pont opaque vers une ressource mobile')
def create_resource_bridge_pairing(
    body: ResourceBridgePairingRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    resource_type = _resource_type(body.resource_type)
    resource = _resource_entity(db, current_user, resource_type, body.resource_id)
    target = _resolve_resource_bridge_target(db, current_user, body.target_user_id, resource_type, resource)
    _resource_entity(db, target, resource_type, body.resource_id)

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
        target_user_id=target.id, device_id=None, resource_type=resource_type,
        resource_id=int(body.resource_id), created_at=now,
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
        logger.error("Resource QR generation failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Échec de génération du QR Code.") from exc

    db.commit()
    db.refresh(record)
    _admin_legacy.audit_service.log(
        db=db, user_id=current_user.id, employer_id=employer_id,
        action="MOBILE_RESOURCE_BRIDGE_ISSUED", resource_type=resource_type,
        resource_id=str(getattr(resource, "id", body.resource_id)), severity="WARNING",
        details=f"Pont mobile {resource_type} généré pour user_id={target.id}; QR opaque sans donnée clinique.",
    )
    return {
        "qr_code": f"data:image/png;base64,{img_str}", "expires_in": 300,
        "lan_url": base_url, "token_code": manual_code, "target_user_id": target.id,
        "target_user_name": target.nom_complet or target.email, "target_role": _role_name(target),
        "resource_type": resource_type, "resource_label": _resource_label(resource_type),
        "contains_patient_data": False, "contains_resource_data": False,
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

    state, reason, _error_status = _context_state(db, mobile_user, context)
    return {
        "destination": "context", "label": _resource_label(str(context["resource_type"])), "fallback": False,
        "context": {"type": context["resource_type"], "key": context["context_key"], "state": state, "reason": reason},
    }


@router.post('/resource-context', summary='Relire une ressource mobile contextuelle autorisée')
def get_resource_context(
    body: ResourceContextRequest,
    authorization: str = Header(...),
    db: Session = Depends(database.get_db),
):
    mobile_user, context = _validated_mobile_context(db, authorization, body.context_key)
    resource_type = str(context["resource_type"])

    if resource_type == "patient":
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

    if resource_type == "panoramic":
        analysis = _panoramic_resource(db, mobile_user, int(context["resource_id"]))
        patient = db.query(models.Patient).filter(
            models.Patient.id == analysis.patient_id,
            models.Patient.employer_id == mobile_user.get_employer_id(),
            models.Patient.deleted_at.is_(None),
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient de la radio panoramique indisponible.")
        detections = analysis.detections_data if isinstance(analysis.detections_data, dict) else {}
        landmarks = detections.get("detections") if isinstance(detections.get("detections"), list) else []
        return {
            "type": "panoramic",
            "label": "Radio panoramique",
            "panoramic": {
                "patient_name": f"{patient.nom.upper()} {patient.prenom}",
                "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                "landmarks_count": len(landmarks),
                "report_saved": bool((analysis.report_narrative or "").strip()),
            },
        }

    if resource_type == "document":
        document = _document_resource(db, mobile_user, int(context["resource_id"]))
        patient = db.query(models.Patient).filter(
            models.Patient.id == document.patient_id,
            models.Patient.employer_id == mobile_user.get_employer_id(),
            models.Patient.deleted_at.is_(None),
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient du document indisponible.")
        doc_type = getattr(document.document_type, "value", document.document_type)
        return {
            "type": "document",
            "label": "Document",
            "document": {
                "patient_name": f"{patient.nom.upper()} {patient.prenom}",
                "document_type": str(doc_type),
                "name": document.title or document.original_filename or document.filename,
                "filename": document.original_filename or document.filename,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "mime_type": mimetypes.guess_type(document.original_filename or document.filename or "")[0] or "application/octet-stream",
            },
        }

    if resource_type == "appointment":
        appointment = _appointment_resource(db, mobile_user, int(context["resource_id"]))
        patient_name = appointment.patient_name or "Patient externe"
        if appointment.patient_id:
            patient = db.query(models.Patient).filter(
                models.Patient.id == appointment.patient_id,
                models.Patient.employer_id == mobile_user.get_employer_id(),
                models.Patient.deleted_at.is_(None),
            ).first()
            if not patient:
                raise HTTPException(status_code=404, detail="Patient du rendez-vous indisponible.")
            patient_name = f"{patient.nom.upper()} {patient.prenom}"
        status_value = getattr(appointment.status, "value", appointment.status)
        scheduling_value = getattr(appointment.scheduling_type, "value", appointment.scheduling_type)
        return {
            "type": "appointment",
            "label": "Rendez-vous",
            "appointment": {
                "patient_name": patient_name,
                "datetime_start": appointment.datetime_start.isoformat() if appointment.datetime_start else None,
                "duration_minutes": appointment.duration_minutes,
                "motif": appointment.motif or "",
                "status": str(status_value),
                "scheduling_type": str(scheduling_value),
                "notes": appointment.notes,
            },
        }

    raise HTTPException(status_code=422, detail="Type de ressource mobile non pris en charge.")


@router.post('/resource-context-media', summary='Charger le média protégé du contexte mobile')
def get_resource_context_media(
    body: ResourceContextRequest,
    authorization: str = Header(...),
    db: Session = Depends(database.get_db),
):
    mobile_user, context = _validated_mobile_context(db, authorization, body.context_key)
    resource_type = str(context["resource_type"])

    if resource_type == "panoramic":
        analysis = _panoramic_resource(db, mobile_user, int(context["resource_id"]))
        raw_path = str(analysis.image_path or "").strip().lstrip("/")
        if raw_path.startswith("api/"):
            raw_path = raw_path[4:]

        backend_root = Path(__file__).resolve().parents[1]
        allowed_root = (backend_root / "static" / "uploads" / "panoramic").resolve()
        candidate = (backend_root / raw_path).resolve()
        if candidate != allowed_root and allowed_root not in candidate.parents:
            raise HTTPException(status_code=404, detail="Média panoramique invalide.")
        if not candidate.is_file():
            raise HTTPException(status_code=404, detail="Média panoramique introuvable.")

        media_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        return FileResponse(
            path=str(candidate),
            media_type=media_type,
            filename=None,
            headers={"Cache-Control": "private, no-store, max-age=0", "Pragma": "no-cache"},
        )

    if resource_type == "document":
        document = _document_resource(db, mobile_user, int(context["resource_id"]))
        candidate = _document_file(document)
        media_type = mimetypes.guess_type(document.original_filename or candidate.name)[0] or "application/octet-stream"
        _admin_legacy.audit_service.log(
            db=db,
            user_id=mobile_user.id,
            employer_id=mobile_user.get_employer_id(),
            action="MEDIA_ACCESS_GRANTED",
            resource_type=str(getattr(document.document_type, "value", document.document_type)),
            resource_id=str(document.id),
            severity="INFO",
            details=f"Document mobile contextuel {document.id} chargé sur appareil appairé.",
        )
        return FileResponse(
            path=str(candidate),
            media_type=media_type,
            filename=None,
            headers={"Cache-Control": "private, no-store, max-age=0", "Pragma": "no-cache"},
        )

    raise HTTPException(status_code=422, detail="Ce contexte mobile ne contient pas de média chargeable.")
