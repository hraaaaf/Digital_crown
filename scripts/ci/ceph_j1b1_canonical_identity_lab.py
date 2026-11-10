"""Run the Ceph J1.B1 synthetic identity tests without backend app initialization.

The real backend/__init__.py registers database models and business policies at
import time. This test-only process creates namespace placeholders for the
specific modules under test; it never imports the production backend bootstrap,
FastAPI, SQLAlchemy, models, image files or a runtime ONNX asset.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _register_namespace(name: str, subdirectory: str) -> None:
    module = types.ModuleType(name)
    module.__path__ = [str(ROOT / subdirectory)]
    module.__package__ = name
    sys.modules[name] = module


def main() -> int:
    # Keep this explicit and auditable: only the source contract, evidence
    # schemas and identity bridge may be imported for these pure tests.
    _register_namespace("backend", "backend")
    _register_namespace("backend.services", "backend/services")
    _register_namespace("backend.schemas", "backend/schemas")
    _register_namespace("backend.tests", "backend/tests")

    import pytest

    test_file = ROOT / "backend/tests/test_cephalo_vnext_lot06_landmark_identity_bridge.py"
    exit_code = pytest.main([
        "--noconftest",
        "--import-mode=importlib",
        "-q",
        str(test_file),
    ])
    forbidden = (
        "backend.models",
        "backend.database",
        "backend.main",
        "backend.services.archive_service",
    )
    imported = [name for name in forbidden if name in sys.modules]
    if imported:
        raise RuntimeError(f"Forbidden backend import(s) in J1.B1 isolated lab: {imported}")
    print("CEPH_J1B1_SYNTHETIC_FAIL_CLOSED_TESTS_" + ("PASS" if exit_code == 0 else "FAIL"))
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
