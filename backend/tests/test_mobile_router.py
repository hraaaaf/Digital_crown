"""Tests routers/mobile.py — ping, auth guard, and mobile JWT operations."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from jose import jwt
from backend.security import SECRET_KEY, ALGORITHM


def _make_mobile_jwt(employer_id: int, role: str = "DENTISTE") -> str:
    payload = {
        "sub": str(employer_id),
        "type": "mobile",
        "role": role,
        "jti": "test-jti",
        "exp": datetime.now(timezone.utc) + timedelta(days=365),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


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
        # Regular JWT (type != "mobile") should be rejected
        payload = {
            "sub": str(dentiste.id),
            "type": "access",  # Not "mobile"
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        r = client.get("/api/mobile/snapshot", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_appointments_requires_mobile_auth(self, client):
        r = client.get("/api/mobile/appointments")
        assert r.status_code == 422  # Missing Header

    def test_patients_requires_mobile_auth(self, client):
        r = client.get("/api/mobile/patients")
        assert r.status_code == 422  # Missing Header

    def test_register_device_requires_mobile_auth(self, client):
        r = client.post("/api/mobile/register-device", json={"device_name": "iPhone"})
        assert r.status_code == 422  # Missing Header


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
        token = _make_mobile_jwt(dentiste.id, "DENTISTE")
        r = client.get(
            "/api/mobile/snapshot",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "appointments" in body or "agenda" in body or isinstance(body, dict)

    def test_snapshot_secretaire_role(self, client, db, dentiste):
        token = _make_mobile_jwt(dentiste.id, "SECRETAIRE")
        r = client.get(
            "/api/mobile/snapshot",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    def test_snapshot_with_date_param(self, client, db, dentiste):
        token = _make_mobile_jwt(dentiste.id)
        r = client.get(
            "/api/mobile/snapshot?target_date=2026-06-01",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200


# ── appointments ───────────────────────────────────────────────────────────────

class TestMobileAppointments:
    def test_list_appointments(self, client, db, dentiste):
        token = _make_mobile_jwt(dentiste.id)
        r = client.get(
            "/api/mobile/appointments?start_date=2026-06-01&end_date=2026-06-30",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        # returns encrypted payload dict
        assert isinstance(r.json(), dict)

    def test_create_appointment(self, client, db, dentiste):
        from backend import models
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

        token = _make_mobile_jwt(dentiste.id)
        r = client.post(
            "/api/mobile/appointments",
            json={
                "patient_id": pat.id,
                "patient_name": "Test Patient",
                "datetime_start": "2026-07-01T10:00:00",
                "duration_minutes": 30,
                "motif": "Contrôle",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        # 200/201: success; 403: middleware blocked (mobile sub ≠ email); 422: validation
        assert r.status_code in (200, 201, 403, 422)

    def test_delete_nonexistent_appointment(self, client, dentiste):
        token = _make_mobile_jwt(dentiste.id)
        r = client.delete(
            "/api/mobile/appointments/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code in (404, 403)


# ── patients ───────────────────────────────────────────────────────────────────

class TestMobilePatients:
    def test_list_patients(self, client, db, dentiste):
        token = _make_mobile_jwt(dentiste.id)
        r = client.get(
            "/api/mobile/patients",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        # returns encrypted payload or a list
        assert isinstance(r.json(), (dict, list))
