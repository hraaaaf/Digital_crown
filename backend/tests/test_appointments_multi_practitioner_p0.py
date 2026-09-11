from datetime import datetime

import pytest
from fastapi import HTTPException

from backend import models, schemas
from backend.routers.appointments import (
    _validate_practitioner,
    check_conflicts,
    create_appointment,
    create_bulk_appointments,
    get_multi_practitioner_appointments,
    update_appointment,
)


def _team_user(db, owner, *, role=models.UserRole.DENTISTE, active=True, approval="approved"):
    user = models.User(
        email=f"team-{owner.id}-{role.value}-{len(owner.email)}-{datetime.now().timestamp()}@test.ma",
        hashed_password="x",
        role=role,
        is_active=active,
        is_licensed=True,
        approval_status=approval,
        employer_id=owner.id,
        nom_complet="Dr Team",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _foreign_owner(db):
    user = models.User(
        email=f"foreign-{datetime.now().timestamp()}@test.ma",
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        approval_status="approved",
        nom_complet="Dr Foreign",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _appt(start, practitioner_id=None, name="Patient"):
    return schemas.AppointmentCreate(
        patient_name=name,
        praticien_id=practitioner_id,
        datetime_start=start,
        duration_minutes=30,
    )


def test_praticien_mapping_is_nullable_indexed_fk():
    column = models.Appointment.__table__.c.praticien_id
    assert column.nullable is True
    assert column.index is True
    assert {fk.target_fullname for fk in column.foreign_keys} == {"users.id"}


def test_same_practitioner_conflicts_but_different_practitioner_can_share_slot(db, dentiste):
    team = _team_user(db, dentiste)
    slot = datetime(2026, 9, 14, 10, 0)

    first = create_appointment(_appt(slot, dentiste.id, "A"), db, dentiste)
    second = create_appointment(_appt(slot, team.id, "B"), db, dentiste)

    assert first.praticien_id == dentiste.id
    assert second.praticien_id == team.id

    with pytest.raises(HTTPException) as exc:
        create_appointment(_appt(slot, dentiste.id, "C"), db, dentiste)
    assert exc.value.status_code == 409


def test_legacy_unassigned_appointment_blocks_every_practitioner(db, dentiste):
    team = _team_user(db, dentiste)
    slot = datetime(2026, 9, 15, 11, 0)
    legacy = models.Appointment(
        patient_name="Legacy",
        datetime_start=slot,
        duration_minutes=30,
        employer_id=dentiste.id,
        praticien_id=None,
    )
    db.add(legacy)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        create_appointment(_appt(slot, team.id), db, dentiste)
    assert exc.value.status_code == 409


def test_invalid_practitioners_are_rejected(db, dentiste):
    secretary = _team_user(db, dentiste, role=models.UserRole.SECRETAIRE)
    pending = _team_user(db, dentiste, approval="pending")
    inactive = _team_user(db, dentiste, active=False)
    foreign = _foreign_owner(db)

    for practitioner in (secretary, pending, inactive, foreign):
        with pytest.raises(HTTPException) as exc:
            _validate_practitioner(db, dentiste.id, practitioner.id)
        assert exc.value.status_code == 403


def test_check_conflicts_validates_practitioner_tenant(db, dentiste):
    foreign = _foreign_owner(db)
    with pytest.raises(HTTPException) as exc:
        check_conflicts(
            datetime_start="2026-09-16T09:00:00",
            duration_minutes=30,
            praticien_id=foreign.id,
            exclude_id=None,
            db=db,
            current_user=dentiste,
        )
    assert exc.value.status_code == 403


def test_update_reassignment_rechecks_practitioner_conflicts(db, dentiste):
    team = _team_user(db, dentiste)
    slot = datetime(2026, 9, 16, 9, 0)
    create_appointment(_appt(slot, dentiste.id, "Owner"), db, dentiste)
    team_appt = create_appointment(_appt(datetime(2026, 9, 16, 10, 0), team.id, "Team"), db, dentiste)

    with pytest.raises(HTTPException) as exc:
        update_appointment(
            team_appt.id,
            schemas.AppointmentUpdate(praticien_id=dentiste.id, datetime_start=slot),
            db,
            dentiste,
        )
    assert exc.value.status_code == 409


def test_bulk_detects_internal_collision_before_insert(db, dentiste):
    slot = datetime(2026, 9, 17, 14, 0)
    payload = schemas.AppointmentBulkCreate(
        appointments=[
            schemas.AppointmentImportItem(
                patient_name="A",
                praticien_id=dentiste.id,
                datetime_start=slot,
                duration_minutes=30,
            ),
            schemas.AppointmentImportItem(
                patient_name="B",
                praticien_id=dentiste.id,
                datetime_start=datetime(2026, 9, 17, 14, 15),
                duration_minutes=30,
            ),
        ]
    )

    with pytest.raises(HTTPException) as exc:
        create_bulk_appointments(payload, db, dentiste)
    assert exc.value.status_code == 409
    assert db.query(models.Appointment).count() == 0


def test_bulk_allows_same_slot_for_different_practitioners(db, dentiste):
    team = _team_user(db, dentiste)
    slot = datetime(2026, 9, 17, 16, 0)
    payload = schemas.AppointmentBulkCreate(
        appointments=[
            schemas.AppointmentImportItem(
                patient_name="A",
                praticien_id=dentiste.id,
                datetime_start=slot,
                duration_minutes=30,
            ),
            schemas.AppointmentImportItem(
                patient_name="B",
                praticien_id=team.id,
                datetime_start=slot,
                duration_minutes=30,
            ),
        ]
    )

    created = create_bulk_appointments(payload, db, dentiste)
    assert {appt.praticien_id for appt in created} == {dentiste.id, team.id}


def test_multi_practitioner_groups_real_assignments_and_legacy(db, dentiste):
    dentiste.subscription_plan = models.SubscriptionPlan.PREMIUM.value
    team = _team_user(db, dentiste)
    db.commit()

    create_appointment(_appt(datetime(2026, 9, 18, 9, 0), dentiste.id, "Owner"), db, dentiste)
    create_appointment(_appt(datetime(2026, 9, 18, 9, 0), team.id, "Team"), db, dentiste)
    db.add(models.Appointment(
        patient_name="Legacy",
        datetime_start=datetime(2026, 9, 18, 12, 0),
        duration_minutes=30,
        employer_id=dentiste.id,
        praticien_id=None,
    ))
    db.commit()

    result = get_multi_practitioner_appointments(db=db, current_user=dentiste)
    grouped = {entry["dentist_id"]: entry["appointments"] for entry in result["dentists"]}

    assert len(grouped[dentiste.id]) == 1
    assert len(grouped[team.id]) == 1
    assert len(result["legacy_unassigned"]) == 1
    assert result["total_appointments"] == 3
