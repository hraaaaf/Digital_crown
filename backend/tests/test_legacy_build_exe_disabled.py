"""SEC-P0 regression: deprecated EXE builder cannot package credentials.

These tests use only synthetic local paths; they do not invoke build tools.
"""

from pathlib import Path
import runpy
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
LEGACY_BUILDER = ROOT / "scripts" / "build_exe.py"


def test_legacy_builder_refuses_programmatic_build() -> None:
    # The module must remain importable, but packaging through it is forbidden.
    namespace = runpy.run_path(str(LEGACY_BUILDER), run_name="__security_test__")
    with pytest.raises(RuntimeError, match="SEC-P0: legacy builder disabled"):
        namespace["build_executable"]()


def test_legacy_builder_refuses_command_line_build() -> None:
    result = subprocess.run(
        [sys.executable, str(LEGACY_BUILDER)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode != 0
    assert "SEC-P0: legacy builder disabled" in result.stderr


def test_legacy_builder_has_no_package_copy_logic() -> None:
    source = LEGACY_BUILDER.read_text(encoding="utf-8")
    assert "firebase_creds.json" not in source
    assert "--add-data" not in source
    assert "subprocess.run" not in source
