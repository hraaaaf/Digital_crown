import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db
from backend.models_agenda_a3 import PractitionerAgendaException, PractitionerAgendaSettings
from backend.schemas.agenda import (
    CabinetSettingsOut,
    CabinetSettingsUpdate,
    AgendaExceptionOut,
    AgendaExceptionCreate,
    PractitionerAgendaExceptionCreate,
    PractitionerAgendaExceptionOut,
    PractitionerAgendaSettingsOut,
    PractitionerAgendaSettingsUpdate,
    PractitionerAgendaSummaryOut,
    PractitionerWeeklySchedule,
)
from backend.routers.auth import require_permission
from backend.services.holiday_engine import holiday_engine

router = APIRouter(prefix="/agenda", tags=["Agenda"])

_LEGACY_SETTINGS_FIELDS = (
    "opening_time_morning",
    "closing_time_morning",
    "opening_time_afternoon",
    "closing_time_afternoon",
    "is_continuous",
    "agenda_mode",
    "use_tickets",
)

_WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def _ensure_tenant_columns(db: Session) -> None:
    """Add tenant and additive Agenda columns idempotently for legacy installations."""
    bind = db.get_bind()
    inspector = inspect(bind)
    for table_name in ("cabinet_settings", "agenda_exceptions"):
        columns = {col["name"] for col in inspector.get_columns(table_name)}
        if "employer_id" not in columns:
            db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN employer_id INTEGER"))
            db.commit()
        if table_name == "cabinet_settings" and "weekly_schedule_json" not in columns:
            db.execute(text("ALTER TABLE cabinet_settings ADD COLUMN weekly_schedule_json TEXT"))
            db.commit()
        db.execute(text(
            f"CREATE INDEX IF NOT EXISTS ix_{table_name}_employer_id "
            f"ON {table_name} (employer_id)"
        ))
        db.commit()


def _claim_legacy_rows_if_unambiguous(db: Session, employer_id: int) -> None:
    """Claim pre-tenant rows only when exactly one root practice owner exists."""
    root_ids = [
        row[0]
        for row in db.query(models.User.id).filter(
            models.User.employer_id.is_(None),
            models.User.role.in_([models.UserRole.ADMIN, models.UserRole.DENTISTE]),
        ).all()
    ]
    if root_ids != [employer_id]:
        return
    for table_name in ("cabinet_settings", "agenda_exceptions"):
        db.execute(
            text(f"UPDATE {table_name} SET employer_id = :employer_id WHERE employer_id IS NULL"),
            {"employer_id": employer_id},
        )
    db.commit()


def _prepare_tenant(db: Session, current_user: models.User) -> int:
    employer_id = current_user.get_employer_id()
    _ensure_tenant_columns(db)
    _claim_legacy_rows_if_unambiguous(db, employer_id)
    return employer_id


def _legacy_weekly_schedule(row: dict) -> dict:
    day = {
        "is_open": True,
        "is_continuous": bool(row.get("is_continuous")),
        "morning_start": row.get("opening_time_morning") or "09:00",
        "morning_end": row.get("closing_time_morning") or "13:00",
        "afternoon_start": row.get("opening_time_afternoon") or "14:00",
        "afternoon_end": row.get("closing_time_afternoon") or "18:00",
    }
    return {weekday: dict(day) for weekday in _WEEKDAYS}


def _hydrate_settings_row(row):
    if row is None:
        return None
    data = dict(row)
    raw_schedule = data.pop("weekly_schedule_json", None)
    if raw_schedule:
        try:
            data["weekly_schedule"] = json.loads(raw_schedule)
        except (TypeError, json.JSONDecodeError):
            data["weekly_schedule"] = _legacy_weekly_schedule(data)
    else:
        data["weekly_schedule"] = _legacy_weekly_schedule(data)
    return data


def _settings_row(db: Session, employer_id: int):
    row = db.execute(
        text(
            "SELECT id, opening_time_morning, closing_time_morning, "
            "opening_time_afternoon, closing_time_afternoon, is_continuous, "
            "agenda_mode, use_tickets, weekly_schedule_json FROM cabinet_settings "
            "WHERE employer_id = :employer_id ORDER BY id LIMIT 1"
        ),
        {"employer_id": employer_id},
    ).mappings().first()
    return _hydrate_settings_row(row)


def _create_default_settings(db: Session, employer_id: int):
    defaults = CabinetSettingsUpdate().model_dump()
    defaults.pop("weekly_schedule", None)
    mode = defaults["agenda_mode"]
    defaults["agenda_mode"] = getattr(mode, "value", mode)
    db.execute(
        text(
            "INSERT INTO cabinet_settings ("
            "opening_time_morning, closing_time_morning, opening_time_afternoon, "
            "closing_time_afternoon, is_continuous, agenda_mode, use_tickets, employer_id, weekly_schedule_json"
            ") VALUES ("
            ":opening_time_morning, :closing_time_morning, :opening_time_afternoon, "
            ":closing_time_afternoon, :is_continuous, :agenda_mode, :use_tickets, :employer_id, NULL"
            ")"
        ),
        {**defaults, "employer_id": employer_id},
    )
    db.commit()
    return _settings_row(db, employer_id)


def _is_assignable_practitioner(user: models.User, employer_id: int) -> bool:
    if not user.is_active or user.approval_status != models.ApprovalStatus.APPROVED.value:
        return False
    if user.id == employer_id:
        return user.role in (models.UserRole.DENTISTE, models.UserRole.ADMIN)
    return user.employer_id == employer_id and user.role == models.UserRole.DENTISTE


def _get_practitioner(db: Session, employer_id: int, practitioner_id: int) -> models.User:
    practitioner = db.query(models.User).filter(models.User.id == practitioner_id).first()
    if not practitioner or not _is_assignable_practitioner(practitioner, employer_id):
        raise HTTPException(status_code=404, detail="Praticien introuvable dans ce cabinet")
    return practitioner


def _practitioner_name(practitioner: models.User) -> str:
    return practitioner.nom_complet or practitioner.email


def _parse_practitioner_schedule(raw: str) -> PractitionerWeeklySchedule:
    try:
        return PractitionerWeeklySchedule.model_validate(json.loads(raw))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Configuration horaire praticien invalide. Corrigez-la avant toute nouvelle réservation.",
        ) from exc


def _practitioner_settings_payload(
    practitioner: models.User,
    row: PractitionerAgendaSettings | None,
) -> dict:
    if row is None:
        return {
            "practitioner_id": practitioner.id,
            "practitioner_name": _practitioner_name(practitioner),
            "inherits_cabinet": True,
            "weekly_schedule": None,
            "updated_at": None,
        }
    return {
        "practitioner_id": practitioner.id,
        "practitioner_name": _practitioner_name(practitioner),
        "inherits_cabinet": False,
        "weekly_schedule": _parse_practitioner_schedule(row.weekly_schedule_json),
        "updated_at": row.updated_at,
    }


@router.get("/settings", response_model=CabinetSettingsOut)
def get_cabinet_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = _prepare_tenant(db, current_user)
    row = _settings_row(db, employer_id)
    return row or _create_default_settings(db, employer_id)


@router.put("/settings", response_model=CabinetSettingsOut)
def update_cabinet_settings(
    settings_update: CabinetSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("settings")),
):
    employer_id = _prepare_tenant(db, current_user)
    if not _settings_row(db, employer_id):
        _create_default_settings(db, employer_id)

    payload = settings_update.model_dump()
    weekly_schedule = payload.pop("weekly_schedule", None)
    mode = payload["agenda_mode"]
    payload["agenda_mode"] = getattr(mode, "value", mode)

    assignments = [f"{field} = :{field}" for field in _LEGACY_SETTINGS_FIELDS]
    params = {**payload, "employer_id": employer_id}
    if weekly_schedule is not None:
        assignments.append("weekly_schedule_json = :weekly_schedule_json")
        params["weekly_schedule_json"] = json.dumps(weekly_schedule, ensure_ascii=False, separators=(",", ":"))

    db.execute(
        text(f"UPDATE cabinet_settings SET {', '.join(assignments)} WHERE employer_id = :employer_id"),
        params,
    )
    db.commit()
    return _settings_row(db, employer_id)


@router.get("/exceptions", response_model=List[AgendaExceptionOut])
def list_exceptions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = _prepare_tenant(db, current_user)
    rows = db.execute(
        text(
            "SELECT id, start_date, end_date, reason, is_holiday, created_at "
            "FROM agenda_exceptions WHERE employer_id = :employer_id "
            "ORDER BY start_date, id"
        ),
        {"employer_id": employer_id},
    ).mappings().all()
    return list(rows)


@router.post("/exceptions", response_model=AgendaExceptionOut)
def create_exception(
    exc_in: AgendaExceptionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = _prepare_tenant(db, current_user)
    payload = exc_in.model_dump()
    created_at = datetime.utcnow()
    result = db.execute(
        text(
            "INSERT INTO agenda_exceptions "
            "(start_date, end_date, reason, is_holiday, created_at, employer_id) "
            "VALUES (:start_date, :end_date, :reason, :is_holiday, :created_at, :employer_id)"
        ),
        {**payload, "created_at": created_at, "employer_id": employer_id},
    )
    db.commit()
    exc_id = result.lastrowid
    if exc_id is None:
        row = db.execute(
            text(
                "SELECT id, start_date, end_date, reason, is_holiday, created_at "
                "FROM agenda_exceptions WHERE employer_id = :employer_id "
                "ORDER BY id DESC LIMIT 1"
            ),
            {"employer_id": employer_id},
        ).mappings().first()
    else:
        row = db.execute(
            text(
                "SELECT id, start_date, end_date, reason, is_holiday, created_at "
                "FROM agenda_exceptions WHERE id = :id AND employer_id = :employer_id"
            ),
            {"id": exc_id, "employer_id": employer_id},
        ).mappings().first()
    return row


@router.delete("/exceptions/{exc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exception(
    exc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = _prepare_tenant(db, current_user)
    result = db.execute(
        text("DELETE FROM agenda_exceptions WHERE id = :id AND employer_id = :employer_id"),
        {"id": exc_id, "employer_id": employer_id},
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="Exception not found")
    db.commit()
    return None


@router.get("/practitioners", response_model=List[PractitionerAgendaSummaryOut])
def list_practitioner_agenda_summaries(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = current_user.get_employer_id()
    owner = db.query(models.User).filter(models.User.id == employer_id).first()
    practitioners = db.query(models.User).filter(
        models.User.employer_id == employer_id,
        models.User.role == models.UserRole.DENTISTE,
        models.User.is_active.is_(True),
        models.User.approval_status == models.ApprovalStatus.APPROVED.value,
    ).order_by(models.User.id).all()
    all_practitioners = list(practitioners)
    if owner and _is_assignable_practitioner(owner, employer_id):
        all_practitioners.insert(0, owner)

    configured_ids = {
        row[0]
        for row in db.query(PractitionerAgendaSettings.practitioner_id).filter(
            PractitionerAgendaSettings.employer_id == employer_id
        ).all()
    }
    return [
        {
            "practitioner_id": practitioner.id,
            "practitioner_name": _practitioner_name(practitioner),
            "inherits_cabinet": practitioner.id not in configured_ids,
        }
        for practitioner in all_practitioners
    ]


@router.get("/practitioners/{practitioner_id}/settings", response_model=PractitionerAgendaSettingsOut)
def get_practitioner_agenda_settings(
    practitioner_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = current_user.get_employer_id()
    practitioner = _get_practitioner(db, employer_id, practitioner_id)
    row = db.query(PractitionerAgendaSettings).filter(
        PractitionerAgendaSettings.employer_id == employer_id,
        PractitionerAgendaSettings.practitioner_id == practitioner_id,
    ).first()
    return _practitioner_settings_payload(practitioner, row)


@router.put("/practitioners/{practitioner_id}/settings", response_model=PractitionerAgendaSettingsOut)
def update_practitioner_agenda_settings(
    practitioner_id: int,
    settings_update: PractitionerAgendaSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("settings")),
):
    employer_id = current_user.get_employer_id()
    practitioner = _get_practitioner(db, employer_id, practitioner_id)
    row = db.query(PractitionerAgendaSettings).filter(
        PractitionerAgendaSettings.employer_id == employer_id,
        PractitionerAgendaSettings.practitioner_id == practitioner_id,
    ).first()
    serialized = json.dumps(
        settings_update.weekly_schedule.model_dump(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    if row is None:
        row = PractitionerAgendaSettings(
            employer_id=employer_id,
            practitioner_id=practitioner_id,
            weekly_schedule_json=serialized,
            updated_at=datetime.utcnow(),
        )
        db.add(row)
    else:
        row.weekly_schedule_json = serialized
        row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return _practitioner_settings_payload(practitioner, row)


@router.delete("/practitioners/{practitioner_id}/settings", status_code=status.HTTP_204_NO_CONTENT)
def reset_practitioner_agenda_settings(
    practitioner_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("settings")),
):
    employer_id = current_user.get_employer_id()
    _get_practitioner(db, employer_id, practitioner_id)
    db.query(PractitionerAgendaSettings).filter(
        PractitionerAgendaSettings.employer_id == employer_id,
        PractitionerAgendaSettings.practitioner_id == practitioner_id,
    ).delete(synchronize_session=False)
    db.commit()
    return None


@router.get(
    "/practitioners/{practitioner_id}/exceptions",
    response_model=List[PractitionerAgendaExceptionOut],
)
def list_practitioner_exceptions(
    practitioner_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = current_user.get_employer_id()
    _get_practitioner(db, employer_id, practitioner_id)
    return db.query(PractitionerAgendaException).filter(
        PractitionerAgendaException.employer_id == employer_id,
        PractitionerAgendaException.practitioner_id == practitioner_id,
    ).order_by(PractitionerAgendaException.start_date, PractitionerAgendaException.id).all()


@router.post(
    "/practitioners/{practitioner_id}/exceptions",
    response_model=PractitionerAgendaExceptionOut,
)
def create_practitioner_exception(
    practitioner_id: int,
    exc_in: PractitionerAgendaExceptionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("settings")),
):
    employer_id = current_user.get_employer_id()
    _get_practitioner(db, employer_id, practitioner_id)
    row = PractitionerAgendaException(
        employer_id=employer_id,
        practitioner_id=practitioner_id,
        **exc_in.model_dump(),
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete(
    "/practitioners/{practitioner_id}/exceptions/{exc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_practitioner_exception(
    practitioner_id: int,
    exc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("settings")),
):
    employer_id = current_user.get_employer_id()
    _get_practitioner(db, employer_id, practitioner_id)
    deleted = db.query(PractitionerAgendaException).filter(
        PractitionerAgendaException.id == exc_id,
        PractitionerAgendaException.employer_id == employer_id,
        PractitionerAgendaException.practitioner_id == practitioner_id,
    ).delete(synchronize_session=False)
    if not deleted:
        db.rollback()
        raise HTTPException(status_code=404, detail="Indisponibilité praticien introuvable")
    db.commit()
    return None


@router.get("/upcoming-holidays")
def get_upcoming_holidays():
    return holiday_engine.get_upcoming_holidays(90)
