from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db
from backend.schemas.agenda import (
    CabinetSettingsOut,
    CabinetSettingsUpdate,
    AgendaExceptionOut,
    AgendaExceptionCreate,
)
from backend.routers.auth import require_permission
from backend.services.holiday_engine import holiday_engine

router = APIRouter(prefix="/agenda", tags=["Agenda"])

_SETTINGS_FIELDS = (
    "opening_time_morning",
    "closing_time_morning",
    "opening_time_afternoon",
    "closing_time_afternoon",
    "is_continuous",
    "agenda_mode",
    "use_tickets",
)


def _ensure_tenant_columns(db: Session) -> None:
    """Add the tenant columns idempotently for legacy installations.

    The project historically used self-healing additive migrations rather than
    Alembic. Keep that contract here, but never silently assign ambiguous legacy
    rows to a cabinet.
    """
    bind = db.get_bind()
    inspector = inspect(bind)
    for table_name in ("cabinet_settings", "agenda_exceptions"):
        columns = {col["name"] for col in inspector.get_columns(table_name)}
        if "employer_id" not in columns:
            db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN employer_id INTEGER"))
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


def _settings_row(db: Session, employer_id: int):
    return db.execute(
        text(
            "SELECT id, opening_time_morning, closing_time_morning, "
            "opening_time_afternoon, closing_time_afternoon, is_continuous, "
            "agenda_mode, use_tickets FROM cabinet_settings "
            "WHERE employer_id = :employer_id ORDER BY id LIMIT 1"
        ),
        {"employer_id": employer_id},
    ).mappings().first()


def _create_default_settings(db: Session, employer_id: int):
    defaults = CabinetSettingsUpdate().model_dump()
    mode = defaults["agenda_mode"]
    defaults["agenda_mode"] = getattr(mode, "value", mode)
    db.execute(
        text(
            "INSERT INTO cabinet_settings ("
            "opening_time_morning, closing_time_morning, opening_time_afternoon, "
            "closing_time_afternoon, is_continuous, agenda_mode, use_tickets, employer_id"
            ") VALUES ("
            ":opening_time_morning, :closing_time_morning, :opening_time_afternoon, "
            ":closing_time_afternoon, :is_continuous, :agenda_mode, :use_tickets, :employer_id"
            ")"
        ),
        {**defaults, "employer_id": employer_id},
    )
    db.commit()
    return _settings_row(db, employer_id)


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
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = _prepare_tenant(db, current_user)
    if not _settings_row(db, employer_id):
        _create_default_settings(db, employer_id)

    payload = settings_update.model_dump()
    mode = payload["agenda_mode"]
    payload["agenda_mode"] = getattr(mode, "value", mode)
    assignments = ", ".join(f"{field} = :{field}" for field in _SETTINGS_FIELDS)
    db.execute(
        text(f"UPDATE cabinet_settings SET {assignments} WHERE employer_id = :employer_id"),
        {**payload, "employer_id": employer_id},
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


@router.get("/upcoming-holidays")
def get_upcoming_holidays():
    return holiday_engine.get_upcoming_holidays(90)
