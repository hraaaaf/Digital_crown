"""Tests d'intégration — endpoints /api/auth/"""

import pytest
from pydantic import ValidationError

from backend.schemas.auth import RefreshRequest, UserSignup


class TestLogin:
    def test_login_success_returns_tokens(self, client, dentiste):
        resp = client.post(
            "/api/auth/login",
            data={"username": dentiste.email, "password": "TestPass123!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, dentiste):
        resp = client.post(
            "/api/auth/login",
            data={"username": dentiste.email, "password": "mauvais"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post(
            "/api/auth/login",
            data={"username": "fantome@inexistant.ma", "password": "abc"},
        )
        assert resp.status_code == 401

    def test_login_inactive_user(self, client, db):
        from backend.tests.conftest import make_user
        inactive = make_user(db, password="Pass123!", active=False)
        resp = client.post(
            "/api/auth/login",
            data={"username": inactive.email, "password": "Pass123!"},
        )
        assert resp.status_code == 403


class TestMe:
    def test_me_returns_user(self, client, auth_headers, dentiste):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == dentiste.email

    def test_me_without_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_bad_token(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer fake.token.here"})
        assert resp.status_code == 401


class TestRefresh:
    def test_refresh_returns_new_tokens(self, client, dentiste, refresh_token):
        resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        # Les nouveaux tokens doivent être différents (rotation)
        assert body["refresh_token"] != refresh_token

    def test_refresh_old_token_is_revoked(self, client, dentiste, refresh_token):
        """Après une rotation, l'ancien refresh token ne doit plus fonctionner."""
        client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        resp2 = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert resp2.status_code == 401

    def test_refresh_with_access_token_fails(self, client, dentiste, auth_headers):
        """Un access token ne doit pas être accepté comme refresh token."""
        access = auth_headers["Authorization"].split(" ")[1]
        resp = client.post("/api/auth/refresh", json={"refresh_token": access})
        assert resp.status_code == 401

    def test_refresh_with_garbage_fails(self, client):
        resp = client.post("/api/auth/refresh", json={"refresh_token": "garbage"})
        assert resp.status_code == 401


class TestLogout:
    def test_logout_revokes_access_token(self, client, dentiste):
        login = client.post(
            "/api/auth/login",
            data={"username": dentiste.email, "password": "TestPass123!"},
        )
        tokens = login.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Logout
        resp = client.post(
            "/api/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers=headers,
        )
        assert resp.status_code == 204

        # L'access token ne doit plus fonctionner
        me = client.get("/api/auth/me", headers=headers)
        assert me.status_code == 401

    def test_logout_requires_auth(self, client, dentiste, refresh_token):
        # refresh_token fixture logs in via TestClient, setting access_token cookie;
        # clear it to simulate a truly unauthenticated request.
        client.cookies.clear()
        resp = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
        assert resp.status_code == 401


class TestSignup:
    def test_signup_requires_legal_consent(self, client):
        resp = client.post(
            "/api/auth/signup",
            json={
                "email": "new-client@cabinet.ma",
                "password": "Pass123!",
                "nom_complet": "Dr New Client",
                "accept_terms": False,
                "accept_privacy": True,
            },
        )
        assert resp.status_code == 400

    def test_signup_with_legal_consent_creates_pending_user(self, client):
        resp = client.post(
            "/api/auth/signup",
            json={
                "email": "new-client@cabinet.ma",
                "password": "Pass123!",
                "nom_complet": "Dr New Client",
                "accept_terms": True,
                "accept_privacy": True,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "new-client@cabinet.ma"
        assert body["is_active"] is False
        assert body["is_licensed"] is False


class TestUrlencodedBodyLimit:
    def test_oversized_urlencoded_login_is_rejected_before_form_parser(self, client):
        body = "username=" + ("a" * (64 * 1024)) + "&password=x"
        response = client.post(
            "/api/auth/login",
            content=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 413

    def test_normal_urlencoded_login_still_reaches_auth_handler(self, client):
        response = client.post(
            "/api/auth/login",
            content="username=missing%40example.invalid&password=x",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 401


def test_signup_firebase_payload_excludes_local_contact_and_db_identifiers():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "routers" / "auth.py").read_text(encoding="utf-8")
    start = source.index("firebase_db.collection('pending_clients')")
    payload_block = source[start:start + 700]

    assert '"email": req.email' in payload_block
    assert '"nom_complet": req.nom_complet' in payload_block
    assert '"telephone_mobile"' not in payload_block
    assert '"adresse_complete"' not in payload_block
    assert '"local_user_id"' not in payload_block


def test_signup_and_refresh_public_payloads_are_bounded():
    with pytest.raises(ValidationError):
        UserSignup(
            email="new@example.com",
            password="StrongPass123!",
            nom_complet="N" * 161,
            accept_terms=True,
            accept_privacy=True,
        )
    with pytest.raises(ValidationError):
        UserSignup(
            email="new@example.com",
            password="StrongPass123!",
            nom_complet="Dr Test",
            telephone_mobile="1" * 41,
            accept_terms=True,
            accept_privacy=True,
        )
    with pytest.raises(ValidationError):
        UserSignup(
            email="new@example.com",
            password="StrongPass123!",
            nom_complet="Dr Test",
            adresse_complete="A" * 501,
            accept_terms=True,
            accept_privacy=True,
        )
    with pytest.raises(ValidationError):
        RefreshRequest(refresh_token="x" * 4097)


def test_signup_is_rate_limited_and_google_callback_checks_team_approval():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "routers" / "auth.py").read_text(encoding="utf-8")
    signup_start = source.index("async def signup_client")
    signup_block = source[signup_start:signup_start + 900]
    assert 'check_rate_limit(request, scope="signup")' in signup_block

    callback_start = source.index("async def google_callback")
    callback_block = source[callback_start:]
    assert 'getattr(user, "employer_id", None) is not None and approval != "approved"' in callback_block


def test_signup_pending_clients_cloud_payload_is_minimized():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "routers" / "auth.py").read_text(encoding="utf-8")
    start = source.index("firebase_db.collection('pending_clients')")
    block = source[start:start + 520]

    for required in ['"email": req.email', '"nom_complet": req.nom_complet', '"status": "pending"', '"created_at":']:
        assert required in block

    for forbidden in [
        "telephone_mobile",
        "adresse_complete",
        '"user_id"',
        '"id": new_user.id',
        "hashed_password",
    ]:
        assert forbidden not in block
