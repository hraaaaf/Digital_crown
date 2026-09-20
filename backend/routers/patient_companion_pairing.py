from __future__ import annotations

import base64
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionIdentity,
    PatientCompanionInvitation,
)
from backend.routers.auth import get_current_user
from backend.routers.patient_companion_common import (
    LOCAL_BRIDGE_PROVIDER,
    create_patient_device_token,
    generate_manual_code,
    get_db,
    manual_code_hash,
    require_companion_cabinet_write_license,
    safe_patient_context,
    staff_patient_or_404,
    token_hash,
)
from backend.services.audit_service import audit_service
from backend.services.patient_companion_key_protection import OsKeyProtectionUnavailable
from backend.services.patient_companion_remote_keys import (
    enroll_remote_keyset,
    public_keyset_response,
)
from backend.services.patient_companion_relay_client import (
    deprovision_relay_mailboxes,
    provision_relay_binding,
)
from backend.config import settings
from backend.services.qr_service import qr_service
from backend.utils.rate_limit import check_rate_limit

router = APIRouter()


class LocalInvitationRequest(BaseModel):
    relationship_type: Literal["SELF", "PARENT", "GUARDIAN", "CAREGIVER"] = "SELF"
    expires_in_minutes: int = Field(default=15, ge=5, le=60)


class RemoteKeyEnrollmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signing_kid: str = Field(min_length=36, max_length=36)
    signing_public_jwk: dict
    encryption_kid: str = Field(min_length=36, max_length=36)
    encryption_public_jwk: dict


class LocalPairRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str | None = Field(default=None, max_length=256)
    manual_code: str | None = Field(default=None, max_length=32)
    remote_keys: RemoteKeyEnrollmentRequest | None = None


@router.post("/admin/patients/{patient_id}/local-invitation", status_code=201)
def create_local_invitation(
    patient_id: int,
    body: LocalInvitationRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    now = datetime.utcnow()

    db.query(PatientCompanionInvitation).filter(
        PatientCompanionInvitation.employer_id == employer_id,
        PatientCompanionInvitation.patient_id == patient.id,
        PatientCompanionInvitation.recipient_type == "local_bridge",
        PatientCompanionInvitation.consumed_at.is_(None),
        PatientCompanionInvitation.revoked_at.is_(None),
        PatientCompanionInvitation.expires_at > now,
    ).update({PatientCompanionInvitation.revoked_at: now}, synchronize_session=False)

    raw_token = secrets.token_urlsafe(32)
    manual_code = generate_manual_code()
    invitation = PatientCompanionInvitation(
        employer_id=employer_id,
        patient_id=patient.id,
        token_hash=token_hash(raw_token),
        manual_code_hash=manual_code_hash(manual_code),
        recipient_type="local_bridge",
        recipient_hash=token_hash(f"local_bridge:{patient.id}:{raw_token}"),
        relationship_type=body.relationship_type,
        created_by_user_id=current_user.id,
        expires_at=now + timedelta(minutes=body.expires_in_minutes),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    qr_data_url = "data:image/png;base64," + base64.b64encode(
        qr_service.generate_qr_bytes(raw_token, qr_style="classic").getvalue()
    ).decode("ascii")

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_LOCAL_INVITATION_CREATED",
        resource_type="Patient",
        resource_id=str(patient.id),
        details=f"Local-first pairing invitation created ({body.relationship_type}).",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "invitation_id": invitation.public_id,
        "qr_data_url": qr_data_url,
        "manual_code": manual_code,
        "expires_at": invitation.expires_at,
        "relationship_type": invitation.relationship_type,
    }


@router.post("/pair", status_code=201)
def pair_local_patient_device(
    body: LocalPairRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    check_rate_limit(request, scope="patient-companion-local-pair")
    if int(bool(body.token)) + int(bool(body.manual_code)) != 1:
        raise HTTPException(status_code=422, detail="Fournir un QR token ou un code manuel.")

    query = db.query(PatientCompanionInvitation).filter(
        PatientCompanionInvitation.recipient_type == "local_bridge"
    )
    if body.token:
        query = query.filter(PatientCompanionInvitation.token_hash == token_hash(body.token))
    else:
        query = query.filter(PatientCompanionInvitation.manual_code_hash == manual_code_hash(body.manual_code or ""))

    invitation = query.first()
    now = datetime.utcnow()
    if (
        invitation is None
        or invitation.revoked_at is not None
        or invitation.consumed_at is not None
        or invitation.expires_at <= now
    ):
        raise HTTPException(status_code=400, detail="Invitation invalide ou expirée.")

    require_companion_cabinet_write_license(db, invitation.employer_id)
    patient = db.query(models.Patient).filter(
        models.Patient.id == invitation.patient_id,
        models.Patient.employer_id == invitation.employer_id,
        models.Patient.deleted_at.is_(None),
    ).first()
    if patient is None:
        raise HTTPException(status_code=400, detail="Invitation invalide ou expirée.")

    identity = PatientCompanionIdentity(
        provider=LOCAL_BRIDGE_PROVIDER,
        subject=f"device:{uuid.uuid4()}",
        last_seen_at=now,
    )
    db.add(identity)
    db.flush()

    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=invitation.employer_id,
        patient_id=invitation.patient_id,
        relationship_type=invitation.relationship_type,
    )
    db.add(access)
    db.flush()

    remote_keyset = None
    cabinet_signing_key = None
    cabinet_encryption_key = None
    relay_bootstrap = None
    if body.remote_keys is not None:
        try:
            remote_keyset, cabinet_signing_key, cabinet_encryption_key = enroll_remote_keyset(
                db,
                access=access,
                patient_signing_kid=body.remote_keys.signing_kid,
                patient_signing_public_jwk=body.remote_keys.signing_public_jwk,
                patient_encryption_kid=body.remote_keys.encryption_kid,
                patient_encryption_public_jwk=body.remote_keys.encryption_public_jwk,
            )
        except OsKeyProtectionUnavailable as exc:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Protection OS des clés distantes indisponible sur ce cabinet.",
            ) from exc
        except OSError as exc:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Protection OS des clés distantes indisponible sur ce cabinet.",
            ) from exc
        except ValueError as exc:
            db.rollback()
            raise HTTPException(status_code=422, detail=str(exc)) from None

        relay_url = settings.PATIENT_COMPANION_RELAY_URL.strip()
        relay_secret = settings.PATIENT_COMPANION_RELAY_BOOTSTRAP_SECRET.strip()
        if bool(relay_url) != bool(relay_secret):
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Configuration relay Patient Companion incomplète.",
            )
        if relay_url and relay_secret:
            try:
                _binding, relay_bootstrap = provision_relay_binding(
                    db,
                    access=access,
                    relay_url=relay_url,
                    bootstrap_secret=relay_secret,
                )
            except Exception as exc:
                db.rollback()
                raise HTTPException(
                    status_code=503,
                    detail="Relay Patient Companion indisponible pour cet appairage.",
                ) from exc

    consumed = db.query(PatientCompanionInvitation).filter(
        PatientCompanionInvitation.id == invitation.id,
        PatientCompanionInvitation.consumed_at.is_(None),
        PatientCompanionInvitation.revoked_at.is_(None),
        PatientCompanionInvitation.expires_at > now,
    ).update(
        {
            PatientCompanionInvitation.consumed_at: now,
            PatientCompanionInvitation.consumed_by_identity_id: identity.id,
        },
        synchronize_session=False,
    )
    if consumed != 1:
        db.rollback()
        if relay_bootstrap is not None:
            deprovision_relay_mailboxes(
                relay_url=relay_bootstrap.relay_url,
                bootstrap_secret=settings.PATIENT_COMPANION_RELAY_BOOTSTRAP_SECRET.strip(),
                mailbox_ids=(relay_bootstrap.cabinet_inbox_id, relay_bootstrap.patient_inbox_id),
            )
        raise HTTPException(status_code=409, detail="Invitation déjà traitée.")

    try:
        db.commit()
    except Exception:
        db.rollback()
        if relay_bootstrap is not None:
            deprovision_relay_mailboxes(
                relay_url=relay_bootstrap.relay_url,
                bootstrap_secret=settings.PATIENT_COMPANION_RELAY_BOOTSTRAP_SECRET.strip(),
                mailbox_ids=(relay_bootstrap.cabinet_inbox_id, relay_bootstrap.patient_inbox_id),
            )
        raise
    db.refresh(access)
    access_token = create_patient_device_token(identity, access)

    audit_service.log(
        db=db,
        user_id=None,
        employer_id=access.employer_id,
        action="PATIENT_COMPANION_LOCAL_DEVICE_PAIRED",
        resource_type="PatientCompanionAccess",
        resource_id=access.public_id,
        details="Local-first patient device paired by one-time QR/manual code.",
    )
    response.headers["Cache-Control"] = "no-store"
    remote_transport = {"status": "not_enrolled"}
    if (
        remote_keyset is not None
        and cabinet_signing_key is not None
        and cabinet_encryption_key is not None
    ):
        remote_transport = {
            "status": "enrolled",
            **public_keyset_response(
                remote_keyset,
                cabinet_signing_key,
                cabinet_encryption_key,
            ),
        }
        if relay_bootstrap is not None:
            remote_transport["relay"] = relay_bootstrap.response()
    return {
        "access_token": access_token,
        "context": safe_patient_context(access, patient),
        "paired_at": datetime.now(timezone.utc),
        "storage_policy": "local_encrypted_device",
        "remote_transport": remote_transport,
    }
