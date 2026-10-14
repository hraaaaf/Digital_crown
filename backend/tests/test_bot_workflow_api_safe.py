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
        anonymous = client.post(URL, json={"messages": ["/patient", "1"]})
        assert anonymous.status_code == 401


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
    assert r.status_code in (403, 404)
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


def test_partial_transcript_never_resolves_patient(client, auth_headers):
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        resp = client.post(URL, headers=auth_headers, json={"messages": ["/rdv", "1"]})
    assert resp.status_code == 200
    assert resp.json()["status"] == "clarification"
    assert resp.json()["proposal"] is None


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


def test_invalid_date_cannot_propose_write(client, auth_headers):
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        res = client.post(
            URL, headers=auth_headers,
            json={"messages": ["/rdv", "2", "2020-01-01", "14:30", "30", "consultation", "CONFIRMER"]},
        )
    assert res.status_code == 200
    assert res.json()["proposal"] is None


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
