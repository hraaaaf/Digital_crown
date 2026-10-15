"""Clinical regression gate: REAL canonical application ORM and all booking ingress.

Synthetic patients only. These tests use the shared FastAPI fixture/schema and
assert the business rules at the actual route/service boundary; they do NOT
certify independent-process PostgreSQL/SQLCipher by themselves.
"""
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from backend import models, schemas
from backend.routers.appointments import create_appointment, create_bulk_appointments, update_appointment
from backend.routers.frontdesk import confirm_appointment
from backend.routers.mobile_legacy import create_mobile_appointment, MobileAppointmentCreate
from backend.services.agenda_availability import validate_appointment_availability


def _slot(days=8, hour=11):
    return (datetime.now() + timedelta(days=days)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )


def _appointment(db, owner, slot, *, patient_name="Clinical Fixture", practitioner=None):
    obj = models.Appointment(
        patient_name=patient_name, employer_id=owner.get_employer_id(),
        praticien_id=practitioner if practitioner is not None else owner.id,
        datetime_start=slot, duration_minutes=30,
        scheduling_type=models.SchedulingType.EXACT_TIME,
        status=models.AppointmentStatus.PREVU,
    )
    db.add(obj)
    db.commit()
    return obj


def _cabinet_week(db, employer_id, *, closed_day=None):
    week = {
        key: {"is_open": key != closed_day, "is_continuous": False,
              "morning_start": "09:00", "morning_end": "13:00",
              "afternoon_start": "14:00", "afternoon_end": "18:00"}
        for key in ("monday", "tuesday", "wednesday", "thursday",
                    "friday", "saturday", "sunday")
    }
    db.execute(text(
        "INSERT INTO cabinet_settings "
        "(opening_time_morning, closing_time_morning, opening_time_afternoon, "
        "closing_time_afternoon, is_continuous, agenda_mode, use_tickets, "
        "employer_id, weekly_schedule_json) "
        "VALUES ('09:00','13:00','14:00','18:00',0,'EXACT',0,:id,:week)"
    ), {"id": employer_id, "week": json.dumps(week)})
    db.commit()


def test_clinic_real_closed_day_rejects_bot_and_canonical_booking(db, dentiste):
    slot = _slot(8, 11)
    _cabinet_week(db, dentiste.get_employer_id(), closed_day=slot.strftime("%A").lower())
    assert "fermé" in validate_appointment_availability(
        db, dentiste.get_employer_id(), slot, 30,
        models.SchedulingType.EXACT_TIME, practitioner_id=dentiste.id
    )
    before = db.query(models.Appointment).count()
    with pytest.raises(HTTPException) as exc:
        create_appointment(
            schemas.AppointmentCreate(
                patient_name="Clinical Fixture", datetime_start=slot,
                praticien_id=dentiste.id, duration_minutes=30,
            ), db, dentiste,
        )
    assert exc.value.status_code == 422
    assert db.query(models.Appointment).count() == before


def test_clinic_mobile_cannot_bypass_existing_canonical_slot(db, dentiste):
    slot = _slot(9, 11)
    _appointment(db, dentiste, slot)
    before = db.query(models.Appointment).count()
    with pytest.raises(HTTPException) as exc:
        create_mobile_appointment(
            MobileAppointmentCreate(
                datetime_start=slot.isoformat(), patient_name="Mobile Clinical",
                motif="Consultation", duration_minutes=30,
            ), employer_id=dentiste.get_employer_id(),
            _mobile_user=dentiste, db=db,
        )
    assert exc.value.status_code == 409
    assert db.query(models.Appointment).count() == before


def test_clinic_bulk_cannot_bypass_existing_bot_slot(db, dentiste):
    slot = _slot(10, 11)
    _appointment(db, dentiste, slot)
    payload = schemas.AppointmentBulkCreate(appointments=[
        schemas.AppointmentImportItem(
            patient_name="Bulk Clinical", datetime_start=slot,
            praticien_id=dentiste.id, duration_minutes=30,
        )
    ])
    with pytest.raises(HTTPException) as exc:
        create_bulk_appointments(payload, db, dentiste)
    assert exc.value.status_code == 409


def test_clinic_reschedule_cannot_collide_with_other_booking(db, dentiste):
    first = _appointment(db, dentiste, _slot(11, 11))
    second = _appointment(db, dentiste, _slot(11, 15))
    with pytest.raises(HTTPException) as exc:
        update_appointment(
            second.id, schemas.AppointmentUpdate(datetime_start=first.datetime_start),
            db, dentiste,
        )
    assert exc.value.status_code == 409
    db.refresh(second)
    assert second.datetime_start != first.datetime_start


def test_clinic_frontdesk_confirmation_rejects_conflicting_confirmed_slot(db, dentiste):
    slot = _slot(12, 11)
    _appointment(db, dentiste, slot)
    request = models.Appointment(
        employer_id=dentiste.get_employer_id(), patient_name="Frontdesk Clinical",
        datetime_start=slot, duration_minutes=30,
        status=models.AppointmentStatus.EN_ATTENTE_DEMANDE,
        scheduling_type=models.SchedulingType.EXACT_TIME,
    )
    db.add(request)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        asyncio.run(confirm_appointment(request.id, db=db, current_user=dentiste))
    assert exc.value.status_code == 409
    db.refresh(request)
    assert request.status == models.AppointmentStatus.EN_ATTENTE_DEMANDE


def test_clinic_real_cabinet_closure_rejects_booking(db, dentiste):
    slot = _slot(13, 11)
    _cabinet_week(db, dentiste.get_employer_id())
    db.execute(text(
        "INSERT INTO agenda_exceptions "
        "(start_date,end_date,reason,is_holiday,employer_id) "
        "VALUES (:start,:end,'Synthetic closure',0,:employer)"
    ), {
        "start": slot - timedelta(minutes=15),
        "end": slot + timedelta(minutes=45),
        "employer": dentiste.get_employer_id(),
    })
    db.commit()
    with pytest.raises(HTTPException) as exc:
        create_appointment(
            schemas.AppointmentCreate(
                patient_name="Clinical Closure", datetime_start=slot,
                praticien_id=dentiste.id, duration_minutes=30,
            ), db, dentiste,
        )
    assert exc.value.status_code == 422
    assert "Synthetic closure" in str(exc.value.detail)


def test_clinic_write_requires_unambiguous_full_patient_name(db, dentiste):
    from backend.services.bot.action_dispatcher import ActionDispatcher
    names = [
        models.Patient(
            prenom="Ahmed", nom="Bennani", date_naissance=datetime(1990, 1, 1),
            sexe="M", employer_id=dentiste.get_employer_id(),
        ),
        models.Patient(
            prenom="Ahmed", nom="Bennani", date_naissance=datetime(1988, 1, 1),
            sexe="M", employer_id=dentiste.get_employer_id(),
        ),
    ]
    db.add_all(names)
    db.commit()
    matcher = ActionDispatcher()
    tenant = dentiste.get_employer_id()
    assert matcher._find_patient_for_write(db, tenant, "Ahmed") is None
    assert matcher._find_patient_for_write(db, tenant, "Ahmed Benn") is None
    assert matcher._find_patient_for_write(db, tenant, "Ahmed Bennani") is None
    names[1].deleted_at = datetime.utcnow()
    db.commit()
    assert matcher._find_patient_for_write(db, tenant, "Ahmed Bennani").id == names[0].id


def test_clinic_production_fails_closed_without_agenda_settings(db, dentiste, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    slot = _slot(8, 11)
    with pytest.raises(HTTPException) as exc:
        create_appointment(
            schemas.AppointmentCreate(
                patient_name="Synthetic No Settings", praticien_id=dentiste.id,
                datetime_start=slot, duration_minutes=30,
            ), db, dentiste,
        )
    assert exc.value.status_code == 422
    assert "configurez les horaires" in str(exc.value.detail)
    assert db.query(models.Appointment).count() == 0
