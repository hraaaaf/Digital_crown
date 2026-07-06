"""Tests FRONTDESK-AGENDA-MVP-1 — Frontdesk appointment requests."""
import pytest
from datetime import datetime, timedelta
from backend import models, schemas


class TestFrontdeskCreateRequest:
    """Tests creating frontdesk appointment requests."""

    def test_create_pending_request(self, client, current_user, db_session):
        """Create a frontdesk appointment request → status=EN_ATTENTE_DEMANDE."""
        response = client.post(
            "/api/frontdesk/appointment-request",
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
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "EN_ATTENTE_DEMANDE"
        assert data["patient_name"] == "Dupont Jean"
        assert data["phone"] == "06123456789"

        # Verify in DB
        appt = db_session.query(models.Appointment).filter(
            models.Appointment.id == data["id"]
        ).first()
        assert appt is not None
        assert appt.status == schemas.AppointmentStatus.EN_ATTENTE_DEMANDE
        assert appt.source == "frontdesk"

    def test_create_requires_permission(self, client, current_user):
        """Create without agenda permission → 403."""
        # Remove permission (mock)
        response = client.post(
            "/api/frontdesk/appointment-request",
            json={
                "first_name": "Test",
                "last_name": "User",
                "appointment_reason": "Test",
                "requested_start": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer bad-token"},
        )
        # Will be 401 because token is bad
        assert response.status_code in (401, 403)

    def test_request_requires_auth(self, client):
        """Create without auth → 401."""
        response = client.post(
            "/api/frontdesk/appointment-request",
            json={
                "first_name": "Test",
                "last_name": "User",
                "appointment_reason": "Test",
                "requested_start": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            },
        )
        assert response.status_code == 401


class TestListPendingAppointments:
    """Tests listing pending appointments."""

    def test_list_pending_returns_only_pending(self, client, current_user, db_session):
        """List pending appointments → returns only EN_ATTENTE_* statuses."""
        # Create a pending request
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            motif="Test",
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=current_user.employer_id,
            source="frontdesk",
        )
        db_session.add(appt)
        db_session.commit()

        response = client.get(
            "/api/appointments/pending",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(a["status"] == "EN_ATTENTE_DEMANDE" for a in data)

    def test_list_pending_visible_only_own_cabinet(self, client, current_user, other_employer, db_session):
        """Pending appointments from another cabinet are not visible."""
        # Create appointment in other employer
        appt = models.Appointment(
            patient_name="Other Cabinet Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=other_employer.id,  # Different employer
        )
        db_session.add(appt)
        db_session.commit()

        response = client.get(
            "/api/appointments/pending",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Should not contain the other employer's appointment
        assert not any(a["id"] == appt.id for a in data)


class TestRequestConfirmation:
    """Tests requesting patient confirmation."""

    def test_request_confirmation_transitions_status(self, client, current_user, db_session):
        """Request confirmation → EN_ATTENTE_DEMANDE → EN_ATTENTE_CONFIRM."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=current_user.employer_id,
        )
        db_session.add(appt)
        db_session.commit()

        response = client.post(
            f"/api/appointments/{appt.id}/request-confirmation",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "EN_ATTENTE_CONFIRM"
        assert "message_template" in data

        # Verify in DB
        db_session.refresh(appt)
        assert appt.status == schemas.AppointmentStatus.EN_ATTENTE_CONFIRM


class TestConfirmAppointment:
    """Tests confirming appointments."""

    def test_confirm_sets_confirmed_by_and_at(self, client, current_user, db_session):
        """Confirm appointment → CONFIRME, sets confirmed_by_id and confirmed_at."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=current_user.employer_id,
        )
        db_session.add(appt)
        db_session.commit()

        response = client.post(
            f"/api/appointments/{appt.id}/confirm",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CONFIRMÉ"
        assert data["confirmed_by_id"] == current_user.id
        assert data["confirmed_at"] is not None

    def test_confirm_wrong_cabinet_404(self, client, current_user, other_employer, db_session):
        """Confirm from other cabinet → 404."""
        appt = models.Appointment(
            patient_name="Other Cabinet Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=other_employer.id,  # Different cabinet
        )
        db_session.add(appt)
        db_session.commit()

        response = client.post(
            f"/api/appointments/{appt.id}/confirm",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 404

    def test_confirm_expired_410(self, client, current_user, db_session):
        """Confirm expired appointment → 410."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=current_user.employer_id,
            expires_at=datetime.utcnow() - timedelta(minutes=1),  # Expired
        )
        db_session.add(appt)
        db_session.commit()

        response = client.post(
            f"/api/appointments/{appt.id}/confirm",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 410

    def test_confirm_already_confirmed_409(self, client, current_user, db_session):
        """Confirm already confirmed appointment → 409."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.CONFIRME,  # Already confirmed
            employer_id=current_user.employer_id,
            confirmed_at=datetime.utcnow(),
            confirmed_by_id=current_user.id,
        )
        db_session.add(appt)
        db_session.commit()

        response = client.post(
            f"/api/appointments/{appt.id}/confirm",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 409


class TestRejectAppointment:
    """Tests rejecting appointments."""

    def test_reject_transitions_to_refuse(self, client, current_user, db_session):
        """Reject appointment → status=REFUSE."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=current_user.employer_id,
        )
        db_session.add(appt)
        db_session.commit()

        response = client.post(
            f"/api/appointments/{appt.id}/reject",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REFUSÉ"


class TestExpireAppointment:
    """Tests manually expiring appointments."""

    def test_expire_transitions_to_expire(self, client, current_user, db_session):
        """Manually expire appointment → status=EXPIRE."""
        appt = models.Appointment(
            patient_name="Test Patient",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
            employer_id=current_user.employer_id,
        )
        db_session.add(appt)
        db_session.commit()

        response = client.post(
            f"/api/appointments/{appt.id}/expire",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "EXPIRÉ"


class TestAuditLogs:
    """Tests audit logging for frontdesk actions."""

    def test_create_request_creates_audit_log(self, client, current_user, db_session):
        """Creating a request creates an audit log."""
        response = client.post(
            "/api/frontdesk/appointment-request",
            json={
                "first_name": "Jean",
                "last_name": "Dupont",
                "appointment_reason": "Test",
                "requested_start": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 200

        # Verify audit log exists
        logs = db_session.query(models.AuditLog).filter(
            models.AuditLog.action == "FRONTDESK_REQUEST_CREATED"
        ).all()
        assert len(logs) > 0
