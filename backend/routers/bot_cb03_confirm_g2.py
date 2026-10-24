"""CB-03 G2 explicit confirmation + per-ID reconciliation, separately OFF.

Prepared actions are NEVER eligible for the legacy /bot/execute endpoint.
Only an authenticated same-user same-cabinet POST containing explicit confirm=true
may execute. A single DB transaction encompasses action claim, canonical
business mutation, durable receipt and audit. Unknown network outcome -> GET.
"""
from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.config import settings
from backend.database import get_db
from backend.routers.auth import get_current_user, has_permission
from backend.services.bot.action_dispatcher import ActionDispatcher
from backend.services.bot.guided_status_cb03 import transition_allowed

router = APIRouter(tags=["bot-cb03-g2-experimental"])
dispatcher = ActionDispatcher()

_APPOINTMENT_KEYS = frozenset({
    "patient_id", "praticien_id", "resource_id", "datetime_start",
    "duration_minutes", "motif",
})
_STATUS_KEYS = frozenset({
    "appointment_id", "patient_id", "expected_status",
    "expected_revision", "status", "status_label",
})
_ALLOWED_TYPES = frozenset({"CREATE_APPOINTMENT", "CHANGE_STATUS"})


class CB03ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preparation_id: UUID
    # Explicit, strict user intent. Never inferred from a preview or GET.
    confirm: bool = Field(..., strict=True)


def _gate(user: models.User) -> int:
    if not (
        settings.CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED
        and settings.CROWN_BOT_GUIDED_NLU_ENABLED
        and settings.CROWN_BOT_CB03_CONFIRMATION_ENABLED
    ):
        raise HTTPException(status_code=404, detail="Not found")
    owner = user.get_employer_id()
    if (isinstance(owner, bool) or not isinstance(owner, int) or owner <= 0
            or isinstance(user.id, bool) or not isinstance(user.id, int) or user.id <= 0):
        raise HTTPException(status_code=403, detail="Accès refusé.")
    return owner


def _owned_action(db: Session, owner: int, user_id: int, action_id: str):
    record = db.query(models.BotPendingAction).filter(
        models.BotPendingAction.id == action_id,
        models.BotPendingAction.user_id == user_id,
        models.BotPendingAction.employer_id == owner,
        models.BotPendingAction.action_type.in_(tuple(_ALLOWED_TYPES)),
    ).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Préparation introuvable.")
    # Must be a G1-A/G1-B session owned by this principal, not a forged
    # historical pending record or a cross-tenant orphan.
    session = db.query(models.BotSession).filter(
        models.BotSession.id == record.session_id,
        models.BotSession.user_id == user_id,
        models.BotSession.employer_id == owner,
    ).first()
    expected_title = (
        "CB-03 - preparation RDV" if record.action_type == "CREATE_APPOINTMENT"
        else "CB-03 - préparation statut RDV"
    )
    if session is None or session.title != expected_title:
        raise HTTPException(status_code=404, detail="Préparation introuvable.")
    return record, session


def _permissions(user: models.User, action_type: str):
    if action_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=403, detail="Action non autorisée.")
    # G2 cannot bypass the narrower G1 rights via old ACTION_PERMISSIONS.
    if not all(has_permission(user, p) for p in ("agenda", "patients")):
        raise HTTPException(status_code=403, detail="Accès refusé.")
    if action_type == "CREATE_APPOINTMENT":
        enabled = settings.CROWN_BOT_CB03_PREPARATION_ENABLED
    else:
        enabled = settings.CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED
    if not enabled:
        raise HTTPException(status_code=404, detail="Not found")


def _integer(value, *, positive: bool = True) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)
            and (value > 0 if positive else value >= 0))


def _validate_payload(action_type: str, data: dict, session_patient_id: int):
    # Persistent DB payload is not an unbounded dispatcher command language.
    if not isinstance(data, dict):
        raise HTTPException(status_code=409, detail="Proposition incohérente.")
    if action_type == "CREATE_APPOINTMENT":
        if set(data) != _APPOINTMENT_KEYS:
            raise HTTPException(status_code=409, detail="Proposition incohérente.")
        if (not _integer(data["patient_id"])
                or not _integer(data["praticien_id"])
                or data["patient_id"] != session_patient_id
                or (data["resource_id"] is not None and not _integer(data["resource_id"]))
                or not _integer(data["duration_minutes"])
                or not 5 <= data["duration_minutes"] <= 480
                or data["motif"] not in ("CONTROLE", "CONSULTATION", "DETARTRAGE")
                or not isinstance(data["datetime_start"], str)):
            raise HTTPException(status_code=409, detail="Proposition incohérente.")
        try:
            start = datetime.fromisoformat(data["datetime_start"])
            local_now = datetime.now(ZoneInfo(settings.CROWN_BOT_CABINET_TIMEZONE)).replace(
                tzinfo=None
            )
        except (ValueError, TypeError, KeyError):
            raise HTTPException(status_code=409, detail="Date invalide.")
        if start.tzinfo is not None or start <= local_now:
            raise HTTPException(status_code=409, detail="Créneau expiré ou invalide.")
    elif action_type == "CHANGE_STATUS":
        if set(data) != _STATUS_KEYS:
            raise HTTPException(status_code=409, detail="Proposition incohérente.")
        if (not _integer(data["appointment_id"]) or not _integer(data["patient_id"])
                or data["patient_id"] != session_patient_id
                or not _integer(data["expected_revision"], positive=False)
                or not isinstance(data["status_label"], str)
                or len(data["status_label"]) > 60):
            raise HTTPException(status_code=409, detail="Proposition incohérente.")
        try:
            old = models.AppointmentStatus[data["expected_status"]]
            new = models.AppointmentStatus[data["status"]]
        except (KeyError, TypeError):
            raise HTTPException(status_code=409, detail="Statut invalide.")
        if not transition_allowed(old, new):
            raise HTTPException(status_code=409, detail="Transition non autorisée.")
    else:
        raise HTTPException(status_code=403, detail="Action non autorisée.")


def _validate_live_status(db, owner: int, data: dict):
    """Recheck live patient/status/revision before dispatcher's SQL CAS."""
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == data["appointment_id"],
        models.Appointment.employer_id == owner,
        models.Appointment.patient_id == data["patient_id"],
        models.Appointment.deleted_at.is_(None),
    ).first()
    patient = db.query(models.Patient).filter(
        models.Patient.id == data["patient_id"],
        models.Patient.employer_id == owner,
        models.Patient.deleted_at.is_(None),
    ).first()
    if (appointment is None or patient is None
            or appointment.status.name != data["expected_status"]
            or appointment.clinical_revision != data["expected_revision"]):
        raise HTTPException(status_code=409, detail="Rendez-vous modifié : nouvelle préparation requise.")


def _receipt(db, record):
    """Receipt is stored in the action JSON in the SAME business transaction."""
    details = record.params_json.get("_cb03_receipt") if isinstance(record.params_json, dict) else None
    audit = db.query(models.AuditLog.id).filter(
        models.AuditLog.action == "CB03_ACTION_CONFIRMED",
        models.AuditLog.resource_id == record.id,
        models.AuditLog.employer_id == record.employer_id,
        models.AuditLog.user_id == record.user_id,
    ).first()
    if (not isinstance(details, dict) or not _integer(details.get("appointment_id"))
            or audit is None):
        return None
    if (record.action_type == "CHANGE_STATUS" and
            details.get("status") != record.params_json.get("status")):
        return None
    if (record.action_type == "CREATE_APPOINTMENT" and
            details.get("status") != "CREATED"):
        return None
    return {"appointment_id": details["appointment_id"], "status": details["status"]}


@router.get("/guided/actions/{preparation_id}")
def reconcile_preparation(
    preparation_id: UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Per-ID read-only reconciliation, including when a POST response was lost.

    No replay, status reset, reservation, or PII disclosure.
    """
    owner = _gate(user)
    action, _ = _owned_action(db, owner, user.id, str(preparation_id))
    _permissions(user, action.action_type)
    status = action.status
    outcome = None
    manual = status == "executing"
    if status == "prepared" and action.expires_at <= datetime.utcnow():
        status = "expired"
    if status == "executed":
        outcome = _receipt(db, action)
        if outcome is None:
            status = "uncertain"
            manual = True
    if status not in {"prepared", "executed", "expired", "cancelled", "failed"}:
        manual = True
    return {
        "preparation_id": action.id,
        "action_type": action.action_type,
        "status": status,
        "result": outcome,
        "safe_to_retry_automatically": False,
        "manual_reconciliation_required": manual,
        "next_step": (
            "verify_business_state_manually" if manual else
            "explicit_confirmation_required" if status == "prepared" else
            "none"
        ),
    }


@router.post("/guided/confirm")
def confirm_preparation(
    req: CB03ConfirmRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """One explicit confirmation, with an atomic claim and canonical mutation.

    On any failure: rollback both claim and business writes. Do NOT blindly
    retry after an ambiguous network outcome; GET /guided/actions/{id} first.
    """
    owner = _gate(user)
    if req.confirm is not True:
        raise HTTPException(status_code=422, detail="Confirmation explicite requise.")
    action, session = _owned_action(db, owner, user.id, str(req.preparation_id))
    _permissions(user, action.action_type)
    if action.status != "prepared":
        raise HTTPException(status_code=409, detail="Action déjà traitée ; consultez son état.")
    if action.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=410, detail="Préparation expirée ; recommencez.")
    _validate_payload(action.action_type, action.params_json, session.patient_id)

    # The conditional UPDATE locks the action row until final COMMIT.
    # PostgreSQL serializes competing confirmations; SQLite fences writes.
    from backend.services.bot.atomic_action_claim import claim_prepared_action
    try:
        if not claim_prepared_action(
            db, models.BotPendingAction, action.id, user.id, owner,
            datetime.utcnow(),
        ):
            db.rollback()
            raise HTTPException(status_code=409, detail="Action déjà traitée ou expirée.")
        if action.action_type == "CHANGE_STATUS":
            _validate_live_status(db, owner, action.params_json)

        response = dispatcher.execute(
            {"type": action.action_type, "params": action.params_json},
            db, user, transactional=True,
        )
        if response.action_type != "write_done":
            raise HTTPException(status_code=409, detail="Exécution refusée ; nouvelle préparation requise.")
        appointment_id = response.data.get("appointment_id") if isinstance(response.data, dict) else None
        if not _integer(appointment_id):
            raise HTTPException(status_code=409, detail="Résultat métier invérifiable.")

        # Prove the affected appointment belongs to the same patient and
        # cabinet and reflects the outcome BEFORE storing executed receipt.
        saved = db.query(models.Appointment).filter(
            models.Appointment.id == appointment_id,
            models.Appointment.employer_id == owner,
            models.Appointment.patient_id == action.params_json["patient_id"],
            models.Appointment.deleted_at.is_(None),
        ).first()
        if saved is None or (
            action.action_type == "CHANGE_STATUS"
            and saved.status.name != action.params_json["status"]
        ):
            raise HTTPException(status_code=409, detail="Résultat métier non confirmé.")

        outcome = {
            "appointment_id": appointment_id,
            "status": (
                action.params_json["status"]
                if action.action_type == "CHANGE_STATUS" else "CREATED"
            ),
        }
        db.add(models.AuditLog(
            user_id=user.id, employer_id=owner,
            action="CB03_ACTION_CONFIRMED",
            resource_type="BotPendingAction", resource_id=action.id,
            details=f"Transaction clinique atomique: {action.action_type}",
        ))
        # No separate result table or migration; preserve full DB-owned
        # original snapshot and durable receipt in JSON.
        from sqlalchemy import update
        result = db.execute(
            update(models.BotPendingAction).where(
                models.BotPendingAction.id == action.id,
                models.BotPendingAction.user_id == user.id,
                models.BotPendingAction.employer_id == owner,
                models.BotPendingAction.status == "executing",
            ).values(
                status="executed", executed_at=datetime.utcnow(),
                params_json={**action.params_json, "_cb03_receipt": outcome},
            )
        )
        if result.rowcount != 1:
            raise HTTPException(status_code=409, detail="État d'action incohérent.")
        db.commit()  # ONE commit: canonical business write + receipt + audit.
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        # The connection may fail during commit after the server sends it.
        # The caller MUST reconcile by action ID; never auto-replay.
        raise HTTPException(
            status_code=503, detail="Résultat incertain ; vérifiez l'identifiant de préparation."
        )

    return {
        "preparation_id": str(req.preparation_id),
        "status": "executed",
        "action_type": action.action_type,
        "result": outcome,
        "safe_to_retry_automatically": False,
    }
