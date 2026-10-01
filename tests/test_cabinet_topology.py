from pathlib import Path

import pytest

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
            CABINET_PORT="8443",
            DIGITALCROWN_ENABLE_HTTPS="true",
            DIGITALCROWN_TLS_CERT_FILE=str(cert),
            DIGITALCROWN_TLS_KEY_FILE=str(key),
            PORT="9999",
        )
    )
    assert contract.base_url == "https://192.168.1.20:8443"
    assert contract.lan_exposed is True
    assert contract.tls_ready is True
    assert contract.diagnostics()["remediation"] is None


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
