"""Integration proof for the dedicated SuperAdmin WebAuthn control-plane step-up."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend import models
from backend.models_platform_passkey import PlatformPasskeyCredential
from backend.services.mobile_biometric import WEBAUTHN_ORIGIN


@pytest.fixture
def with_superadmin_env(dentiste):
    with patch("backend.platform_access.settings.PLATFORM_CONTROL_PLANE_ENABLED", True), patch(
        "backend.platform_access.settings.SUPERADMIN_USER_ID", dentiste.id
    ):
        yield


def _web_headers(client, user) -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200
    return {
        "Authorization": f"Bearer {login.json()['access_token']}",
        "Origin": WEBAUTHN_ORIGIN,
    }


def test_platform_passkey_enrollment_sets_httponly_proof_and_unlocks_mutation(
    client,
    db,
    dentiste,
    with_superadmin_env,
):
    headers = _web_headers(client, dentiste)

    status = client.get("/api/superadmin/passkey/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["enrolled"] is False
    assert status.json()["step_up_valid"] is False

    options = client.post("/api/superadmin/passkey/registration/options", headers=headers)
    assert options.status_code == 200
    challenge_id = options.json()["challenge_id"]
    assert len(challenge_id) == 36

    verification = SimpleNamespace(
        credential_id=b"platform-credential-id",
        credential_public_key=b"platform-public-key",
        sign_count=0,
        credential_device_type="single_device",
        credential_backed_up=False,
    )
    with patch("webauthn.verify_registration_response", return_value=verification):
        verified = client.post(
            "/api/superadmin/passkey/registration/verify",
            headers=headers,
            json={
                "challenge_id": challenge_id,
                "credential": {
                    "id": "fake-browser-credential",
                    "response": {"transports": ["internal"]},
                },
            },
        )

    assert verified.status_code == 200
    assert "access_token" not in verified.json()
    set_cookie = verified.headers.get("set-cookie", "").lower()
    assert "platform_step_up=" in set_cookie
    assert "httponly" in set_cookie
    assert "secure" in set_cookie
    assert "samesite=strict" in set_cookie
    assert "path=/api/superadmin" in set_cookie

    credential = db.query(PlatformPasskeyCredential).filter(
        PlatformPasskeyCredential.user_id == dentiste.id
    ).one()
    assert credential.transports == ["internal"]

    audit = db.query(models.AuditLog).filter(
        models.AuditLog.action == "SUPERADMIN_PASSKEY_REGISTER",
        models.AuditLog.user_id == dentiste.id,
    ).one()
    assert audit.employer_id is None
    assert audit.severity == "CRITICAL"

    # The test transport is HTTP, so a correctly Secure cookie is deliberately
    # not replayed automatically by the cookie jar. Inject the exact server-issued
    # proof to exercise the real dependency without weakening production flags.
    step_up = verified.cookies.get("platform_step_up")
    assert step_up

    status_with_proof = client.get(
        "/api/superadmin/passkey/status",
        headers={
            **headers,
            "Cookie": f"platform_step_up={step_up}",
        },
    )
    assert status_with_proof.status_code == 200
    assert status_with_proof.json()["enrolled"] is True
    assert status_with_proof.json()["step_up_valid"] is True

    mutation = client.post(
        "/api/superadmin/clients/999999/validate",
        headers={
            "Authorization": headers["Authorization"],
            "Cookie": f"platform_step_up={step_up}",
        },
    )
    assert mutation.status_code == 404


def test_platform_passkey_routes_reject_non_superadmin(client, dentiste):
    headers = _web_headers(client, dentiste)
    response = client.get("/api/superadmin/passkey/status", headers=headers)
    assert response.status_code == 403
