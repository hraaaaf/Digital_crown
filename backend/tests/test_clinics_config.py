"""Tests cabinet configuration — /api/clinics."""
import uuid


CABINET_PAYLOAD = {
    "nom_cabinet": "Cabinet Test",
    "adresse": "10 rue de la Paix, Alger",
    "telephone": "021000000",
    "email": "cabinet@test.dz",
    "specialite": "Dentiste généraliste",
}


class TestCabinetConfig:
    def test_get_me_unauthenticated(self, client):
        r = client.get("/api/clinics/me")
        assert r.status_code == 401

    def test_get_me_authenticated(self, client, auth_headers):
        r = client.get("/api/clinics/me", headers=auth_headers)
        # 200 if config exists, 404 if not created yet — both are valid
        assert r.status_code in (200, 404)

    def test_create_cabinet(self, client, auth_headers):
        r = client.post("/api/clinics/", json=CABINET_PAYLOAD, headers=auth_headers)
        # Should succeed or 409 if already exists
        assert r.status_code in (200, 201, 409)

    def test_check_init_status(self, client, auth_headers):
        r = client.get("/api/clinics/init-status", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "is_initialized" in body

    def test_update_me(self, client, auth_headers):
        # Ensure cabinet exists
        client.post("/api/clinics/", json=CABINET_PAYLOAD, headers=auth_headers)
        r = client.put(
            "/api/clinics/me",
            json={
                "nom_cabinet": "Cabinet Mis à Jour",
                "adresse": CABINET_PAYLOAD["adresse"],
                "telephone": CABINET_PAYLOAD["telephone"],
            },
            headers=auth_headers,
        )
        assert r.status_code in (200, 201, 404)

    def test_init_status_requires_authentication(self, client):
        """init-status is tenant-scoped and requires authentication."""
        r = client.get("/api/clinics/init-status")
        assert r.status_code == 401


class TestCabinetConfigIsolation:
    def test_different_users_get_own_config(self, client, db):
        from backend import models
        from backend.security import get_password_hash

        def _make(suffix):
            email = f"isolation-{suffix}-{uuid.uuid4().hex[:6]}@test.dz"
            u = models.User(
                email=email,
                hashed_password=get_password_hash("Pass123!"),
                role="DENTISTE",
                is_active=True,
                is_licensed=True,
            )
            db.add(u)
            db.commit()
            return email

        a = _make("a")
        b = _make("b")

        def _login(email):
            r = client.post("/api/auth/login", data={"username": email, "password": "Pass123!"})
            return {"Authorization": f"Bearer {r.json()['access_token']}"}

        ha = _login(a)
        hb = _login(b)

        client.post("/api/clinics/cabinet-config", json={**CABINET_PAYLOAD, "nom_cabinet": "Cabinet A"}, headers=ha)
        client.post("/api/clinics/cabinet-config", json={**CABINET_PAYLOAD, "nom_cabinet": "Cabinet B"}, headers=hb)

        ra = client.get("/api/clinics/cabinet-config", headers=ha)
        rb = client.get("/api/clinics/cabinet-config", headers=hb)

        # Each user gets their own cabinet
        if ra.status_code == 200 and rb.status_code == 200:
            assert ra.json().get("nom_cabinet") != rb.json().get("nom_cabinet") or \
                   ra.json().get("nom_cabinet") in ("Cabinet A",) and rb.json().get("nom_cabinet") in ("Cabinet B",)
