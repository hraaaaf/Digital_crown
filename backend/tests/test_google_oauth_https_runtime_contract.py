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


def test_google_oauth_authorize_binds_state_to_http_only_cookie(client, monkeypatch) -> None:
    from urllib.parse import parse_qs, urlparse
    from backend.routers import auth

    monkeypatch.setattr(auth.settings, "GOOGLE_CLIENT_ID", "synthetic-client")
    response = client.get("/api/auth/google/authorize", follow_redirects=False)

    assert response.status_code in {302, 307}
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    assert state
    assert client.cookies.get("google_oauth_state") == state
    assert "httponly" in response.headers["set-cookie"].lower()


def test_google_oauth_callback_rejects_state_mismatch_before_token_exchange(client, monkeypatch) -> None:
    from backend.routers import auth

    monkeypatch.setattr(auth.settings, "GOOGLE_CLIENT_ID", "synthetic-client")
    authorize = client.get("/api/auth/google/authorize", follow_redirects=False)
    assert authorize.status_code in {302, 307}

    response = client.get(
        "/api/auth/google/callback?code=synthetic-code&state=wrong-state",
        follow_redirects=False,
    )
    assert response.status_code in {302, 307}
    assert "google_state_invalid" in response.headers["location"]


def test_google_oauth_callback_rejects_missing_state_before_token_exchange(client, monkeypatch) -> None:
    from backend.routers import auth

    monkeypatch.setattr(auth.settings, "GOOGLE_CLIENT_ID", "synthetic-client")
    response = client.get(
        "/api/auth/google/callback?code=synthetic-code",
        follow_redirects=False,
    )

    assert response.status_code in {302, 307}
    assert "google_state_invalid" in response.headers["location"]


def test_google_oauth_success_consumes_state_cookie_once(client, monkeypatch, dentiste) -> None:
    from urllib.parse import parse_qs, urlparse
    from backend.routers import auth

    monkeypatch.setattr(auth.settings, "GOOGLE_CLIENT_ID", "synthetic-client")
    monkeypatch.setattr(auth.settings, "GOOGLE_CLIENT_SECRET", "synthetic-secret")

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, data):
            return FakeResponse(200, {"access_token": "google-access"})

        async def get(self, url, headers):
            return FakeResponse(200, {"email": dentiste.email, "name": dentiste.nom_complet})

    monkeypatch.setattr(auth.httpx, "AsyncClient", FakeAsyncClient)

    authorize = client.get("/api/auth/google/authorize", follow_redirects=False)
    assert authorize.status_code in {302, 307}
    state = parse_qs(urlparse(authorize.headers["location"]).query)["state"][0]
    assert client.cookies.get("google_oauth_state") == state

    callback = client.get(
        f"/api/auth/google/callback?code=synthetic-code&state={state}",
        follow_redirects=False,
    )

    assert callback.status_code in {302, 307}
    assert "google=success" in callback.headers["location"]
    assert client.cookies.get("google_oauth_state") is None
    assert "google_oauth_state=" in callback.headers.get("set-cookie", "")
