"""Flagged Crown Bot workflow preview and atomic-confirmation regression tests.

Synthetic patients; no real clinical or finance data. New preview writes nothing.
"""

from datetime import date, datetime, timedelta
from unittest.mock import patch

from backend import models
from backend.config import settings
from backend.services.bot.action_dispatcher import BotResponse


URL = "/api/bot/workflows/preview"


def _patient(db, owner, *, first="Synthetic", last="Patient"):
    p = models.Patient(
        nom=last, prenom=first, date_naissance=datetime(1990, 1, 1),
        sexe="F", employer_id=owner.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _pending(db, user, patient_id, action_type="OPEN_DEVIS_EDITOR"):
    obj = models.BotPendingAction(
        session_id="synthetic-poc-session",
        user_id=user.id,
        employer_id=user.get_employer_id(),
        action_type=action_type,
        params_json={"patient_id": patient_id},
        status="pending",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _tomorrow():
    return (date.today() + timedelta(days=1)).isoformat()


def test_flag_off_default_and_user_gate(client, auth_headers):
    # Even valid auth cannot access preview unless explicitly enabled.
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", False):
        r = client.post(URL, headers=auth_headers, json={"messages": ["/patient", "1"]})
        assert r.status_code == 404
        assert "patient" not in r.text.lower()
        # auth_headers fixture logged in through this TestClient. Login also
        # set an HttpOnly access_token cookie: omitting Authorization alone
        # does not make this request anonymous.
        assert client.cookies.get("access_token")
        client.cookies.clear()
        anonymous = client.post(URL, json={"messages": ["/patient", "1"]})
        assert anonymous.status_code == 401

    # The same anonymous client must also be rejected when the feature flag
    # is enabled, without ever reaching patient resolution.
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        anonymous_enabled = client.post(
            URL, json={"messages": ["/patient", "1"]}
        )
        assert anonymous_enabled.status_code == 401


def test_feature_flag_true_patient_lookup_is_tenant_scoped(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste)
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        resp = client.post(
            URL, headers=auth_headers,
            json={"messages": ["/patient", str(patient.id)]},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "read"
    assert body["patient"]["id"] == patient.id
    assert body["patient"]["nom"] == "Patient"
    assert body["proposal"] is None
    assert "pending_action_id" not in body


def test_live_tenant_guard_rejects_foreign_patient(client, db, auth_headers):
    from backend.tests.conftest import make_user
    other_owner = make_user(db)
    other = _patient(db, other_owner, first="Foreign", last="Tenant")
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        r = client.post(
            URL, headers=auth_headers,
            json={"messages": ["/patient", str(other.id)]},
        )
    assert r.status_code == 404
    assert "Foreign" not in r.text
    assert "Tenant" not in r.text


def test_permission_is_checked_before_patient_query(client, auth_headers):
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), \
         patch("backend.routers.bot_workflows.has_permission", return_value=False):
        r = client.post(URL, headers=auth_headers, json={"messages": ["/rdv", "5"]})
    assert r.status_code == 403


def test_appointment_preview_is_non_executable(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste)
    before_appointments = db.query(models.Appointment).count()
    before_actions = db.query(models.BotPendingAction).count()
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        res = client.post(
            URL, headers=auth_headers,
            json={"messages": [
                "/rdv", str(patient.id), _tomorrow(), "14:30", "30",
                "consultation", "CONFIRMER",
            ]},
        )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "proposal_only"
    assert data["proposal"]["type"] == "CREATE_APPOINTMENT"
    assert data["proposal"]["params"]["motif"] == "CONSULTATION"
    assert "pending_action_id" not in data
    assert db.query(models.Appointment).count() == before_appointments
    assert db.query(models.BotPendingAction).count() == before_actions


def test_devis_preview_never_creates_document_or_action(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste)
    before = db.query(models.BotPendingAction).count()
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        res = client.post(
            URL, headers=auth_headers,
            json={"messages": ["/devis", str(patient.id), "couronne", "CONFIRMER"]},
        )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["proposal"]["type"] == "OPEN_DEVIS_EDITOR"
    assert data["proposal"]["params"]["draft_only"] is True
    assert "pending_action_id" not in data
    assert db.query(models.BotPendingAction).count() == before


def test_partial_transcript_never_resolves_patient(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste)
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        resp = client.post(
            URL, headers=auth_headers,
            json={"messages": ["/rdv", f"id:{patient.id}"]},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "clarification"
    assert resp.json()["proposal"] is None
    assert "patient" not in resp.json()


def test_transcript_is_strictly_bounded(client, auth_headers):
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        for messages in [[], ["/rdv"] * 9, ["/rdv", "x" * 81]]:
            res = client.post(URL, headers=auth_headers, json={"messages": messages})
            assert res.status_code == 422
        unknown = client.post(URL, headers=auth_headers, json={"messages": ["openai"]})
        assert unknown.status_code == 422
        extra = client.post(
            URL, headers=auth_headers, json={"messages": ["/patient", "1"], "execute": True},
        )
        assert extra.status_code == 422


def test_invalid_date_cannot_propose_write(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste)
    before = (db.query(models.Appointment).count(),
              db.query(models.BotPendingAction).count())
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        res = client.post(
            URL, headers=auth_headers,
            json={"messages": [
                "/rdv", f"id:{patient.id}", "2020-01-01", "14:30",
                "30", "consultation", "CONFIRMER",
            ]},
        )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "clarification"
    assert res.json()["proposal"] is None
    assert (db.query(models.Appointment).count(),
            db.query(models.BotPendingAction).count()) == before


def test_atomic_claim_prevents_replay_of_success(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste)
    action = _pending(db, dentiste, patient.id)
    response1 = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert response1.status_code == 200, response1.text
    db.refresh(action)
    assert action.status == "executed"
    assert action.executed_at is not None
    response2 = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert response2.status_code == 409


def test_dispatcher_error_cannot_be_recorded_as_executed(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste)
    action = _pending(db, dentiste, patient.id)
    with patch(
        "backend.routers.bot.dispatcher.execute",
        return_value=BotResponse("Échec synthétique", action_type="error"),
    ) as executor:
        res = client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
        assert res.status_code == 409, res.text
        assert executor.call_count == 1
        db.refresh(action)
        assert action.status == "failed"
        assert action.executed_at is None
        again = client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
        assert again.status_code == 409
        assert executor.call_count == 1


def test_stale_claim_is_not_retryable(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste)
    action = _pending(db, dentiste, patient.id)
    action.status = "executing"
    db.commit()
    with patch("backend.routers.bot.dispatcher.execute") as executor:
        res = client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
        assert res.status_code == 409
        executor.assert_not_called()


def test_unexpected_nonerror_dispatch_response_cannot_be_recorded_as_executed(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    action = _pending(db, dentiste, patient.id)
    with patch(
        "backend.routers.bot.dispatcher.execute",
        return_value=BotResponse("Pas de redirection", action_type="read"),
    ) as executor:
        res = client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
        assert res.status_code == 409, res.text
        assert executor.call_count == 1
    db.refresh(action)
    assert action.status == "failed"
    assert action.executed_at is None


def test_soft_deleted_patient_not_visible_in_preview(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste)
    patient.deleted_at = datetime.utcnow()
    db.commit()
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        res = client.post(
            URL, headers=auth_headers,
            json={"messages": ["/patient", str(patient.id)]},
        )
    assert res.status_code == 404
    assert res.json()["detail"] == "Patient introuvable."
    assert "Synthetic" not in res.text


def test_stale_cancel_never_overwrites_executing_state(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    action = _pending(db, dentiste, patient.id)

    def concurrent_claim(_db, *_args, **_kwargs):
        _db.query(models.BotPendingAction).filter(
            models.BotPendingAction.id == action.id,
        ).update({"status": "executing"}, synchronize_session=False)
        _db.commit()
        return False

    with patch("backend.routers.bot.transition_pending_action", side_effect=concurrent_claim):
        res = client.post(
            f"/api/bot/execute/{action.id}/cancel", headers=auth_headers,
        )
    assert res.status_code == 409
    db.refresh(action)
    assert action.status == "executing"


def test_expired_stale_request_never_overwrites_executing_state(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    action = _pending(db, dentiste, patient.id)
    action.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    def concurrent_claim(_db, *_args, **_kwargs):
        _db.query(models.BotPendingAction).filter(
            models.BotPendingAction.id == action.id,
        ).update({"status": "executing"}, synchronize_session=False)
        _db.commit()
        return False

    with patch("backend.routers.bot.transition_pending_action", side_effect=concurrent_claim):
        res = client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
    assert res.status_code == 409
    db.refresh(action)
    assert action.status == "executing"


def test_bot_booking_rejects_canonical_conflict_without_duplicate_write(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    future = datetime.now() + timedelta(days=8)
    future = future.replace(hour=10, minute=30, second=0, microsecond=0)
    existing = models.Appointment(
        patient_id=patient.id,
        employer_id=dentiste.get_employer_id(),
        praticien_id=dentiste.id,
        datetime_start=future,
        duration_minutes=30,
        motif="Consultation",
    )
    db.add(existing)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CREATE_APPOINTMENT")
    action.params_json = {
        "patient_id": patient.id,
        "datetime_start": future.isoformat(),
        "motif": "Consultation",
        "duration_minutes": 30,
    }
    db.commit()
    before = db.query(models.Appointment).count()
    # Keep the real canonical practitioner/conflict query; isolate weekly
    # calendar availability to test the overlap contract specifically.
    with patch(
        "backend.routers.appointments.validate_appointment_availability",
        return_value=None,
    ) as availability:
        res = client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
    assert availability.call_count == 1
    assert res.status_code == 409, res.text
    assert db.query(models.Appointment).count() == before
    db.refresh(action)
    assert action.status == "failed"


def test_bot_booking_atomic_business_and_action_state_on_success(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    future = (datetime.now() + timedelta(days=7)).replace(
        hour=11, minute=0, second=0, microsecond=0
    )
    action = _pending(db, dentiste, patient.id, action_type="CREATE_APPOINTMENT")
    action.params_json = {
        "patient_id": patient.id,
        "datetime_start": future.isoformat(),
        "motif": "Consultation",
        "duration_minutes": 30,
    }
    db.commit()
    baseline = db.query(models.Appointment).count()
    with patch(
        "backend.routers.appointments.validate_appointment_availability",
        return_value=None,
    ):
        res = client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
    assert res.status_code == 200, res.text
    assert db.query(models.Appointment).count() == baseline + 1
    db.refresh(action)
    assert action.status == "executed"
    assert action.executed_at is not None
    replay = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert replay.status_code == 409
    assert db.query(models.Appointment).count() == baseline + 1


def test_bot_booking_exception_after_flush_rolls_back_business_write(
    client, db, dentiste, auth_headers
):
    import pytest
    from backend.services.bot.action_dispatcher import ActionDispatcher

    patient = _patient(db, dentiste)
    future = (datetime.now() + timedelta(days=7)).replace(
        hour=14, minute=0, second=0, microsecond=0
    )
    action = _pending(db, dentiste, patient.id, action_type="CREATE_APPOINTMENT")
    action.params_json = {
        "patient_id": patient.id,
        "datetime_start": future.isoformat(),
        "motif": "Consultation",
        "duration_minutes": 30,
    }
    db.commit()
    baseline = db.query(models.Appointment).count()

    real = ActionDispatcher()
    def inject_failure_after_business_flush(pending, session, user, **kwargs):
        response = real.execute(pending, session, user, **kwargs)
        assert response.action_type == "write_done"
        assert session.query(models.Appointment).count() == baseline + 1
        raise RuntimeError("synthetic-crash-before-final-commit")

    with patch(
        "backend.routers.appointments.validate_appointment_availability",
        return_value=None,
    ), patch(
        "backend.routers.bot.dispatcher.execute",
        side_effect=inject_failure_after_business_flush,
    ), pytest.raises(RuntimeError, match="synthetic-crash-before-final-commit"):
        client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
    assert db.query(models.Appointment).count() == baseline
    db.refresh(action)
    assert action.status == "failed"
    assert action.executed_at is None

def test_bot_status_change_is_atomic_on_precommit_failure(
    client, db, dentiste, auth_headers
):
    import pytest
    from backend.services.bot.action_dispatcher import ActionDispatcher

    patient = _patient(db, dentiste)
    future = datetime.now() + timedelta(days=8)
    appt = models.Appointment(
        patient_id=patient.id,
        employer_id=dentiste.get_employer_id(),
        datetime_start=future,
        duration_minutes=30,
        motif="Consultation",
        status=models.AppointmentStatus.PREVU,
    )
    db.add(appt)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CHANGE_STATUS")
    action.params_json = {
        "appointment_id": appt.id,
        "patient_id": patient.id,
        "expected_status": "PREVU", "expected_revision": appt.clinical_revision,
        "status": "ANNULE",
        "patient_name": "Synthetic Patient",
    }
    db.commit()
    original = ActionDispatcher()

    def inject_after_flush(pending, session, user, **kwargs):
        result = original.execute(pending, session, user, **kwargs)
        assert result.action_type == "write_done"
        assert session.get(models.Appointment, appt.id).status == models.AppointmentStatus.ANNULE
        raise RuntimeError("synthetic-status-crash-before-commit")

    with patch(
        "backend.routers.bot.dispatcher.execute",
        side_effect=inject_after_flush,
    ), pytest.raises(RuntimeError, match="synthetic-status-crash-before-commit"):
        client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
    db.refresh(appt)
    db.refresh(action)
    assert appt.status == models.AppointmentStatus.PREVU
    assert action.status == "failed"


def test_bot_status_change_and_action_status_commit_together(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    appt = models.Appointment(
        patient_id=patient.id,
        employer_id=dentiste.get_employer_id(),
        datetime_start=datetime.now() + timedelta(days=7),
        duration_minutes=30, motif="Consultation",
        status=models.AppointmentStatus.PREVU,
    )
    db.add(appt)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CHANGE_STATUS")
    action.params_json = {
        "appointment_id": appt.id,
        "patient_id": patient.id,
        "expected_status": "PREVU", "expected_revision": appt.clinical_revision,
        "status": "ANNULE",
        "patient_name": "Synthetic Patient",
    }
    db.commit()
    res = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert res.status_code == 200, res.text
    db.refresh(appt)
    db.refresh(action)
    assert appt.status == models.AppointmentStatus.ANNULE
    assert action.status == "executed"

def test_foreign_patient_denial_does_not_commit_executing_claim(
    client, db, dentiste, auth_headers
):
    from backend.tests.conftest import make_user
    other_owner = make_user(db)
    foreign = _patient(db, other_owner, first="Foreign", last="Hidden")
    action = _pending(db, dentiste, foreign.id, action_type="CREATE_APPOINTMENT")
    action.params_json = {
        "patient_id": foreign.id,
        "datetime_start": (datetime.now() + timedelta(days=9)).isoformat(),
        "motif": "Consultation",
        "duration_minutes": 30,
    }
    db.commit()
    before = db.query(models.Appointment).count()
    res = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert res.status_code == 404
    assert "Foreign" not in res.text
    db.refresh(action)
    assert action.status == "failed", "Tenant denial must not strand executing"
    assert db.query(models.Appointment).count() == before


def test_foreign_patient_redirect_denial_does_not_commit_executing_claim(
    client, db, dentiste, auth_headers
):
    from backend.tests.conftest import make_user
    other_owner = make_user(db)
    foreign = _patient(db, other_owner, first="Foreign", last="Hidden")
    action = _pending(db, dentiste, foreign.id, action_type="OPEN_DEVIS_EDITOR")
    res = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert res.status_code == 404
    assert "Foreign" not in res.text
    db.refresh(action)
    assert action.status == "failed"


def test_legacy_executing_inventory_is_read_only_and_owner_scoped(
    client, db, dentiste, auth_headers
):
    from backend.tests.conftest import make_user
    own = _pending(db, dentiste, 1, action_type="CREATE_APPOINTMENT")
    own.status = "executing"
    another_owner = make_user(db)
    foreign = _pending(db, another_owner, 1, action_type="CREATE_APPOINTMENT")
    foreign.status = "executing"
    db.commit()

    r = client.get("/api/bot/execute/reconciliation", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "manual_reconciliation_required"
    assert body["safe_to_retry"] is False
    assert body["automatic_reset"] is False
    assert len(body["actions"]) == 1
    assert body["actions"][0]["action_id"] == own.id
    assert foreign.id not in r.text
    assert "params_json" not in r.text
    assert "patient_id" not in r.text
    db.refresh(own)
    assert own.status == "executing"

    client.cookies.clear()
    anonymous = client.get("/api/bot/execute/reconciliation")
    assert anonymous.status_code == 401


def test_bot_status_rejects_archived_appointment_even_same_tenant(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    appt = models.Appointment(
        patient_id=patient.id, employer_id=dentiste.get_employer_id(),
        datetime_start=datetime.now() + timedelta(days=8),
        duration_minutes=30, motif="Synthetic",
        status=models.AppointmentStatus.PREVU,
        deleted_at=datetime.utcnow(),
    )
    db.add(appt)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CHANGE_STATUS")
    action.params_json = {"appointment_id": appt.id, "patient_id": patient.id,
                          "expected_status": "PREVU", "expected_revision": appt.clinical_revision, "status": "ANNULE"}
    db.commit()
    response = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert response.status_code == 409, response.text
    db.refresh(appt)
    db.refresh(action)
    assert appt.status == models.AppointmentStatus.PREVU
    assert action.status == "failed"


def test_bot_status_rejects_patient_reassignment_after_confirmation_preview(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    other = _patient(db, dentiste)
    appt = models.Appointment(
        patient_id=patient.id, employer_id=dentiste.get_employer_id(),
        datetime_start=datetime.now() + timedelta(days=8),
        duration_minutes=30, motif="Synthetic",
        status=models.AppointmentStatus.PREVU,
    )
    db.add(appt)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CHANGE_STATUS")
    action.params_json = {"appointment_id": appt.id, "patient_id": patient.id,
                          "expected_status": "PREVU", "expected_revision": appt.clinical_revision, "status": "ANNULE"}
    db.commit()
    appt.patient_id = other.id  # change between proposal and confirmation
    db.commit()
    response = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert response.status_code == 409, response.text
    db.refresh(appt)
    db.refresh(action)
    assert appt.status == models.AppointmentStatus.PREVU
    assert appt.patient_id == other.id
    assert action.status == "failed"


def test_bot_status_cannot_reactivate_cancelled_appointment_after_preview(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    appt = models.Appointment(
        patient_id=patient.id, employer_id=dentiste.get_employer_id(),
        datetime_start=datetime.now() + timedelta(days=8),
        duration_minutes=30, motif="Synthetic delayed confirmation",
        status=models.AppointmentStatus.PREVU,
    )
    db.add(appt)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CHANGE_STATUS")
    action.params_json = {
        "appointment_id": appt.id, "patient_id": patient.id,
        "expected_status": "PREVU", "expected_revision": appt.clinical_revision, "status": "EN_FAUTEUIL",
    }
    db.commit()
    appt.status = models.AppointmentStatus.ANNULE
    db.commit()  # a second clinical actor changed state after bot preview
    response = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert response.status_code == 409, response.text
    db.refresh(appt)
    db.refresh(action)
    assert appt.status == models.AppointmentStatus.ANNULE
    assert action.status == "failed"


def test_bot_historical_status_action_without_expected_status_fails_closed(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    appt = models.Appointment(
        patient_id=patient.id, employer_id=dentiste.get_employer_id(),
        datetime_start=datetime.now() + timedelta(days=8),
        duration_minutes=30, motif="Synthetic legacy action",
        status=models.AppointmentStatus.PREVU,
    )
    db.add(appt)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CHANGE_STATUS")
    action.params_json = {
        "appointment_id": appt.id, "patient_id": patient.id,
        "status": "ANNULE",
    }
    db.commit()
    response = client.post(
        "/api/bot/execute", headers=auth_headers,
        json={"pending_action_id": action.id},
    )
    assert response.status_code == 409, response.text
    db.refresh(appt)
    db.refresh(action)
    assert appt.status == models.AppointmentStatus.PREVU
    assert action.status == "failed"


def test_bot_status_rejects_aba_after_cancel_then_restore(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    appt = models.Appointment(
        patient_id=patient.id, employer_id=dentiste.get_employer_id(),
        datetime_start=datetime.now() + timedelta(days=20),
        duration_minutes=30, status=models.AppointmentStatus.PREVU,
    )
    db.add(appt)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CHANGE_STATUS")
    action.params_json = {
        "appointment_id": appt.id, "patient_id": patient.id,
        "expected_status": "PREVU", "expected_revision": appt.clinical_revision,
        "status": "EN_FAUTEUIL",
    }
    db.commit()
    expected = appt.clinical_revision
    # Both updates are direct SQL, bypassing ORM events: the DB trigger
    # MUST still advance revision, even if the final status looks unchanged.
    from sqlalchemy import text
    db.execute(text("UPDATE appointments SET status='ANNULE' WHERE id=:id"), {"id": appt.id})
    db.execute(text("UPDATE appointments SET status='PREVU' WHERE id=:id"), {"id": appt.id})
    db.commit()
    db.refresh(appt)
    assert appt.status == models.AppointmentStatus.PREVU
    assert appt.clinical_revision == expected + 2
    result = client.post("/api/bot/execute", headers=auth_headers,
                         json={"pending_action_id": action.id})
    assert result.status_code == 409, result.text
    db.refresh(appt)
    db.refresh(action)
    assert appt.status == models.AppointmentStatus.PREVU
    assert action.status == "failed"


def test_bot_status_rejects_rescheduled_same_patient_and_same_status(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    slot = datetime.now() + timedelta(days=21)
    appt = models.Appointment(
        patient_id=patient.id, employer_id=dentiste.get_employer_id(),
        datetime_start=slot, duration_minutes=30,
        status=models.AppointmentStatus.PREVU,
    )
    db.add(appt)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CHANGE_STATUS")
    action.params_json = {
        "appointment_id": appt.id, "patient_id": patient.id,
        "expected_status": "PREVU", "expected_revision": appt.clinical_revision,
        "status": "TERMINE",
    }
    db.commit()
    appt.datetime_start = slot + timedelta(hours=2)
    db.commit()
    db.refresh(appt)
    assert appt.clinical_revision >= 1
    result = client.post("/api/bot/execute", headers=auth_headers,
                         json={"pending_action_id": action.id})
    assert result.status_code == 409, result.text
    db.refresh(appt)
    assert appt.status == models.AppointmentStatus.PREVU


def test_bot_legacy_status_without_revision_is_rejected_even_if_status_matches(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste)
    appt = models.Appointment(
        patient_id=patient.id, employer_id=dentiste.get_employer_id(),
        datetime_start=datetime.now() + timedelta(days=22),
        duration_minutes=30, status=models.AppointmentStatus.PREVU,
    )
    db.add(appt)
    db.commit()
    action = _pending(db, dentiste, patient.id, action_type="CHANGE_STATUS")
    action.params_json = {
        "appointment_id": appt.id, "patient_id": patient.id,
        "expected_status": "PREVU", "status": "TERMINE",
    }
    db.commit()
    result = client.post("/api/bot/execute", headers=auth_headers,
                         json={"pending_action_id": action.id})
    assert result.status_code == 409
    db.refresh(appt)
    db.refresh(action)
    assert appt.status == models.AppointmentStatus.PREVU
    assert action.status == "failed"


def test_bot_status_preview_captures_database_owned_revision(db, dentiste):
    from types import SimpleNamespace
    from backend.services.bot.action_dispatcher import ActionDispatcher
    patient = _patient(db, dentiste)
    appt = models.Appointment(
        patient_id=patient.id, employer_id=dentiste.get_employer_id(),
        datetime_start=datetime.now() + timedelta(days=24),
        duration_minutes=30, status=models.AppointmentStatus.PREVU,
    )
    db.add(appt)
    db.commit()
    parsed = SimpleNamespace(
        entities={"patient_id": patient.id},
        raw_message="annuler le rendez-vous",
    )
    response = ActionDispatcher()._handle_change_status(parsed, db, dentiste)
    assert response.action_type == "write_pending"
    params = response.pending_action["params"]
    assert params["appointment_id"] == appt.id
    assert params["patient_id"] == patient.id
    assert params["expected_status"] == appt.status.name
    assert params["expected_revision"] == appt.clinical_revision
