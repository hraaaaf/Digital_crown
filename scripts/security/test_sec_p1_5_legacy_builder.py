"""SEC-P1.5 / SEC-P0: legacy exe builder must fail before any side effects.

No actual packaging tools, credential files, network, or patient records used.
"""
from __future__ import annotations

import ast
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "scripts" / "build_exe.py"
ERROR = "SEC-P0: legacy builder disabled"


def test_legacy_builder_programmatic_call_is_disabled() -> None:
    entry = runpy.run_path(str(LEGACY), run_name="__sec_p15_import__")
    with pytest.raises(RuntimeError, match=ERROR):
        entry["build_executable"]()


def test_legacy_builder_main_is_disabled() -> None:
    entry = runpy.run_path(str(LEGACY), run_name="__sec_p15_import__")
    with pytest.raises(SystemExit, match=ERROR):
        entry["main"]()


def test_cli_never_runs_packaging_or_touches_existing_data(tmp_path: Path) -> None:
    sentinel = tmp_path / "do-not-touch-clinic-data.txt"
    sentinel.write_text("fictional sentinel unchanged", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-B", str(LEGACY)],
        cwd=tmp_path, capture_output=True, text=True,
        timeout=15, check=False,
    )
    assert result.returncode != 0
    assert ERROR in result.stderr
    assert "Traceback" not in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "fictional sentinel unchanged"
    assert not (tmp_path / "dist").exists()
    assert not (tmp_path / "build_output").exists()
    assert not (tmp_path / "frontend").exists()


def test_source_contains_no_credentials_or_packaging_invocation() -> None:
    source = LEGACY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "firebase_creds.json" not in source
    assert "--add-data" not in source
    assert "subprocess.run" not in source
    assert "npm install" not in source
    assert "npm ci" not in source
    assert "shutil.rmtree" not in source
    assert "shell=True" not in source
    imports = {
        alias.name for node in ast.walk(tree)
        if isinstance(node, ast.Import) for alias in node.names
    }
    assert not (imports & {"subprocess", "shutil", "firebase_admin", "PyInstaller"})


def test_release_gate_path_remains_separate() -> None:
    # This verifies presence, not success of a certified commercial build.
    spec = (ROOT / "DigitalCrown.spec").read_text("utf-8")
    launcher = (ROOT / "run.py").read_text("utf-8")
    assert "verify_installable_release_directory" in spec
    assert "verify_installable_release_identity" in launcher
