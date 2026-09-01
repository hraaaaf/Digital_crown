from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUTH_SOURCE = ROOT / "backend" / "routers" / "auth.py"


def test_google_oauth_uses_https_loopback_on_secure_cabinet_runtime() -> None:
    source = AUTH_SOURCE.read_text(encoding="utf-8")

    assert '_GOOGLE_LOCAL_HTTPS_ORIGIN = "https://127.0.0.1:8005"' in source
    assert 'os.getenv("DIGITALCROWN_ENABLE_HTTPS", "false")' in source
    assert 'return f"{_google_local_origin()}/api/auth/google/callback"' in source


def test_google_callback_stays_on_same_https_loopback_origin() -> None:
    source = AUTH_SOURCE.read_text(encoding="utf-8")

    assert "if _cabinet_https_enabled():" in source
    assert "frontend_url = _GOOGLE_LOCAL_HTTPS_ORIGIN" in source
    assert '"redirect_uri": _google_redirect_uri(),' in source


def test_legacy_http_loopback_remains_only_as_non_https_fallback() -> None:
    source = AUTH_SOURCE.read_text(encoding="utf-8")

    assert '_GOOGLE_LOCAL_HTTP_ORIGIN = "http://127.0.0.1:8005"' in source
    assert 'return _GOOGLE_LOCAL_HTTPS_ORIGIN if _cabinet_https_enabled() else _GOOGLE_LOCAL_HTTP_ORIGIN' in source
