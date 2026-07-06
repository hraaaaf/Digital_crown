"""Tests CROWN-BOT-ACTION-STRICT-1 — Sécurité exécution Crown Bot.

Le endpoint /bot/execute ne doit accepter que { pending_action_id }
Tout autre champ → 422 (extra forbid).
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend import models


class TestBotExecuteSchema:
    """Tests schéma BotExecuteRequest."""

    def test_execute_rejects_extra_fields_422(self, client: TestClient, db_session, current_user):
        """Body {pending_action_id, action_type} → 422."""
        # Créer une action pending valide d'abord
        action = models.BotPendingAction(
            id="valid-uuid",
            session_id="test-session",
            user_id=current_user.id,
            employer_id=current_user.employer_id,
            action_type="CHANGE_STATUS",
            params_json={"patient_id": 1},
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db_session.add(action)
        db_session.commit()

        response = client.post(
            "/api/bot/execute",
            json={
                "pending_action_id": "valid-uuid",
                "action_type": "CHANGE_STATUS",  # Extra field → 422
            },
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"

    def test_execute_rejects_full_payload_422(self, client: TestClient, db_session, current_user):
        """Body avec action_type + params + patient_id → 422."""
        action = models.BotPendingAction(
            id="valid-uuid",
            session_id="test-session",
            user_id=current_user.id,
            employer_id=current_user.employer_id,
            action_type="CHANGE_STATUS",
            params_json={"patient_id": 1},
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db_session.add(action)
        db_session.commit()

        response = client.post(
            "/api/bot/execute",
            json={
                "pending_action_id": "valid-uuid",
                "action_type": "CHANGE_STATUS",
                "params": {"patient_id": 1},
                "patient_id": 1,
            },
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 422

    def test_execute_rejects_empty_body_422(self, client: TestClient, current_user):
        """Body {} → 422."""
        response = client.post(
            "/api/bot/execute",
            json={},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 422

    def test_execute_rejects_missing_id_422(self, client: TestClient, current_user):
        """Body {other: 1} → 422."""
        response = client.post(
            "/api/bot/execute",
            json={"other": 1},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 422

    def test_execute_rejects_empty_string_422(self, client: TestClient, current_user):
        """pending_action_id="" → 422 (min_length=1)."""
        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": ""},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 422

    def test_execute_accepts_only_pending_action_id(self, client: TestClient, db_session, current_user):
        """Body exact {pending_action_id} → 404 (not found, but no 422)."""
        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "nonexistent-uuid"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        # 404 because action doesn't exist, NOT 422 because schema is valid
        assert response.status_code == 404


class TestBotExecuteSecurity:
    """Tests sécurité execution bot actions."""

    def test_execute_nonexistent_id_404(self, client: TestClient, current_user):
        """UUID inconnu → 404."""
        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "unknown-uuid"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 404

    def test_execute_wrong_tenant_404(self, client: TestClient, db_session, current_user, other_employer):
        """Autre employer_id → 404."""
        action = models.BotPendingAction(
            id="test-uuid",
            session_id="test-session",
            user_id=current_user.id,
            employer_id=other_employer.id,  # Different employer
            action_type="CHANGE_STATUS",
            params_json={"patient_id": 1},
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db_session.add(action)
        db_session.commit()

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "test-uuid"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 404

    def test_execute_expired_action_410(self, client: TestClient, db_session, current_user):
        """TTL dépassé → 410."""
        action = models.BotPendingAction(
            id="expired-uuid",
            session_id="test-session",
            user_id=current_user.id,
            employer_id=current_user.employer_id,
            action_type="CHANGE_STATUS",
            params_json={"patient_id": 1},
            status="pending",
            expires_at=datetime.utcnow() - timedelta(minutes=1),  # Expired
        )
        db_session.add(action)
        db_session.commit()

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "expired-uuid"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 410

    def test_execute_already_executed_409(self, client: TestClient, db_session, current_user):
        """Double-exec → 409."""
        action = models.BotPendingAction(
            id="executed-uuid",
            session_id="test-session",
            user_id=current_user.id,
            employer_id=current_user.employer_id,
            action_type="CHANGE_STATUS",
            params_json={"patient_id": 1},
            status="executed",  # Already executed
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            executed_at=datetime.utcnow(),
        )
        db_session.add(action)
        db_session.commit()

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "executed-uuid"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 409

    def test_execute_cancelled_action_409(self, client: TestClient, db_session, current_user):
        """Annulé → 409."""
        action = models.BotPendingAction(
            id="cancelled-uuid",
            session_id="test-session",
            user_id=current_user.id,
            employer_id=current_user.employer_id,
            action_type="CHANGE_STATUS",
            params_json={"patient_id": 1},
            status="cancelled",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db_session.add(action)
        db_session.commit()

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "cancelled-uuid"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 409

    def test_execute_unknown_action_type_403(self, client: TestClient, db_session, current_user):
        """Type hors whitelist → 403."""
        action = models.BotPendingAction(
            id="unknown-type-uuid",
            session_id="test-session",
            user_id=current_user.id,
            employer_id=current_user.employer_id,
            action_type="INVALID_ACTION_TYPE",
            params_json={"patient_id": 1},
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db_session.add(action)
        db_session.commit()

        response = client.post(
            "/api/bot/execute",
            json={"pending_action_id": "unknown-type-uuid"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 403


class TestBotChatSchema:
    """Tests schéma BotChatRequest."""

    def test_chat_stream_rejects_extra_fields_422(self, client: TestClient, current_user):
        """Champs inconnus → 422."""
        response = client.post(
            "/api/bot/chat/stream",
            json={
                "message": "Hello",
                "unknown_field": "value",  # Extra field
            },
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 422

    def test_chat_stream_message_too_long_422(self, client: TestClient, current_user):
        """Message > 2000 chars → 422."""
        long_message = "a" * 2001
        response = client.post(
            "/api/bot/chat/stream",
            json={"message": long_message},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 422

    def test_chat_stream_accepts_message_at_limit(self, client: TestClient, current_user):
        """Message = 2000 chars → accepted."""
        long_message = "a" * 2000
        response = client.post(
            "/api/bot/chat/stream",
            json={"message": long_message},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        # Should not be 422 (validation passed)
        assert response.status_code != 422


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
