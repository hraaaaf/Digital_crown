from datetime import datetime, timedelta

from backend import models
from backend.routers import agenda_settings
from backend.schemas.agenda import AgendaExceptionCreate, CabinetSettingsUpdate
from backend.security import get_password_hash


def _owner(db, email: str):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TenantTest123!"),
        role=models.UserRole.DENTISTE,
        nom_complet=email,
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_agenda_settings_are_isolated_between_two_cabinets(db):
    owner_a = _owner(db, "owner-a@cabinet.test")
    owner_b = _owner(db, "owner-b@cabinet.test")

    agenda_settings.update_cabinet_settings(
        CabinetSettingsUpdate(opening_time_morning="08:00", closing_time_morning="12:00"),
        db,
        owner_a,
    )
    agenda_settings.update_cabinet_settings(
        CabinetSettingsUpdate(opening_time_morning="10:00", closing_time_morning="14:00"),
        db,
        owner_b,
    )

    settings_a = agenda_settings.get_cabinet_settings(db, owner_a)
    settings_b = agenda_settings.get_cabinet_settings(db, owner_b)

    assert settings_a["opening_time_morning"] == "08:00"
    assert settings_b["opening_time_morning"] == "10:00"
    assert settings_a["id"] != settings_b["id"]


def test_agenda_exceptions_cannot_be_listed_or_deleted_cross_tenant(db):
    owner_a = _owner(db, "exception-a@cabinet.test")
    owner_b = _owner(db, "exception-b@cabinet.test")
    start = datetime(2026, 8, 20, 9, 0)

    created_a = agenda_settings.create_exception(
        AgendaExceptionCreate(
            start_date=start,
            end_date=start + timedelta(hours=8),
            reason="Cabinet A fermé",
            is_holiday=False,
        ),
        db,
        owner_a,
    )
    agenda_settings.create_exception(
        AgendaExceptionCreate(
            start_date=start + timedelta(days=1),
            end_date=start + timedelta(days=1, hours=8),
            reason="Cabinet B fermé",
            is_holiday=False,
        ),
        db,
        owner_b,
    )

    rows_a = agenda_settings.list_exceptions(db, owner_a)
    rows_b = agenda_settings.list_exceptions(db, owner_b)

    assert [row["reason"] for row in rows_a] == ["Cabinet A fermé"]
    assert [row["reason"] for row in rows_b] == ["Cabinet B fermé"]

    try:
        agenda_settings.delete_exception(created_a["id"], db, owner_b)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 404
    else:
        raise AssertionError("Cross-tenant delete must fail closed")

    assert [row["reason"] for row in agenda_settings.list_exceptions(db, owner_a)] == ["Cabinet A fermé"]


def test_ambiguous_legacy_rows_are_not_claimed(db):
    owner_a = _owner(db, "legacy-a@cabinet.test")
    _owner(db, "legacy-b@cabinet.test")

    agenda_settings._ensure_tenant_columns(db)
    # Model-created legacy row has employer_id NULL because the new column is
    # deliberately additive and not mapped in the historical ORM class.
    legacy = models.CabinetSettings()
    db.add(legacy)
    db.commit()

    agenda_settings._claim_legacy_rows_if_unambiguous(db, owner_a.id)

    row = db.execute(
        agenda_settings.text("SELECT employer_id FROM cabinet_settings WHERE id = :id"),
        {"id": legacy.id},
    ).first()
    assert row[0] is None
