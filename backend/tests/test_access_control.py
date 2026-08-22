"""
Tests RBAC — matrice legacy fail-closed, permissions explicites et auth invalide.
"""
import pytest
from backend import models
from backend.security import get_password_hash


def _make_user(db, email: str, role: str = "DENTISTE", permissions: dict = None, employer_id: int = None):
    u = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role=role,
        nom_complet="Test",
        is_active=True,
        is_licensed=True,
        permissions=permissions or {},
        employer_id=employer_id,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


def _token(client, email: str) -> str:
    r = client.post("/api/auth/login", data={"username": email, "password": "TestPass123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# --- Secrétaire : fallback legacy + matrice explicite ---

def test_secretaire_can_read_patients_with_permission(client, db):
    boss = _make_user(db, "boss-rbac1@test.ma")
    sec = _make_user(db, "sec-rbac1@test.ma", role="SECRETAIRE",
                     permissions={"patients": True}, employer_id=boss.id)
    tok = _token(client, sec.email)
    resp = client.get("/api/patients/", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200


def test_secretaire_legacy_empty_permissions_can_read_patients(client, db):
    boss = _make_user(db, "boss-rbac2@test.ma")
    sec = _make_user(db, "sec-rbac2@test.ma", role="SECRETAIRE",
                     permissions={}, employer_id=boss.id)
    tok = _token(client, sec.email)
    resp = client.get("/api/patients/", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200


def test_secretaire_explicit_patient_denial_is_enforced(client, db):
    boss = _make_user(db, "boss-rbac3@test.ma")
    sec = _make_user(db, "sec-rbac3@test.ma", role="SECRETAIRE",
                     permissions={"patients": False}, employer_id=boss.id)
    tok = _token(client, sec.email)
    resp = client.get("/api/patients/", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403


# --- Réglages : permission backend + scoping employeur ---

def _make_owner_config(db, owner, name="Cabinet RBAC"):
    config = models.CabinetConfig(
        owner_id=owner.id,
        nom_cabinet=name,
        nom_praticien=owner.nom_complet or "Dr. Owner",
        is_initialized=True,
    )
    db.add(config); db.commit(); db.refresh(config)
    return config


def test_subaccount_without_settings_cannot_update_owner_clinic(client, db):
    boss = _make_user(db, "boss-settings-deny@test.ma")
    config = _make_owner_config(db, boss, "Cabinet Initial")
    child = _make_user(
        db,
        "child-settings-deny@test.ma",
        role="DENTISTE",
        permissions={"settings": False},
        employer_id=boss.id,
    )
    tok = _token(client, child.email)
    resp = client.put(
        "/api/clinics/me",
        json={"nom_cabinet": "Cabinet Interdit"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 403
    db.refresh(config)
    assert config.nom_cabinet == "Cabinet Initial"
    assert db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == child.id).first() is None


def test_subaccount_with_settings_updates_owner_clinic_only(client, db):
    boss = _make_user(db, "boss-settings-allow@test.ma")
    config = _make_owner_config(db, boss, "Cabinet Initial")
    child = _make_user(
        db,
        "child-settings-allow@test.ma",
        role="DENTISTE",
        permissions={"settings": True},
        employer_id=boss.id,
    )
    tok = _token(client, child.email)
    resp = client.put(
        "/api/clinics/me",
        json={"nom_cabinet": "Cabinet Autorisé"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 200, resp.text
    db.refresh(config)
    assert config.nom_cabinet == "Cabinet Autorisé"
    assert resp.json()["owner_id"] == boss.id
    assert db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == child.id).first() is None


def test_subaccount_without_settings_cannot_upload_logo(client, db):
    import io
    boss = _make_user(db, "boss-settings-logo@test.ma")
    _make_owner_config(db, boss)
    child = _make_user(
        db,
        "child-settings-logo@test.ma",
        role="SECRETAIRE",
        permissions={"settings": False},
        employer_id=boss.id,
    )
    tok = _token(client, child.email)
    resp = client.post(
        "/api/clinics/me/logo",
        files={"file": ("logo.txt", io.BytesIO(b"not-an-image"), "text/plain")},
        headers={"Authorization": f"Bearer {tok}"},
    )
    # Dependency authorization must fail before file-type validation.
    assert resp.status_code == 403


# --- Accès non authentifié ---

def test_unauthenticated_request_rejected(client):
    assert client.get("/api/patients/").status_code == 401


def test_invalid_token_rejected(client):
    resp = client.get("/api/patients/", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401


# --- Suppression du bypass admin ---

@pytest.mark.skip(reason="sync-supabase endpoint removed; SUPABASE_URL no longer in settings")
def test_sync_supabase_fails_without_supabase_config(client, db):
    pass
