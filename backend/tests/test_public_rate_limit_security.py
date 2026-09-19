from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

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
