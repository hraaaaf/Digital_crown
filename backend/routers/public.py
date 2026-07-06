"""
Routes publiques (sans authentification) — landing page, demandes de démo.
"""
import json
import os
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.config import settings
from backend.main import invalidate_license_cache
from backend.services.license_service import LicenseService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Public"])

_DEMO_REQUESTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "demo_requests.json"
)


def _load_requests() -> list:
    if not os.path.exists(_DEMO_REQUESTS_FILE):
        return []
    try:
        with open(_DEMO_REQUESTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_requests(requests: list) -> None:
    os.makedirs(os.path.dirname(_DEMO_REQUESTS_FILE), exist_ok=True)
    with open(_DEMO_REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)


class DemoRequestIn(BaseModel):
    nom: str
    email: EmailStr
    cabinet: str
    telephone: str = ""
    message: str = ""


def _get_valid_trial_code(db: Session, code_value: str) -> models.TrialActivationCode:
    normalized = code_value.strip().upper()
    code = db.query(models.TrialActivationCode).filter(models.TrialActivationCode.code == normalized).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code d'activation introuvable.")
    if code.revoked_at:
        raise HTTPException(status_code=400, detail="Ce code d'activation a été révoqué.")
    if code.consumed_at:
        raise HTTPException(status_code=400, detail="Ce code d'activation a déjà été utilisé.")
    if code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Ce code d'activation a expiré.")
    return code


@router.post("/demo-request", summary="Soumettre une demande de démo")
def submit_demo_request(payload: DemoRequestIn):
    requests = _load_requests()
    entry = {
        "id": len(requests) + 1,
        "nom": payload.nom.strip(),
        "email": payload.email,
        "cabinet": payload.cabinet.strip(),
        "telephone": payload.telephone.strip(),
        "message": payload.message.strip(),
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "NEW",
    }
    requests.append(entry)
    _save_requests(requests)

    # Notification email non-bloquante
    try:
        from backend.services.email_service import email_service
        body = (
            f"Nouvelle demande de démo DigitalCrown\n\n"
            f"Nom : {entry['nom']}\n"
            f"Email : {entry['email']}\n"
            f"Cabinet : {entry['cabinet']}\n"
            f"Téléphone : {entry['telephone']}\n"
            f"Message : {entry['message']}\n"
            f"Date : {entry['submitted_at']}"
        )
        email_service.send_email(
            to_email="contact@digitalcrown.dz",
            subject=f"[DÉMO] {entry['nom']} — {entry['cabinet']}",
            body=body,
        )
    except Exception:
        pass  # Email optionnel — on ne bloque pas si non configuré

    return {"success": True, "message": "Votre demande a bien été reçue. Nous vous contacterons sous 24h."}


@router.get("/demo-requests", summary="Lister les demandes (super-admin)")
def list_demo_requests(secret: str = ""):
    """Protégé par un simple secret en query param pour le super-admin."""
    expected = os.getenv("SUPERADMIN_SECRET", "")
    if not expected or secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    return _load_requests()


@router.get("/trial-code/{code}", response_model=schemas.TrialActivationPreview, summary="Prévisualiser un code d'activation")
def preview_trial_code(code: str, db: Session = Depends(database.get_db)):
    trial_code = _get_valid_trial_code(db, code)
    return schemas.TrialActivationPreview(
        email=trial_code.email,
        nom_complet=trial_code.nom_complet,
        cabinet_name=trial_code.cabinet_name,
        trial_days=trial_code.trial_days,
        expires_at=trial_code.expires_at,
    )


@router.post("/activate-trial", summary="Activer un essai 30 jours via code")
async def activate_trial_code(
    payload: schemas.TrialActivationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    if not payload.accept_terms or not payload.accept_privacy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous devez accepter les CGU et la politique de confidentialité pour activer l'essai.",
        )

    trial_code = _get_valid_trial_code(db, payload.code)
    normalized_email = payload.email.lower().strip()
    if normalized_email != trial_code.email.lower().strip():
        raise HTTPException(status_code=400, detail="Ce code est lié à une autre adresse email.")

    user = db.query(models.User).filter(models.User.email == normalized_email).first()
    from backend.security import get_password_hash

    now = datetime.utcnow()
    expiry = now + timedelta(days=trial_code.trial_days)

    if user and user.is_active:
        raise HTTPException(status_code=400, detail="Un compte actif existe déjà pour cet email.")

    if user:
        user.hashed_password = get_password_hash(payload.password)
        user.nom_complet = payload.nom_complet
        user.role = models.UserRole.ADMIN
        user.is_active = True
        user.is_licensed = True
        user.license_expires_at = expiry
        user.subscription_plan = models.SubscriptionPlan.ELITE.value
        user.approval_status = models.ApprovalStatus.APPROVED.value
    else:
        user = models.User(
            email=normalized_email,
            hashed_password=get_password_hash(payload.password),
            role=models.UserRole.ADMIN,
            nom_complet=payload.nom_complet,
            is_active=True,
            is_licensed=True,
            license_expires_at=expiry,
            subscription_plan=models.SubscriptionPlan.ELITE.value,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        db.add(user)
        db.flush()

    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
    if not cabinet:
        display_name = payload.nom_complet if payload.nom_complet.startswith("Dr.") else f"Dr. {payload.nom_complet}"
        cabinet = models.CabinetConfig(
            owner_id=user.id,
            nom_cabinet=(payload.cabinet_name or trial_code.cabinet_name or payload.nom_complet).strip(),
            nom_praticien=payload.nom_complet,
            header_lines_fr=[display_name],
            is_initialized=False,
            font_fr="Inter",
            font_ar="Amiri",
            primary_color="#003380",
            secondary_color="#1e40af",
            accent_color="#60a5fa",
            margin_top=3.6,
            margin_bottom=3.2,
        )
        db.add(cabinet)
        db.flush()
    else:
        cabinet.nom_cabinet = (payload.cabinet_name or trial_code.cabinet_name or cabinet.nom_cabinet or payload.nom_complet).strip()
        cabinet.nom_praticien = payload.nom_complet
        cabinet.is_initialized = False

    trial_code.consumed_at = now
    trial_code.consumed_by_user_id = user.id

    db.add(models.LicenseHistory(
        user_id=user.id,
        admin_id=trial_code.created_by_admin_id,
        action="TRIAL_CODE_ACTIVATED",
        duration=trial_code.trial_days,
    ))
    db.commit()
    db.refresh(cabinet)

    invalidate_license_cache(user.email)
    background_tasks.add_task(
        LicenseService().write_license,
        public_id=cabinet.public_id,
        active=True,
        expiration_date=expiry,
    )

    return {
        "status": "success",
        "message": "Essai activé avec succès. Connectez-vous pour finaliser l'installation.",
        "email": user.email,
        "license_expires_at": expiry,
        "activation_url": f"{settings.APP_PUBLIC_URL.rstrip('/')}/login",
    }
