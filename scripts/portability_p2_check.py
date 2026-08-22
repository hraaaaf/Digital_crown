from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
import threading
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLATFORM_FILE = ROOT / "backend" / "core" / "platform.py"
SUPERVISOR_FILE = ROOT / "backend" / "core" / "runtime_supervisor.py"
RUN_FILE = ROOT / "run.py"
MAIN_FILE = ROOT / "backend" / "main.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_runtime_modules():
    backend_pkg = types.ModuleType("backend")
    backend_pkg.__path__ = [str(ROOT / "backend")]
    core_pkg = types.ModuleType("backend.core")
    core_pkg.__path__ = [str(ROOT / "backend" / "core")]
    sys.modules["backend"] = backend_pkg
    sys.modules["backend.core"] = core_pkg
    platform_mod = _load("backend.core.platform", PLATFORM_FILE)
    supervisor_mod = _load("backend.core.runtime_supervisor", SUPERVISOR_FILE)
    return platform_mod, supervisor_mod


class _HealthHandler(BaseHTTPRequestHandler):
    payload = {"status": "ok", "db": "ok"}

    def do_GET(self):
        body = json.dumps(type(self).payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def _lock_contract(platform_mod, supervisor_mod) -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        adapter = platform_mod.PlatformAdapter(home=root)
        supervisor = supervisor_mod.RuntimeSupervisor(8005, adapter=adapter, runtime_dir=root)
        assert supervisor.health_url == "http://127.0.0.1:8005/health"
        first = supervisor.try_acquire_instance()
        assert first is not None
        assert supervisor.try_acquire_instance() is None
        first.release()
        replacement = supervisor.try_acquire_instance()
        assert replacement is not None
        replacement.release()


def _readiness_and_existing_instance_contract(platform_mod, supervisor_mod) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            adapter = platform_mod.PlatformAdapter(home=root)
            owner = supervisor_mod.RuntimeSupervisor(
                server.server_port,
                adapter=adapter,
                runtime_dir=root,
                request_timeout=0.5,
            )
            assert owner.is_ready() is True

            first = owner.try_acquire_instance()
            assert first is not None
            try:
                contender = supervisor_mod.RuntimeSupervisor(
                    server.server_port,
                    adapter=adapter,
                    runtime_dir=root,
                    request_timeout=0.5,
                )
                with patch.object(adapter, "open_uri", return_value=True) as opener:
                    assert contender.claim_or_focus_existing(timeout=1.0) is None
                opener.assert_called_once_with(contender.ui_url)
            finally:
                first.release()

            _HealthHandler.payload = {"status": "degraded", "db": "ok"}
            assert owner.is_ready() is False
            _HealthHandler.payload = {"status": "ok", "db": "ok"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _source_contract() -> None:
    run_source = RUN_FILE.read_text(encoding="utf-8")
    main_source = MAIN_FILE.read_text(encoding="utf-8")

    assert "time.sleep(2)" not in run_source
    assert "RuntimeSupervisor" in run_source
    assert "claim_or_focus_existing" in run_source
    assert "target=supervisor.open_ui_when_ready" in run_source
    assert "DIGITALCROWN_RESTORE_RESTART" in run_source
    assert "open_existing=not suppress_browser" in run_source
    assert "_load_launcher_environment()\n    host, port = _resolve_host_port()" in run_source
    assert "load_backend_env(override=False)" in run_source
    assert "http://127.0.0.1:8000" not in main_source
    assert "webbrowser.open(" not in main_source
    assert "import webbrowser" not in main_source

    run_tree = ast.parse(run_source, filename="run.py")
    for node in run_tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "backend.main":
            raise AssertionError("backend.main must be imported lazily after packaged single-instance arbitration")


def main() -> int:
    platform_mod, supervisor_mod = _load_runtime_modules()
    _lock_contract(platform_mod, supervisor_mod)
    _readiness_and_existing_instance_contract(platform_mod, supervisor_mod)
    _source_contract()
    print(f"P2 runtime supervisor PASS on runner={platform_mod.PlatformAdapter().kind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
