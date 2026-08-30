"""Security boundary tests for privileged Superadmin sessions."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import uuid

import pytest
from jose import jwt

from backend.security import ALGORITHM, SECRET_KEY


@pytest.fixture
def with_superadmin_env(dentiste):
    """Enable platform authority and bind it to the test dentist immutable id."""
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
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _mobile_token_for(user) -> str:
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    tenant_id = user.get_employer_id()
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "tenant_id": int(tenant_id),
            "device_id": "superadmin-boundary-test-device",
            "type": "mobile",
            "role": role,
            "jti": f"mobile:{int(tenant_id)}:{int(now.timestamp() * 1_000_000)}:{uuid.uuid4().hex}",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _platform_step_up_token(
    user_id: int,
    *,
    issued_at: datetime | None = None,
    token_type: str = "platform_step_up",
    expires_at: datetime | None = None,
) -> str:
    now = issued_at or datetime.now(timezone.utc)
    exp = expires_at or (datetime.now(timezone.utc) + timedelta(minutes=5))
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": token_type,
            "jti": f"platform-step-up:{uuid.uuid4().hex}",
            "iat": int(now.timestamp()),
            "exp": exp,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def test_superadmin_web_access_token_remains_authorized(client, dentiste, with_superadmin_env):
    response = client.get(
        "/api/superadmin/clients",
        headers=_web_headers(client, dentiste),
    )
    assert response.status_code == 200


def test_superadmin_mobile_token_is_rejected_even_for_owner_identity(
    client,
    dentiste,
    with_superadmin_env,
):
    token = _mobile_token_for(dentiste)
    tenant_id = dentiste.get_employer_id()

    # Device validation belongs to the mobile boundary and is tested elsewhere.
    # Here we prove that even an otherwise valid mobile identity resolving to the
    # immutable Superadmin user cannot cross into the platform control plane.
    with patch(
        "backend.routers.mobile_legacy._decode_mobile_identity",
        return_value=(dentiste, tenant_id, {"type": "mobile"}),
    ):
        response = client.get(
            "/api/superadmin/clients",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Accès plateforme réservé à une session web privilégiée."


def test_superadmin_mutation_requires_step_up(client, dentiste, with_superadmin_env):
    response = client.post(
        "/api/superadmin/clients/999999/validate",
        headers=_web_headers(client, dentiste),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PLATFORM_STEP_UP_REQUIRED"


def test_superadmin_valid_recent_platform_step_up_allows_mutation_to_reach_route(
    client,
    dentiste,
    with_superadmin_env,
):
    headers = _web_headers(client, dentiste)
    headers["X-Platform-Step-Up"] = _platform_step_up_token(dentiste.id)

    response = client.post(
        "/api/superadmin/clients/999999/validate",
        headers=headers,
    )

    # 404 proves the security dependency passed and the request reached the route.
    assert response.status_code == 404


def test_superadmin_step_up_cookie_is_accepted(client, dentiste, with_superadmin_env):
    headers = _web_headers(client, dentiste)
    client.cookies.set("platform_step_up", _platform_step_up_token(dentiste.id), path="/api/superadmin")

    response = client.post(
        "/api/superadmin/clients/999999/validate",
        headers=headers,
    )

    assert response.status_code == 404


def test_superadmin_step_up_must_match_web_identity(client, dentiste, with_superadmin_env):
    headers = _web_headers(client, dentiste)
    headers["X-Platform-Step-Up"] = _platform_step_up_token(dentiste.id + 1000)

    response = client.post(
        "/api/superadmin/clients/999999/validate",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PLATFORM_STEP_UP_IDENTITY_MISMATCH"


def test_superadmin_step_up_rejects_non_platform_token_type(client, dentiste, with_superadmin_env):
    headers = _web_headers(client, dentiste)
    headers["X-Platform-Step-Up"] = _platform_step_up_token(dentiste.id, token_type="mobile")

    response = client.post(
        "/api/superadmin/clients/999999/validate",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PLATFORM_STEP_UP_INVALID_TYPE"


def test_superadmin_step_up_rejects_stale_proof(client, dentiste, with_superadmin_env):
    headers = _web_headers(client, dentiste)
    headers["X-Platform-Step-Up"] = _platform_step_up_token(
        dentiste.id,
        issued_at=datetime.now(timezone.utc) - timedelta(minutes=6),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
    )

    response = client.post(
        "/api/superadmin/clients/999999/validate",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PLATFORM_STEP_UP_EXPIRED"
