from pathlib import Path

import pytest

import backend.core.cabinet_topology as topology
from backend.core.cabinet_topology import TOPOLOGY_ROLES, resolve_cabinet_network


def _env(**overrides):
    env = {
        "ENVIRONMENT": "cabinet",
        "CABINET_HOST": "127.0.0.1",
        "CABINET_PORT": "8005",
        "DIGITALCROWN_ENABLE_HTTPS": "false",
    }
    env.update(overrides)
    return env


def test_topology_roles_are_descriptive_and_explicit():
    assert TOPOLOGY_ROLES == ("server", "workstation", "reception", "connected_device")


def test_first_boot_contract_is_loopback_http():
    contract = resolve_cabinet_network(_env())
    assert contract.base_url == "http://127.0.0.1:8005"
    assert contract.lan_exposed is False
    assert contract.diagnostics()["remediation"] == "LAN_DISABLED_LOOPBACK_ONLY"


def test_cabinet_lan_fails_closed_without_https():
    with pytest.raises(RuntimeError, match="exposition réseau cabinet/production refusée"):
        resolve_cabinet_network(_env(CABINET_HOST="0.0.0.0"))


def test_https_requires_both_tls_paths():
    with pytest.raises(RuntimeError, match="HTTPS cabinet exige"):
        resolve_cabinet_network(
            _env(
                CABINET_HOST="0.0.0.0",
                DIGITALCROWN_ENABLE_HTTPS="true",
                DIGITALCROWN_TLS_CERT_FILE="cert.pem",
            ),
            validate_tls_files=False,
        )


def test_https_lan_contract_uses_canonical_cabinet_port(tmp_path: Path):
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    cert.write_text("test")
    key.write_text("test")
    contract = resolve_cabinet_network(
        _env(
            CABINET_HOST="192.168.1.20",
            CABINET_PORT="8005",
            DIGITALCROWN_ENABLE_HTTPS="true",
            DIGITALCROWN_TLS_CERT_FILE=str(cert),
            DIGITALCROWN_TLS_KEY_FILE=str(key),
            PORT="9999",
        )
    )
    assert contract.base_url == "https://192.168.1.20:8005"
    assert contract.lan_exposed is True
    assert contract.tls_ready is True
    assert contract.diagnostics()["remediation"] is None


def test_https_rejects_noncanonical_mobile_port():
    with pytest.raises(RuntimeError, match="CABINET_PORT=8005"):
        resolve_cabinet_network(
            _env(
                CABINET_HOST="192.168.1.20",
                CABINET_PORT="8443",
                DIGITALCROWN_ENABLE_HTTPS="true",
                DIGITALCROWN_TLS_CERT_FILE="cert.pem",
                DIGITALCROWN_TLS_KEY_FILE="key.pem",
            ),
            validate_tls_files=False,
        )


@pytest.mark.parametrize("port", ["0", "65536", "abc"])
def test_invalid_cabinet_port_fails_closed(port):
    with pytest.raises(RuntimeError, match="CABINET_PORT"):
        resolve_cabinet_network(_env(CABINET_PORT=port))


def test_mobile_pairing_url_uses_canonical_network_contract():
    source = Path("backend/routers/mobile_legacy.py").read_text(encoding="utf-8")
    start = source.index("def get_lan_base_url")
    end = source.index("def get_lan_frontend_url", start)
    function_source = source[start:end]
    assert "get_cabinet_base_url" in function_source
    assert 'os.getenv("PORT"' not in function_source
    assert "http://{_detect_lan_ip()}" not in function_source


def test_lan_discovery_does_not_depend_on_public_internet():
    source = Path("backend/core/cabinet_topology.py").read_text(encoding="utf-8")
    assert "8.8.8.8" not in source
    assert "192.0.2.1" in source
    assert "198.51.100.1" in source
    assert "203.0.113.1" in source


def test_lan_discovery_rejects_loopback_and_link_local():
    assert topology._usable_lan_ipv4("127.0.0.1") is None
    assert topology._usable_lan_ipv4("169.254.10.20") is None
    assert topology._usable_lan_ipv4("0.0.0.0") is None
    assert topology._usable_lan_ipv4("192.168.10.20") == "192.168.10.20"


def test_wildcard_publication_fails_closed_when_discovery_fails(monkeypatch):
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
