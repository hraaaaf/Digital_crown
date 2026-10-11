"""Regression: PyInstaller windowed (console=False) has no TTY streams.

The immutable previous CODE_CERTIFIED master 9c41d327400b failed its
Windows frozen runtime smoke because Uvicorn's default formatter called
sys.stderr.isatty() when sys.stderr was None. This test checks the actual
run.py launch argument without importing run.py (which starts the cabinet).
"""
from __future__ import annotations

import ast
import http.client
import os
from pathlib import Path
import socket
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


def _uvicorn_log_config_expression() -> ast.expr:
    tree = ast.parse((ROOT / "run.py").read_text(encoding="utf-8-sig"))
    main = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    calls = [
        node for node in ast.walk(main)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "uvicorn"
            and node.func.attr == "run"
        )
    ]
    assert len(calls) == 1, "One production Uvicorn launcher required"
    kwargs = [arg.value for arg in calls[0].keywords if arg.arg == "log_config"]
    assert len(kwargs) == 1, "Windowed mode must pass explicit log_config"
    return kwargs[0]


def test_frozen_launcher_keeps_file_logging_and_avoids_console_formatter():
    expr = _uvicorn_log_config_expression()
    assert isinstance(expr, ast.IfExp)
    assert isinstance(expr.body, ast.Constant) and expr.body.value is None
    assert ast.unparse(expr.test) == "getattr(sys, 'frozen', False)"
    assert ast.unparse(expr.orelse) == "uvicorn.config.LOGGING_CONFIG"
    # The AST requires an explicit frozen-only condition and leaves
    # development's original Uvicorn console default unchanged. Avoid eval.
    assert isinstance(expr.test, ast.Call)
    assert isinstance(expr.test.func, ast.Name)
    assert expr.test.func.id == "getattr"


def test_uvicorn_accepts_no_console_streams_when_logging_config_disabled():
    # Subprocess ensures this test cannot mutate pytest's own sys.stdout/stderr.
    # Uvicorn.Config is configured but never launches/imports the clinical app.
    script = (
        "import sys, uvicorn\n"
        "sys.stdout = None\n"
        "sys.stderr = None\n"
        "cfg = uvicorn.Config('fake_unused_app:app', log_config=None)\n"
        "cfg.configure_logging()\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

def test_real_asgi_loopback_with_no_console_streams():
    """Start a real Uvicorn server, not a mock, with Windows-like None streams.

    Clinical backend is never imported and no patient/database is touched.
    Only 127.0.0.1 on an ephemeral port is reachable by this test.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    server = (
        "import os,sys,uvicorn\\n"
        "sys.stdout = None\\n"
        "sys.stderr = None\\n"
        "async def app(scope, receive, send):\\n"
        "    assert scope['type']=='http'\\n"
        "    await send({'type':'http.response.start','status':200,'headers':[]})\\n"
        "    await send({'type':'http.response.body','body':b'OK'})\\n"
        "uvicorn.run(app,host='127.0.0.1',port=int(os.environ['FUE_G04_PORT']),log_config=None)\\n"
    )
    environment = dict(os.environ)
    environment["FUE_G04_PORT"] = str(port)
    process = subprocess.Popen(
        [sys.executable, "-c", server],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    try:
        deadline = time.monotonic() + 20
        last_error = ""
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stderr = process.stderr.read().decode("utf-8", errors="replace")[:1000]
                raise AssertionError(f"Consoleless Uvicorn exited early: {process.returncode}; {stderr}")
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
            try:
                conn.request("GET", "/health")
                response = conn.getresponse()
                assert response.status == 200
                assert response.read() == b"OK"
                break
            except (OSError, TimeoutError) as error:
                last_error = type(error).__name__
                time.sleep(0.25)
            finally:
                conn.close()
        else:
            raise AssertionError(f"Consoleless Uvicorn failed to bind loopback within 20s: {last_error}")
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
