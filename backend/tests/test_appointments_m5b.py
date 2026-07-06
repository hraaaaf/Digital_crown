"""Tests M5-B — Agenda intelligent : conflits, rappels, multi-praticien."""
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_user(db, role="DENTISTE", plan="GOLD"):
    from backend import models
    from backend.security import get_password_hash
    email = f"test-{uuid.uuid4().hex[:8]}@cabinet.dz"
    u = models.User(
        email=email,
        hashed_password=get_password_hash("Pass123!"),
        role=role,
        is_active=True,
        is_licensed=True,
        subscription_plan=plan,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _login(client, email, password="Pass123!"):
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _create_appt(client, headers, dt_start: datetime, duration: int = 60):
    payload = {
        "datetime_start": dt_start.isoformat(),
        "duration_minutes": duration,
        "motif": "Test",
        "status": "PRÉVU",
        "patient_name": "Test Patient",
    }
    r = client.post("/api/appointments/", json=payload, headers=headers)
    assert r.status_code in (200, 201), r.text
    return r.json()


# ── conflict detection ────���───────────────────────────────────────────────────

class TestConflictDetection:
    def test_no_conflict_empty_agenda(self, client, auth_headers):
        dt = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        r = client.get(
            "/api/appointments/check-conflicts",
            params={"datetime_start": dt.isoformat(), "duration_minutes": 30},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["has_conflict"] is False

    def test_conflict_overlapping_appointment(self, client, auth_headers):
        dt = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=2)
        _create_appt(client, auth_headers, dt, duration=60)

        # Try to book 15 min inside the existing slot
        r = client.get(
            "/api/appointments/check-conflicts",
            params={"datetime_start": (dt + timedelta(minutes=20)).isoformat(), "duration_minutes": 30},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["has_conflict"] is True
        assert len(r.json()["conflicts"]) >= 1

    def test_no_conflict_exclude_self(self, client, auth_headers):
        dt = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=3)
        appt = _create_appt(client, auth_headers, dt, duration=60)
        # Exclude self → should not flag
        r = client.get(
            "/api/appointments/check-conflicts",
            params={
                "datetime_start": dt.isoformat(),
                "duration_minutes": 60,
                "exclude_id": appt["id"],
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["has_conflict"] is False

    def test_unauthenticated_returns_401(self, client):
        dt = datetime.now().isoformat()
        r = client.get("/api/appointments/check-conflicts", params={"datetime_start": dt, "duration_minutes": 30})
        assert r.status_code == 401


# ── individual reminder ───���───────────────────────────────────────────────────

class TestIndividualReminder:
    def test_remind_sets_flag(self, client, db, auth_headers, dentiste):
        from backend import models

        # Create patient with phone
        pat = models.Patient(
            nom="TESTREMIND", prenom="Bob",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            telephone="0612345678",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        dt = datetime.now() + timedelta(days=5)
        appt = models.Appointment(
            patient_id=pat.id,
            patient_name=f"{pat.nom} {pat.prenom}",
            datetime_start=dt,
            duration_minutes=30,
            status=models.AppointmentStatus.PREVU,
            employer_id=dentiste.id,
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        with patch("backend.services.notification_service.notification_service.send_appointment_reminder", return_value=True):
            r = client.post(f"/api/appointments/{appt.id}/remind", headers=auth_headers)

        assert r.status_code == 200
        assert r.json()["status"] == "success"
        assert r.json()["appointment_id"] == appt.id

    def test_remind_404_not_found(self, client, auth_headers):
        with patch("backend.services.notification_service.notification_service.send_appointment_reminder", return_value=True):
            r = client.post("/api/appointments/999999/remind", headers=auth_headers)
        assert r.status_code == 404

    def test_remind_unauthenticated(self, client):
        r = client.post("/api/appointments/1/remind")
        assert r.status_code == 401


# ── multi-practitioner view ────────��──────────────────────────────────────────

class TestMultiPractitioner:
    def test_gold_plan_returns_403(self, client, db):
        """GOLD plan should be blocked from multi-practitioner view."""
        doc = _make_user(db, plan="GOLD")
        headers = _login(client, doc.email)
        dt_start = datetime.now().isoformat()
        dt_end = (datetime.now() + timedelta(days=7)).isoformat()
        r = client.get(
            "/api/appointments/multi-practitioner",
            params={"start_date": dt_start, "end_date": dt_end},
            headers=headers,
        )
        assert r.status_code == 403

    def test_premium_plan_returns_data(self, client, db):
        """PREMIUM plan should return dentist list."""
        doc = _make_user(db, plan="PREMIUM")
        headers = _login(client, doc.email)
        dt_start = datetime.now().isoformat()
        dt_end = (datetime.now() + timedelta(days=7)).isoformat()
        r = client.get(
            "/api/appointments/multi-practitioner",
            params={"start_date": dt_start, "end_date": dt_end},
            headers=headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert "dentists" in body
        assert "total_appointments" in body

    def test_elite_plan_returns_data(self, client, db):
        """ELITE plan should also return dentist list."""
        doc = _make_user(db, plan="ELITE")
        headers = _login(client, doc.email)
        dt_start = datetime.now().isoformat()
        dt_end = (datetime.now() + timedelta(days=7)).isoformat()
        r = client.get(
            "/api/appointments/multi-practitioner",
            params={"start_date": dt_start, "end_date": dt_end},
            headers=headers,
        )
        assert r.status_code == 200

    def test_unauthenticated_returns_401(self, client):
        r = client.get("/api/appointments/multi-practitioner")
        assert r.status_code == 401


# ── appointment CRUD basics ─��─────────────────────────────────────────────────

class TestAppointmentCRUD:
    def test_create_appointment(self, client, auth_headers):
        dt = datetime.now() + timedelta(days=10)
        appt = _create_appt(client, auth_headers, dt)
        assert "id" in appt
        assert appt["duration_minutes"] == 60

    def test_list_appointments(self, client, auth_headers):
        dt = datetime.now() + timedelta(days=11)
        _create_appt(client, auth_headers, dt)
        dt_start = (datetime.now() + timedelta(days=10)).isoformat()
        dt_end = (datetime.now() + timedelta(days=12)).isoformat()
        r = client.get(
            "/api/appointments/",
            params={"start_date": dt_start, "end_date": dt_end},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_update_appointment_status(self, client, auth_headers):
        dt = datetime.now() + timedelta(days=15)
        appt = _create_appt(client, auth_headers, dt)
        # Appointments use PUT (not PATCH)
        r = client.put(
            f"/api/appointments/{appt['id']}",
            json={
                "datetime_start": (dt + timedelta(days=15)).isoformat(),
                "duration_minutes": 60,
                "status": "EN_FAUTEUIL",
                "patient_name": "Test Patient",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "EN_FAUTEUIL"

    def test_delete_appointment(self, client, auth_headers):
        dt = datetime.now() + timedelta(days=20)
        appt = _create_appt(client, auth_headers, dt)
        r = client.delete(f"/api/appointments/{appt['id']}", headers=auth_headers)
        assert r.status_code in (200, 204)
