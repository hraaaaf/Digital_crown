"""Tests routers/superadmin.py — superadmin guard + client management."""
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def superadmin_headers(client, dentiste):
    """Auth headers for the dentiste fixture (used as superadmin when env is patched)."""
    r = client.post(
        "/api/auth/login",
        data={"username": dentiste.email, "password": "TestPass123!"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def with_superadmin_env(dentiste):
    """Patch the module-level _SUPERADMIN_EMAIL to match the dentiste fixture."""
    with patch("backend.routers.superadmin._SUPERADMIN_EMAIL", dentiste.email.lower()):
        yield


# ── access guard ──────────────────────────────────────────────────────────────

class TestSuperadminGuard:
    def test_get_clients_requires_auth(self, client):
        r = client.get("/api/superadmin/clients")
        assert r.status_code == 401

    def test_regular_user_gets_403(self, client, auth_headers):
        # auth_headers user is NOT a superadmin
        r = client.get("/api/superadmin/clients", headers=auth_headers)
        assert r.status_code == 403

    def test_validate_client_requires_auth(self, client):
        r = client.post("/api/superadmin/clients/1/validate")
        assert r.status_code == 401

    def test_grant_license_regular_user_403(self, client, auth_headers):
        r = client.post("/api/superadmin/clients/1/grant-license?action=1m", headers=auth_headers)
        assert r.status_code == 403

    def test_archive_regular_user_403(self, client, auth_headers):
        r = client.patch("/api/superadmin/clients/1/archive", headers=auth_headers)
        assert r.status_code == 403

    def test_suspend_regular_user_403(self, client, auth_headers):
        r = client.patch("/api/superadmin/clients/1/suspend", headers=auth_headers)
        assert r.status_code == 403

    def test_set_plan_regular_user_403(self, client, auth_headers):
        r = client.patch("/api/superadmin/clients/1/plan?plan=GOLD", headers=auth_headers)
        assert r.status_code == 403

    def test_notes_regular_user_403(self, client, auth_headers):
        r = client.patch(
            "/api/superadmin/clients/1/notes",
            json={"internal_notes": "test"},
            headers=auth_headers,
        )
        assert r.status_code == 403

    def test_license_history_regular_user_403(self, client, auth_headers):
        r = client.get("/api/superadmin/clients/1/license-history", headers=auth_headers)
        assert r.status_code == 403


# ── superadmin operations ─────────────────────────────────────────────────────

class TestSuperadminOperations:
    def test_list_clients_returns_list(
        self, client, superadmin_headers, with_superadmin_env
    ):
        r = client.get("/api/superadmin/clients", headers=superadmin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_validate_client_404_on_unknown(
        self, client, superadmin_headers, with_superadmin_env
    ):
        r = client.post(
            "/api/superadmin/clients/999999/validate",
            headers=superadmin_headers,
        )
        assert r.status_code == 404

    def test_validate_client_success(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="newdentist_sa@cabinet.ma",
            nom_complet="New Dentist",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=False,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.post(
            f"/api/superadmin/clients/{new_user.id}/validate",
            headers=superadmin_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_grant_license_invalid_action_returns_400(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="granttest_sa@cabinet.ma",
            nom_complet="Grant Test",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.post(
            f"/api/superadmin/clients/{new_user.id}/grant-license?action=invalid",
            headers=superadmin_headers,
        )
        assert r.status_code == 400

    def test_grant_license_1m(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="grant1m_sa@cabinet.ma",
            nom_complet="Grant 1M",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.post(
            f"/api/superadmin/clients/{new_user.id}/grant-license?action=1m",
            headers=superadmin_headers,
        )
        assert r.status_code == 200
        assert "license_expires_at" in r.json()

    def test_grant_license_revoke(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="revoke_sa@cabinet.ma",
            nom_complet="Revoke Test",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
            is_licensed=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.post(
            f"/api/superadmin/clients/{new_user.id}/grant-license?action=revoke",
            headers=superadmin_headers,
        )
        assert r.status_code == 200

    def test_archive_client(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="archive_sa@cabinet.ma",
            nom_complet="Archive Test",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.patch(
            f"/api/superadmin/clients/{new_user.id}/archive",
            headers=superadmin_headers,
        )
        assert r.status_code == 200
        assert "is_archived" in r.json()

    def test_suspend_client(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="suspend_sa@cabinet.ma",
            nom_complet="Suspend Test",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.patch(
            f"/api/superadmin/clients/{new_user.id}/suspend",
            headers=superadmin_headers,
        )
        assert r.status_code == 200

    def test_set_plan_success(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="plan_sa@cabinet.ma",
            nom_complet="Plan Test",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
            subscription_plan="GOLD",
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.patch(
            f"/api/superadmin/clients/{new_user.id}/plan?plan=ELITE",
            headers=superadmin_headers,
        )
        assert r.status_code == 200
        assert r.json()["subscription_plan"] == "ELITE"

        db.refresh(new_user)
        assert new_user.subscription_plan == "ELITE"

    def test_set_plan_invalid_value_returns_400(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="planbad_sa@cabinet.ma",
            nom_complet="Plan Bad Test",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.patch(
            f"/api/superadmin/clients/{new_user.id}/plan?plan=PLATINUM",
            headers=superadmin_headers,
        )
        assert r.status_code == 400

    def test_set_plan_404_on_unknown(
        self, client, superadmin_headers, with_superadmin_env
    ):
        r = client.patch(
            "/api/superadmin/clients/999999/plan?plan=GOLD",
            headers=superadmin_headers,
        )
        assert r.status_code == 404

    def test_list_clients_includes_subscription_plan(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="planlist_sa@cabinet.ma",
            nom_complet="Plan List Test",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
            subscription_plan="PREMIUM",
        )
        db.add(new_user)
        db.commit()

        r = client.get("/api/superadmin/clients", headers=superadmin_headers)
        assert r.status_code == 200
        found = next((c for c in r.json() if c["email"] == "planlist_sa@cabinet.ma"), None)
        assert found is not None
        assert found["subscription_plan"] == "PREMIUM"

    def test_update_notes(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="notes_sa@cabinet.ma",
            nom_complet="Notes Test",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.patch(
            f"/api/superadmin/clients/{new_user.id}/notes",
            json={"internal_notes": "VIP client, renouvellement imminent"},
            headers=superadmin_headers,
        )
        assert r.status_code == 200
        assert r.json()["internal_notes"] == "VIP client, renouvellement imminent"

    def test_license_history_empty(
        self, client, db, superadmin_headers, with_superadmin_env
    ):
        from backend import models
        new_user = models.User(
            email="history_sa@cabinet.ma",
            nom_complet="History Test",
            hashed_password="$2b$12$dummy",
            role=models.UserRole.DENTISTE,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        r = client.get(
            f"/api/superadmin/clients/{new_user.id}/license-history",
            headers=superadmin_headers,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_trial_code(
        self, client, superadmin_headers, with_superadmin_env
    ):
        r = client.post(
            "/api/superadmin/trial-codes",
            json={
                "email": "demo@cabinet.ma",
                "nom_complet": "Dr Demo",
                "cabinet_name": "Cabinet Demo",
                "trial_days": 30,
                "expires_in_days": 14,
            },
            headers=superadmin_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "demo@cabinet.ma"
        assert body["code"].startswith("DC-")
        assert "/activate?code=" in body["activation_url"]

    def test_revoke_trial_code(
        self, client, db, superadmin_headers, with_superadmin_env, dentiste
    ):
        from backend import models

        code = models.TrialActivationCode(
            code="DC-TEST-REVOKE",
            email="revoke-code@cabinet.ma",
            trial_days=30,
            expires_at=datetime.utcnow() + timedelta(days=10),
            created_by_admin_id=dentiste.id,
        )
        db.add(code)
        db.commit()
        db.refresh(code)

        r = client.post(
            f"/api/superadmin/trial-codes/{code.id}/revoke",
            headers=superadmin_headers,
        )
        assert r.status_code == 200
        assert r.json()["revoked_at"] is not None
