"""Targeted V1.5-01 regression gate.

This file deliberately lives under backend/tests so PR CI executes the topology
contract in the fully provisioned backend environment. It also re-exports the
existing mobile HTTPS/auth contract tests because V1.5-01 changes the shared
LAN origin used by those surfaces.
"""

from pathlib import Path

import pytest

import backend.core.cabinet_topology as topology
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


def test_v1_5_01_lan_discovery_has_no_public_internet_dependency():
    source = Path("backend/core/cabinet_topology.py").read_text(encoding="utf-8")
    assert "8.8.8.8" not in source
    assert "192.0.2.1" in source
    assert "198.51.100.1" in source
    assert "203.0.113.1" in source


def test_v1_5_01_lan_address_filter_rejects_unsafe_candidates():
    assert topology._usable_lan_ipv4("127.0.0.1") is None
    assert topology._usable_lan_ipv4("169.254.1.5") is None
    assert topology._usable_lan_ipv4("0.0.0.0") is None
    assert topology._usable_lan_ipv4("10.20.30.40") == "10.20.30.40"


def test_v1_5_01_wildcard_url_fails_closed_without_detected_lan(monkeypatch):
    monkeypatch.setattr(topology, "detect_lan_ip", lambda: None)
    contract = resolve_cabinet_network(
        _env(
            CABINET_HOST="0.0.0.0",
            DIGITALCROWN_ENABLE_HTTPS="true",
            DIGITALCROWN_TLS_CERT_FILE="cert.pem",
            DIGITALCROWN_TLS_KEY_FILE="key.pem",
        ),
        validate_tls_files=False,
    )
    with pytest.raises(RuntimeError, match="aucune adresse LAN utilisable"):
        _ = contract.base_url


def test_v1_5_01_mobile_backend_consumes_canonical_origin_only():
    source = Path("backend/routers/mobile_legacy.py").read_text(encoding="utf-8")
    start = source.index("def get_lan_base_url")
    end = source.index("def get_lan_frontend_url", start)
    function_source = source[start:end]
    assert "get_cabinet_base_url" in function_source
    assert 'os.getenv("PORT"' not in function_source
    assert "_detect_lan_ip" not in function_source


def test_v1_5_01_server_mobile_origin_is_https_and_port_8005(monkeypatch):
    """Integration seam: mobile helper must publish the server contract verbatim."""
    from backend.routers import mobile_legacy

    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    monkeypatch.setenv("CABINET_HOST", "192.168.50.12")
    monkeypatch.setenv("CABINET_PORT", "8005")
    monkeypatch.setenv("DIGITALCROWN_ENABLE_HTTPS", "true")
    monkeypatch.setenv("DIGITALCROWN_TLS_CERT_FILE", "cert.pem")
    monkeypatch.setenv("DIGITALCROWN_TLS_KEY_FILE", "key.pem")
    monkeypatch.setattr(topology.os.path, "isfile", lambda _path: True)

    assert mobile_legacy.get_lan_base_url() == "https://192.168.50.12:8005"


def test_v1_5_01_no_mobile_backend_http_lan_fallback():
    """Prevent regression to an independently constructed insecure backend URL."""
    source = Path("backend/routers/mobile_legacy.py").read_text(encoding="utf-8")
    start = source.index("def get_lan_base_url")
    end = source.index("def get_lan_frontend_url", start)
    function_source = source[start:end]
    assert 'f"http://' not in function_source
    assert "127.0.0.1" not in function_source
