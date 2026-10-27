"""CB-03 G1-A: deterministic server-owned appointment PREPARATION only.

No appointment is inserted, no slot is reserved, and no legacy /bot/execute
call can consume the resulting action (status='prepared', never 'pending').
G2 must add a distinct explicit confirmation endpoint with fresh checks.
"""
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.config import settings
from backend.database import get_db
from backend.routers.auth import get_current_user
from backend.routers.bot_guided_nlu_cb02 import CB02GuidedRequest, guided_nlu_preview
from backend.routers.bot_workflows import cabinet_day_context
from backend.routers.appointments import _find_conflicts, _resolve_practitioner_id
from backend.schemas.base import SchedulingType
from backend.services.agenda_availability import validate_appointment_availability
from backend.services.agenda_resource_conflicts import (
    assert_resource_available,
    validate_assignable_resource,
)

router = APIRouter(tags=["bot-cb03-g1a-experimental"])


class CB03PrepareAppointmentRequest(BaseModel):
    """Explicit scheduling choices; identity and intent remain server-resolved."""

    model_config = ConfigDict(extra="forbid")
    utterance: str = Field(..., min_length=1, max_length=160)
    chosen_patient_id: Optional[int] = Field(default=None, gt=0, strict=True)
    praticien_id: Optional[int] = Field(default=None, gt=0, strict=True)
    resource_id: Optional[int] = Field(default=None, gt=0, strict=True)
    duration_minutes: int = Field(..., ge=5, le=480, strict=True)


@router.post("/guided/prepare-appointment")
def prepare_guided_appointment(
    req: CB03PrepareAppointmentRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Create a non-executable, tenant/owner-bound server preparation.

    G1-A is intentionally NOT the confirmation flow. The preview is replayed
    from original text and current DB state, never accepted as a browser draft.
    All checks here are advisory: G2 must revalidate under booking lock.
    """
    if not (
        settings.CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED
        and settings.CROWN_BOT_GUIDED_NLU_ENABLED
        and settings.CROWN_BOT_CB03_PREPARATION_ENABLED
    ):
        raise HTTPException(status_code=404, detail="Not found")

    # Reuse CB-02 tenant lookup, RBAC (agenda + patients), deterministic
    # parser and fresh homonym selection. Never trust a browser preview.
    preview = guided_nlu_preview(
        CB02GuidedRequest(
            utterance=req.utterance, chosen_patient_id=req.chosen_patient_id
        ),
        db=db,
        user=user,
    )
    if preview.get("intent") != "RDV_PREPARE":
        raise HTTPException(status_code=422, detail="Intention RDV requise.")
    if preview.get("status") in ("clarification", "disambiguation"):
        return {
            "status": preview["status"],
            "message": preview["message"],
            "candidates": preview.get("candidates", []),
            "preparation_id": None,
            "executable": False,
        }
    if preview.get("status") != "preview_only":
        raise HTTPException(status_code=422, detail="Demande RDV non preparable.")

    patient_data = preview.get("patient")
    fields = preview["fields"]
    if (
        not isinstance(patient_data, dict)
        or fields.get("patient", {}).get("source") != "server_verified"
        or any(key not in fields for key in ("date", "time", "motif"))
    ):
        raise HTTPException(status_code=422, detail="Donnees RDV incompletes.")
    patient_id = patient_data["id"]  # Resolved exclusively on the server.
    owner = user.get_employer_id()
    if (isinstance(patient_id, bool) or not isinstance(patient_id, int)
            or not isinstance(owner, int) or owner <= 0):
        raise HTTPException(status_code=403, detail="Acces refuse.")

    # Only a naive cabinet wall-clock date/time is stored. Client never
    # supplies a timezone and cannot substitute server-day context.
    day_ctx = cabinet_day_context()
    try:
        start = datetime.fromisoformat(
            f"{fields['date']['value']}T{fields['time']['value']}:00"
        )
    except ValueError:
        raise HTTPException(status_code=422, detail="Date ou heure invalide.")
    local_now = datetime.now(ZoneInfo(day_ctx["timezone"])).replace(tzinfo=None)
    if start <= local_now:
        raise HTTPException(status_code=422, detail="Creneau passe.")

    practitioner_id = _resolve_practitioner_id(
        db, owner, user, req.praticien_id,
    )
    validate_assignable_resource(db, owner, req.resource_id)
    availability_error = validate_appointment_availability(
        db, owner, start, req.duration_minutes, SchedulingType.EXACT_TIME,
        practitioner_id=practitioner_id,
    )
    if availability_error:
        raise HTTPException(status_code=422, detail=availability_error)
    if _find_conflicts(db, owner, practitioner_id, start, req.duration_minutes):
        # Never disclose competing patient information.
        raise HTTPException(status_code=409, detail="Creneau indisponible.")
    try:
        assert_resource_available(
            db, employer_id=owner, resource_id=req.resource_id,
            datetime_start=start, duration_minutes=req.duration_minutes,
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            raise HTTPException(status_code=409, detail="Ressource indisponible.") from exc
        raise

    # Database-owned params for subsequent G2 revalidation. 'prepared'
    # is deliberately NOT executable by the historical /bot/execute route.
    session = models.BotSession(
        employer_id=owner,
        user_id=user.id,
        patient_id=patient_id,
        title="CB-03 - preparation RDV",
    )
    db.add(session)
    db.flush()
    expires_at = datetime.utcnow() + timedelta(minutes=30)
    action = models.BotPendingAction(
        session_id=session.id,
        user_id=user.id,
        employer_id=owner,
        action_type="CREATE_APPOINTMENT",
        params_json={
            "patient_id": patient_id,
            "praticien_id": practitioner_id,
            "resource_id": req.resource_id,
            "datetime_start": start.isoformat(),
            "duration_minutes": req.duration_minutes,
            "motif": fields["motif"]["value"],
        },
        status="prepared",
        expires_at=expires_at,
    )
    db.add(action)
    db.flush()
    db.add(models.AuditLog(
        user_id=user.id,
        employer_id=owner,
        action="CB03_APPOINTMENT_PREPARED",
        resource_type="BotPendingAction",
        resource_id=action.id,
        details="Preparation seule ; non executable ; controles a refaire en G2.",
    ))
    db.commit()
    return {
        "status": "prepared",
        "message": "Preparation enregistree sans reservation. Confirmation indisponible en G1-A.",
        "preparation_id": action.id,
        "expires_at": expires_at.isoformat(),
        "summary": {
            "patient": patient_data,
            "praticien_id": practitioner_id,
            "resource_id": req.resource_id,
            "datetime_start": start.isoformat(),
            "duration_minutes": req.duration_minutes,
            "motif": fields["motif"]["value"],
        },
        "executable": False,
    }
