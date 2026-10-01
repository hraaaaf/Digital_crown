from pathlib import Path

STABLE_ORIGIN = "https://digitalcrown.local:8005"


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_backend_https_runtime_contract() -> None:
    main = _read("backend/main.py")
    auth = _read("backend/routers/auth.py")
    mobile = _read("backend/routers/mobile_legacy.py")

    assert 'environment == "cabinet" and cabinet_https' in auth
    assert 'if _RUNTIME_ENV in {"development", "local", "test"}' in main
    assert "get_cabinet_base_url" in mobile


def test_mobile_pairing_uses_stable_origin_contract() -> None:
    mobile = _read("backend/routers/mobile_legacy.py")
    assert "get_cabinet_base_url" in mobile
    assert 'os.getenv("PORT"' not in mobile


def test_https_runtime_keeps_canonical_port() -> None:
    topology = _read("backend/core/cabinet_topology.py")
    assert "CABINET_PORT=8005" in topology


def test_https_setup_targets_immutable_runtime() -> None:
    setup = _read("scripts/setup-https.ps1")
    assert STABLE_ORIGIN in setup
    assert "ne pas utiliser Start_DigitalCrown.bat" in setup
    assert "run_real_backend.ps1" in setup


def test_packaged_cabinet_runtime_is_loopback_unless_explicit_tls() -> None:
    run_source = _read("run.py")
    topology_source = _read("backend/core/cabinet_topology.py")
    auth_source = _read("backend/routers/auth.py")
    main_source = _read("backend/main.py")

    # V1.5-01 centralizes host/TLS policy in cabinet_topology; run.py must delegate
    # instead of duplicating the previous string-level implementation.
    assert "resolve_cabinet_network" in run_source
    assert 'CABINET_HOST", "127.0.0.1"' in topology_source
    assert "exposition réseau cabinet/production refusée sans HTTPS explicite" in topology_source
    assert "DIGITALCROWN_TLS_CERT_FILE" in topology_source
    assert "ssl_certfile=cert_file if https_enabled else None" in run_source
    assert 'environment == "cabinet" and cabinet_https' in auth_source
    assert 'if _RUNTIME_ENV in {"development", "local", "test"}' in main_source


def test_controlled_real_launcher_never_exposes_plain_http_on_lan() -> None:
    launcher = _read("backend/scripts/run_real_backend.ps1")
    assert '[string]$BindHost = ""' in launcher
    assert '$BindHost = if ($httpsEnabled) { "0.0.0.0" } else { "127.0.0.1" }' in launcher
    assert 'non-loopback cabinet binding requires HTTPS cert/key' in launcher
