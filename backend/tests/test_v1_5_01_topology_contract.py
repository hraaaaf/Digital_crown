"""Targeted V1.5-01 regression gate.

This file deliberately lives under backend/tests so PR CI executes the topology
contract in the fully provisioned backend environment. It also re-exports the
existing mobile HTTPS/auth contract tests because V1.5-01 changes the shared
LAN origin used by those surfaces.
"""

from pathlib import Path

import pytest

from backend.core.cabinet_topology import TOPOLOGY_ROLES, resolve_cabinet_network
from backend.tests.test_mobile_auth_security_contract import *  # noqa: F401,F403
from backend.tests.test_mobile_https_runtime_contract import *  # noqa: F401,F403


def _env(**overrides):
    env = {
        "ENVIRONMENT": "cabinet",
        "CABINET_HOST": "127.0.0.1",
        "CABINET_PORT": "8005",
        "DIGITALCROWN_ENABLE_HTTPS": "false",
    }
    env.update(overrides)
    return env


def test_v1_5_01_roles_are_descriptive_only():
    assert TOPOLOGY_ROLES == ("server", "workstation", "reception", "connected_device")


def test_v1_5_01_loopback_first_boot_contract():
    contract = resolve_cabinet_network(_env())
    assert contract.base_url == "http://127.0.0.1:8005"
    assert contract.lan_exposed is False
    assert contract.diagnostics()["remediation"] == "LAN_DISABLED_LOOPBACK_ONLY"


def test_v1_5_01_lan_fails_closed_without_https():
    with pytest.raises(RuntimeError, match="exposition réseau cabinet/production refusée"):
        resolve_cabinet_network(_env(CABINET_HOST="0.0.0.0"))


def test_v1_5_01_https_uses_canonical_mobile_origin(tmp_path: Path):
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    cert.write_text("test")
    key.write_text("test")
    contract = resolve_cabinet_network(
        _env(
            CABINET_HOST="192.168.1.20",
            DIGITALCROWN_ENABLE_HTTPS="true",
            DIGITALCROWN_TLS_CERT_FILE=str(cert),
            DIGITALCROWN_TLS_KEY_FILE=str(key),
            PORT="9999",
        )
    )
    assert contract.base_url == "https://192.168.1.20:8005"
    assert contract.lan_exposed is True
    assert contract.tls_ready is True
