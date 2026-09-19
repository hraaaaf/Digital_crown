from __future__ import annotations

import uuid
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionIdentity,
    PatientCompanionRemoteKeyset,
)
from backend.routers.patient_companion_common import (
    get_db,
    patient_identity,
    principal_for_access,
)
from backend.services.patient_companion_key_protection import (
    OsKeyProtectionUnavailable,
    protect_os_bound,
)
from backend.services.patient_companion_remote_keys import (
    enroll_remote_keyset,
    public_keyset_response,
)

router = APIRouter()
ProtectFn = Callable[[bytes], bytes]


class RemoteKeyEnrollmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_signing_kid: uuid.UUID
    patient_signing_public_jwk: dict[str, Any]
    patient_encryption_kid: uuid.UUID
    patient_encryption_public_jwk: dict[str, Any]


def get_remote_key_protector() -> ProtectFn:
    # Production v1 is intentionally fail-closed outside Windows DPAPI.
    return protect_os_bound


@router.post("/contexts/{access_id}/remote-keys/enroll", status_code=201)
def enroll_remote_keys(
    access_id: str,
    body: RemoteKeyEnrollmentRequest,
    response: Response,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
    protect: ProtectFn = Depends(get_remote_key_protector),
):
    """Trusted cabinet-local ceremony. This route is never exposed by the relay."""

    access, _patient = principal_for_access(db, identity, access_id)

    existing = (
        db.query(PatientCompanionRemoteKeyset)
        .filter(
            PatientCompanionRemoteKeyset.access_id == access.id,
            PatientCompanionRemoteKeyset.status == "ACTIVE",
            PatientCompanionRemoteKeyset.revoked_at.is_(None),
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Clés distantes déjà enrôlées. Une nouvelle cérémonie locale "
                "est requise pour toute rotation."
            ),
        )

    try:
        keyset, cabinet_signing, cabinet_encryption = enroll_remote_keyset(
            db,
            access=access,
            patient_signing_kid=str(body.patient_signing_kid),
            patient_signing_public_jwk=body.patient_signing_public_jwk,
            patient_encryption_kid=str(body.patient_encryption_kid),
            patient_encryption_public_jwk=body.patient_encryption_public_jwk,
            protect=protect,
        )
        db.commit()
        db.refresh(keyset)
    except OsKeyProtectionUnavailable as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Protection OS des clés cabinet indisponible.",
        ) from exc
    except (ValueError, IntegrityError) as exc:
        db.rollback()
        if isinstance(exc, IntegrityError):
            raise HTTPException(status_code=409, detail="Enrôlement de clés déjà traité.") from None
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response.headers["Cache-Control"] = "no-store"
    return public_keyset_response(keyset, cabinet_signing, cabinet_encryption)
