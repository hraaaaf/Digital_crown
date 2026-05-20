"""
Tests: RBAC — secrétaire sans permission bloquée, token invalide rejeté,
et confirmation que le bypass admin a bien été supprimé.
"""
from backend import models
from backend.security import get_password_hash


def _make_user(db, email: str, role: str = "DENTISTE", permissions: dict = None, employer_id: int = None):
    u = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role=role,
        nom_complet="Test",
        is_active=True,
        permissions=permissions or {},
        employer_id=employer_id,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


def _token(client, email: str) -> str:
    r = client.post("/api/auth/login", data={"username": email, "password": "TestPass123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# --- Secrétaire avec permission ---

def test_secretaire_can_read_patients_with_permission(client, db):
    boss = _make_user(db, "boss-rbac1@test.ma")
    sec = _make_user(db, "sec-rbac1@test.ma", role="SECRETAIRE",
                     permissions={"patients": True}, employer_id=boss.id)
    tok = _token(client, sec.email)
    resp = client.get("/api/patients/", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200


def test_secretaire_blocked_without_permission(client, db):
    boss = _make_user(db, "boss-rbac2@test.ma")
    sec = _make_user(db, "sec-rbac2@test.ma", role="SECRETAIRE",
                     permissions={}, employer_id=boss.id)
    tok = _token(client, sec.email)
    resp = client.get("/api/patients/", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403


# --- Accès non authentifié ---

def test_unauthenticated_request_rejected(client):
    assert client.get("/api/patients/").status_code == 401


def test_invalid_token_rejected(client):
    resp = client.get("/api/patients/", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401


# --- Suppression du bypass admin ---

def test_sync_supabase_fails_without_supabase_config(client, db):
    """Le bypass admin@digitalcrown.com doit retourner 500, pas un token."""
    from backend.config import settings
    original = settings.SUPABASE_URL
    settings.SUPABASE_URL = None
    try:
        resp = client.post("/api/auth/sync-supabase", json={
            "email": "admin@digitalcrown.com",
            "access_token": "fake_token"
        })
        assert resp.status_code == 500
        assert "token" not in resp.json()
    finally:
        settings.SUPABASE_URL = original
