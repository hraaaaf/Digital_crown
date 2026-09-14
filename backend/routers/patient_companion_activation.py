from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionIdentity,
    PatientCompanionInvitation,
)
from backend.routers.auth import get_current_user, has_permission
from backend.routers.patient_companion_common import (
    PROVIDER,
    generate_manual_code,
    get_db,
    manual_code_hash,
    patient_credential,
    patient_identity,
    principal_for_access,
    safe_patient_context,
    staff_patient_or_404,
    token_hash,
)
from backend.services.audit_service import audit_service
from backend.services.firebase_patient_auth import FirebasePatientCredential
from backend.utils.rate_limit import check_rate_limit

router = APIRouter()


class InvitationCreateRequest(BaseModel):
    relationship_type: Literal["SELF", "PARENT", "GUARDIAN", "CAREGIVER"] = "SELF"
    expires_in_minutes: int = Field(default=15, ge=5, le=60)


class ActivationRequest(BaseModel):
    token: str | None = Field(default=None, max_length=256)
    manual_code: str | None = Field(default=None, max_length=32)


@router.post("/admin/patients/{patient_id}/invitation", status_code=201)
def create_patient_invitation(
    patient_id: int,
    body: InvitationCreateRequest,
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
        PatientCompanionInvitation.consumed_at.is_(None),
        PatientCompanionInvitation.revoked_at.is_(None),
        PatientCompanionInvitation.expires_at > now,
    ).update(
        {PatientCompanionInvitation.revoked_at: now},
        synchronize_session=False,
    )

    raw_token = secrets.token_urlsafe(32)
    manual_code = generate_manual_code()
    invitation = PatientCompanionInvitation(
        employer_id=employer_id,
        patient_id=patient.id,
        token_hash=token_hash(raw_token),
        manual_code_hash=manual_code_hash(manual_code),
        relationship_type=body.relationship_type,
        created_by_user_id=current_user.id,
        expires_at=now + timedelta(minutes=body.expires_in_minutes),
    )
    db.add(invitation)
    try:
        db.commit()
        db.refresh(invitation)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Impossible de générer une invitation unique.") from None

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_INVITATION_CREATED",
        resource_type="Patient",
        resource_id=str(patient.id),
        details=f"Invitation Patient Companion créée ({body.relationship_type}).",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "invitation_id": invitation.public_id,
        "qr_token": raw_token,
        "manual_code": manual_code,
        "expires_at": invitation.expires_at,
        "relationship_type": invitation.relationship_type,
    }


@router.post("/admin/invitations/{invitation_id}/revoke")
def revoke_patient_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Permission patients requise.")
    employer_id = int(current_user.get_employer_id())
    invitation = db.query(PatientCompanionInvitation).filter(
        PatientCompanionInvitation.public_id == invitation_id,
        PatientCompanionInvitation.employer_id == employer_id,
    ).first()
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation introuvable.")
    if invitation.consumed_at is not None:
        raise HTTPException(status_code=409, detail="Invitation déjà consommée.")
    if invitation.revoked_at is None:
        invitation.revoked_at = datetime.utcnow()
        db.commit()
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_INVITATION_REVOKED",
        resource_type="PatientCompanionInvitation",
        resource_id=invitation.public_id,
    )
    return {"status": "revoked", "invitation_id": invitation.public_id}


@router.post("/activate")
def activate_patient_companion(
    body: ActivationRequest,
    request: Request,
    response: Response,
    credential: FirebasePatientCredential = Depends(patient_credential),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, scope="patient-companion-activate")
    if int(bool(body.token)) + int(bool(body.manual_code)) != 1:
        raise HTTPException(status_code=422, detail="Fournir un QR token ou un code manuel.")

    query = db.query(PatientCompanionInvitation)
    if body.token:
        query = query.filter(PatientCompanionInvitation.token_hash == token_hash(body.token))
    else:
        query = query.filter(
            PatientCompanionInvitation.manual_code_hash == manual_code_hash(body.manual_code or "")
        )
    invitation = query.with_for_update().first()
    now = datetime.utcnow()
    if (
        invitation is None
        or invitation.revoked_at is not None
        or invitation.consumed_at is not None
        or invitation.expires_at <= now
    ):
        raise HTTPException(status_code=400, detail="Invitation invalide ou expirée.")

    patient = db.query(models.Patient).filter(
        models.Patient.id == invitation.patient_id,
        models.Patient.employer_id == invitation.employer_id,
        models.Patient.deleted_at.is_(None),
    ).first()
    if patient is None:
        raise HTTPException(status_code=400, detail="Invitation invalide ou expirée.")

    identity = db.query(PatientCompanionIdentity).filter(
        PatientCompanionIdentity.provider == PROVIDER,
        PatientCompanionIdentity.subject == credential.subject,
    ).with_for_update().first()
    if identity is None:
        identity = PatientCompanionIdentity(
            provider=PROVIDER,
            subject=credential.subject,
            last_seen_at=now,
        )
        db.add(identity)
        db.flush()
    else:
        identity.revoked_at = None
        identity.last_seen_at = now

    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.identity_id == identity.id,
        PatientCompanionAccess.employer_id == invitation.employer_id,
        PatientCompanionAccess.patient_id == invitation.patient_id,
    ).with_for_update().first()
    if access is None:
        access = PatientCompanionAccess(
            identity_id=identity.id,
            employer_id=invitation.employer_id,
            patient_id=invitation.patient_id,
            relationship_type=invitation.relationship_type,
        )
        db.add(access)
        db.flush()
    else:
        access.relationship_type = invitation.relationship_type
        access.revoked_at = None

    invitation.consumed_at = now
    invitation.consumed_by_identity_id = identity.id
    try:
        db.commit()
        db.refresh(access)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Activation déjà traitée.") from None

    audit_service.log(
        db=db,
        user_id=None,
        employer_id=access.employer_id,
        action="PATIENT_COMPANION_ACTIVATED",
        resource_type="PatientCompanionAccess",
        resource_id=access.public_id,
        details=f"Activation Firebase ({access.relationship_type}).",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"status": "activated", **safe_patient_context(access, patient)}


@router.get("/me")
def get_patient_companion_me(
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    rows = db.query(PatientCompanionAccess, models.Patient).join(
        models.Patient,
        and_(
            models.Patient.id == PatientCompanionAccess.patient_id,
            models.Patient.employer_id == PatientCompanionAccess.employer_id,
        ),
    ).filter(
        PatientCompanionAccess.identity_id == identity.id,
        PatientCompanionAccess.revoked_at.is_(None),
        models.Patient.deleted_at.is_(None),
    ).order_by(PatientCompanionAccess.created_at.asc()).all()
    if not rows:
        raise HTTPException(status_code=403, detail="Aucun accès patient actif.")
    return {
        "provider": identity.provider,
        "contexts": [safe_patient_context(access, patient) for access, patient in rows],
    }


@router.get("/contexts/{access_id}/appointments")
def get_patient_appointments(
    access_id: str,
    limit: int = Query(default=20, ge=1, le=50),
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    principal, _patient = principal_for_access(db, identity, access_id)
    rows = db.query(models.Appointment).filter(
        models.Appointment.employer_id == principal.employer_id,
        models.Appointment.patient_id == principal.patient_id,
        models.Appointment.datetime_start >= datetime.utcnow(),
        models.Appointment.status != models.AppointmentStatus.ANNULE,
    ).order_by(models.Appointment.datetime_start.asc()).limit(limit).all()
    return {
        "items": [
            {
                "id": row.id,
                "datetime_start": row.datetime_start,
                "duration_minutes": row.duration_minutes,
                "motif": row.motif or "Consultation",
                "status": getattr(row.status, "value", row.status),
                "scheduling_type": getattr(row.scheduling_type, "value", row.scheduling_type),
            }
            for row in rows
        ]
    }
