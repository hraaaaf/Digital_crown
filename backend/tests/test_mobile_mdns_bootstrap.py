from __future__ import annotations

import sys
import types
from pathlib import Path

from backend.services import mobile_mdns


REPO_ROOT = Path(__file__).resolve().parents[2]


class _FakeServiceInfo:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class _FakeZeroconf:
    instances: list["_FakeZeroconf"] = []

    def __init__(self):
        self.registered = []
        self.unregistered = []
        self.closed = False
        self.__class__.instances.append(self)

    def register_service(self, info, allow_name_change=False):
        self.registered.append((info, allow_name_change))

    def unregister_service(self, info):
        self.unregistered.append(info)

    def close(self):
        self.closed = True


def _fake_zeroconf_module() -> types.ModuleType:
    module = types.ModuleType("zeroconf")
    module.ServiceInfo = _FakeServiceInfo
    module.Zeroconf = _FakeZeroconf
    return module


def test_mdns_is_disabled_without_secure_lan(monkeypatch):
    mobile_mdns.stop_mdns()
    monkeypatch.setenv("DIGITALCROWN_ENABLE_HTTPS", "false")
    monkeypatch.setattr(
        mobile_mdns,
        "_detect_lan_ip",
        lambda: (_ for _ in ()).throw(AssertionError("LAN detection must not run over HTTP")),
    )

    mobile_mdns.start_mdns_if_secure()

    assert mobile_mdns._zeroconf is None
    assert mobile_mdns._service_info is None


def test_mdns_secure_publication_is_stable_idempotent_and_stoppable(monkeypatch):
    mobile_mdns.stop_mdns()
    _FakeZeroconf.instances.clear()
    monkeypatch.setenv("DIGITALCROWN_ENABLE_HTTPS", "true")
    monkeypatch.setattr(mobile_mdns, "_detect_lan_ip", lambda: "192.168.50.10")
    monkeypatch.setitem(sys.modules, "zeroconf", _fake_zeroconf_module())

    mobile_mdns.start_mdns_if_secure()
    mobile_mdns.start_mdns_if_secure()

    assert len(_FakeZeroconf.instances) == 1
    zc = _FakeZeroconf.instances[0]
    assert len(zc.registered) == 1
    info, allow_name_change = zc.registered[0]
    assert allow_name_change is False
    assert info.kwargs["type_"] == "_https._tcp.local."
    assert info.kwargs["name"] == "Digital Crown._https._tcp.local."
    assert info.kwargs["server"] == "digitalcrown.local."
    assert info.kwargs["port"] == 5173
    assert info.kwargs["properties"][b"scope"] == b"cabinet-lan"

    mobile_mdns.stop_mdns()

    assert zc.unregistered == [info]
    assert zc.closed is True
    assert mobile_mdns._zeroconf is None
    assert mobile_mdns._service_info is None


def test_runtime_packaging_and_mobile_trust_contracts_are_wired():
    routers_source = (REPO_ROOT / "backend" / "routers" / "__init__.py").read_text(encoding="utf-8")
    spec_source = (REPO_ROOT / "DigitalCrown.spec").read_text(encoding="utf-8")
    setup_source = (REPO_ROOT / "scripts" / "setup-https.ps1").read_text(encoding="utf-8")
    mdns_source = (REPO_ROOT / "backend" / "services" / "mobile_mdns.py").read_text(encoding="utf-8")

    assert "from backend.services.mobile_mdns import start_mdns_if_secure" in routers_source
    assert "start_mdns_if_secure()" in routers_source
    assert "atexit.register(stop_mdns)" in mdns_source
    assert "'zeroconf'" in spec_source
    assert "IMPORTANT : Installation sur Android" in setup_source
    assert "Certificat CA" in setup_source
    assert "Ne JAMAIS copier rootCA-key.pem" in setup_source
