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


def test_superadmin_web_access_token_remains_authorized(client, dentiste, with_superadmin_env):
    login = client.post(
        "/api/auth/login",
        data={"username": dentiste.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    response = client.get(
        "/api/superadmin/clients",
        headers={"Authorization": f"Bearer {token}"},
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
