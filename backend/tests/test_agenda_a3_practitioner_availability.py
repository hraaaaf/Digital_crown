import json
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend.services.agenda_availability import (
    get_practitioner_day_availability,
    validate_appointment_availability,
)


WEEK = {
    weekday: {
        "is_open": True,
        "is_continuous": False,
        "morning_start": "09:00",
        "morning_end": "13:00",
        "afternoon_start": "14:00",
        "afternoon_end": "18:00",
    }
    for weekday in (
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )
}


def practitioner_week(wednesday_intervals):
    return {
        weekday: {"intervals": list(wednesday_intervals) if weekday == "wednesday" else []}
        for weekday in (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        )
    }


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE cabinet_settings (
                id INTEGER PRIMARY KEY,
                opening_time_morning TEXT,
                closing_time_morning TEXT,
                opening_time_afternoon TEXT,
                closing_time_afternoon TEXT,
                is_continuous BOOLEAN,
                agenda_mode TEXT,
                use_tickets BOOLEAN,
                employer_id INTEGER,
                weekly_schedule_json TEXT
            )
        """))
        connection.execute(text("""
            CREATE TABLE agenda_exceptions (
                id INTEGER PRIMARY KEY,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                reason TEXT,
                is_holiday BOOLEAN,
                created_at DATETIME,
                employer_id INTEGER
            )
        """))
        connection.execute(text("""
            CREATE TABLE practitioner_agenda_settings (
                id INTEGER PRIMARY KEY,
                employer_id INTEGER NOT NULL,
                practitioner_id INTEGER NOT NULL,
                weekly_schedule_json TEXT NOT NULL,
                updated_at DATETIME
            )
        """))
        connection.execute(text("""
            CREATE TABLE practitioner_agenda_exceptions (
                id INTEGER PRIMARY KEY,
                employer_id INTEGER NOT NULL,
                practitioner_id INTEGER NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                reason TEXT NOT NULL,
                created_at DATETIME
            )
        """))
        connection.execute(
            text("""
                INSERT INTO cabinet_settings (
                    id, opening_time_morning, closing_time_morning,
                    opening_time_afternoon, closing_time_afternoon,
                    is_continuous, agenda_mode, use_tickets, employer_id, weekly_schedule_json
                ) VALUES (1, '09:00', '13:00', '14:00', '18:00', 0, 'EXACT', 0, 1, :week)
            """),
            {"week": json.dumps(WEEK)},
        )
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def configure(db: Session, practitioner_id: int, intervals):
    db.execute(
        text("""
            INSERT INTO practitioner_agenda_settings
            (employer_id, practitioner_id, weekly_schedule_json, updated_at)
            VALUES (1, :practitioner_id, :week, :updated_at)
        """),
        {
            "practitioner_id": practitioner_id,
            "week": json.dumps(practitioner_week(intervals)),
            "updated_at": datetime(2026, 9, 16, 8, 0),
        },
    )
    db.commit()


def validate(db: Session, practitioner_id: int, hour: int, minute: int = 0, duration: int = 30):
    return validate_appointment_availability(
        db,
        1,
        datetime(2026, 9, 16, hour, minute),
        duration,
        "EXACT_TIME",
        practitioner_id=practitioner_id,
    )


def test_existing_practitioner_without_override_inherits_cabinet(db):
    assert validate(db, practitioner_id=11, hour=10) is None
    day = get_practitioner_day_availability(db, 1, 11, date(2026, 9, 16))
    assert day["inherits_cabinet"] is True
    assert day["intervals"] == []


def test_personal_hours_and_breaks_block_only_target_practitioner(db):
    configure(db, 10, [{"start": "10:00", "end": "12:00"}, {"start": "14:00", "end": "17:00"}])

    assert "horaires de ce praticien" in validate(db, 10, 9, 15)
    assert "pause du praticien" in validate(db, 10, 12, 15)
    assert validate(db, 10, 10, 30) is None
    assert validate(db, 11, 12, 15) is None


def test_practitioner_exception_does_not_block_colleague(db):
    db.execute(
        text("""
            INSERT INTO practitioner_agenda_exceptions
            (employer_id, practitioner_id, start_date, end_date, reason, created_at)
            VALUES (1, 10, :start_date, :end_date, 'Congé', :created_at)
        """),
        {
            "start_date": datetime(2026, 9, 16, 10, 0),
            "end_date": datetime(2026, 9, 16, 11, 0),
            "created_at": datetime(2026, 9, 15, 12, 0),
        },
    )
    db.commit()

    assert "Congé" in validate(db, 10, 10, 15)
    assert validate(db, 11, 10, 15) is None

    day = get_practitioner_day_availability(db, 1, 10, date(2026, 9, 16))
    assert day["exceptions"][0]["reason"] == "Congé"


def test_global_closure_remains_absolute(db):
    db.execute(
        text("""
            INSERT INTO agenda_exceptions
            (start_date, end_date, reason, is_holiday, created_at, employer_id)
            VALUES (:start_date, :end_date, 'Formation équipe', 0, :created_at, 1)
        """),
        {
            "start_date": datetime(2026, 9, 16, 14, 0),
            "end_date": datetime(2026, 9, 16, 16, 0),
            "created_at": datetime(2026, 9, 15, 12, 0),
        },
    )
    db.commit()

    for practitioner_id in (10, 11):
        assert "Formation équipe" in validate(db, practitioner_id, 14, 30)


def test_empty_personal_day_is_day_off(db):
    configure(db, 10, [])
    assert validate(db, 10, 10) == "Ce praticien ne travaille pas ce jour."
    assert validate(db, 11, 10) is None


def test_booking_cannot_escape_cabinet_hours_even_with_personal_override(db):
    configure(db, 10, [{"start": "08:00", "end": "20:00"}])
    assert "cabinet" in validate(db, 10, 8, 30).lower()
    assert "cabinet" in validate(db, 10, 18, 0).lower()
