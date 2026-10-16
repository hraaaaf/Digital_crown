"""CB-00 probe safety checks (synthetic only; does NOT exercise the T2 backend)."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest

path = Path(__file__).resolve().parents[1] / "scripts/ci/crownbot_cb00_t2_read_evidence.py"
spec = importlib.util.spec_from_file_location("cb00_probe", path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.mark.parametrize("url", [
    "https://example.com:443",
    "http://evil.com:8005",
    "http://127.0.0.1:8005/api/admin",
    "http://127.0.0.1:8005?token=x",
    "http://127.0.0.1:8005/#x",
    "http://localhost:8005@other.test:8005",
    "http://localhost:8005",
])
def test_local_origin_only(url):
    if url == "http://localhost:8005":
        assert probe.checked_origin(url) == url
    else:
        with pytest.raises(ValueError):
            probe.checked_origin(url)


def test_redirect_refused():
    assert probe._NoRedirect().redirect_request(
        None, None, 302, "Found", {}, "https://evil.test"
    ) is None


def test_environment_refuses_without_t2(monkeypatch, tmp_path):
    monkeypatch.delenv("DIGITALCROWN_ISOLATED_RUNTIME", raising=False)
    monkeypatch.setenv("T2_USER", "t2-user@example.test")
    monkeypatch.setenv("T2_PASSWORD", "fake")
    monkeypatch.setenv("T2_PATIENT_ID", "1")
    with pytest.raises(ValueError):
        probe.require_t2_environment(SimpleNamespace(
            api="http://127.0.0.1:8005", n=30, out=str(tmp_path/"out.json")
        ))


def test_fail_closed_read_contract():
    valid = {"status": "read", "patient": {"id": 9}, "proposal": None}
    probe.assert_read(200, valid, 9)
    for payload in [
        dict(valid, proposal={"type": "unsafe"}),
        dict(valid, pending_action_id="x"),
        dict(valid, patient={"id": 7}),
    ]:
        with pytest.raises(RuntimeError):
            probe.assert_read(200, payload, 9)


@pytest.mark.parametrize("samples,ratio,expected", [
    ([10, 20, 30], .5, 20),
    ([10, 20, 30], .95, 29),
])
def test_percentile(samples, ratio, expected):
    assert probe.percentile(samples, ratio) == expected


def test_no_redirect_forwarding_network():
    """Local redirect must not forward test bearer token to another endpoint."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    observed = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            observed.append((self.path, self.headers.get("Authorization")))
            if self.path == "/redirect":
                self.send_response(307)
                self.send_header(
                    "Location", f"http://127.0.0.1:{self.server.server_port}/target"
                )
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"read"}')

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with pytest.raises(RuntimeError):
            probe.http_json(
                f"http://127.0.0.1:{server.server_port}/redirect",
                {"messages": ["/patient"]},
                "synthetic-not-real-token",
            )
        assert observed == [("/redirect", "Bearer synthetic-not-real-token")]
    finally:
        server.shutdown()


@pytest.mark.parametrize("enroll,expected_suffixes", [
    (False, ["/api/auth/login"]),
    (True, ["/api/auth/login", "/api/workstation/enroll"]),
])
def test_denied_role_reuses_owner_station_without_enrollment(
    monkeypatch, enroll, expected_suffixes
):
    """A restricted staff user must not attempt the owner-only enrollment route."""
    called = []

    def fake_http(url, data, bearer=None, form=False, anonymous=False):
        called.append(url)
        if url.endswith("/api/auth/login"):
            assert form is True
            return 200, {"access_token": "synthetic-only"}, 1
        if url.endswith("/api/workstation/enroll"):
            assert bearer == "synthetic-only"
            assert data == {"accountPassword": "synthetic-pass"}
            return 200, {"workstationId": "synthetic"}, 1
        raise AssertionError("unexpected endpoint")

    monkeypatch.setattr(probe, "http_json", fake_http)
    assert probe.login(
        "http://127.0.0.1:8005", "t2-denied@example.test",
        "synthetic-pass", enroll_workstation=enroll,
    ) == "synthetic-only"
    assert called == [
        "http://127.0.0.1:8005" + suffix for suffix in expected_suffixes
    ]


@pytest.mark.parametrize("same_404", [True, False])
def test_existing_foreign_patient_must_match_unknown_404(monkeypatch, tmp_path, same_404):
    """No leak if a valid OTHER-tenant patient exists: indistinguishable 404."""
    vals = {
        "DIGITALCROWN_ISOLATED_RUNTIME": "1",
        "T2_USER": "t2-dentist@example.test",
        "T2_PASSWORD": "fictional-only",
        "T2_PATIENT_ID": "1",
        "T2_FOREIGN_PATIENT_ID": "3",
        "T2_UNKNOWN_PATIENT_ID": "10003",
        "T2_SOURCE_HEAD": "synthetic-test-head",
    }
    for name, value in vals.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("T2_DENIED_USER", raising=False)
    monkeypatch.delenv("T2_DENIED_PASSWORD", raising=False)
    monkeypatch.setattr(probe, "login", lambda *args: "fictional-only-token")
    seen = []

    def fake_http(url, data, bearer=None, form=False, anonymous=False):
        messages = data["messages"]
        seen.append(messages)
        if anonymous:
            return 401, {"detail": "Unauthorized"}, 1.0
        if messages == ["/patient"]:
            return 200, {"status": "clarification", "proposal": None}, 1.0
        if messages == ["/patient", "1"]:
            return 200, {"status": "read", "proposal": None, "patient": {"id": 1}}, 1.0
        if messages == ["/patient", "3"]:
            return 404, {"detail": "Patient introuvable."}, 1.0
        if messages == ["/patient", "10003"]:
            return 404, {
                "detail": "Patient introuvable." if same_404 else "Patient externe"
            }, 1.0
        raise AssertionError("unexpected request")

    monkeypatch.setattr(probe, "http_json", fake_http)
    args = SimpleNamespace(api="http://127.0.0.1:8005", n=30,
                           out=str(tmp_path / "evidence.json"))
    if same_404:
        result = probe.run(args)
        assert result["checks"]["foreign_patient_404"] == "PASS"
        assert result["checks"]["foreign_unknown_same_404"] == "PASS"
        assert ["/patient", "3"] in seen and ["/patient", "10003"] in seen
    else:
        with pytest.raises(RuntimeError, match="tenant 404 differs"):
            probe.run(args)
        assert not (tmp_path / "evidence.json").exists()


def test_missing_foreign_pair_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "1")
    monkeypatch.setenv("T2_USER", "t2-dentist@example.test")
    monkeypatch.setenv("T2_PASSWORD", "fake")
    monkeypatch.setenv("T2_PATIENT_ID", "1")
    monkeypatch.setenv("T2_FOREIGN_PATIENT_ID", "3")
    monkeypatch.delenv("T2_UNKNOWN_PATIENT_ID", raising=False)
    with pytest.raises(ValueError, match="both foreign and unknown"):
        probe.require_t2_environment(SimpleNamespace(
            api="http://127.0.0.1:8005", n=30, out=str(tmp_path / "out.json")
        ))


def test_owner_tenant_404_precedes_restricted_login_cookie_change(monkeypatch, tmp_path):
    """Role login changes shared cookie; foreign 404 must use owner session."""
    env = {
        "DIGITALCROWN_ISOLATED_RUNTIME": "1",
        "T2_USER": "t2-owner@example.test", "T2_PASSWORD": "fictional",
        "T2_PATIENT_ID": "1", "T2_FOREIGN_PATIENT_ID": "3",
        "T2_UNKNOWN_PATIENT_ID": "10003",
        "T2_DENIED_USER": "t2-restricted@example.test",
        "T2_DENIED_PASSWORD": "fictional",
        "T2_DENIED_COMMAND": "/patient",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sequence = []

    def fake_login(url, user, password, *, enroll_workstation=True):
        sequence.append("restricted_login" if not enroll_workstation else "owner_login")
        return "owner-token" if enroll_workstation else "restricted-token"

    def fake_http(url, payload, bearer=None, form=False, anonymous=False):
        messages = payload["messages"]
        if anonymous:
            return 401, {"detail": "Unauthorized"}, 1.0
        if messages == ["/patient"]:
            if bearer == "restricted-token":
                return 403, {"detail": "Denied"}, 1.0
            return 200, {"status": "clarification", "proposal": None}, 1.0
        if messages == ["/patient", "1"]:
            return 200, {"status": "read", "patient": {"id": 1},
                         "proposal": None}, 1.0
        if messages in ([ "/patient", "3" ], [ "/patient", "10003" ]):
            sequence.append("foreign_check")
            assert bearer == "owner-token"
            return 404, {"detail": "Patient introuvable."}, 1.0
        raise AssertionError("Unexpected synthetic request")

    monkeypatch.setattr(probe, "login", fake_login)
    monkeypatch.setattr(probe, "http_json", fake_http)
    result = probe.run(SimpleNamespace(
        api="http://127.0.0.1:8005", n=30, out=str(tmp_path/"evidence.json")))
    assert result["checks"]["foreign_unknown_same_404"] == "PASS"
    assert result["checks"]["permission_denied_403"] == "PASS"
    assert sequence.index("foreign_check") < sequence.index("restricted_login")
