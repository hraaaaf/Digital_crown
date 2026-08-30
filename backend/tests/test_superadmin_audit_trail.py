"""Focused proof that privileged Superadmin mutations leave an exact audit trail."""
from unittest.mock import patch
import uuid

import pytest

from backend import models
from backend.security import get_password_hash


@pytest.fixture
def with_superadmin_env(dentiste):
    with patch("backend.platform_access.settings.PLATFORM_CONTROL_PLANE_ENABLED", True), patch(
        "backend.platform_access.settings.SUPERADMIN_USER_ID", dentiste.id
    ):
        yield


def _headers(client, user) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _target_user(db) -> models.User:
    user = models.User(
        email=f"audit-target-{uuid.uuid4().hex[:8]}@cabinet.ma",
        hashed_password=get_password_hash("TargetPass123!"),
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Audit Target",
        is_active=True,
        is_licensed=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_archive_mutation_audit_binds_exact_actor_and_target(
    client,
    db,
    dentiste,
    with_superadmin_env,
):
    target = _target_user(db)
    response = client.patch(
        f"/api/superadmin/clients/{target.id}/archive",
        headers=_headers(client, dentiste),
    )
    assert response.status_code == 200, response.text

    audit = db.query(models.AuditLog).filter(
        models.AuditLog.action == "SUPERADMIN_CLIENT_ARCHIVE",
        models.AuditLog.resource_type == "User",
        models.AuditLog.resource_id == str(target.id),
    ).one()
    assert audit.user_id == dentiste.id
    assert audit.employer_id is None
    assert audit.severity == "WARNING"


def test_trial_creation_audit_never_copies_activation_secret(
    client,
    db,
    dentiste,
    with_superadmin_env,
):
    response = client.post(
        "/api/superadmin/trial-codes",
        headers=_headers(client, dentiste),
        json={
            "email": "trial-audit@cabinet.ma",
            "trial_days": 30,
            "expires_in_days": 14,
            "notes": "commercial note must not enter platform audit details",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    audit = db.query(models.AuditLog).filter(
        models.AuditLog.action == "SUPERADMIN_TRIAL_CREATE",
        models.AuditLog.resource_type == "TrialActivationCode",
        models.AuditLog.resource_id == str(body["id"]),
    ).one()
    assert audit.user_id == dentiste.id
    assert body["code"] not in (audit.details or "")
    assert "commercial note" not in (audit.details or "")
    assert audit.details == "trial_days=30;expires_in_days=14"


def test_notes_audit_records_event_not_sensitive_note_content(
    client,
    db,
    dentiste,
    with_superadmin_env,
):
    target = _target_user(db)
    secret_note = "Confidentiel: ne jamais recopier ceci dans l'audit"
    response = client.patch(
        f"/api/superadmin/clients/{target.id}/notes",
        headers=_headers(client, dentiste),
        json={"internal_notes": secret_note},
    )
    assert response.status_code == 200, response.text

    audit = db.query(models.AuditLog).filter(
        models.AuditLog.action == "SUPERADMIN_CLIENT_NOTES_UPDATE",
        models.AuditLog.resource_id == str(target.id),
    ).one()
    assert audit.user_id == dentiste.id
    assert secret_note not in (audit.details or "")
    assert audit.details == "internal_notes_updated=true"
