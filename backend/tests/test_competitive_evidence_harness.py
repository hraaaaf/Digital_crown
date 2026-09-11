from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts" / "validate_competitive_evidence.py"


def _load_validator_module():
    spec = importlib.util.spec_from_file_location("competitive_evidence_validator", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_competitive_evidence_harness_is_consistent() -> None:
    validator = _load_validator_module()
    counts = validator.validate()

    assert counts == {
        "sources": 6,
        "capabilities": 12,
        "fixtures": 15,
        "scenarios": 11,
    }
