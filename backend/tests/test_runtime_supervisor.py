from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import pytest

from backend.core.platform import PlatformAdapter
from backend.core.runtime_supervisor import RuntimeSupervisor


class _HealthHandler(BaseHTTPRequestHandler):
    payload = {"status": "ok", "db": "ok"}
    status_code = 200

    def do_GET(self):
        body = json.dumps(type(self).payload).encode("utf-8")
        self.send_response(type(self).status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


@pytest.fixture
def health_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_instance_lock_is_exclusive_and_released(tmp_path):
    adapter = PlatformAdapter(home=tmp_path)
    supervisor = RuntimeSupervisor(8005, adapter=adapter, runtime_dir=tmp_path)

    first = supervisor.try_acquire_instance()
    assert first is not None
    assert supervisor.try_acquire_instance() is None

    first.release()
    replacement = supervisor.try_acquire_instance()
    assert replacement is not None
    replacement.release()


def test_health_readiness_requires_status_and_db_ok(tmp_path, health_server):
    adapter = PlatformAdapter(home=tmp_path)
    supervisor = RuntimeSupervisor(
        health_server.server_port,
        adapter=adapter,
        runtime_dir=tmp_path,
        request_timeout=0.5,
    )
    assert supervisor.is_ready() is True

    _HealthHandler.payload = {"status": "degraded", "db": "ok"}
    try:
        assert supervisor.is_ready() is False
    finally:
        _HealthHandler.payload = {"status": "ok", "db": "ok"}


def test_wait_until_ready_uses_health_probe_not_fixed_startup_delay(tmp_path):
    supervisor = RuntimeSupervisor(8005, adapter=PlatformAdapter(home=tmp_path), runtime_dir=tmp_path)
    with patch.object(supervisor, "is_ready", side_effect=[False, False, True]) as probe:
        with patch("backend.core.runtime_supervisor.time.sleep") as sleeper:
            assert supervisor.wait_until_ready(timeout=1.0, poll_interval=0.01) is True
    assert probe.call_count == 3
    assert sleeper.call_count == 2


def test_second_launch_focuses_existing_ready_runtime(tmp_path, health_server):
    adapter = PlatformAdapter(home=tmp_path)
    owner = RuntimeSupervisor(health_server.server_port, adapter=adapter, runtime_dir=tmp_path)
    first = owner.try_acquire_instance()
    assert first is not None
    try:
        contender = RuntimeSupervisor(health_server.server_port, adapter=adapter, runtime_dir=tmp_path)
        with patch.object(adapter, "open_uri", return_value=True) as opener:
            assert contender.claim_or_focus_existing(timeout=1.0) is None
        opener.assert_called_once_with(contender.ui_url)
    finally:
        first.release()


def test_lock_held_but_unready_runtime_opens_recovery_and_fails_closed(tmp_path):
    adapter = PlatformAdapter(home=tmp_path)
    owner = RuntimeSupervisor(65534, adapter=adapter, runtime_dir=tmp_path, request_timeout=0.05)
    first = owner.try_acquire_instance()
    assert first is not None
    try:
        contender = RuntimeSupervisor(65534, adapter=adapter, runtime_dir=tmp_path, request_timeout=0.05)
        with (
            patch.object(contender, "wait_until_ready", return_value=False),
            patch.object(contender, "open_recovery_page", return_value=True) as recovery,
        ):
            with pytest.raises(RuntimeError, match="détient le verrou"):
                contender.claim_or_focus_existing(timeout=0.05)
        recovery.assert_called_once_with("INSTANCE_NOT_READY")
    finally:
        first.release()


def test_open_ui_only_after_readiness(tmp_path):
    adapter = PlatformAdapter(home=tmp_path)
    supervisor = RuntimeSupervisor(8005, adapter=adapter, runtime_dir=tmp_path)
    with (
        patch.object(supervisor, "wait_until_ready", return_value=True) as wait,
        patch.object(adapter, "open_uri", return_value=True) as opener,
    ):
        assert supervisor.open_ui_when_ready(timeout=3.0) is True
    wait.assert_called_once_with(timeout=3.0)
    opener.assert_called_once_with("http://127.0.0.1:8005")


def test_open_ui_timeout_opens_local_recovery_surface(tmp_path):
    supervisor = RuntimeSupervisor(8005, adapter=PlatformAdapter(home=tmp_path), runtime_dir=tmp_path)
    with (
        patch.object(supervisor, "wait_until_ready", return_value=False),
        patch.object(supervisor, "open_recovery_page", return_value=True) as recovery,
    ):
        assert supervisor.open_ui_when_ready(timeout=3.0) is False
    recovery.assert_called_once_with("RUNTIME_NOT_READY")


def test_recovery_page_is_local_actionable_and_non_destructive(tmp_path):
    appdata = tmp_path / "appdata"
    adapter = PlatformAdapter(
        system_name="Windows",
        environ={"APPDATA": str(appdata)},
        home=tmp_path,
    )
    supervisor = RuntimeSupervisor(8005, adapter=adapter, runtime_dir=tmp_path / "runtime")

    with patch.object(adapter, "open_uri", return_value=True) as opener:
        assert supervisor.open_recovery_page("RUNTIME_START_FAILED") is True

    opener.assert_called_once_with(supervisor.recovery_path.resolve().as_uri())
    page = supervisor.recovery_path.read_text(encoding="utf-8")
    assert "Digital Crown n’a pas pu démarrer" in page
    assert "RUNTIME_START_FAILED" in page
    assert "Cet écran de récupération ne lance aucune restauration, suppression ni réinitialisation du cabinet." in page
    assert "Vos données cabinet n’ont pas été modifiées" not in page
    assert "Réessayer l’ouverture" in page
    assert "Copier le chemin du journal" in page
    assert str(supervisor.log_path) in page
    assert "Traceback" not in page
    assert "SECRET_KEY" not in page
