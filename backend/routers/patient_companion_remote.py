from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionIdentity,
    PatientCompanionRemoteKeySet,
)
from backend.routers.patient_companion_common import (
    get_db,
    patient_identity,
    principal_for_access,
)
from backend.services.audit_service import audit_service
from backend.services.patient_companion_remote_jwk import RemotePublicKeyEnrollment
from backend.services.patient_companion_remote_key_vault import CabinetRemoteKeyVault

router = APIRouter()


def get_cabinet_remote_key_vault() -> CabinetRemoteKeyVault:
    return CabinetRemoteKeyVault.from_runtime()


@router.post("/contexts/{access_id}/remote-keys/enroll", status_code=201)
def enroll_remote_public_keys(
    access_id: str,
    body: RemotePublicKeyEnrollment,
    response: Response,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
    cabinet_keys: CabinetRemoteKeyVault = Depends(get_cabinet_remote_key_vault),
):
    principal, _patient = principal_for_access(db, identity, access_id)

    existing = (
        db.query(PatientCompanionRemoteKeySet)
        .filter(
            PatientCompanionRemoteKeySet.access_id == principal.id,
            PatientCompanionRemoteKeySet.state == "ACTIVE",
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clés distantes déjà enrôlées. Une nouvelle cérémonie locale est requise pour les remplacer.",
        )

    row = PatientCompanionRemoteKeySet(
        access_id=principal.id,
        signing_kid=body.signing.kid,
        signing_public_jwk=body.signing.canonical_json(),
        encryption_kid=body.encryption.kid,
        encryption_public_jwk=body.encryption.canonical_json(),
        state="ACTIVE",
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Enrôlement de clés déjà traité.") from None
    db.refresh(row)

    public_bundle = cabinet_keys.public_bundle()
    audit_service.log(
        db=db,
        user_id=None,
        employer_id=principal.employer_id,
        action="PATIENT_COMPANION_REMOTE_KEYS_ENROLLED",
        resource_type="PatientCompanionAccess",
        resource_id=principal.public_id,
        details="Patient device public signing/encryption keys enrolled during trusted cabinet-local session.",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "protocol_version": "dc-pc-remote-v1",
        "patient_key_set_id": row.public_id,
        "patient_signing_kid": row.signing_kid,
        "patient_encryption_kid": row.encryption_kid,
        "cabinet_keys": public_bundle,
        "enrolled_at": row.created_at,
    }
