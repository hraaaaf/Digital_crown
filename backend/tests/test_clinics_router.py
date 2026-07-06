"""Tests routers/clinics.py — init-status, get/update clinic config."""
import pytest


BASE = "/api/clinics"


class TestInitStatus:
    def test_init_status_no_auth_required(self, client):
        r = client.get(f"{BASE}/init-status")
        assert r.status_code == 200

    def test_init_status_with_dentiste_returns_initialized(self, client, dentiste):
        r = client.get(f"{BASE}/init-status")
        assert r.status_code == 200
        body = r.json()
        assert body["is_initialized"] is True
        assert body["needs_setup"] is False

    def test_init_status_prefers_authenticated_user_cabinet_flag(self, client, db, auth_headers, dentiste):
        from backend import models

        config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == dentiste.id).first()
        if not config:
            config = models.CabinetConfig(
                owner_id=dentiste.id,
                nom_cabinet="Cabinet Test",
                nom_praticien="Dr Test",
                is_initialized=False,
            )
            db.add(config)
        else:
            config.is_initialized = False
        db.commit()

        r = client.get(f"{BASE}/init-status", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["is_initialized"] is False
        assert body["needs_setup"] is True


class TestGetMyClinic:
    def test_get_requires_auth(self, client):
        r = client.get(f"{BASE}/me")
        assert r.status_code == 401

    def test_get_returns_config(self, client, auth_headers):
        r = client.get(f"{BASE}/me", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "nom_cabinet" in body or "primary_color" in body

    def test_get_creates_config_if_missing(self, client, auth_headers):
        r = client.get(f"{BASE}/me", headers=auth_headers)
        assert r.status_code == 200


class TestUpdateMyClinic:
    def test_update_requires_auth(self, client):
        r = client.put(f"{BASE}/me", json={"primary_color": "#FF0000"})
        assert r.status_code == 401

    def test_update_primary_color(self, client, auth_headers):
        r = client.put(f"{BASE}/me", json={"primary_color": "#123456"}, headers=auth_headers)
        assert r.status_code == 200

    def test_update_nom(self, client, auth_headers):
        r = client.put(f"{BASE}/me", json={"nom": "Dr. Test Cabinet"}, headers=auth_headers)
        assert r.status_code == 200

    def test_update_footer_phones(self, client, auth_headers):
        r = client.put(
            f"{BASE}/me",
            json={"footer_phones": "0661112233 / 0522334455"},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_update_font(self, client, auth_headers):
        r = client.put(f"{BASE}/me", json={"font_fr": "Roboto"}, headers=auth_headers)
        assert r.status_code == 200

    def test_update_watermark(self, client, auth_headers):
        r = client.put(
            f"{BASE}/me",
            json={"watermark_enabled": True, "watermark_opacity": 0.15},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_update_header_lines(self, client, auth_headers):
        r = client.put(
            f"{BASE}/me",
            json={"header_lines_fr": ["Dr. Test", "Chirurgien-Dentiste"]},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_update_adresse_alias(self, client, auth_headers):
        r = client.put(
            f"{BASE}/me",
            json={"adresse": "123 Rue Principale, Casablanca"},
            headers=auth_headers,
        )
        assert r.status_code == 200


class TestLogoUpload:
    def test_upload_logo_requires_auth(self, client):
        import io
        r = client.post(
            f"{BASE}/me/logo",
            files={"file": ("logo.png", io.BytesIO(b"fake"), "image/png")},
        )
        assert r.status_code == 401

    def test_upload_unsupported_format_returns_400(self, client, auth_headers):
        import io
        r = client.post(
            f"{BASE}/me/logo",
            files={"file": ("logo.txt", io.BytesIO(b"fake"), "text/plain")},
            headers=auth_headers,
        )
        assert r.status_code == 400
