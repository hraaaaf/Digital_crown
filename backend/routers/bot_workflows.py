"""Flagged ZERO-LLM Crown Bot workflow preview (NO mutation, NO action UUID).

Server replays a bounded deterministic transcript; the transcript is not trusted.
All read results and write proposals are subject to live user/tenant checks.
Do not wire proposal dictionaries into ActionDispatcher.execute.
"""

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.config import settings
from backend.database import get_db
from backend.routers.auth import get_current_user, has_permission
from backend.services.bot.workflow_poc import PocConversation
from backend.utils.access_control import assert_patient_access


router = APIRouter(tags=["bot-zero-llm-experimental"])

COMMAND_PERMISSIONS = {
    "/patient": "patients",
    "/rdv": "agenda",
    "/devis": "accounting",
}


class BotWorkflowPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Caller-provided transcript is deliberately NOT durable state. Replayed
    # from a fresh FSM on every request and cannot authorize a backend write.
    messages: List[str] = Field(..., min_length=1, max_length=8)


@router.post("/workflows/preview")
def preview_bot_workflow(
    req: BotWorkflowPreviewRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Preview a deterministic plan, never create a BotPendingAction or write."""
    if not settings.CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")

    if any(not item.strip() or len(item) > 80 for item in req.messages):
        raise HTTPException(status_code=422, detail="Messages invalides (1-80 caractères).")

    command = req.messages[0].strip().casefold()
    permission = COMMAND_PERMISSIONS.get(command)
    if permission is None:
        raise HTTPException(status_code=422, detail="Commande non reconnue.")
    if not has_permission(user, permission):
        raise HTTPException(status_code=403, detail="Accès refusé.")

    workflow = PocConversation(today=date.today())
    for message in req.messages:
        result = workflow.handle(message)
    payload = {"status": result.status, "message": result.message, "proposal": None}

    if result.proposal is None:
        return payload

    action = result.proposal
    expected = {
        "/patient": "QUERY_PATIENT",
        "/rdv": "CREATE_APPOINTMENT",
        "/devis": "OPEN_DEVIS_EDITOR",
    }[command]
    if action.get("type") != expected:
        raise HTTPException(status_code=409, detail="Workflow incohérent.")

    patient_id = action.get("params", {}).get("patient_id")
    if not isinstance(patient_id, int) or isinstance(patient_id, bool) or patient_id <= 0:
        raise HTTPException(status_code=422, detail="Patient invalide.")

    # Independent server-side tenant resolution: not just the client's claim.
    # Cross-cabinet data never enters the preview response.
    assert_patient_access(patient_id, user, db)
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.employer_id == user.get_employer_id(),
    ).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient introuvable.")

    if command == "/patient":
        return {
            "status": "read",
            "message": "Patient identifié dans votre cabinet.",
            "patient": {"id": patient.id, "nom": patient.nom, "prenom": patient.prenom},
            "proposal": None,
        }

    # Do NOT create an actionable pending UUID, even with the flag ON.
    # Appointment availability/closure and final business rules have NOT
    # been verified, so this is intentionally not an executable reservation.
    payload["proposal"] = action
    payload["message"] = (
        "Simulation uniquement, non exécutée. Le contrôle de disponibilité, "
        "les règles métier et la confirmation serveur restent obligatoires."
    )
    return payload
