from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from backend import models
from backend.routers.appointments import _find_conflicts


BASE = "/api/appointments"


def _stored_appointment(db, dentiste, start: datetime, duration: int = 30):
    appointment = models.Appointment(
        employer_id=dentiste.id,
        patient_name="M63 Existing",
        datetime_start=start,
        duration_minutes=duration,
        status=models.AppointmentStatus.PREVU,
        scheduling_type=models.SchedulingType.EXACT_TIME,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def test_find_conflicts_accepts_aware_input_against_naive_db(db, dentiste):
    start = datetime(2026, 9, 7, 10, 0)
    existing = _stored_appointment(db, dentiste, start)

    conflicts = _find_conflicts(
        db,
        dentiste.id,
        start.replace(tzinfo=timezone.utc) + timedelta(minutes=15),
        30,
    )

    assert [appointment.id for appointment in conflicts] == [existing.id]


def test_canonical_create_rejects_overlap(client, db, auth_headers, dentiste):
    start = datetime(2026, 9, 7, 10, 0)
    existing = _stored_appointment(db, dentiste, start)
    payload = {
        "patient_name": "M63 New",
        "datetime_start": (start + timedelta(minutes=15)).isoformat(),
        "duration_minutes": 30,
        "motif": "Contrôle",
        "scheduling_type": "EXACT_TIME",
    }

    with patch("backend.routers.appointments.validate_appointment_availability", return_value=None):
        response = client.post(f"{BASE}/", json=payload, headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["detail"]["conflicts"][0]["id"] == existing.id


def test_canonical_update_excludes_itself_but_rejects_other_overlap(client, db, auth_headers, dentiste):
    first_start = datetime(2026, 9, 7, 10, 0)
    first = _stored_appointment(db, dentiste, first_start)

    with patch("backend.routers.appointments.validate_appointment_availability", return_value=None):
        unchanged = client.put(
            f"{BASE}/{first.id}",
            json={"datetime_start": first_start.isoformat()},
            headers=auth_headers,
        )
    assert unchanged.status_code == 200

    second = _stored_appointment(db, dentiste, first_start + timedelta(hours=1))
    with patch("backend.routers.appointments.validate_appointment_availability", return_value=None):
        overlap = client.put(
            f"{BASE}/{first.id}",
            json={"datetime_start": (second.datetime_start + timedelta(minutes=10)).isoformat()},
            headers=auth_headers,
        )

    assert overlap.status_code == 409
    conflict_ids = {item["id"] for item in overlap.json()["detail"]["conflicts"]}
    assert second.id in conflict_ids
    assert first.id not in conflict_ids
