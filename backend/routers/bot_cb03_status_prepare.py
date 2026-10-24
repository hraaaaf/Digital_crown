"""CB-03 G1-B: prepare a strictly scoped status change, NEVER execute it.

The status intent comes from a bounded French parser, the appointment is chosen
explicitly, and original patient/status/revision are captured from live SQL.
G2 must provide fresh RBAC/tenant/transition/revision checks before any CAS.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.config import settings
from backend.database import get_db
from backend.routers.auth import get_current_user, has_permission
from backend.services.bot.guided_status_cb03 import (
    parse_status_preparation,
    transition_allowed,
)

router = APIRouter(tags=["bot-cb03-g1b-experimental"])


class CB03PrepareStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    utterance: str = Field(..., min_length=1, max_length=160, strict=True)
    # Explicitly selected appointment, NOT the "first upcoming" appointment
    # and NOT an action/patient proof supplied by a browser.
    selected_appointment_id: int = Field(..., gt=0, strict=True)


@router.post("/guided/prepare-status")
def prepare_guided_status(
    req: CB03PrepareStatusRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Store one NON-executable, non-clinical preparation (status='prepared')."""
    if not (
        settings.CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED
        and settings.CROWN_BOT_GUIDED_NLU_ENABLED
        and settings.CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED
    ):
        raise HTTPException(status_code=404, detail="Not found")

    owner = user.get_employer_id()
    if (isinstance(owner, bool) or not isinstance(owner, int) or owner <= 0
            or isinstance(user.id, bool) or not isinstance(user.id, int) or user.id <= 0):
        raise HTTPException(status_code=403, detail="Accès refusé.")
    # Permissions BEFORE patient or appointment reads. Bot legacy requires
    # agenda only, but CB-03 status preparation intentionally also needs patients.
    if not all(has_permission(user, permission) for permission in ("agenda", "patients")):
        raise HTTPException(status_code=403, detail="Accès refusé.")

    intent = parse_status_preparation(req.utterance)
    if intent is None:
        raise HTTPException(
            status_code=422,
            detail="Demande ambiguë : indiquez uniquement un nouveau statut reconnu.",
        )
    next_status, next_status_label = intent

    # No automatic appointment inference. Missing, foreign or soft-deleted IDs
    # all yield the exact same 404, without leaking any other tenant's data.
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == req.selected_appointment_id,
        models.Appointment.employer_id == owner,
        models.Appointment.deleted_at.is_(None),
    ).first()
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")
    patient_id = appointment.patient_id
    if isinstance(patient_id, bool) or not isinstance(patient_id, int) or patient_id <= 0:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.employer_id == owner,
        models.Patient.deleted_at.is_(None),
    ).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")

    original_status = appointment.status
    original_revision = appointment.clinical_revision
    if (not isinstance(original_status, models.AppointmentStatus)
            or isinstance(original_revision, bool)
            or not isinstance(original_revision, int) or original_revision < 0):
        raise HTTPException(status_code=409, detail="Statut ou révision invérifiable.")
    if not transition_allowed(original_status, next_status):
        raise HTTPException(
            status_code=409,
            detail="Transition de statut non autorisée ou rendez-vous déjà finalisé.",
        )

    session = models.BotSession(
        employer_id=owner,
        user_id=user.id,
        patient_id=patient_id,
        title="CB-03 - préparation statut RDV",
    )
    db.add(session)
    db.flush()
    expires_at = datetime.utcnow() + timedelta(minutes=30)
    action = models.BotPendingAction(
        session_id=session.id,
        user_id=user.id,
        employer_id=owner,
        action_type="CHANGE_STATUS",
        params_json={
            # Server-owned snapshot. Client cannot supply any of these fields.
            "appointment_id": appointment.id,
            "patient_id": patient_id,
            "expected_status": original_status.name,
            "expected_revision": original_revision,
            "status": next_status.name,
            "status_label": next_status_label,
        },
        # Legacy /bot/execute can only claim 'pending'. G2 must use a distinct
        # explicit confirmation transaction with freshness checks and CAS.
        status="prepared",
        expires_at=expires_at,
    )
    db.add(action)
    db.flush()
    db.add(models.AuditLog(
        user_id=user.id,
        employer_id=owner,
        action="CB03_STATUS_PREPARED",
        resource_type="BotPendingAction",
        resource_id=action.id,
        details="Préparation seule ; aucune mutation RDV ; vérification G2 requise.",
    ))
    db.commit()
    return {
        "status": "prepared",
        "message": "Changement de statut préparé, non exécuté. Confirmation indisponible en G1-B.",
        "preparation_id": action.id,
        "expires_at": expires_at.isoformat(),
        "summary": {
            "appointment_id": appointment.id,
            "patient": {
                "id": patient.id,
                "nom": patient.nom,
                "prenom": patient.prenom,
                "numero_dossier": patient.numero_dossier,
            },
            "datetime_start": appointment.datetime_start.isoformat(),
            "expected_status": original_status.name,
            "expected_revision": original_revision,
            "new_status": next_status.name,
            "new_status_label": next_status_label,
        },
        "executable": False,
    }
