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
