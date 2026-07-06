"""Tests landing page — POST /api/public/demo-request."""
import json
import os
from unittest.mock import patch, mock_open


VALID_PAYLOAD = {
    "nom": "Dr. Benziane",
    "email": "benziane@cabinet.dz",
    "cabinet": "Cabinet Benziane",
    "telephone": "0556789012",
    "message": "Je voudrais une démo complète.",
}


class TestDemoRequest:
    def test_submit_valid_request(self, client, tmp_path, monkeypatch):
        demo_file = tmp_path / "demo_requests.json"
        monkeypatch.setattr(
            "backend.routers.public._DEMO_REQUESTS_FILE", str(demo_file)
        )
        r = client.post("/api/public/demo-request", json=VALID_PAYLOAD)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "24h" in body["message"]

        # Verify persisted
        assert demo_file.exists()
        saved = json.loads(demo_file.read_text(encoding="utf-8"))
        assert len(saved) == 1
        assert saved[0]["email"] == VALID_PAYLOAD["email"]

    def test_submit_accumulates_requests(self, client, tmp_path, monkeypatch):
        demo_file = tmp_path / "demo_requests.json"
        monkeypatch.setattr(
            "backend.routers.public._DEMO_REQUESTS_FILE", str(demo_file)
        )
        client.post("/api/public/demo-request", json=VALID_PAYLOAD)
        second = {**VALID_PAYLOAD, "nom": "Dr. Autre", "email": "autre@cabinet.dz"}
        client.post("/api/public/demo-request", json=second)

        saved = json.loads(demo_file.read_text(encoding="utf-8"))
        assert len(saved) == 2

    def test_submit_missing_email_returns_422(self, client):
        bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "email"}
        r = client.post("/api/public/demo-request", json=bad)
        assert r.status_code == 422

    def test_submit_invalid_email_returns_422(self, client):
        r = client.post("/api/public/demo-request", json={**VALID_PAYLOAD, "email": "not-an-email"})
        assert r.status_code == 422

    def test_submit_missing_nom_returns_422(self, client):
        bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "nom"}
        r = client.post("/api/public/demo-request", json=bad)
        assert r.status_code == 422

    def test_submit_missing_cabinet_returns_422(self, client):
        bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "cabinet"}
        r = client.post("/api/public/demo-request", json=bad)
        assert r.status_code == 422

    def test_email_notification_called_if_configured(self, client, tmp_path, monkeypatch):
        demo_file = tmp_path / "demo_requests.json"
        monkeypatch.setattr(
            "backend.routers.public._DEMO_REQUESTS_FILE", str(demo_file)
        )
        with patch("backend.services.email_service.email_service.send_email") as mock_email:
            mock_email.return_value = True
            r = client.post("/api/public/demo-request", json=VALID_PAYLOAD)
        assert r.status_code == 200
        mock_email.assert_called_once()

    def test_email_failure_does_not_block_save(self, client, tmp_path, monkeypatch):
        """Email error must NOT prevent the request from being saved."""
        demo_file = tmp_path / "demo_requests.json"
        monkeypatch.setattr(
            "backend.routers.public._DEMO_REQUESTS_FILE", str(demo_file)
        )
        with patch("backend.services.email_service.email_service.send_email", side_effect=Exception("SMTP down")):
            r = client.post("/api/public/demo-request", json=VALID_PAYLOAD)
        assert r.status_code == 200
        assert demo_file.exists()

    def test_list_requires_secret(self, client, tmp_path, monkeypatch):
        demo_file = tmp_path / "demo_requests.json"
        monkeypatch.setattr(
            "backend.routers.public._DEMO_REQUESTS_FILE", str(demo_file)
        )
        r = client.get("/api/public/demo-requests")
        assert r.status_code == 403

    def test_list_with_correct_secret(self, client, tmp_path, monkeypatch):
        demo_file = tmp_path / "demo_requests.json"
        monkeypatch.setattr(
            "backend.routers.public._DEMO_REQUESTS_FILE", str(demo_file)
        )
        monkeypatch.setenv("SUPERADMIN_SECRET", "mysecret")
        # Save a request first
        demo_file.write_text(
            json.dumps([{"nom": "Test", "email": "t@t.dz"}]), encoding="utf-8"
        )
        r = client.get("/api/public/demo-requests", params={"secret": "mysecret"})
        assert r.status_code == 200
        assert len(r.json()) == 1
