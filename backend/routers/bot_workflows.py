"""Flagged ZERO-LLM Crown Bot workflow preview (NO mutation, NO action UUID).

Server replays a bounded deterministic transcript; the transcript is not trusted.
All read results and write proposals are subject to live user/tenant checks.
Do not wire proposal dictionaries into ActionDispatcher.execute.
"""

from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.config import settings
from backend.database import get_db
from backend.routers.auth import get_current_user, has_permission, require_permission
from backend.services.bot.workflow_poc import PocConversation
from backend.services.bot.patient_selector import lookup_patient_candidates


router = APIRouter(tags=["bot-zero-llm-experimental"])

COMMAND_PERMISSIONS = {
    "/patient": "patients",
    "/rdv": "agenda",
    "/devis": "accounting",
}


def cabinet_day_context(*, at_utc: datetime | None = None, timezone_name: str | None = None) -> dict:
    """CB-01: derive clinic business day server-side, not staff browser time.

    One timezone per runtime for the pilot. Multi-cabinet timezone persistence
    remains a separate Agenda A5 mission, never inferred from a client header.
    """
    zone_name = timezone_name if timezone_name is not None else settings.CROWN_BOT_CABINET_TIMEZONE
    try:
        zone = ZoneInfo(zone_name)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise HTTPException(status_code=503, detail="Fuseau horaire du cabinet non configuré.")
    instant = at_utc if at_utc is not None else datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("at_utc must include a timezone")
    now_local = instant.astimezone(zone)
    day = now_local.date().isoformat()
    return {
        "day": day,
        "timezone": zone_name,
        "start_date": f"{day}T00:00:00",
        "end_date": f"{day}T23:59:59.999",
        "consulted_at": now_local.strftime("%H:%M"),
    }


@router.get("/workflows/cabinet-day")
def get_cabinet_day(
    user: models.User = Depends(require_permission("agenda")),
):
    """Read-only clinic day metadata. No clinical mutation and no identity disclosure."""
    if not settings.CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")
    return cabinet_day_context()


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

    # A patient selector is resolved on the SERVER, after authorization and
    # employer scoping. Never trust a client-supplied resolved identity.
    transcript = list(req.messages)
    selected_patient = None
    if len(transcript) > 1 and transcript[1].strip().casefold() not in (
        "/annuler", "/cancel",
    ):
        if not has_permission(user, "patients"):
            raise HTTPException(status_code=403, detail="Accès refusé.")
        matches, truncated = lookup_patient_candidates(
            db, employer_id=user.get_employer_id(), selector=transcript[1]
        )
        if not matches:
            # Identical for unknown, foreign, and soft-deleted selectors.
            raise HTTPException(status_code=404, detail="Patient introuvable.")
        if truncated:
            return {
                "status": "clarification",
                "message": "Plusieurs correspondances. Précisez le numéro de dossier.",
                "proposal": None,
            }
        if len(matches) > 1:
            return {
                "status": "disambiguation",
                "message": "Plusieurs patients correspondent. Choisissez le bon dossier.",
                "candidates": [
                    {
                        "id": p.id, "nom": p.nom, "prenom": p.prenom,
                        "numero_dossier": p.numero_dossier,
                    } for p in matches
                ],
                "proposal": None,
            }
        # Replayed FSM receives only a verified, scoped internal numeric ID.
        selected_patient = matches[0]
        transcript[1] = str(matches[0].id)

    workflow = PocConversation(today=date.fromisoformat(cabinet_day_context()["day"]))
    for message in transcript:
        result = workflow.handle(message)
    payload = {"status": result.status, "message": result.message, "proposal": None}
    # Revalidated tenant-scoped patient identity is display-only, not an
    # authorization token. Each POST replays and rechecks the full transcript.
    if selected_patient is not None:
        payload["patient"] = {
            "id": selected_patient.id,
            "nom": selected_patient.nom,
            "prenom": selected_patient.prenom,
            "numero_dossier": selected_patient.numero_dossier,
        }

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

    # Single scoped lookup: a foreign, unknown or soft-deleted patient gives
    # the same generic 404 (no global-ID existence oracle).
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.employer_id == user.get_employer_id(),
        models.Patient.deleted_at.is_(None),
    ).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient introuvable.")

    if command == "/patient":
        return {
            "status": "read",
            "message": "Patient identifié dans votre cabinet.",
            "patient": {
                "id": patient.id, "nom": patient.nom, "prenom": patient.prenom,
                "numero_dossier": patient.numero_dossier,
            },
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
