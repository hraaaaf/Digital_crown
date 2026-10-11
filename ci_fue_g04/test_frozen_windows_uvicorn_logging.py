"""Regression: PyInstaller windowed (console=False) has no TTY streams.

The immutable previous CODE_CERTIFIED master 9c41d327400b failed its
Windows frozen runtime smoke because Uvicorn's default formatter called
sys.stderr.isatty() when sys.stderr was None. This test checks the actual
run.py launch argument without importing run.py (which starts the cabinet).
"""
from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys


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
