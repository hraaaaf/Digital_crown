"""Tests CROWN-BOT-ACTION-STRICT-1 — Sécurité exécution Crown Bot.

Le endpoint /bot/execute ne doit accepter que { pending_action_id }
Tout autre champ → 422 (extra forbid).
"""
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend import models
from backend.tests.conftest import make_user


def _mk_action(db, dentiste, action_id, status="pending", action_type="CHANGE_STATUS",
               employer_id=None, expires_delta=timedelta(minutes=30), executed_at=None):
    action = models.BotPendingAction(
        id=action_id,
        session_id="test-session",
        user_id=dentiste.id,
        employer_id=employer_id if employer_id is not None else dentiste.get_employer_id(),
        action_type=action_type,
        params_json={"patient_id": 1},
        status=status,
        expires_at=datetime.utcnow() + expires_delta,
        executed_at=executed_at,
    )
    db.add(action)
    db.commit()
    return action


class TestBotExecuteSchema:
    """Tests schéma BotExecuteRequest."""

    def test_execute_rejects_extra_fields_422(self, client: TestClient, db, dentiste, auth_headers):
        """Body {pending_action_id, action_type} → 422."""
        _mk_action(db, dentiste, "valid-uuid")

        response = client.post(
            "/api/bot/execute",
            json={
                "pending_action_id": "valid-uuid",
                "action_type": "CHANGE_STATUS",  # Extra field → 422
            },
            headers=auth_headers,
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"

    def test_execute_rejects_full_payload_422(self, client: TestClient, db, dentiste, auth_headers):
        """Body avec action_type + params + patient_id → 422."""
        _mk_action(db, dentiste, "valid-uuid-2")

        response = client.post(
            "/api/bot/execute",
            json={
                "pending_action_id": "valid-uuid-2",
                "action_type": "CHANGE_STATUS",
                "params": {"patient_id": 1},
                "patient_id": 1,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_execute_rejects_empty_body_422(self, client: TestClient, auth_headers):
        """Body {} → 422."""
        response = client.post("/api/bot/execute", json={}, headers=auth_headers)
        assert response.status_code == 422

    def test_execute_rejects_missing_id_422(self, client: TestClient, auth_headers):
        """Body {other: 1} → 422."""
        response = client.post("/api/bot/execute", json={"other": 1}, headers=auth_headers)
        assert response.status_code == 422

    def test_execute_rejects_empty_string_422(self, client: TestClient, auth_headers):
        """pending_action_id="" → 422 (min_length=1)."""
        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_execute_accepts_only_pending_action_id(self, client: TestClient, auth_headers):
        """Body exact {pending_action_id} → 404 (not found, but no 422)."""
        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "nonexistent-uuid"},
            headers=auth_headers,
        )
        # 404 because action doesn't exist, NOT 422 because schema is valid
        assert response.status_code == 404


class TestBotExecuteSecurity:
    """Tests sécurité execution bot actions."""

    def test_execute_nonexistent_id_404(self, client: TestClient, auth_headers):
        """UUID inconnu → 404."""
        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "unknown-uuid"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_execute_wrong_tenant_404(self, client: TestClient, db, dentiste, auth_headers):
        """Autre employer_id → 404."""
        other_user = make_user(db)
        _mk_action(db, dentiste, "test-uuid-tenant", employer_id=other_user.get_employer_id())

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "test-uuid-tenant"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_execute_expired_action_410(self, client: TestClient, db, dentiste, auth_headers):
        """TTL dépassé → 410."""
        _mk_action(db, dentiste, "expired-uuid", expires_delta=timedelta(minutes=-1))

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "expired-uuid"},
            headers=auth_headers,
        )
        assert response.status_code == 410

    def test_execute_already_executed_409(self, client: TestClient, db, dentiste, auth_headers):
        """Double-exec → 409."""
        _mk_action(db, dentiste, "executed-uuid", status="executed", executed_at=datetime.utcnow())

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "executed-uuid"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_execute_cancelled_action_409(self, client: TestClient, db, dentiste, auth_headers):
        """Annulé → 409."""
        _mk_action(db, dentiste, "cancelled-uuid", status="cancelled")

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "cancelled-uuid"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_execute_unknown_action_type_403(self, client: TestClient, db, dentiste, auth_headers):
        """Type hors whitelist → 403."""
        _mk_action(db, dentiste, "unknown-type-uuid", action_type="INVALID_ACTION_TYPE")

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "unknown-type-uuid"},
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestBotChatSchema:
    """Tests schéma BotChatRequest."""

    def test_chat_stream_rejects_extra_fields_422(self, client: TestClient, auth_headers):
        """Champs inconnus → 422."""
        response = client.post(
            "/api/bot/chat/stream",
            json={
                "message": "Hello",
                "unknown_field": "value",  # Extra field
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_chat_stream_message_too_long_422(self, client: TestClient, auth_headers):
        """Message > 2000 chars → 422."""
        long_message = "a" * 2001
        response = client.post(
            "/api/bot/chat/stream",
            json={"message": long_message},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestBotExecuteAnonymous:
    """Tests sans auth."""

    def test_execute_requires_auth_401(self, client: TestClient):
        """Pas de token → 401."""
        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "test-uuid"},
        )
        assert response.status_code == 401

    def test_chat_requires_auth_401(self, client: TestClient):
        """Pas de token → 401."""
        response = client.post(
            "/api/bot/chat",
            json={"message": "Hello"},
        )
        assert response.status_code == 401
