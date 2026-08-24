"""Tests routers/mobile.py — ping, auth guard, canonical handoff, and mobile JWT operations."""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from jose import jwt

from backend import models
from backend.routers.mobile import _create_mobile_jwt
from backend.security import SECRET_KEY, ALGORITHM, get_password_hash


def _make_mobile_jwt(db, user) -> str:
    """Create a valid device-bound mobile JWT using the production helper."""
    device_id = str(uuid.uuid4())
    db.add(models.MobilePairedDevice(
        device_id=device_id,
        user_id=user.id,
        employer_id=user.get_employer_id(),
        client_public_key_hex='04' + ('11' * 64),
        refresh_jti=f'test-refresh-{uuid.uuid4().hex}',
    ))
    db.commit()
    role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    return _create_mobile_jwt(user.id, role, user.get_employer_id(), device_id)


def _make_secretary(db, dentiste):
    user = models.User(
        email=f"mobile-router-{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=get_password_hash("Pass123!"),
        role=models.UserRole.SECRETAIRE,
        is_active=True,
        is_licensed=False,
        employer_id=dentiste.id,
        permissions={"agenda": True, "patients": True},
        approval_status="approved",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── public endpoints (no auth) ─────────────────────────────────────────────────

class TestMobilePing:
    def test_ping_returns_ok(self, client):
        r = client.get("/api/mobile/ping")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["mode"] == "lan"


# ── auth guard (mobile JWT required) ──────────────────────────────────────────

class TestMobileAuthGuard:
    def test_snapshot_requires_auth(self, client):
        r = client.get("/api/mobile/snapshot")
        assert r.status_code == 422  # Missing Header

    def test_snapshot_invalid_token_returns_401(self, client):
        r = client.get("/api/mobile/snapshot", headers={"Authorization": "Bearer invalidtoken"})
        assert r.status_code == 401

    def test_snapshot_wrong_token_type_returns_401(self, client, dentiste):
        payload = {
            "sub": str(dentiste.id),
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        r = client.get("/api/mobile/snapshot", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_appointments_requires_mobile_auth(self, client):
        r = client.get("/api/mobile/appointments")
        assert r.status_code == 422

    def test_patients_requires_mobile_auth(self, client):
        r = client.get("/api/mobile/patients")
        assert r.status_code == 422

    def test_register_device_requires_mobile_auth(self, client):
        r = client.post("/api/mobile/register-device", json={"device_name": "iPhone"})
        assert r.status_code == 422


# ── claim-token endpoint ───────────────────────────────────────────────────────

class TestClaimToken:
    def test_invalid_token_returns_4xx(self, client):
        r = client.post(
            "/api/mobile/claim-token",
            json={"token": "nonexistent-uuid", "client_public_key_hex": None},
        )
        assert r.status_code in (404, 400, 422)

    def test_missing_token_returns_422(self, client):
        r = client.post("/api/mobile/claim-token", json={})
        assert r.status_code == 422


# ── mobile snapshot with valid JWT ────────────────────────────────────────────

class TestMobileSnapshot:
    def test_snapshot_with_valid_mobile_jwt(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        r = client.get(
            "/api/mobile/snapshot",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "appointments" in body or "agenda" in body or isinstance(body, dict)

    def test_snapshot_secretaire_role(self, client, db, dentiste):
        secretary = _make_secretary(db, dentiste)
        token = _make_mobile_jwt(db, secretary)
        r = client.get(
            "/api/mobile/snapshot",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    def test_snapshot_with_date_param(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        r = client.get(
            "/api/mobile/snapshot?target_date=2026-06-01",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200


# ── appointments ───────────────────────────────────────────────────────────────

class TestMobileAppointments:
    def test_list_appointments(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        r = client.get(
            "/api/mobile/appointments?start_date=2026-06-01&end_date=2026-06-30",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_legacy_create_appointment_fails_closed(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        before = db.query(models.Appointment).count()
        r = client.post(
            "/api/mobile/appointments",
            json={
                "patient_name": "Legacy Mobile",
                "datetime_start": "2026-09-07T10:00:00",
                "duration_minutes": 30,
                "motif": "Contrôle",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 410
        assert db.query(models.Appointment).count() == before

    def test_canonical_create_appointment_accepts_mobile_token(self, client, db, dentiste):
        pat = models.Patient(
            nom="MOBILEPAT", prenom="Test",
            date_naissance=datetime(1985, 5, 5),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        token = _make_mobile_jwt(db, dentiste)
        with patch("backend.routers.appointments.validate_appointment_availability", return_value=None):
            r = client.post(
                "/api/appointments/",
                json={
                    "patient_id": pat.id,
                    "patient_name": "Test MOBILEPAT",
                    "datetime_start": "2026-09-07T10:00:00",
                    "duration_minutes": 30,
                    "motif": "Contrôle",
                    "scheduling_type": "EXACT_TIME",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200
        assert r.json()["patient_id"] == pat.id

    def test_legacy_quick_appointment_without_patient_id_fails_closed(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        before = db.query(models.Appointment).count()
        r = client.post(
            "/api/mobile/appointments",
            json={
                "patient_name": "Patient rapide",
                "phone": "0600000000",
                "datetime_start": "2026-09-07T11:00:00",
                "duration_minutes": 20,
                "motif": "Urgence",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 410
        assert db.query(models.Appointment).count() == before

    def test_delete_nonexistent_appointment_is_idempotent(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        r = client.delete(
            "/api/mobile/appointments/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json() == {"status": "deleted", "already_absent": True}


# ── patients ───────────────────────────────────────────────────────────────────

class TestMobilePatients:
    def test_list_patients(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        r = client.get(
            "/api/mobile/patients",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), (dict, list))

    def test_legacy_create_patient_fails_closed(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        before = db.query(models.Patient).count()
        r = client.post(
            "/api/mobile/patients",
            json={"nom": "LEGACY", "prenom": "Patient", "telephone": "0600000000", "sexe": "M"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 410
        assert db.query(models.Patient).count() == before

    def test_canonical_create_patient_accepts_mobile_token(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        r = client.post(
            "/api/patients/",
            json={
                "nom": "CANONICAL",
                "prenom": "Mobile",
                "date_naissance": "1992-03-04",
                "sexe": "F",
                "telephone": "0600000001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["sexe"] == "F"
        assert r.json()["nom"] == "CANONICAL"
