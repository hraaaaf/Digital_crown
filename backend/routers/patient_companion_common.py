from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.routers.auth import has_permission, is_superadmin_user
from backend.security import ALGORITHM, SECRET_KEY
from backend.services.firebase_patient_auth import (
    FirebasePatientAuthInvalid,
    FirebasePatientAuthUnavailable,
    FirebasePatientCredential,
    verify_patient_id_token,
)

get_db = database.get_db
PROVIDER = "firebase"
LOCAL_BRIDGE_PROVIDER = "local_bridge"
PATIENT_DEVICE_TOKEN_TTL = timedelta(days=30)
MANUAL_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


@dataclass(frozen=True)
class PatientPrincipal:
    identity_id: int
    subject: str
    access_id: str
    employer_id: int
    patient_id: int
    relationship_type: str


def token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_manual_code(raw: str) -> str:
    return "".join(ch for ch in raw.upper() if ch.isalnum())


def manual_code_hash(raw: str) -> str:
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        normalize_manual_code(raw).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_manual_code() -> str:
    compact = "".join(secrets.choice(MANUAL_ALPHABET) for _ in range(12))
    return "-".join(compact[i:i + 4] for i in range(0, 12, 4))


def normalize_recipient(recipient_type: str, raw: str) -> str:
    if recipient_type == "email":
        value = raw.strip().lower()
        if not value or "@" not in value or len(value) > 254:
            raise ValueError("invalid email")
        return value
    if recipient_type == "phone":
        value = re.sub(r"[\s().-]", "", raw.strip())
        if value.startswith("00"):
            value = "+" + value[2:]
        if not re.fullmatch(r"\+[1-9]\d{7,14}", value):
            raise ValueError("phone must be E.164")
        return value
    raise ValueError("unsupported recipient type")


def recipient_hash(recipient_type: str, raw: str) -> str:
    normalized = normalize_recipient(recipient_type, raw)
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        f"{recipient_type}:{normalized}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def credential_recipient_hash(
    credential: FirebasePatientCredential,
    recipient_type: str,
) -> str | None:
    raw = credential.verified_email if recipient_type == "email" else credential.phone_number
    if not raw:
        return None
    try:
        return recipient_hash(recipient_type, raw)
    except ValueError:
        return None


def require_companion_admin(current_user: models.User) -> None:
    if is_superadmin_user(current_user):
        return
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role in {"ADMIN", "DENTISTE"} and current_user.employer_id is None:
        return
    raise HTTPException(
        status_code=403,
        detail="Administration Patient Companion réservée au praticien principal.",
    )


def require_companion_cabinet_write_license(db: Session, employer_id: int) -> None:
    """Mirror the cabinet write lock for Firebase-authenticated activation.

    Patient Companion Firebase requests intentionally do not use a cabinet JWT, so
    the global license middleware cannot resolve a staff account for them. Activation
    is a write and must therefore enforce the cabinet owner's local licence state
    before creating any identity/access binding.
    """
    owner = db.query(models.User).filter(
        models.User.id == int(employer_id),
        models.User.employer_id.is_(None),
    ).first()
    if owner is None:
        raise HTTPException(status_code=403, detail="Cabinet indisponible.")
    if owner.is_suspended or owner.is_archived or not owner.is_licensed:
        raise HTTPException(status_code=403, detail="Licence cabinet inactive.")
    if owner.license_expires_at and datetime.utcnow() > owner.license_expires_at:
        raise HTTPException(status_code=403, detail="Licence cabinet expirée.")


def staff_patient_or_404(db: Session, current_user: models.User, patient_id: int) -> models.Patient:
    require_companion_admin(current_user)
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Permission patients requise.")
    employer_id = int(current_user.get_employer_id())
    patient = (
        db.query(models.Patient)
        .filter(
            models.Patient.id == int(patient_id),
            models.Patient.employer_id == employer_id,
            models.Patient.deleted_at.is_(None),
        )
        .first()
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient introuvable.")
    return patient


def create_patient_device_token(identity: PatientCompanionIdentity, access: PatientCompanionAccess) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": identity.subject,
        "identity_id": identity.id,
        "access_id": access.public_id,
        "tenant_id": access.employer_id,
        "type": "patient_companion",
        "jti": f"patient-companion:{uuid.uuid4().hex}",
        "iat": now,
        "exp": now + PATIENT_DEVICE_TOKEN_TTL,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _patient_device_identity(raw_token: str, db: Session) -> PatientCompanionIdentity:
    err = HTTPException(status_code=401, detail="Session Patient Companion invalide ou expirée.")
    try:
        payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "patient_companion":
            raise err
        identity_id = int(payload["identity_id"])
        access_id = str(payload["access_id"])
        tenant_id = int(payload["tenant_id"])
        identity = db.query(PatientCompanionIdentity).filter(
            PatientCompanionIdentity.id == identity_id,
            PatientCompanionIdentity.provider == LOCAL_BRIDGE_PROVIDER,
            PatientCompanionIdentity.subject == str(payload["sub"]),
            PatientCompanionIdentity.revoked_at.is_(None),
        ).first()
        if identity is None:
            raise err
        access = db.query(PatientCompanionAccess).filter(
            PatientCompanionAccess.identity_id == identity.id,
            PatientCompanionAccess.public_id == access_id,
            PatientCompanionAccess.employer_id == tenant_id,
            PatientCompanionAccess.revoked_at.is_(None),
        ).first()
        if access is None:
            raise err
        return identity
    except HTTPException:
        raise
    except (JWTError, KeyError, TypeError, ValueError):
        raise err from None


def patient_credential(
    authorization: str | None = Header(default=None),
) -> FirebasePatientCredential:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentification patient requise.")
    scheme, separator, raw = authorization.partition(" ")
    if not separator or scheme.lower() != "firebase" or not raw.strip():
        raise HTTPException(status_code=401, detail="Authentification patient requise.")
    try:
        return verify_patient_id_token(raw.strip())
    except FirebasePatientAuthUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Authentification patient temporairement indisponible.",
        ) from None
    except FirebasePatientAuthInvalid:
        raise HTTPException(status_code=401, detail="Authentification patient invalide.") from None


def patient_identity(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> PatientCompanionIdentity:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentification patient requise.")
    scheme, separator, raw = authorization.partition(" ")
    if not separator or not raw.strip():
        raise HTTPException(status_code=401, detail="Authentification patient requise.")

    if scheme.lower() == "bearer":
        return _patient_device_identity(raw.strip(), db)

    if scheme.lower() != "firebase":
        raise HTTPException(status_code=401, detail="Authentification patient requise.")

    try:
        credential = verify_patient_id_token(raw.strip())
    except FirebasePatientAuthUnavailable:
        raise HTTPException(status_code=503, detail="Authentification patient temporairement indisponible.") from None
    except FirebasePatientAuthInvalid:
        raise HTTPException(status_code=401, detail="Authentification patient invalide.") from None

    identity = (
        db.query(PatientCompanionIdentity)
        .filter(
            PatientCompanionIdentity.provider == PROVIDER,
            PatientCompanionIdentity.subject == credential.subject,
            PatientCompanionIdentity.revoked_at.is_(None),
        )
        .first()
    )
    if identity is None:
        raise HTTPException(status_code=403, detail="Aucun accès patient actif.")
    return identity


def principal_for_access(
    db: Session,
    identity: PatientCompanionIdentity,
    access_public_id: str,
) -> tuple[PatientPrincipal, models.Patient]:
    row = (
        db.query(PatientCompanionAccess, models.Patient)
        .join(
            models.Patient,
            and_(
                models.Patient.id == PatientCompanionAccess.patient_id,
                models.Patient.employer_id == PatientCompanionAccess.employer_id,
            ),
        )
        .filter(
            PatientCompanionAccess.public_id == access_public_id,
            PatientCompanionAccess.identity_id == identity.id,
            PatientCompanionAccess.revoked_at.is_(None),
            models.Patient.deleted_at.is_(None),
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Contexte patient introuvable.")
    access, patient = row
    return PatientPrincipal(
        identity_id=identity.id,
        subject=identity.subject,
        access_id=access.public_id,
        employer_id=access.employer_id,
        patient_id=access.patient_id,
        relationship_type=access.relationship_type,
    ), patient


def safe_patient_context(access: PatientCompanionAccess, patient: models.Patient) -> dict:
    return {
        "access_id": access.public_id,
        "relationship_type": access.relationship_type,
        "patient": {
            "display_name": f"{patient.prenom or ''} {patient.nom or ''}".strip(),
            "prenom": patient.prenom,
            "nom": patient.nom,
        },
    }
