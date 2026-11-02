"""Tests routers/mobile.py — ping, auth guard, canonical handoff, and mobile JWT operations."""
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from jose import jwt

from backend import models
from backend.routers.mobile import _create_mobile_jwt
from backend.security import SECRET_KEY, ALGORITHM, get_password_hash
from backend.utils import rate_limit


@pytest.fixture(autouse=True)
def _reset_pairing_rate_limit():
    path = Path(rate_limit._store_path())
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False
        path.unlink(missing_ok=True)
    yield
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False
        path.unlink(missing_ok=True)


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

    def test_removed_register_device_is_not_mounted(self, client):
        r = client.post("/api/mobile/register-device", json={"device_name": "iPhone"})
        assert r.status_code == 404


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

    def test_mobile_create_appointment_rejects_incomplete_contract(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        before = db.query(models.Appointment).count()
        r = client.post(
            "/api/mobile/appointments",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422
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
                "/api/mobile/appointments",
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
        assert r.status_code == 200, r.text
        created = db.query(models.Appointment).filter(
            models.Appointment.patient_id == pat.id,
            models.Appointment.employer_id == dentiste.id,
        ).order_by(models.Appointment.id.desc()).first()
        assert created is not None
        assert created.patient_id == pat.id

    def test_mobile_external_appointment_without_patient_id_is_supported(self, client, db, dentiste):
        from backend.routers.agenda_settings import _create_default_settings
        _create_default_settings(db, dentiste.id)
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
        assert r.status_code == 200, r.text
        assert db.query(models.Appointment).count() == before + 1

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

    def test_mobile_create_patient_requires_canonical_fields(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        before = db.query(models.Patient).count()
        r = client.post(
            "/api/mobile/patients",
            json={"nom": "INCOMPLET", "prenom": "Patient", "telephone": "0600000000", "sexe": "M"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422
        assert db.query(models.Patient).count() == before

    def test_canonical_create_patient_accepts_mobile_token(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        r = client.post(
            "/api/mobile/patients",
            json={
                "nom": "CANONICAL",
                "prenom": "Mobile",
                "date_naissance": "1992-03-04",
                "sexe": "F",
                "telephone": "0600000001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200, r.text
        created = db.query(models.Patient).filter(
            models.Patient.nom == "CANONICAL",
            models.Patient.employer_id == dentiste.id,
        ).order_by(models.Patient.id.desc()).first()
        assert created is not None
        assert created.sexe == "F"
        assert created.nom == "CANONICAL"
# CPV2-02B — paired Pocket creation contracts (isolated, real FastAPI routes).
# Keep all business validations in the canonical desktop services; Pocket JWT
# must remain scoped to /api/mobile/* and must never become a desktop session.
class TestCPV202BMobileCreationContracts:
    @staticmethod
    def _patient_payload(nom="POCKETCONTRACT"):
        return {
            "nom": nom,
            "prenom": "Essai",
            "date_naissance": "1991-05-12",
            "sexe": "F",
            "telephone": "0600000042",
        }

    @staticmethod
    def _appointment_payload(patient_id):
        return {
            "patient_id": patient_id,
            "patient_name": "Essai POCKETCONTRACT",
            "datetime_start": "2026-09-07T10:00:00",
            "duration_minutes": 30,
            "motif": "Contrôle clinique",
            "scheduling_type": "EXACT_TIME",
        }

    def test_patient_creation_refused_without_patient_permission(self, client, db, dentiste):
        secretary = _make_secretary(db, dentiste)
        secretary.permissions = {"agenda": True, "patients": False}
        db.commit()
        token = _make_mobile_jwt(db, secretary)
        before = db.query(models.Patient).count()

        response = client.post(
            "/api/mobile/patients",
            headers={"Authorization": f"Bearer {token}"},
            json=self._patient_payload("PERMISSIONDENIED"),
        )

        assert response.status_code == 403, response.text
        assert db.query(models.Patient).count() == before

    def test_appointment_creation_refused_without_agenda_permission(self, client, db, dentiste):
        secretary = _make_secretary(db, dentiste)
        secretary.permissions = {"patients": True, "agenda": False}
        db.commit()
        token = _make_mobile_jwt(db, secretary)
        before = db.query(models.Appointment).count()

        response = client.post(
            "/api/mobile/appointments",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "patient_name": "External control",
                "datetime_start": "2026-09-07T10:00:00",
                "duration_minutes": 30,
                "motif": "Contrôle",
            },
        )

        assert response.status_code == 403, response.text
        assert db.query(models.Appointment).count() == before

    def test_patient_duplicate_is_409_with_no_second_dossier(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        headers = {"Authorization": f"Bearer {token}"}
        payload = self._patient_payload("DUPLICATEPOCKET")
        first = client.post("/api/mobile/patients", headers=headers, json=payload)
        assert first.status_code == 200, first.text
        count = db.query(models.Patient).count()

        second = client.post("/api/mobile/patients", headers=headers, json=payload)

        assert second.status_code == 409, second.text
        assert second.json()["detail"]["existing_patient"]["id"] == first.json()["id"]
        assert db.query(models.Patient).count() == count

    def test_soft_deleted_patient_absent_from_pocket_appointment_picker(
        self, client, db, dentiste, monkeypatch,
    ):
        # Read the actual Pocket GET facade, not a synthetic frontend mock.
        from backend.routers import mobile_legacy

        monkeypatch.setattr(mobile_legacy, "encrypt_payload", lambda value: value)
        active = models.Patient(
            nom="ACTIVEPOCKET", prenom="Visible",
            date_naissance=datetime(1990, 1, 1), sexe="F",
            employer_id=dentiste.id,
        )
        deleted = models.Patient(
            nom="DELETEDPOCKET", prenom="Hidden",
            date_naissance=datetime(1990, 1, 2), sexe="M",
            employer_id=dentiste.id, deleted_at=datetime.utcnow(),
        )
        db.add_all([active, deleted])
        db.commit()
        token = _make_mobile_jwt(db, dentiste)

        response = client.get(
            "/api/mobile/patients",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        names = [row["name"] for row in response.json()["data"]]
        assert "Visible ACTIVEPOCKET" in names
        assert "Hidden DELETEDPOCKET" not in names

    def test_foreign_cabinet_patient_cannot_be_booked(self, client, db, dentiste):
        other_owner = models.User(
            email=f"cpv2-02b-other-{uuid.uuid4().hex[:8]}@test.local",
            hashed_password=get_password_hash("Pass123!"),
            role=models.UserRole.DENTISTE,
            is_active=True,
            is_licensed=True,
            approval_status="approved",
        )
        db.add(other_owner)
        db.flush()
        foreign_patient = models.Patient(
            nom="FOREIGNPOCKET", prenom="Wrong",
            date_naissance=datetime(1990, 1, 1), sexe="M",
            employer_id=other_owner.id,
        )
        db.add(foreign_patient)
        db.commit()
        token = _make_mobile_jwt(db, dentiste)
        before = db.query(models.Appointment).count()

        response = client.post(
            "/api/mobile/appointments",
            headers={"Authorization": f"Bearer {token}"},
            json=self._appointment_payload(foreign_patient.id),
        )

        assert response.status_code in (403, 404), response.text
        assert db.query(models.Appointment).count() == before

    def test_overlap_returns_409_without_double_booking(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        headers = {"Authorization": f"Bearer {token}"}
        patient = client.post(
            "/api/mobile/patients", headers=headers,
            json=self._patient_payload("OVERLAPPOCKET"),
        )
        assert patient.status_code == 200, patient.text
        payload = self._appointment_payload(patient.json()["id"])

        # Keep the real tenant, practitioner and conflict validator. Only
        # disable opening-hour configuration for this synthetic isolated fixture.
        with patch("backend.routers.appointments.validate_appointment_availability", return_value=None):
            first = client.post("/api/mobile/appointments", headers=headers, json=payload)
            assert first.status_code == 200, first.text
            before = db.query(models.Appointment).count()
            overlap = client.post(
                "/api/mobile/appointments", headers=headers,
                json={**payload, "datetime_start": "2026-09-07T10:15:00"},
            )

        assert overlap.status_code == 409, overlap.text
        assert db.query(models.Appointment).count() == before

    def test_revoked_pocket_device_cannot_create_patient(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        device = db.query(models.MobilePairedDevice).filter(
            models.MobilePairedDevice.user_id == dentiste.id,
            models.MobilePairedDevice.employer_id == dentiste.id,
        ).first()
        assert device is not None
        device.revoked_at = datetime.utcnow()
        db.commit()
        before = db.query(models.Patient).count()

        response = client.post(
            "/api/mobile/patients",
            headers={"Authorization": f"Bearer {token}"},
            json=self._patient_payload("REVOKEDPOCKET"),
        )

        assert response.status_code == 401, response.text
        assert db.query(models.Patient).count() == before

# CPV2-02C — JWT Pocket document PREVIEW only. Never authorize archive
# or a raw Desktop /api/documents/generate call via a paired-device token.
class TestCPV202CMobileDocumentPreview:
    @staticmethod
    def _patient(db, dentiste, *, employer_id=None, deleted_at=None):
        patient = models.Patient(
            nom="PDFPOCKET", prenom="Essai",
            date_naissance=datetime(1990, 1, 1), sexe="F",
            employer_id=employer_id if employer_id is not None else dentiste.id,
            deleted_at=deleted_at,
        )
        db.add(patient)
        db.commit()
        return patient

    @staticmethod
    def _payload(patient_id, document_type="certificat"):
        return {
            "patient_id": patient_id,
            "type": document_type,
            "data": {"reason": "Certificat de Présence", "doc_date": "2026-11-01"},
        }

    def test_paired_preview_is_pdf_no_store_without_archive_or_static_url(
        self, client, db, dentiste, tmp_path, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        patient = self._patient(db, dentiste)
        pdf = tmp_path / "documents" / "isolated" / "preview.pdf"
        pdf.parent.mkdir(parents=True)
        pdf.write_bytes(b"%PDF-1.4\nsynthetic-isolated-preview")
        monkeypatch.setattr(documents, "MEDIA_DIR", tmp_path)
        mocked = AsyncMock(return_value={
            "pdf_url": "static/documents/isolated/preview.pdf?preview_token=never_exposed",
        })
        monkeypatch.setattr(documents, "generate_document", mocked)
        token = _make_mobile_jwt(db, dentiste)

        response = client.post(
            "/api/mobile/documents/preview?archive=true",
            headers={"Authorization": f"Bearer {token}"},
            json=self._payload(patient.id),
        )

        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["cache-control"] == "no-store, private"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.content == pdf.read_bytes()
        assert b"static/documents/" not in response.content
        assert mocked.await_count == 1
        assert mocked.await_args.kwargs["archive"] is False
        assert mocked.await_args.kwargs["preview"] is True
        assert mocked.await_args.kwargs["force"] is False
        assert mocked.await_args.kwargs["current_user"].id == dentiste.id

    def test_preview_rejects_wrong_document_type_before_generator(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        patient = self._patient(db, dentiste)
        mocked = AsyncMock()
        monkeypatch.setattr(documents, "generate_document", mocked)
        token = _make_mobile_jwt(db, dentiste)

        response = client.post(
            "/api/mobile/documents/preview",
            headers={"Authorization": f"Bearer {token}"},
            json=self._payload(patient.id, "lettre"),
        )

        assert response.status_code == 403, response.text
        mocked.assert_not_awaited()

    def test_preview_rejects_payment_mutation_before_generator(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        patient = self._patient(db, dentiste)
        mocked = AsyncMock()
        monkeypatch.setattr(documents, "generate_document", mocked)
        token = _make_mobile_jwt(db, dentiste)
        payload = self._payload(patient.id)
        payload["payment_status"] = "PAYE"

        response = client.post(
            "/api/mobile/documents/preview",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )

        assert response.status_code == 403, response.text
        mocked.assert_not_awaited()

    def test_preview_denied_without_document_permission(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        secretary = _make_secretary(db, dentiste)
        secretary.permissions = {"patients": True, "agenda": True, "prescriptions": False}
        db.commit()
        patient = self._patient(db, dentiste)
        mocked = AsyncMock()
        monkeypatch.setattr(documents, "generate_document", mocked)
        token = _make_mobile_jwt(db, secretary)

        response = client.post(
            "/api/mobile/documents/preview",
            headers={"Authorization": f"Bearer {token}"},
            json=self._payload(patient.id, "ordonnance"),
        )

        assert response.status_code == 403, response.text
        mocked.assert_not_awaited()

    def test_preview_denied_without_patients_permission(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        secretary = _make_secretary(db, dentiste)
        secretary.permissions = {"patients": False, "agenda": True}
        db.commit()
        patient = self._patient(db, dentiste)
        mocked = AsyncMock()
        monkeypatch.setattr(documents, "generate_document", mocked)
        token = _make_mobile_jwt(db, secretary)

        response = client.post(
            "/api/mobile/documents/preview",
            headers={"Authorization": f"Bearer {token}"},
            json=self._payload(patient.id),
        )

        assert response.status_code == 403, response.text
        mocked.assert_not_awaited()

    def test_preview_rejects_deleted_patient_without_generating(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        patient = self._patient(db, dentiste, deleted_at=datetime.utcnow())
        mocked = AsyncMock()
        monkeypatch.setattr(documents, "generate_document", mocked)
        token = _make_mobile_jwt(db, dentiste)

        response = client.post(
            "/api/mobile/documents/preview",
            headers={"Authorization": f"Bearer {token}"},
            json=self._payload(patient.id),
        )

        assert response.status_code == 404, response.text
        mocked.assert_not_awaited()

    def test_preview_rejects_other_cabinet_without_generating(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        other_owner = models.User(
            email=f"doc-other-{uuid.uuid4().hex[:8]}@test.local",
            hashed_password=get_password_hash("Pass123!"),
            role=models.UserRole.DENTISTE,
            is_active=True, is_licensed=True, approval_status="approved",
        )
        db.add(other_owner)
        db.flush()
        patient = self._patient(db, dentiste, employer_id=other_owner.id)
        mocked = AsyncMock()
        monkeypatch.setattr(documents, "generate_document", mocked)
        token = _make_mobile_jwt(db, dentiste)

        response = client.post(
            "/api/mobile/documents/preview",
            headers={"Authorization": f"Bearer {token}"},
            json=self._payload(patient.id),
        )

        assert response.status_code == 404, response.text
        mocked.assert_not_awaited()

    def test_preview_rejects_desktop_jwt_on_mobile_facade(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        mocked = AsyncMock()
        monkeypatch.setattr(documents, "generate_document", mocked)
        mobile_token = _make_mobile_jwt(db, dentiste)
        payload = jwt.decode(mobile_token, SECRET_KEY, algorithms=[ALGORITHM])
        payload["type"] = "access"
        forged_desktop = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        patient = self._patient(db, dentiste)

        response = client.post(
            "/api/mobile/documents/preview",
            headers={"Authorization": f"Bearer {forged_desktop}"},
            json=self._payload(patient.id),
        )

        # Desktop authentication middleware can reject a malformed "access"
        # token with 403; the paired-device boundary can reject it with 401.
        # Both must deny the request before any PDF generation occurs.
        assert response.status_code in (401, 403), response.text
        mocked.assert_not_awaited()

    def test_preview_rejects_revoked_mobile_device(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        device = db.query(models.MobilePairedDevice).filter(
            models.MobilePairedDevice.user_id == dentiste.id,
            models.MobilePairedDevice.revoked_at.is_(None),
        ).first()
        assert device is not None
        device.revoked_at = datetime.utcnow()
        db.commit()
        patient = self._patient(db, dentiste)

        response = client.post(
            "/api/mobile/documents/preview",
            headers={"Authorization": f"Bearer {token}"},
            json=self._payload(patient.id),
        )

        assert response.status_code == 401, response.text

    def test_preview_rejects_path_traversal_from_generator(
        self, client, db, dentiste, tmp_path, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        patient = self._patient(db, dentiste)
        (tmp_path / "other.pdf").write_bytes(b"%PDF-1.4\nshould-not-expose")
        monkeypatch.setattr(documents, "MEDIA_DIR", tmp_path)
        mocked = AsyncMock(return_value={"pdf_url": "static/documents/../../other.pdf"})
        monkeypatch.setattr(documents, "generate_document", mocked)
        token = _make_mobile_jwt(db, dentiste)

        response = client.post(
            "/api/mobile/documents/preview",
            headers={"Authorization": f"Bearer {token}"},
            json=self._payload(patient.id),
        )

        assert response.status_code == 503, response.text

def test_archive_returns_pdf_only_with_matching_active_archive_row(
        self, client, db, dentiste, tmp_path, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        patient = self._patient(db, dentiste)
        path = 'static/archives/isolated/safe.pdf'
        pdf = tmp_path / 'archives' / 'isolated' / 'safe.pdf'
        pdf.parent.mkdir(parents=True)
        pdf.write_bytes(b'%PDF-1.4\nsynthetic-archive')
        monkeypatch.setattr(documents, 'MEDIA_DIR', tmp_path)
        doc = models.DocumentArchive(
            patient_id=patient.id, uploaded_by_id=dentiste.id,
            document_type=models.DocumentType.CERTIFICAT,
            filename='safe.pdf', original_filename='safe.pdf',
            file_path=path, file_hash='abc', file_size=pdf.stat().st_size,
        )
        db.add(doc)
        db.commit()
        mocked = AsyncMock(return_value={'pdf_url': path})
        monkeypatch.setattr(documents, 'generate_document', mocked)
        token = _make_mobile_jwt(db, dentiste)
        response = client.post(
            '/api/mobile/documents/archive',
            headers={'Authorization': f'Bearer {token}'},
            json=self._payload(patient.id),
        )
        assert response.status_code == 200, response.text
        assert response.content == pdf.read_bytes()
        assert response.headers['cache-control'] == 'no-store, private'
        assert response.headers['x-document-id'] == str(doc.id)
        assert mocked.await_args.kwargs['archive'] is True
        assert mocked.await_args.kwargs['preview'] is False
        assert mocked.await_args.kwargs['force'] is False
        assert mocked.await_args.kwargs['current_user'].id == dentiste.id

    def test_archive_refuses_ghost_without_claiming_success(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        patient = self._patient(db, dentiste)
        mocked = AsyncMock(return_value={'pdf_url': 'static/archives/ghost.pdf'})
        monkeypatch.setattr(documents, 'generate_document', mocked)
        token = _make_mobile_jwt(db, dentiste)
        response = client.post(
            '/api/mobile/documents/archive',
            headers={'Authorization': f'Bearer {token}'},
            json=self._payload(patient.id),
        )
        assert response.status_code == 503, response.text

    def test_archive_blocks_billing_and_foreign_patient_before_generator(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        mocked = AsyncMock()
        monkeypatch.setattr(documents, 'generate_document', mocked)
        patient = self._patient(db, dentiste)
        token = _make_mobile_jwt(db, dentiste)
        headers = {'Authorization': f'Bearer {token}'}
        note = client.post(
            '/api/mobile/documents/archive', headers=headers,
            json=self._payload(patient.id, 'note'),
        )
        assert note.status_code == 403, note.text
        payment = client.post(
            '/api/mobile/documents/archive', headers=headers,
            json={**self._payload(patient.id), 'payment_status': 'PAYE'},
        )
        assert payment.status_code == 403, payment.text
        foreign = self._patient(db, dentiste, employer_id=dentiste.id + 999)
        denied = client.post(
            '/api/mobile/documents/archive', headers=headers,
            json=self._payload(foreign.id),
        )
        assert denied.status_code == 404, denied.text
        mocked.assert_not_awaited()

    def test_archive_denies_revoked_paired_device_before_generator(
        self, client, db, dentiste, monkeypatch,
    ):
        from unittest.mock import AsyncMock
        from backend.routers import documents

        mocked = AsyncMock()
        monkeypatch.setattr(documents, 'generate_document', mocked)
        patient = self._patient(db, dentiste)
        token = _make_mobile_jwt(db, dentiste)
        device = db.query(models.MobilePairedDevice).filter(
            models.MobilePairedDevice.user_id == dentiste.id,
            models.MobilePairedDevice.revoked_at.is_(None),
        ).first()
        assert device is not None
        device.revoked_at = datetime.utcnow()
        db.commit()
        denied = client.post(
            '/api/mobile/documents/archive',
            headers={'Authorization': f'Bearer {token}'},
            json=self._payload(patient.id),
        )
        assert denied.status_code == 401, denied.text
        mocked.assert_not_awaited()
