"""Tests routers/bot.py — sessions, messages, archive, chat guards."""


BASE = "/api/bot"


class TestBotSessions:
    def test_get_sessions_requires_auth(self, client):
        r = client.get(f"{BASE}/sessions")
        assert r.status_code == 401

    def test_get_sessions_returns_list(self, client, auth_headers):
        r = client.get(f"{BASE}/sessions", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_session_messages_requires_auth(self, client):
        r = client.get(f"{BASE}/sessions/nonexistent/messages")
        assert r.status_code == 401

    def test_get_session_messages_nonexistent_returns_404(self, client, auth_headers):
        r = client.get(f"{BASE}/sessions/nonexistent-session-id/messages", headers=auth_headers)
        assert r.status_code == 404

    def test_archive_session_requires_auth(self, client):
        r = client.delete(f"{BASE}/sessions/some-session")
        assert r.status_code == 401

    def test_archive_session_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete(f"{BASE}/sessions/nonexistent-session-id", headers=auth_headers)
        assert r.status_code == 404


class TestBotChat:
    def test_chat_requires_auth(self, client):
        r = client.post(f"{BASE}/chat", json={"message": "Bonjour"})
        assert r.status_code == 401

    def test_chat_stream_requires_auth(self, client):
        r = client.post(f"{BASE}/chat/stream", json={"message": "Bonjour"})
        assert r.status_code == 401

    def test_chat_with_message(self, client, auth_headers):
        r = client.post(
            f"{BASE}/chat",
            json={"message": "Bonjour, liste mes patients"},
            headers=auth_headers,
        )
        # Bot may respond or fail — as long as it's not 401/403
        assert r.status_code not in (401, 403)

    def test_chat_empty_message(self, client, auth_headers):
        r = client.post(
            f"{BASE}/chat",
            json={"message": ""},
            headers=auth_headers,
        )
        # Empty message might return 422 or some bot response
        assert r.status_code in (200, 400, 422)


class TestBotExecute:
    def test_execute_requires_auth(self, client):
        r = client.post(f"{BASE}/execute", json={"action": "test"})
        assert r.status_code == 401

    def test_execute_nonexistent_action(self, client, auth_headers):
        r = client.post(
            f"{BASE}/execute",
            json={"pending_action_id": "nonexistent-id-12345"},
            headers=auth_headers,
        )
        # Should fail gracefully with 400/404/422/200
        assert r.status_code in (200, 400, 404, 422)

    def test_cancel_action_requires_auth(self, client):
        r = client.post(f"{BASE}/execute/some-action-id/cancel")
        assert r.status_code == 401

    def test_cancel_action_nonexistent(self, client, auth_headers):
        r = client.post(
            f"{BASE}/execute/nonexistent-action-id/cancel",
            headers=auth_headers,
        )
        assert r.status_code in (200, 400, 404, 422)
