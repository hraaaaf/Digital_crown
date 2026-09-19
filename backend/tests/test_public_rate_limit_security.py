from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from backend.schemas.auth import TrialActivationRequest
from backend.utils import rate_limit


class _Request:
    client = SimpleNamespace(host="127.0.0.1")


def _reset_rate_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(rate_limit, "_attempts", {})
    monkeypatch.setattr(rate_limit, "_loaded", True)
    monkeypatch.setattr(rate_limit, "_store_path", lambda: tmp_path / "rate_limit_store.json")


def test_rate_limit_remains_active_if_persistence_fails(monkeypatch, tmp_path):
    _reset_rate_limit(monkeypatch, tmp_path)
    monkeypatch.setattr(rate_limit, "_save", lambda: None)
    request = _Request()

    for _ in range(rate_limit.MAX_ATTEMPTS):
        rate_limit.check_rate_limit(request, scope="test")

    with pytest.raises(HTTPException) as exc:
        rate_limit.check_rate_limit(request, scope="test")
    assert exc.value.status_code == 429


def test_public_superadmin_secret_is_not_accepted_from_query_string():
    source = (
        Path(__file__).resolve().parents[1] / "routers" / "public.py"
    ).read_text(encoding="utf-8")
    assert 'alias="X-Superadmin-Secret"' in source
    assert "hmac.compare_digest" in source
    assert 'def list_demo_requests(secret:' not in source


def test_public_sensitive_routes_are_rate_limited():
    source = (
        Path(__file__).resolve().parents[1] / "routers" / "public.py"
    ).read_text(encoding="utf-8")
    assert 'scope="public_demo_request"' in source
    assert 'scope="trial_code_preview"' in source
    assert 'scope="trial_code_activation"' in source


def test_trial_codes_use_128_bits_of_entropy():
    source = (
        Path(__file__).resolve().parents[1] / "routers" / "superadmin.py"
    ).read_text(encoding="utf-8")
    assert "secrets.token_hex(4)" in source
    assert "for _ in range(4)" in source


def test_trial_activation_public_fields_are_bounded():
    base = {
        "code": "ABCD1234-EFGH5678-IJKL9012-MNOP3456",
        "email": "cabinet@example.com",
        "password": "StrongPass123!",
        "nom_complet": "Dr Test",
        "cabinet_name": "Cabinet Test",
        "accept_terms": True,
        "accept_privacy": True,
    }

    for field, oversized in (
        ("code", "X" * 129),
        ("nom_complet", "N" * 161),
        ("cabinet_name", "C" * 161),
    ):
        with pytest.raises(ValidationError):
            TrialActivationRequest(**{**base, field: oversized})


def test_trial_code_lookup_rejects_oversized_path_input_before_db_query():
    source = (
        Path(__file__).resolve().parents[1] / "routers" / "public.py"
    ).read_text(encoding="utf-8")
    assert "len(normalized) > 128" in source


def test_small_public_json_routes_have_preparse_body_limit():
    source = (
        Path(__file__).resolve().parents[1] / "main.py"
    ).read_text(encoding="utf-8")

    assert "_MAX_PUBLIC_JSON_BODY_BYTES = 64 * 1024" in source
    for path in (
        "/api/auth/signup",
        "/api/auth/refresh",
        "/api/public/demo-request",
        "/api/public/activate-trial",
        "/api/mobile/claim-token",
        "/api/mobile/refresh-token",
    ):
        assert f'"{path}"' in source
    assert 'status_code=411' in source
    assert 'status_code=413' in source
    assert '"Corps JSON trop volumineux"' in source
