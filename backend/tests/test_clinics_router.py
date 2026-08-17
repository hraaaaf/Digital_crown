"""Tests routers/clinics.py — init-status, get/update clinic config."""
import pytest


BASE = "/api/clinics"


class TestInitStatus:
    def test_init_status_requires_auth(self, client):
        r = client.get(f"{BASE}/init-status")
        assert r.status_code == 401

    def test_init_status_with_dentiste_returns_initialized(self, client, auth_headers, dentiste):
        r = client.get(f"{BASE}/init-status", headers=auth_headers)
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


class TestLetterheadUpload:
    def _png_bytes(self, width=200, height=300, color=(10, 40, 120)):
        """Vraie image PNG en mémoire (Pillow est une dépendance du projet)."""
        import io
        from PIL import Image
        img = Image.new("RGB", (width, height), color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _pdf_bytes(self):
        """Vrai PDF 1 page en mémoire via ReportLab (dépendance du projet)."""
        import io
        from reportlab.pdfgen import canvas as rl_canvas
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf)
        c.drawString(100, 750, "EN-TETE CABINET TEST")
        c.drawString(100, 400, "CONTENU PATIENT A SUPPRIMER")
        c.drawString(100, 50, "PIED DE PAGE TEST")
        c.save()
        return buf.getvalue()

    def test_upload_requires_auth(self, client):
        import io
        r = client.post(
            f"{BASE}/me/letterhead",
            files={"file": ("model.png", io.BytesIO(self._png_bytes()), "image/png")},
        )
        assert r.status_code == 401

    def test_upload_png_succeeds_and_activates_letterhead(self, client, auth_headers):
        import io
        client.get(f"{BASE}/me", headers=auth_headers)
        r = client.post(
            f"{BASE}/me/letterhead",
            files={"file": ("model.png", io.BytesIO(self._png_bytes()), "image/png")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["use_letterhead"] is True
        assert body["letterhead_url"].endswith(".png")

    def test_upload_pdf_is_converted_to_real_png(self, client, auth_headers):
        """Le bug historique stockait les octets PDF bruts renommés .png.
        Désormais le fichier stocké doit être un vrai PNG (signature magique)."""
        import io, os
        client.get(f"{BASE}/me", headers=auth_headers)
        r = client.post(
            f"{BASE}/me/letterhead",
            files={"file": ("model.pdf", io.BytesIO(self._pdf_bytes()), "application/pdf")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        rel = r.json()["letterhead_url"].replace("/static/uploads/", "")
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        stored = os.path.join(backend_dir, "static", "uploads", rel)
        with open(stored, "rb") as f:
            magic = f.read(8)
        assert magic == b"\x89PNG\r\n\x1a\n"
        assert not magic.startswith(b"%PDF")

    def test_strip_body_blanks_the_middle_band(self, client, auth_headers):
        """strip_body=true : la bande centrale devient blanche, l'en-tête (bande
        haute) garde sa couleur d'origine."""
        import io, os
        from PIL import Image
        client.get(f"{BASE}/me", headers=auth_headers)
        colored = self._png_bytes(width=100, height=200, color=(200, 30, 30))
        r = client.post(
            f"{BASE}/me/letterhead",
            files={"file": ("filled.png", io.BytesIO(colored), "image/png")},
            data={"strip_body": "true", "header_pct": "20", "footer_pct": "15"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        rel = r.json()["letterhead_url"].replace("/static/uploads/", "")
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        stored = os.path.join(backend_dir, "static", "uploads", rel)
        img = Image.open(stored).convert("RGB")
        w, h = img.size
        assert img.getpixel((w // 2, int(h * 0.10))) == (200, 30, 30)
        assert img.getpixel((w // 2, int(h * 0.50))) == (255, 255, 255)
        assert img.getpixel((w // 2, int(h * 0.95))) == (200, 30, 30)

    def test_corrupt_pdf_returns_400_not_500(self, client, auth_headers):
        import io
        client.get(f"{BASE}/me", headers=auth_headers)
        r = client.post(
            f"{BASE}/me/letterhead",
            files={"file": ("bad.pdf", io.BytesIO(b"not a real pdf"), "application/pdf")},
            headers=auth_headers,
        )
        assert r.status_code == 400

    def test_delete_letterhead_via_put_me(self, client, auth_headers):
        """La suppression passe par PUT /me (letterhead_path=null) — vérifie que le
        backend l'accepte bien, c'est ce que le nouveau bouton frontend appellera."""
        import io
        client.get(f"{BASE}/me", headers=auth_headers)
        up = client.post(
            f"{BASE}/me/letterhead",
            files={"file": ("model.png", io.BytesIO(self._png_bytes()), "image/png")},
            headers=auth_headers,
        )
        assert up.status_code == 200
        r = client.put(
            f"{BASE}/me",
            json={"letterhead_path": None, "use_letterhead": False},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["use_letterhead"] is False
        assert body["letterhead_path"] in (None, "")
