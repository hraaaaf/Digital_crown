"""V1.5-01.1 FUE-0: topology contract proof (stdlib only, read-only).

Tests code/transport invariants, not an installer journey or a TLS handshake.
No database, network probe, backend server or certificate material is required.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path
import tempfile
from unittest.mock import patch

# Load the actual pure contract directly. Importing backend/__init__.py would
# initialize clinical ORM models (SQLAlchemy), which is intentionally excluded
# from this isolated FUE-0 gate. Stub only package namespace resolution used
# by the real legacy frontend helper's import; never stub contract behavior.
_contract_source = Path("backend/core/cabinet_topology.py")
_spec = importlib.util.spec_from_file_location("backend.core.cabinet_topology", _contract_source)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Cannot load the canonical topology source")
sys.modules["backend"] = ModuleType("backend")
sys.modules["backend.core"] = ModuleType("backend.core")
topology = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = topology
_spec.loader.exec_module(topology)


ARTIFACT = Path("artifacts/fue-v15-01-1/topology-fue0-report.json")
HEAD = os.environ.get("PRODUCT_HEAD") or os.environ.get("GITHUB_HEAD_SHA") or "local"
cases: list[dict] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    cases.append({"check": label, "result": "PASS" if condition else "FAIL", "detail": detail})
    if not condition:
        raise AssertionError(label + ": " + detail)


def rejected(label: str, settings: dict, expected: str, *, validate_files: bool = True) -> None:
    try:
        topology.resolve_cabinet_network(settings, validate_tls_files=validate_files)
    except RuntimeError as error:
        check(label, expected in str(error), type(error).__name__)
        return
    check(label, False, "insecure configuration was accepted")


def env(**overrides: str) -> dict:
    settings = {
        "ENVIRONMENT": "cabinet",
        "CABINET_HOST": "127.0.0.1",
        "CABINET_PORT": "8005",
        "DIGITALCROWN_ENABLE_HTTPS": "false",
    }
    settings.update(overrides)
    return settings


try:
    check("descriptive-only topology roles",
          topology.TOPOLOGY_ROLES == ("server", "workstation", "reception", "connected_device"))
    default = topology.resolve_cabinet_network(env())
    diag = default.diagnostics()
    check("first boot loopback and canonical port",
          default.base_url == "http://127.0.0.1:8005")
    check("loopback is never advertised for remote connection",
          diag["connectionUrl"] is None and diag["lanExposed"] is False)
    check("readable non-secret remediation",
          diag["remediation"] == "LAN_DISABLED_LOOPBACK_ONLY"
          and diag["topologyRole"] == "server")
    check("no secrets or authorization tokens in diagnostics",
          not (set(diag) & {"cert_file", "key_file", "token", "password", "permissions",
                            "DIGITALCROWN_TLS_CERT_FILE", "DIGITALCROWN_TLS_KEY_FILE"}))
    rejected("cabinet LAN without TLS fails closed",
             env(CABINET_HOST="192.168.1.20"), "refusée sans HTTPS")
    rejected("production wildcard LAN without TLS fails closed",
             env(ENVIRONMENT="production", CABINET_HOST="0.0.0.0"), "refusée sans HTTPS")
    rejected("HTTPS requires certificate and key",
             env(CABINET_HOST="192.168.1.20", DIGITALCROWN_ENABLE_HTTPS="true"),
             "exige DIGITALCROWN_TLS_CERT_FILE")
    rejected("HTTPS WebAuthn origin is fixed to port 8005",
             env(CABINET_HOST="192.168.1.20", CABINET_PORT="8443",
                 DIGITALCROWN_ENABLE_HTTPS="true"), "CABINET_PORT=8005")
    rejected("invalid port is refused",
             env(CABINET_PORT="70000"), "compris entre 1 et 65535")
    with tempfile.TemporaryDirectory() as dirname:
        cert = Path(dirname) / "cert.pem"
        key = Path(dirname) / "key.pem"
        cert.write_text("fue fixture only", encoding="utf-8")
        key.write_text("fue fixture only", encoding="utf-8")
        secure_env = env(
            CABINET_HOST="192.168.1.20",
            DIGITALCROWN_ENABLE_HTTPS="true",
            DIGITALCROWN_TLS_CERT_FILE=str(cert),
            DIGITALCROWN_TLS_KEY_FILE=str(key),
            PORT="9999",
        )
        secure = topology.resolve_cabinet_network(secure_env)
        check("secure published origin uses canonical cabinet port, not PORT",
              secure.connection_url == "https://192.168.1.20:8005")
        check("LAN-ready diagnostic is truthful",
              secure.diagnostics()["remediation"] is None
              and secure.diagnostics()["tlsReady"] is True)
    with patch.object(topology, "detect_lan_ip", return_value=None):
        wild = topology.resolve_cabinet_network(
            env(CABINET_HOST="0.0.0.0", DIGITALCROWN_ENABLE_HTTPS="true",
                DIGITALCROWN_TLS_CERT_FILE="fixture-cert",
                DIGITALCROWN_TLS_KEY_FILE="fixture-key"),
            validate_tls_files=False,
        )
        try:
            _ = wild.connection_url
        except RuntimeError as error:
            check("wildcard cannot invent a LAN address", "aucune adresse LAN utilisable" in str(error))
        else:
            check("wildcard cannot invent a LAN address", False)
    launcher = Path("run.py").read_text(encoding="utf-8")
    mobile = Path("backend/routers/mobile_legacy.py").read_text(encoding="utf-8")
    main = Path("backend/main.py").read_text(encoding="utf-8")
    mobile_section = mobile.split("def get_lan_base_url()", 1)[1].split("def get_lan_frontend_url", 1)[0]
    check("launcher delegates network authority to canonical resolver",
          "from backend.core.cabinet_topology import resolve_cabinet_network" in launcher)
    check("legacy mobile backend origin delegates to canonical resolver",
          "get_cabinet_base_url" in mobile_section
          and 'os.getenv("PORT"' not in mobile_section
          and "_detect_lan_ip" not in mobile_section)
    # Execute the actual legacy frontend URL helper without importing the
    # database-dependent router module. Cabinet mode must not advertise Vite
    # on an invented plaintext LAN address; development Vite remains supported.
    legacy_frontend_function = next(
        node for node in ast.parse(mobile).body
        if isinstance(node, ast.FunctionDef) and node.name == "get_lan_frontend_url"
    )
    frontend_globals = {"_detect_lan_ip": lambda: "192.168.10.20"}
    exec(compile(ast.Module(body=[legacy_frontend_function], type_ignores=[]),
                 "mobile_legacy.py", "exec"), frontend_globals)
    get_frontend = frontend_globals["get_lan_frontend_url"]
    with patch.object(topology, "resolve_cabinet_network", return_value=default):
        check("cabinet HTTP does not advertise a phantom LAN frontend",
              get_frontend() == "http://127.0.0.1:8005")
    with patch.object(topology, "resolve_cabinet_network", return_value=secure):
        check("cabinet HTTPS frontend follows canonical TLS origin",
              get_frontend() == "https://192.168.1.20:8005")
    dev = topology.resolve_cabinet_network(env(ENVIRONMENT="development"))
    with patch.object(topology, "resolve_cabinet_network", return_value=dev):
        check("local development Vite frontend compatibility retained",
              get_frontend() == "http://192.168.10.20:5173")
    check("topology diagnostic is explicitly exposed",
          '@app.get("/api/health/topology"' in main
          and "resolve_cabinet_network().diagnostics()" in main)
    push = Path("backend/routers/mobile_push.py").read_text(encoding="utf-8")
    push_initialization = push.split("def install_secure_lan_url_overrides()", 1)[1].split("@router.get", 1)[0]
    check("Web Push installer cannot replace canonical LAN URL authority",
          "_legacy.get_lan_base_url =" not in push_initialization
          and "_legacy.get_lan_frontend_url =" not in push_initialization)
    # Execute the actual exported hook body with a stub legacy module. This
    # catches dynamic monkey-patching without importing DB-dependent push APIs.
    push_function = next(node for node in ast.parse(push).body
                         if isinstance(node, ast.FunctionDef)
                         and node.name == "install_secure_lan_url_overrides")
    ast_module = ast.Module(body=[push_function], type_ignores=[])
    base_origin = lambda: "http://127.0.0.1:8005"
    frontend_origin = lambda: "http://127.0.0.1:5173"
    legacy_stub = SimpleNamespace(get_lan_base_url=base_origin,
                                  get_lan_frontend_url=frontend_origin,
                                  _detect_lan_ip=lambda: "192.168.10.20")
    installed = []
    namespace = {"_legacy": legacy_stub,
                 "_disable_legacy_fcm_registration_route": lambda: installed.append("disabled")}
    exec(compile(ast_module, "mobile_push.py", "exec"), namespace)
    namespace["install_secure_lan_url_overrides"]()
    check("Web Push hook preserves canonical backend and frontend functions",
          legacy_stub.get_lan_base_url is base_origin
          and legacy_stub.get_lan_frontend_url is frontend_origin)
    check("Web Push keeps obsolete FCM registration disabled",
          installed == ["disabled"])

    source = Path("backend/core/cabinet_topology.py").read_text(encoding="utf-8")
    check("passive local route discovery does not rely on public DNS",
          "8.8.8.8" not in source
          and "192.0.2.1" in source
          and "198.51.100.1" in source)
finally:
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "scope": "V1.5-01.1 FUE-0: pure topology/transport, not user FUE or real TLS",
        "productHead": HEAD,
        "checks": cases,
        "passed": sum(c["result"] == "PASS" for c in cases),
        "total": len(cases),
    }
    ARTIFACT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("FUE_01_1_CONTRACT_REPORT " + json.dumps({"passed": report["passed"], "total": report["total"],
                                                        "productHead": HEAD}))
