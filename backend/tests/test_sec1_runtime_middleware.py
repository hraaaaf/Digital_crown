import asyncio
import json

from fastapi import Response
from jose import jwt
from starlette.requests import Request

from backend import main
from backend.security import ALGORITHM, SECRET_KEY


def _request(method: str, path: str, token: str | None = None) -> Request:
    headers = []
    if token:
        headers.append((b"authorization", f"Bearer {token}".encode()))
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "raw_path": path.encode(),
            "headers": headers,
            "query_string": b"",
            "scheme": "https",
            "server": ("test", 443),
            "client": ("127.0.0.1", 12345),
        }
    )


async def _next(_request):
    return Response(status_code=204)


def _web_token(email: str = "doctor@example.com") -> str:
    return jwt.encode(
        {"sub": email, "type": "access"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _mobile_token(user_id: int = 7) -> str:
    return jwt.encode(
        {"sub": str(user_id), "type": "mobile"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _json_body(response) -> dict:
    return json.loads(response.body.decode())


def test_web_mutation_is_blocked_by_signed_runtime_authority(monkeypatch):
    async def invalid(_email):
        return False, "invalid_signature_or_claims"

    monkeypatch.setattr(main, "get_user_license_status", invalid)

    response = asyncio.run(
        main.license_check_middleware(
            _request("POST", "/api/patients", _web_token()),
            _next,
        )
    )

    assert response.status_code == 403
    assert _json_body(response)["detail"] == "invalid_signature_or_claims"


def test_mobile_legacy_mutation_is_blocked_by_same_signed_authority(monkeypatch):
    async def invalid(_user_id):
        return False, "SIGNED_LICENSE_REQUIRED"

    monkeypatch.setattr(main, "get_mobile_user_license_status", invalid)

    response = asyncio.run(
        main.license_check_middleware(
            _request("PATCH", "/api/mobile/appointments/12/status", _mobile_token()),
            _next,
        )
    )

    assert response.status_code == 403
    assert _json_body(response)["detail"] == "SIGNED_LICENSE_REQUIRED"


def test_unlicensed_reads_remain_available_in_read_only_mode(monkeypatch):
    async def invalid(_email):
        return False, "SIGNED_LICENSE_REQUIRED"

    monkeypatch.setattr(main, "get_user_license_status", invalid)

    response = asyncio.run(
        main.license_check_middleware(
            _request("GET", "/api/patients", _web_token()),
            _next,
        )
    )

    assert response.status_code == 204


def test_superadmin_surface_bypasses_commercial_gate_only(monkeypatch):
    async def must_not_run(_email):
        raise AssertionError("commercial license lookup must not gate platform control-plane routes")

    monkeypatch.setattr(main, "get_user_license_status", must_not_run)

    response = asyncio.run(
        main.license_check_middleware(
            _request("POST", "/api/superadmin/trial-codes", _web_token()),
            _next,
        )
    )

    assert response.status_code == 204


def test_initial_cabinet_shell_can_be_created_before_license(monkeypatch):
    async def must_not_run(_email):
        raise AssertionError("initial cabinet creation must not require a pre-existing cabinet license")

    monkeypatch.setattr(main, "get_user_license_status", must_not_run)

    response = asyncio.run(
        main.license_check_middleware(
            _request("POST", "/api/clinics", _web_token()),
            _next,
        )
    )

    assert response.status_code == 204
