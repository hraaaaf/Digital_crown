"""
Routes publiques (sans authentification) — landing page, demandes de démo et
activation Trial. SEC-1 sépare strictement cabinet et control-plane : un cabinet
ne possède jamais la clé de signature et ne fait que vérifier un token signé.
"""
import hashlib
import json
import os
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.config import settings
from backend.license_issuer import LicenseIssuerUnavailable, issue_license
from backend.license_security import LicenseSecurityError
from backend.main import invalidate_license_cache
from backend.platform_access import is_platform_superadmin
from backend.routers.auth import get_current_user
from backend.services.license_control_plane_client import (
    LicenseControlPlaneClient,
    LicenseControlPlaneError,
)
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
    """Control-plane-only lookup of the authoritative Trial code table."""
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


def _license_identifier(cabinet: models.CabinetConfig) -> str:
    return str(cabinet.clinic_id or cabinet.public_id)


def _stable_trial_public_id(email: str, code: str) -> str:
    """Stable across a rolled-back first activation so remote redemption is retryable."""
    material = f"{email.strip().lower()}|{code.strip().upper()}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:16]


async def _sign_and_store_trial_license(
    *,
    cabinet: models.CabinetConfig,
    trial_code: models.TrialActivationCode,
    expiry: datetime,
) -> str:
    """Control-plane-only direct issuance. Distributed cabinets never call this."""
    if not settings.PLATFORM_CONTROL_PLANE_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")
    if trial_code.created_by_admin_id is None:
        raise HTTPException(
            status_code=409,
            detail="Code d'activation legacy non attribué : émission signée impossible.",
        )

    clinic_id = _license_identifier(cabinet)
    expiry_utc = expiry.replace(tzinfo=timezone.utc) if expiry.tzinfo is None else expiry.astimezone(timezone.utc)
    try:
        signed_license = issue_license(
            cabinet_id=clinic_id,
            license_type="TRIAL",
            created_by_user_id=trial_code.created_by_admin_id,
            expires_at=expiry_utc,
            release_channel="stable",
            feature_set=models.SubscriptionPlan.GOLD.value,
            max_devices=1,
        )
    except (LicenseIssuerUnavailable, LicenseSecurityError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Activation indisponible : service de signature de licence non provisionné.",
        ) from exc

    stored = await LicenseService().write_signed_license(
        public_id=clinic_id,
        signed_license=signed_license,
    )
    if not stored:
        raise HTTPException(
            status_code=503,
            detail="Licence signée non persistée. L'essai n'a pas été activé.",
        )
    return signed_license


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
        pass

    return {"success": True, "message": "Votre demande a bien été reçue. Nous vous contacterons sous 24h."}


@router.get("/demo-requests", summary="Lister les demandes (super-admin)")
def list_demo_requests(current_user: models.User = Depends(get_current_user)):
    if not is_platform_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Forbidden")
    return _load_requests()


@router.get(
    "/trial-code/{code}",
    response_model=schemas.TrialActivationPreview,
    summary="Prévisualiser un code d'activation",
)
async def preview_trial_code(code: str, db: Session = Depends(database.get_db)):
    if settings.PLATFORM_CONTROL_PLANE_ENABLED:
        trial_code = _get_valid_trial_code(db, code)
        return schemas.TrialActivationPreview(
            email=trial_code.email,
            nom_complet=trial_code.nom_complet,
            cabinet_name=trial_code.cabinet_name,
            trial_days=trial_code.trial_days,
            expires_at=trial_code.expires_at,
        )

    try:
        data = await LicenseControlPlaneClient().preview_trial(code)
    except LicenseControlPlaneError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    try:
        return schemas.TrialActivationPreview(**data)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Réponse Trial distante invalide.") from exc


@router.post("/activate-trial", summary="Activer un essai via code")
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

    normalized_code = payload.code.strip().upper()
    normalized_email = payload.email.lower().strip()
    trial_code = None
    remote_preview = None

    if settings.PLATFORM_CONTROL_PLANE_ENABLED:
        trial_code = _get_valid_trial_code(db, normalized_code)
        expected_email = trial_code.email.lower().strip()
    else:
        try:
            remote_preview = await LicenseControlPlaneClient().preview_trial(normalized_code)
        except LicenseControlPlaneError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        expected_email = str(remote_preview.get("email") or "").lower().strip()

    if normalized_email != expected_email:
        raise HTTPException(status_code=400, detail="Ce code est lié à une autre adresse email.")

    user = db.query(models.User).filter(models.User.email == normalized_email).first()
    if user and user.is_active:
        raise HTTPException(status_code=400, detail="Un compte actif existe déjà pour cet email.")

    from backend.security import get_password_hash

    now_utc = datetime.now(timezone.utc)
    now_db = now_utc.replace(tzinfo=None)

    try:
        if user:
            user.hashed_password = get_password_hash(payload.password)
            user.nom_complet = payload.nom_complet
            user.role = models.UserRole.ADMIN
            user.is_active = True
            user.is_licensed = False
            user.license_expires_at = None
            user.subscription_plan = models.SubscriptionPlan.GOLD.value
            user.approval_status = models.ApprovalStatus.APPROVED.value
        else:
            user = models.User(
                email=normalized_email,
                hashed_password=get_password_hash(payload.password),
                role=models.UserRole.ADMIN,
                nom_complet=payload.nom_complet,
                is_active=True,
                is_licensed=False,
                license_expires_at=None,
                subscription_plan=models.SubscriptionPlan.GOLD.value,
                approval_status=models.ApprovalStatus.APPROVED.value,
            )
            db.add(user)
            db.flush()

        cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
        if not cabinet:
            preview_cabinet_name = (
                trial_code.cabinet_name if trial_code is not None
                else (remote_preview or {}).get("cabinet_name")
            )
            display_name = payload.nom_complet if payload.nom_complet.startswith("Dr.") else f"Dr. {payload.nom_complet}"
            cabinet = models.CabinetConfig(
                owner_id=user.id,
                public_id=_stable_trial_public_id(normalized_email, normalized_code),
                nom_cabinet=(payload.cabinet_name or preview_cabinet_name or payload.nom_complet).strip(),
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
            preview_cabinet_name = (
                trial_code.cabinet_name if trial_code is not None
                else (remote_preview or {}).get("cabinet_name")
            )
            cabinet.nom_cabinet = (
                payload.cabinet_name
                or preview_cabinet_name
                or cabinet.nom_cabinet
                or payload.nom_complet
            ).strip()
            cabinet.is_initialized = False

        clinic_id = _license_identifier(cabinet)
        local_admin_id = None

        if settings.PLATFORM_CONTROL_PLANE_ENABLED:
            expiry_db = now_db + timedelta(days=trial_code.trial_days)
            signed_license = await _sign_and_store_trial_license(
                cabinet=cabinet,
                trial_code=trial_code,
                expiry=expiry_db,
            )
            # The issuer timestamps at signing time, which is necessarily after
            # the request timestamp captured above. Verify against a fresh UTC
            # instant so a newly issued token cannot be rejected as "future".
            installed = LicenseService._verify_signed_license(
                signed_license,
                clinic_id,
                datetime.now(timezone.utc),
            )
            license_type = installed.license_type
            feature_set = installed.claims.get("feature_set")
            expiry_utc = installed.expires_at
            local_admin_id = trial_code.created_by_admin_id
        else:
            try:
                redemption = await LicenseControlPlaneClient().redeem_trial(
                    code=normalized_code,
                    email=normalized_email,
                    cabinet_id=clinic_id,
                )
            except LicenseControlPlaneError as exc:
                raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

            installed = LicenseService().install_signed_license(
                clinic_id,
                redemption.signed_license,
            )
            license_type = installed.get("license_type")
            feature_set = installed.get("feature_set")
            expiry_utc = installed.get("expiration_date")

        if license_type != "TRIAL" or feature_set != models.SubscriptionPlan.GOLD.value:
            if not settings.PLATFORM_CONTROL_PLANE_ENABLED:
                LicenseService()._clear_local_vault()
            raise HTTPException(
                status_code=503,
                detail="Entitlement Trial signé incompatible avec la politique locale.",
            )
        if not isinstance(expiry_utc, datetime):
            raise HTTPException(status_code=503, detail="Expiration signée invalide.")

        expiry_db = expiry_utc.astimezone(timezone.utc).replace(tzinfo=None)
        user.is_licensed = True
        user.license_expires_at = expiry_db

        if trial_code is not None:
            trial_code.consumed_at = now_db
            trial_code.consumed_by_user_id = user.id

        duration_days = max(1, int((expiry_utc - now_utc).total_seconds() // 86400))
        db.add(models.LicenseHistory(
            user_id=user.id,
            admin_id=local_admin_id,
            action=(
                "TRIAL_CODE_ACTIVATED_SIGNED_CONTROL_PLANE"
                if settings.PLATFORM_CONTROL_PLANE_ENABLED
                else "TRIAL_CODE_ACTIVATED_SIGNED_REMOTE"
            ),
            duration=duration_days,
        ))
        db.commit()
        db.refresh(cabinet)
    except HTTPException:
        db.rollback()
        raise
    except (LicenseSecurityError, RuntimeError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Licence Trial reçue mais non vérifiable/localement persistable.",
        ) from exc
    except Exception:
        db.rollback()
        raise

    invalidate_license_cache(user.email)

    return {
        "status": "success",
        "message": "Essai activé avec succès. Connectez-vous pour finaliser l'installation.",
        "email": user.email,
        "license_expires_at": expiry_db,
        "activation_url": f"{settings.APP_PUBLIC_URL.rstrip('/')}/login",
    }


# The issuer endpoints are mounted under /api/public/license-control by the same
# application only when the server is explicitly provisioned as a control-plane.
from backend.routers.license_control_plane import router as license_control_plane_router
router.include_router(license_control_plane_router, prefix="/license-control")
