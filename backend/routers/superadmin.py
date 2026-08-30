import secrets
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from backend import database, models
from backend.config import settings
from backend.license_issuer import LicenseIssuerUnavailable, issue_license
from backend.license_security import LicenseSecurityError
from backend.main import invalidate_license_cache
from backend.platform_access import has_platform_permission, is_platform_superadmin
from backend.platform_step_up import enforce_platform_step_up_for_mutation
from backend.routers.auth import get_current_user
from backend.routers.superadmin_passkey import router as platform_passkey_router
from backend.schemas.superadmin import (
    ClientBaseStats,
    ClientOut,
    LicenseHistoryOut,
    SendRenewalEmailRequest,
    TrialActivationCodeCreate,
    TrialActivationCodeOut,
    UpdateClientNotes,
)
from backend.services.license_service import LicenseService
from backend.services.notification_service import notification_service

router = APIRouter(tags=["SuperAdmin"])
router.include_router(platform_passkey_router)
_LICENSE_DURATIONS = {"1m": 30, "3m": 90, "6m": 180, "1y": 365}


def verify_superadmin(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not is_platform_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Accès refusé. Réservé au SuperAdmin.")
    enforce_platform_step_up_for_mutation(request, current_user=current_user, db=db)
    return current_user


def _assert_platform_permission(
    permission: str,
    *,
    request: Request,
    db: Session,
    current_user: models.User,
) -> None:
    if not has_platform_permission(current_user, permission):
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Permission plateforme insuffisante.",
        )
    enforce_platform_step_up_for_mutation(request, current_user=current_user, db=db)


def require_platform_permission(permission: str):
    def dependency(
        request: Request,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user),
    ):
        _assert_platform_permission(
            permission,
            request=request,
            db=db,
            current_user=current_user,
        )
        return current_user
    return dependency


def _paid_license_permission(effective: dict) -> str:
    """Choose create-vs-extend authority from signed entitlement truth."""
    if effective.get("active") and str(effective.get("license_type") or "").upper() == "PAID":
        return "license.extend"
    return "license.create_paid"


def add_license_history(db: Session, user_id: int, admin_id: int, action: str, duration: int = None):
    history = models.LicenseHistory(
        user_id=user_id,
        admin_id=admin_id,
        action=action,
        duration=duration,
    )
    db.add(history)


def add_platform_audit(
    db: Session,
    *,
    admin_id: int,
    action: str,
    resource_type: str,
    resource_id: int | str | None = None,
    details: str | None = None,
    severity: str = "INFO",
) -> None:
    """Stage a privileged audit event in the caller's transaction."""
    db.add(
        models.AuditLog(
            user_id=admin_id,
            employer_id=None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            severity=severity,
            details=details,
        )
    )


def _build_activation_url(code: str) -> str:
    base_url = settings.APP_PUBLIC_URL.rstrip("/")
    return f"{base_url}/activate?code={code}"


def _serialize_trial_code(code: models.TrialActivationCode) -> TrialActivationCodeOut:
    return TrialActivationCodeOut(
        id=code.id,
        code=code.code,
        email=code.email,
        nom_complet=code.nom_complet,
        cabinet_name=code.cabinet_name,
        trial_days=code.trial_days,
        notes=code.notes,
        expires_at=code.expires_at,
        consumed_at=code.consumed_at,
        revoked_at=code.revoked_at,
        created_at=code.created_at,
        activation_url=_build_activation_url(code.code),
    )


def _generate_trial_code() -> str:
    chunks = [
        secrets.token_hex(2).upper(),
        secrets.token_hex(2).upper(),
        secrets.token_hex(2).upper(),
    ]
    return f"DC-{chunks[0]}-{chunks[1]}-{chunks[2]}"


def _license_identifier(cabinet: models.CabinetConfig) -> str:
    return str(cabinet.clinic_id or cabinet.public_id)


async def _issue_and_store_signed_license(
    *,
    cabinet: models.CabinetConfig,
    license_type: str,
    created_by_user_id: int,
    expires_at: datetime | None,
    status: str = "ACTIVE",
    max_devices: int | None = 1,
    subject_user_id: int | None = None,
    feature_set: str = "full",
) -> str:
    clinic_id = _license_identifier(cabinet)
    try:
        signed_license = issue_license(
            cabinet_id=clinic_id,
            license_type=license_type,
            created_by_user_id=created_by_user_id,
            expires_at=expires_at,
            release_channel="stable",
            feature_set=feature_set,
            max_devices=max_devices,
            status=status,
            subject_user_id=subject_user_id,
        )
    except (LicenseIssuerUnavailable, LicenseSecurityError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Émission de licence indisponible. Clé de signature non provisionnée.",
        ) from exc

    stored = await LicenseService().write_signed_license(
        public_id=clinic_id,
        signed_license=signed_license,
    )
    if not stored:
        raise HTTPException(
            status_code=503,
            detail="Licence signée générée mais non persistée. Aucune activation appliquée.",
        )
    return signed_license


@router.get("/clients", response_model=List[ClientOut])
def get_clients(
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_platform_permission("license.read")),
):
    clients = db.query(models.User).filter(
        models.User.role.in_([models.UserRole.ADMIN, models.UserRole.DENTISTE]),
        models.User.employer_id == None,
    ).all()

    result = []
    for c in clients:
        total_patients = db.query(models.Patient).filter(models.Patient.employer_id == c.id).count()
        patients_subquery = db.query(models.Patient.id).filter(models.Patient.employer_id == c.id).subquery()
        total_pano = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.patient_id.in_(patients_subquery)).count()
        total_ceph = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id.in_(patients_subquery)).count()

        c_dict = c.__dict__.copy()
        c_dict["stats"] = ClientBaseStats(
            total_patients=total_patients,
            total_ia_panoramique=total_pano,
            total_ia_cephalo=total_ceph,
        )
        result.append(c_dict)
    return result


@router.get("/audit")
def get_platform_audit(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_platform_permission("audit.read")),
):
    rows = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.action.like("SUPERADMIN_%"))
        .order_by(models.AuditLog.timestamp.desc(), models.AuditLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "timestamp": row.timestamp,
            "user_id": row.user_id,
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "severity": row.severity,
            "details": row.details,
        }
        for row in rows
    ]


@router.post("/clients/{user_id}/validate")
async def validate_client(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(verify_superadmin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
    if not cabinet:
        raise HTTPException(
            status_code=409,
            detail="Cabinet non configuré : impossible d'émettre une licence signée.",
        )

    now_utc = datetime.now(timezone.utc)
    expiry_utc = now_utc + timedelta(days=30)
    await _issue_and_store_signed_license(
        cabinet=cabinet,
        license_type="TRIAL",
        created_by_user_id=admin.id,
        expires_at=expiry_utc,
        max_devices=1,
        feature_set=user.subscription_plan or models.SubscriptionPlan.GOLD.value,
    )

    user.is_active = True
    user.is_licensed = True
    user.license_expires_at = expiry_utc.replace(tzinfo=None)
    add_license_history(db, user_id, admin.id, "COMPTE_VALIDE_ESSAI_30J", 30)
    add_platform_audit(
        db,
        admin_id=admin.id,
        action="SUPERADMIN_CLIENT_VALIDATE",
        resource_type="User",
        resource_id=user_id,
        details="trial_days=30",
        severity="WARNING",
    )
    db.commit()
    invalidate_license_cache(user.email)

    try:
        from backend.services.email_service import email_service
        background_tasks.add_task(
            email_service.send_account_activated,
            user.email,
            user.nom_complet,
            user.license_expires_at,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Email activation non programme pour %s: %s", user.email, e)

    return {"status": "success", "message": f"Compte de {user.email} activé avec 30 jours d'essai."}


@router.get("/trial-codes", response_model=List[TrialActivationCodeOut])
def list_trial_codes(
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_platform_permission("license.read")),
):
    codes = (
        db.query(models.TrialActivationCode)
        .order_by(models.TrialActivationCode.created_at.desc())
        .all()
    )
    return [_serialize_trial_code(code) for code in codes]


@router.post("/trial-codes", response_model=TrialActivationCodeOut)
def create_trial_code(
    payload: TrialActivationCodeCreate,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_platform_permission("license.create_trial")),
):
    expires_in_days = max(1, min(payload.expires_in_days, 60))
    trial_days = max(1, min(payload.trial_days, 90))
    code = models.TrialActivationCode(
        code=_generate_trial_code(),
        email=payload.email.lower().strip(),
        nom_complet=(payload.nom_complet or "").strip() or None,
        cabinet_name=(payload.cabinet_name or "").strip() or None,
        trial_days=trial_days,
        notes=(payload.notes or "").strip() or None,
        expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
        created_by_admin_id=admin.id,
    )
    db.add(code)
    db.flush()
    add_platform_audit(
        db,
        admin_id=admin.id,
        action="SUPERADMIN_TRIAL_CREATE",
        resource_type="TrialActivationCode",
        resource_id=code.id,
        details=f"trial_days={trial_days};expires_in_days={expires_in_days}",
        severity="WARNING",
    )
    db.commit()
    db.refresh(code)
    return _serialize_trial_code(code)


@router.post("/trial-codes/{code_id}/revoke", response_model=TrialActivationCodeOut)
def revoke_trial_code(
    code_id: int,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_platform_permission("license.revoke")),
):
    code = db.query(models.TrialActivationCode).filter(models.TrialActivationCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code introuvable.")
    if code.consumed_at:
        raise HTTPException(status_code=400, detail="Ce code a déjà été consommé.")

    code.revoked_at = datetime.utcnow()
    add_platform_audit(
        db,
        admin_id=admin.id,
        action="SUPERADMIN_TRIAL_REVOKE",
        resource_type="TrialActivationCode",
        resource_id=code_id,
        severity="WARNING",
    )
    db.commit()
    db.refresh(code)
    return _serialize_trial_code(code)


@router.post("/clients/{user_id}/grant-license")
async def grant_license(
    user_id: int,
    request: Request,
    action: str = Query(...),
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_user),
):
    if action == "revoke":
        _assert_platform_permission(
            "license.revoke", request=request, db=db, current_user=admin
        )
    elif action in _LICENSE_DURATIONS:
        if not (
            has_platform_permission(admin, "license.create_paid")
            or has_platform_permission(admin, "license.extend")
        ):
            raise HTTPException(
                status_code=403,
                detail="Accès refusé. Permission plateforme insuffisante.",
            )
        enforce_platform_step_up_for_mutation(request, current_user=admin, db=db)
    else:
        raise HTTPException(status_code=400, detail="Action non valide.")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
    if not cabinet:
        raise HTTPException(status_code=409, detail="Cabinet non configuré : impossible d'émettre une licence signée.")

    clinic_id = _license_identifier(cabinet)
    effective = await LicenseService().get_effective_license(clinic_id)
    effective_type = str(effective.get("license_type") or "").upper()
    if effective.get("active") and effective_type == "OWNER":
        raise HTTPException(
            status_code=400,
            detail="L'entitlement OWNER ne peut pas être modifié via une licence client.",
        )

    now_utc = datetime.now(timezone.utc)
    now_db = now_utc.replace(tzinfo=None)
    current_expiry_db = (
        user.license_expires_at
        if user.license_expires_at and user.license_expires_at > now_db
        else now_db
    )

    if action == "revoke":
        previous_expiry = user.license_expires_at
        expiry_utc = previous_expiry.replace(tzinfo=timezone.utc) if previous_expiry else now_utc
        await _issue_and_store_signed_license(
            cabinet=cabinet,
            license_type="PAID",
            created_by_user_id=admin.id,
            expires_at=expiry_utc,
            status="REVOKED",
            max_devices=1,
            feature_set=user.subscription_plan or models.SubscriptionPlan.GOLD.value,
        )
        user.license_expires_at = now_db - timedelta(days=1)
        user.is_licensed = False
        add_license_history(db, user_id, admin.id, "revoke")
        add_platform_audit(
            db,
            admin_id=admin.id,
            action="SUPERADMIN_LICENSE_REVOKE",
            resource_type="User",
            resource_id=user_id,
            severity="CRITICAL",
        )
        db.commit()
        invalidate_license_cache(user.email)
        return {"status": "success", "license_expires_at": user.license_expires_at}

    required_permission = _paid_license_permission(effective)
    if not has_platform_permission(admin, required_permission):
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Permission plateforme insuffisante.",
        )

    duration = _LICENSE_DURATIONS[action]
    new_expiry_db = current_expiry_db + timedelta(days=duration)
    new_expiry_utc = new_expiry_db.replace(tzinfo=timezone.utc)
    await _issue_and_store_signed_license(
        cabinet=cabinet,
        license_type="PAID",
        created_by_user_id=admin.id,
        expires_at=new_expiry_utc,
        max_devices=1,
        feature_set=user.subscription_plan or models.SubscriptionPlan.GOLD.value,
    )
    user.license_expires_at = new_expiry_db
    user.is_licensed = True
    add_license_history(db, user_id, admin.id, "grant", duration)
    add_platform_audit(
        db,
        admin_id=admin.id,
        action="SUPERADMIN_LICENSE_GRANT",
        resource_type="User",
        resource_id=user_id,
        details=f"duration_days={duration};permission={required_permission}",
        severity="WARNING",
    )
    db.commit()
    invalidate_license_cache(user.email)
    return {"status": "success", "license_expires_at": user.license_expires_at}


@router.patch("/clients/{user_id}/archive")
def archive_client(
    user_id: int,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(verify_superadmin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    user.is_archived = not user.is_archived
    action = "SUPERADMIN_CLIENT_ARCHIVE" if user.is_archived else "SUPERADMIN_CLIENT_UNARCHIVE"
    add_license_history(db, user_id, admin.id, "archive" if user.is_archived else "unarchive")
    add_platform_audit(
        db,
        admin_id=admin.id,
        action=action,
        resource_type="User",
        resource_id=user_id,
        severity="WARNING",
    )
    db.commit()
    invalidate_license_cache(user.email)
    return {"status": "success", "is_archived": user.is_archived}


@router.patch("/clients/{user_id}/suspend")
def suspend_client(
    user_id: int,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(verify_superadmin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    user.is_suspended = not user.is_suspended
    action = "SUPERADMIN_CLIENT_SUSPEND" if user.is_suspended else "SUPERADMIN_CLIENT_UNSUSPEND"
    add_license_history(db, user_id, admin.id, "suspend" if user.is_suspended else "unsuspend")
    add_platform_audit(
        db,
        admin_id=admin.id,
        action=action,
        resource_type="User",
        resource_id=user_id,
        severity="CRITICAL" if user.is_suspended else "WARNING",
    )
    db.commit()
    invalidate_license_cache(user.email)
    return {"status": "success", "is_suspended": user.is_suspended}


@router.patch("/clients/{user_id}/plan")
async def set_client_plan(
    user_id: int,
    plan: str = Query(...),
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(verify_superadmin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    valid_plans = {p.value for p in models.SubscriptionPlan}
    if plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Pack invalide. Valeurs autorisées : {sorted(valid_plans)}")

    previous_plan = user.subscription_plan
    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
    if user.is_licensed:
        if not cabinet:
            raise HTTPException(status_code=409, detail="Cabinet non configuré : impossible de réaligner la licence signée.")

        clinic_id = _license_identifier(cabinet)
        effective = await LicenseService().get_effective_license(clinic_id)
        if not effective.get("active"):
            raise HTTPException(status_code=409, detail="Licence signée active introuvable : changement de pack refusé.")

        license_type = str(effective.get("license_type") or "PAID")
        if license_type == "OWNER":
            raise HTTPException(status_code=400, detail="Le plan commercial OWNER ne peut pas être modifié via un client.")

        expiry = effective.get("expiration_date")
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        if isinstance(expiry, datetime) and expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        await _issue_and_store_signed_license(
            cabinet=cabinet,
            license_type=license_type,
            created_by_user_id=admin.id,
            expires_at=expiry,
            max_devices=1,
            feature_set=plan,
        )

    user.subscription_plan = plan
    add_license_history(db, user_id, admin.id, f"SET_PLAN_{plan}")
    add_platform_audit(
        db,
        admin_id=admin.id,
        action="SUPERADMIN_PLAN_CHANGE",
        resource_type="User",
        resource_id=user_id,
        details=f"from={previous_plan or 'NONE'};to={plan}",
        severity="WARNING",
    )
    db.commit()
    invalidate_license_cache(user.email)
    return {"status": "success", "subscription_plan": user.subscription_plan}


@router.patch("/clients/{user_id}/notes")
def update_client_notes(
    user_id: int,
    data: UpdateClientNotes,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(verify_superadmin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    user.internal_notes = data.internal_notes
    add_platform_audit(
        db,
        admin_id=admin.id,
        action="SUPERADMIN_CLIENT_NOTES_UPDATE",
        resource_type="User",
        resource_id=user_id,
        details="internal_notes_updated=true",
    )
    db.commit()
    return {"status": "success", "internal_notes": user.internal_notes}


@router.get("/clients/{user_id}/license-history", response_model=List[LicenseHistoryOut])
def get_license_history(
    user_id: int,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_platform_permission("license.read")),
):
    return (
        db.query(models.LicenseHistory)
        .filter(models.LicenseHistory.user_id == user_id)
        .order_by(models.LicenseHistory.timestamp.desc())
        .all()
    )


@router.post("/clients/{user_id}/send-renewal-email")
def send_renewal_email(
    user_id: int,
    data: SendRenewalEmailRequest,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(verify_superadmin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    phone = user.telephone_mobile or user.telephone_fixe
    add_platform_audit(
        db,
        admin_id=admin.id,
        action="SUPERADMIN_RENEWAL_REQUESTED",
        resource_type="User",
        resource_id=user_id,
        details="channel=whatsapp" if phone else "channel=whatsapp;not_sent=no_phone",
    )
    add_license_history(db, user_id, admin.id, "renewal_whatsapp_requested")
    db.commit()

    if phone:
        msg = f"Bonjour Dr. {user.nom_complet}, votre licence Digital Crown expire bientôt. {data.message}"
        notification_service.send_whatsapp_via_whatsmate(phone, msg)
        message_status = f"WhatsApp de relance envoyé avec succès à {phone}."
    else:
        message_status = "Aucun numéro de téléphone trouvé pour l'envoi WhatsApp."

    return {"status": "success", "message": message_status}
