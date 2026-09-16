from datetime import datetime

import pytest
from fastapi import HTTPException

from backend import models
from backend.routers.appointments import get_appointments


def _team_dentist(db, owner, *, name="Dr Team"):
    user = models.User(
        email=f"agenda-a1-team-{owner.id}-{datetime.now().timestamp()}@test.ma",
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        approval_status=models.ApprovalStatus.APPROVED.value,
        employer_id=owner.id,
        nom_complet=name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _foreign_owner(db):
    user = models.User(
        email=f"agenda-a1-foreign-{datetime.now().timestamp()}@test.ma",
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        approval_status=models.ApprovalStatus.APPROVED.value,
        nom_complet="Dr Foreign",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _seed_appointment(db, owner_id, practitioner_id, name, hour):
    appointment = models.Appointment(
        patient_name=name,
        datetime_start=datetime(2026, 9, 21, hour, 0),
        duration_minutes=30,
        employer_id=owner_id,
        praticien_id=practitioner_id,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def test_practitioner_filter_returns_selected_and_legacy_only(db, dentiste):
    team = _team_dentist(db, dentiste)
    owner_appt = _seed_appointment(db, dentiste.id, dentiste.id, "Owner", 9)
    team_appt = _seed_appointment(db, dentiste.id, team.id, "Team", 10)
    legacy_appt = _seed_appointment(db, dentiste.id, None, "Legacy", 11)

    result = get_appointments(
        praticien_id=dentiste.id,
        db=db,
        current_user=dentiste,
    )

    assert [appointment.id for appointment in result] == [owner_appt.id, legacy_appt.id]
    assert team_appt.id not in {appointment.id for appointment in result}


def test_practitioner_filter_preserves_cabinet_wide_read_when_omitted(db, dentiste):
    team = _team_dentist(db, dentiste)
    owner_appt = _seed_appointment(db, dentiste.id, dentiste.id, "Owner", 9)
    team_appt = _seed_appointment(db, dentiste.id, team.id, "Team", 10)
    legacy_appt = _seed_appointment(db, dentiste.id, None, "Legacy", 11)

    result = get_appointments(
        praticien_id=None,
        db=db,
        current_user=dentiste,
    )

    assert [appointment.id for appointment in result] == [owner_appt.id, team_appt.id, legacy_appt.id]


def test_practitioner_filter_rejects_foreign_practitioner(db, dentiste):
    foreign = _foreign_owner(db)

    with pytest.raises(HTTPException) as exc:
        get_appointments(
            praticien_id=foreign.id,
            db=db,
            current_user=dentiste,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Praticien non assignable dans ce cabinet"
