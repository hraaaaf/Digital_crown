from pathlib import Path

from backend.services import mobile_mdns


ROOT = Path(__file__).resolve().parents[2]
STABLE_ORIGIN = "https://digitalcrown.local:8005"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_stable_https_origin_is_single_runtime_port() -> None:
    assert mobile_mdns.STABLE_LAN_HOSTNAME == "digitalcrown.local"
    assert mobile_mdns.STABLE_HTTPS_PORT == 8005
    assert mobile_mdns.STABLE_HTTPS_ORIGIN == STABLE_ORIGIN

    biometric = _read("backend/services/mobile_biometric.py")
    client = _read("frontend/src/services/zka/mobilePasskey.ts")
    gate = _read("frontend/src/features/mobile/Security/MobileBiometricGate.tsx")

    assert 'f"https://{WEBAUTHN_RP_ID}:8005"' in biometric
    assert STABLE_ORIGIN in client
    assert STABLE_ORIGIN in gate
    assert ":5173" not in client
    assert ":5173" not in gate


def test_real_launcher_enables_tls_without_reload() -> None:
    launcher = _read("backend/scripts/run_real_backend.ps1")

    assert '$env:DIGITALCROWN_ENABLE_HTTPS = "true"' in launcher
    assert '$env:DIGITALCROWN_WEBAUTHN_ORIGIN = "https://digitalcrown.local:$Port"' in launcher
    assert '"--ssl-certfile", $TlsCertFile, "--ssl-keyfile", $TlsKeyFile' in launcher
    assert "HTTPS mobile/WebAuthn contract requires the real runtime on port 8005" in launcher

    invocation = next(
        line.strip()
        for line in launcher.splitlines()
        if line.strip().startswith("& $VenvPython")
    )
    assert invocation == "& $VenvPython @uvicornArgs"
    assert "--reload" not in invocation


def test_secure_pairing_url_override_and_mdns_share_origin() -> None:
    source = _read("backend/services/mobile_mdns.py")

    assert "install_stable_lan_url_overrides()" in source
    assert "legacy.get_lan_base_url = lambda: STABLE_HTTPS_ORIGIN" in source
    assert "legacy.get_lan_frontend_url = lambda: STABLE_HTTPS_ORIGIN" in source
    assert "port=STABLE_HTTPS_PORT" in source


def test_mdns_registration_runs_off_application_event_loop(monkeypatch) -> None:
    started = {}

    class FakeThread:
        def __init__(self, *, target, args, name, daemon):
            started.update(target=target, args=args, name=name, daemon=daemon, started=False)

        def start(self):
            started["started"] = True

    monkeypatch.setenv("DIGITALCROWN_ENABLE_HTTPS", "true")
    monkeypatch.setattr(mobile_mdns, "install_stable_lan_url_overrides", lambda: None)
    monkeypatch.setattr(mobile_mdns, "_detect_lan_ip", lambda: "192.168.11.128")
    monkeypatch.setattr(mobile_mdns.threading, "Thread", FakeThread)

    mobile_mdns._zeroconf = None
    mobile_mdns._service_info = None
    mobile_mdns._starting = False
    try:
        mobile_mdns.start_mdns_if_secure()
        assert started["target"] is mobile_mdns._start_mdns_sync
        assert started["args"] == ("192.168.11.128",)
        assert started["name"] == "digitalcrown-mdns-start"
        assert started["daemon"] is True
        assert started["started"] is True
        assert mobile_mdns._starting is True
    finally:
        mobile_mdns._zeroconf = None
        mobile_mdns._service_info = None
        mobile_mdns._starting = False


def test_zeroconf_runtime_dependency_is_declared() -> None:
    requirements = _read("backend/requirements.txt")
    assert "zeroconf>=0.131.0,<1.0" in requirements.splitlines()


def test_https_setup_targets_immutable_runtime() -> None:
    setup = _read("scripts/setup-https.ps1")

    assert STABLE_ORIGIN in setup
    assert "ne pas utiliser Start_DigitalCrown.bat" in setup
    assert "run_real_backend.ps1" in setup
