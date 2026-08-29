import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "p13_update_operator.py"
SPEC = importlib.util.spec_from_file_location("p13_update_operator", SCRIPT)
assert SPEC and SPEC.loader
operator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(operator)


def test_operator_accepts_loopback_only():
    assert operator._base_url("http://127.0.0.1:8005/") == "http://127.0.0.1:8005"
    assert operator._base_url("https://localhost:8443") == "https://localhost:8443"

    for value in (
        "http://192.168.1.10:8005",
        "https://cabinet.example.test",
        "ftp://127.0.0.1:8005",
        "http://user:pass@127.0.0.1:8005",
    ):
        with pytest.raises(operator.OperatorError):
            operator._base_url(value)


def test_operator_confirmation_token_matches_runtime():
    from backend.services.update_apply import CONFIRMATION_TOKEN

    assert operator.CONFIRMATION_TOKEN == CONFIRMATION_TOKEN == "METTRE_A_JOUR"
