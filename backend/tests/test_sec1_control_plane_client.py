import asyncio

import pytest

from backend.config import Settings
from backend.services import license_control_plane_client as client_module
from backend.services.license_control_plane_client import LicenseControlPlaneClient


class _Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class _AsyncClient:
    calls = []
    response = _Response()

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.get("timeout")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def get(self, url, **kwargs):
        self.__class__.calls.append(("GET", url, kwargs))
        return self.__class__.response

    async def post(self, url, **kwargs):
        self.__class__.calls.append(("POST", url, kwargs))
        return self.__class__.response


@pytest.fixture(autouse=True)
def _reset_fake_client():
    _AsyncClient.calls = []
    _AsyncClient.response = _Response()


def test_cabinet_control_plane_url_must_be_https():
    with pytest.raises(ValueError, match="HTTPS"):
        Settings(
            _env_file=None,
            ENVIRONMENT="cabinet",
            LICENSE_CONTROL_PLANE_URL="http://licenses.example.test",
        )

    cfg = Settings(
        _env_file=None,
        ENVIRONMENT="cabinet",
        LICENSE_CONTROL_PLANE_URL="https://licenses.example.test",
    )
    assert cfg.LICENSE_CONTROL_PLANE_URL.startswith("https://")


def test_trial_redemption_sends_only_code_email_and_cabinet_id(monkeypatch):
    monkeypatch.setattr(client_module.httpx, "AsyncClient", _AsyncClient)
    _AsyncClient.response = _Response(
        payload={
            "signed_license": "header.payload.signature",
            "expires_at": "2026-09-27T12:00:00+00:00",
            "feature_set": "GOLD",
            "license_type": "TRIAL",
        }
    )

    result = asyncio.run(
        LicenseControlPlaneClient("https://licenses.example.test").redeem_trial(
            code="dc-abcd-1234-ffff",
            email="Dentist@Example.com",
            cabinet_id="cab-123",
        )
    )

    assert result.license_type == "TRIAL"
    assert len(_AsyncClient.calls) == 1
    method, url, kwargs = _AsyncClient.calls[0]
    assert method == "POST"
    assert url == "https://licenses.example.test/api/public/license-control/activate-trial"
    assert kwargs["json"] == {
        "code": "DC-ABCD-1234-FFFF",
        "email": "dentist@example.com",
        "cabinet_id": "cab-123",
    }
    assert "password" not in kwargs["json"]
    assert "signing" not in str(kwargs).lower()
    assert "firebase" not in str(kwargs).lower()


def test_trial_preview_uses_public_control_plane_surface(monkeypatch):
    monkeypatch.setattr(client_module.httpx, "AsyncClient", _AsyncClient)
    _AsyncClient.response = _Response(
        payload={
            "email": "dentist@example.com",
            "nom_complet": "Dr Test",
            "cabinet_name": "Cabinet Test",
            "trial_days": 30,
            "expires_at": "2026-09-10T00:00:00+00:00",
        }
    )

    result = asyncio.run(
        LicenseControlPlaneClient("https://licenses.example.test").preview_trial("dc-abcd")
    )

    assert result["email"] == "dentist@example.com"
    assert _AsyncClient.calls[0][1] == (
        "https://licenses.example.test/api/public/license-control/trial-code/DC-ABCD"
    )
