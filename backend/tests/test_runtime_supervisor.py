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


def test_lock_held_but_unready_runtime_fails_closed(tmp_path):
    adapter = PlatformAdapter(home=tmp_path)
    owner = RuntimeSupervisor(65534, adapter=adapter, runtime_dir=tmp_path, request_timeout=0.05)
    first = owner.try_acquire_instance()
    assert first is not None
    try:
        contender = RuntimeSupervisor(65534, adapter=adapter, runtime_dir=tmp_path, request_timeout=0.05)
        with patch.object(contender, "wait_until_ready", return_value=False):
            with pytest.raises(RuntimeError, match="détient le verrou"):
                contender.claim_or_focus_existing(timeout=0.05)
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
