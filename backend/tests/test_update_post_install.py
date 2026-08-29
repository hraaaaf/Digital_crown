from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.services import update_post_install
from backend.services.update_post_install import (
    UpdatePostInstallError,
    verify_package_self_test,
    verify_post_install,
    wait_runtime_health,
)


def _fake_executable(tmp_path: Path) -> Path:
    path = tmp_path / "DigitalCrown.exe"
    path.write_bytes(b"candidate")
    return path


def _install_fake_self_test(monkeypatch, *, version: str = "1.1.0", weights=None, returncode: int = 0):
    def fake_run(args, **kwargs):
        report = Path(kwargs["env"]["DIGITALCROWN_PACKAGE_SELF_TEST_REPORT"])
        report.write_text(
            json.dumps(
                {
                    "status": "ok",
                    "frozen": True,
                    "version": version,
                    "missing": [],
                    "forbidden_present": [],
                    "unqualified_scientific_weights_present": [] if weights is None else weights,
                    "scientific_manifest_policy_ok": True,
                    "scientific_capabilities": "FAIL_CLOSED_NO_WEIGHTS",
                }
            ),
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=returncode, stdout="")

    monkeypatch.setattr(update_post_install.subprocess, "run", fake_run)


class _HealthResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b'{"status":"ok","db":"ok"}'


def test_package_self_test_uses_exact_packaged_version(tmp_path, monkeypatch):
    executable = _fake_executable(tmp_path)
    _install_fake_self_test(monkeypatch, version="1.1.0")

    result = verify_package_self_test(
        executable,
        expected_version="1.1.0",
        report_dir=tmp_path / "reports",
    )

    assert result == {
        "status": "ok",
        "version": "1.1.0",
        "frozen": True,
        "scientific_capabilities": "FAIL_CLOSED_NO_WEIGHTS",
    }
    assert list((tmp_path / "reports").glob("package-self-test-*.json")) == []


def test_package_self_test_rejects_version_mismatch(tmp_path, monkeypatch):
    executable = _fake_executable(tmp_path)
    _install_fake_self_test(monkeypatch, version="1.0.0")

    with pytest.raises(UpdatePostInstallError, match="version"):
        verify_package_self_test(
            executable,
            expected_version="1.1.0",
            report_dir=tmp_path / "reports",
        )


def test_package_self_test_rejects_unqualified_scientific_weights(tmp_path, monkeypatch):
    executable = _fake_executable(tmp_path)
    _install_fake_self_test(monkeypatch, weights=["backend/ai_models/model.onnx"])

    with pytest.raises(UpdatePostInstallError, match="unqualified_scientific_weights_present"):
        verify_package_self_test(
            executable,
            expected_version="1.1.0",
            report_dir=tmp_path / "reports",
        )


def test_health_gate_is_loopback_only(monkeypatch):
    with pytest.raises(UpdatePostInstallError, match="NOT_LOOPBACK"):
        wait_runtime_health(health_url="https://example.com/health", timeout=1, poll_interval=0.05)


def test_verify_post_install_cross_checks_package_and_runtime(tmp_path, monkeypatch):
    executable = _fake_executable(tmp_path)
    _install_fake_self_test(monkeypatch, version="1.1.0")
    monkeypatch.setattr(update_post_install.urllib.request, "urlopen", lambda *a, **k: _HealthResponse())

    result = verify_post_install(
        executable,
        expected_version="1.1.0",
        report_dir=tmp_path / "reports",
        health_timeout=1,
    )

    assert result["status"] == "ok"
    assert result["version"] == "1.1.0"
    assert result["package_self_test"] == "passed"
    assert result["runtime_health"] == {"status": "ok", "db": "ok"}
