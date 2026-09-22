from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionIdentity,
    PatientCompanionRemoteKeyset,
)
from backend.routers.patient_companion_common import get_db, patient_identity, principal_for_access
from backend.services.patient_companion_notifications import project_notifications
from backend.services.patient_companion_remote_worker import process_remote_envelope
from backend.utils.rate_limit import check_rate_limit

router = APIRouter()


class RemoteCommandEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blob: str = Field(min_length=16, max_length=256 * 1024)


def _active_access(
    db: Session,
    identity: PatientCompanionIdentity,
    access_id: str,
) -> PatientCompanionAccess:
    principal, _patient = principal_for_access(db, identity, access_id)
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == principal.access_id,
        PatientCompanionAccess.identity_id == principal.identity_id,
        PatientCompanionAccess.employer_id == principal.employer_id,
        PatientCompanionAccess.patient_id == principal.patient_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    if access is None:
        raise HTTPException(status_code=404, detail="Contexte patient introuvable.")
    return access


@router.get("/contexts/{access_id}/notifications")
def patient_notifications(
    access_id: str,
    response: Response,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    access = _active_access(db, identity, access_id)
    response.headers["Cache-Control"] = "no-store"
    return project_notifications(db, access)


@router.post("/contexts/{access_id}/notifications/remote-command")
def patient_notifications_remote_command(
    access_id: str,
    body: RemoteCommandEnvelope,
    request: Request,
    response: Response,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, scope="patient-companion-notifications-remote-command")
    access = _active_access(db, identity, access_id)
    keyset = db.query(PatientCompanionRemoteKeyset).filter(
        PatientCompanionRemoteKeyset.access_id == access.id,
        PatientCompanionRemoteKeyset.status == "ACTIVE",
        PatientCompanionRemoteKeyset.revoked_at.is_(None),
    ).first()
    if keyset is None:
        raise HTTPException(status_code=409, detail="Transport sécurisé Patient Companion non initialisé.")
    try:
        ack = process_remote_envelope(
            db,
            access=access,
            keyset=keyset,
            compact_jwe=body.blob,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Commande distante Patient Companion invalide.") from None
    response.headers["Cache-Control"] = "no-store"
    return {"blob": ack}
