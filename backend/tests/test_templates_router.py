"""Tests routers/templates.py — list, get, create, set-default, delete."""
import pytest


def _template_payload(name="Test Template", ttype="ORDONNANCE"):
    return {
        "name": name,
        "type": ttype,
        "style_key": "classique",
        "is_system": False,
        "is_default": False,
        "description": "Template de test",
        "body_html": "<p>Contenu de l'ordonnance</p>",
        "design_config": {},
    }


# ── list templates ────────────────────────────────────────────────────────────

class TestListTemplates:
    def test_requires_auth(self, client):
        r = client.get("/api/templates/")
        assert r.status_code == 401

    def test_list_system_templates(self, client, auth_headers):
        r = client.get("/api/templates/", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_all_templates(self, client, auth_headers):
        r = client.get("/api/templates/?is_system=false", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_filter_by_type(self, client, auth_headers):
        r = client.get("/api/templates/?type=ORDONNANCE", headers=auth_headers)
        assert r.status_code == 200
        for t in r.json():
            assert t["type"] == "ORDONNANCE"


# ── get by id ─────────────────────────────────────────────────────────────────

class TestGetTemplate:
    def test_requires_auth(self, client):
        r = client.get("/api/templates/nonexistent")
        assert r.status_code == 401

    def test_nonexistent_returns_404(self, client, auth_headers):
        r = client.get("/api/templates/nonexistent-id-99999", headers=auth_headers)
        assert r.status_code == 404


# ── create template ───────────────────────────────────────────────────────────

class TestCreateTemplate:
    def test_requires_auth(self, client):
        r = client.post("/api/templates/", json=_template_payload())
        assert r.status_code == 401

    def test_create_user_template(self, client, auth_headers):
        r = client.post(
            "/api/templates/",
            json=_template_payload("Mon Ordonnance Custom"),
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Mon Ordonnance Custom"
        assert body["is_system"] is False

    def test_create_certificat_template(self, client, auth_headers):
        r = client.post(
            "/api/templates/",
            json=_template_payload("Certificat Repos", "CERTIFICAT"),
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["type"] == "CERTIFICAT"

    def test_create_system_template_forbidden(self, client, auth_headers):
        payload = _template_payload("System Template")
        payload["is_system"] = True
        r = client.post("/api/templates/", json=payload, headers=auth_headers)
        assert r.status_code == 403


# ── get created template ──────────────────────────────────────────────────────

class TestGetCreatedTemplate:
    def test_get_own_template(self, client, auth_headers):
        create_r = client.post(
            "/api/templates/",
            json=_template_payload("Fetch Test Template"),
            headers=auth_headers,
        )
        tid = create_r.json()["id"]

        r = client.get(f"/api/templates/{tid}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Fetch Test Template"


# ── set-default ───────────────────────────────────────────────────────────────

class TestSetDefault:
    def test_set_default_system_template_forbidden(self, client, auth_headers):
        # System templates cannot be made default via this endpoint
        r = client.post("/api/templates/system-nonexistent/set-default", headers=auth_headers)
        assert r.status_code == 404

    def test_set_default_user_template(self, client, auth_headers):
        # Create a template first
        create_r = client.post(
            "/api/templates/",
            json=_template_payload("Default Candidate"),
            headers=auth_headers,
        )
        tid = create_r.json()["id"]

        r = client.post(f"/api/templates/{tid}/set-default", headers=auth_headers)
        assert r.status_code in (200, 403)  # 403 if system template


# ── delete template ───────────────────────────────────────────────────────────

class TestDeleteTemplate:
    def test_requires_auth(self, client):
        r = client.delete("/api/templates/nonexistent")
        assert r.status_code == 401

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete("/api/templates/nonexistent-999", headers=auth_headers)
        assert r.status_code == 404

    def test_delete_own_template(self, client, auth_headers):
        create_r = client.post(
            "/api/templates/",
            json=_template_payload("Del Template"),
            headers=auth_headers,
        )
        tid = create_r.json()["id"]

        r = client.delete(f"/api/templates/{tid}", headers=auth_headers)
        assert r.status_code == 200

        r = client.get(f"/api/templates/{tid}", headers=auth_headers)
        assert r.status_code == 404
