"""Tests FRONTDESK-AGENDA-MVP-1 — Frontdesk appointment requests."""
from datetime import datetime, timedelta
from backend import models, schemas
from backend.tests.conftest import make_user

BASE = "/api"


class TestFrontdeskCreateRequest:
    """Tests creating frontdesk appointment requests."""

    def test_create_pending_request(self, client, auth_headers, dentiste, db):
        """Create a frontdesk appointment request → status=EN_ATTENTE_DEMANDE."""
        response = client.post(
            f"{BASE}/frontdesk/appointment-request",
            json={
                "first_name": "Jean",
                "last_name": "Dupont",
                "phone": "06123456789",
                "appointment_reason": "Détartrage",
                "requested_start": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                "duration_minutes": 30,
                "source": "frontdesk",
                "notes": "Test demande",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "EN_ATTENTE_DEMANDE"
        assert data["patient_name"] == "Dupont Jean"
        assert data["phone"] == "06123456789"

        appt = db.query(models.Appointment).filter(
            models.Appointment.id == data["id"]
        ).first()
        assert appt is not None
        assert appt.status == schemas.AppointmentStatus.EN_ATTENTE_DEMANDE
        assert appt.source == "frontdesk"

    def test_request_requires_auth(self, client):
        """Create without auth → 401."""
        response = client.post(
            f"{BASE}/frontdesk/appointment-request",
            json={
                "first_name": "Test",
                "last_name": "User",
                "appointment_reason": "Test",
                "requested_start": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            },
        )
        assert response.status_code == 401

    def test_create_request_no_clinical_fields_required(self, client, auth_headers):
        """Minimal payload (no clinical fields) still succeeds."""
        response = client.post(
            f"{BASE}/frontdesk/appointment-request",
            json={
                "first_name": "Jean",
                "last_name": "Dupont",
                "requested_start": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            },
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text


class TestListPendingAppointments:
    """Tests listing pending appointments."""

    def test_list_pending_returns_only_pending(self, client, auth_headers, dentiste, db):
        """List pending appointments → returns only EN_ATTENTE_* statuses."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            motif="Test",
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=dentiste.get_employer_id(),
            source="frontdesk",
        )
        db.add(appt)
        db.commit()

        response = client.get(f"{BASE}/appointments/pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(a["status"] == "EN_ATTENTE_DEMANDE" for a in data)

    def test_list_pending_visible_only_own_cabinet(self, client, auth_headers, dentiste, db):
        """Pending appointments from another cabinet are not visible."""
        other_user = make_user(db)
        appt = models.Appointment(
            patient_name="Other Cabinet Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=other_user.get_employer_id(),
        )
        db.add(appt)
        db.commit()

        response = client.get(f"{BASE}/appointments/pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert not any(a["id"] == appt.id for a in data)


class TestRequestConfirmation:
    """Tests requesting patient confirmation."""

    def test_request_confirmation_transitions_status(self, client, auth_headers, dentiste, db):
        """Request confirmation → EN_ATTENTE_DEMANDE → EN_ATTENTE_CONFIRM."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=dentiste.get_employer_id(),
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        response = client.post(
            f"{BASE}/appointments/{appt.id}/request-confirmation",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "EN_ATTENTE_CONFIRM"
        assert "message_template" in data

        db.refresh(appt)
        assert appt.status == schemas.AppointmentStatus.EN_ATTENTE_CONFIRM


class TestConfirmAppointment:
    """Tests confirming appointments."""

    def test_confirm_sets_confirmed_by_and_at(self, client, auth_headers, dentiste, db):
        """Confirm appointment → CONFIRME, sets confirmed_by_id and confirmed_at."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=dentiste.get_employer_id(),
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        response = client.post(
            f"{BASE}/appointments/{appt.id}/confirm",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "CONFIRMÉ"
        assert data["confirmed_by_id"] == dentiste.id
        assert data["confirmed_at"] is not None

    def test_confirm_wrong_cabinet_404(self, client, auth_headers, db):
        """Confirm from other cabinet → 404."""
        other_user = make_user(db)
        appt = models.Appointment(
            patient_name="Other Cabinet Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=other_user.get_employer_id(),
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        response = client.post(
            f"{BASE}/appointments/{appt.id}/confirm",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_confirm_expired_410(self, client, auth_headers, dentiste, db):
        """Confirm expired appointment → 410."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=dentiste.get_employer_id(),
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        response = client.post(
            f"{BASE}/appointments/{appt.id}/confirm",
            headers=auth_headers,
        )
        assert response.status_code == 410

    def test_confirm_already_confirmed_409(self, client, auth_headers, dentiste, db):
        """Confirm already confirmed appointment → 409."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.CONFIRME,
            employer_id=dentiste.get_employer_id(),
            confirmed_at=datetime.utcnow(),
            confirmed_by_id=dentiste.id,
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        response = client.post(
            f"{BASE}/appointments/{appt.id}/confirm",
            headers=auth_headers,
        )
        assert response.status_code == 409


class TestRejectAppointment:
    """Tests rejecting appointments."""

    def test_reject_transitions_to_refuse(self, client, auth_headers, dentiste, db):
        """Reject appointment → status=REFUSE."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=dentiste.get_employer_id(),
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        response = client.post(
            f"{BASE}/appointments/{appt.id}/reject",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "REFUSÉ"


class TestExpireAppointment:
    """Tests manually expiring appointments."""

    def test_expire_transitions_to_expire(self, client, auth_headers, dentiste, db):
        """Manually expire appointment → status=EXPIRE."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=dentiste.get_employer_id(),
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        response = client.post(
            f"{BASE}/appointments/{appt.id}/expire",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "EXPIRÉ"


class TestAuditLogs:
    """Tests audit logging for frontdesk actions."""

    def test_create_request_creates_audit_log(self, client, auth_headers, db):
        """Creating a request creates an audit log."""
        response = client.post(
            f"{BASE}/frontdesk/appointment-request",
            json={
                "first_name": "Jean",
                "last_name": "Dupont",
                "appointment_reason": "Test",
                "requested_start": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        logs = db.query(models.AuditLog).filter(
            models.AuditLog.action == "FRONTDESK_REQUEST_CREATED"
        ).all()
        assert len(logs) > 0
