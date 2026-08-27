from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
DEFAULT_HEALTH_URL = "http://127.0.0.1:8005/health"


class UpdatePostInstallError(RuntimeError):
    pass


def _require_packaged_version(value: str) -> str:
    version = str(value or "").strip()
    if VERSION_PATTERN.fullmatch(version) is None:
        raise UpdatePostInstallError("UPDATE_POST_INSTALL_VERSION_INVALID")
    return version


def verify_package_self_test(
    executable: Path | str,
    *,
    expected_version: str,
    report_dir: Path,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Verify the installed frozen package before trusting runtime health.

    Digital Crown's frozen executable already owns the authoritative package
    self-test and reads the bundled root VERSION. P10 reuses that contract
    rather than trusting Git metadata, installer labels, or an HTTP header.
    """
    expected = _require_packaged_version(expected_version)
    executable_path = Path(executable)
    if not executable_path.is_file():
        raise UpdatePostInstallError("UPDATE_POST_INSTALL_EXECUTABLE_MISSING")

    report_root = Path(report_dir)
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / f"package-self-test-{uuid.uuid4().hex}.json"
    env = os.environ.copy()
    env["DIGITALCROWN_PACKAGE_SELF_TEST_REPORT"] = str(report_path)

    try:
        proc = subprocess.run(
            [str(executable_path), "--package-self-test"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=max(1.0, float(timeout)),
            env=env,
            check=False,
        )
        if proc.returncode != 0:
            raise UpdatePostInstallError("UPDATE_POST_INSTALL_SELF_TEST_FAILED")
        if not report_path.is_file():
            raise UpdatePostInstallError("UPDATE_POST_INSTALL_REPORT_MISSING")
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise UpdatePostInstallError("UPDATE_POST_INSTALL_REPORT_INVALID") from exc
        if not isinstance(payload, dict):
            raise UpdatePostInstallError("UPDATE_POST_INSTALL_REPORT_INVALID")

        checks = {
            "status": payload.get("status") == "ok",
            "frozen": payload.get("frozen") is True,
            "version": str(payload.get("version") or "") == expected,
            "missing": payload.get("missing") == [],
            "forbidden_present": payload.get("forbidden_present") == [],
            "unqualified_scientific_weights_present": payload.get("unqualified_scientific_weights_present") == [],
            "scientific_manifest_policy_ok": payload.get("scientific_manifest_policy_ok") is True,
            "scientific_capabilities": payload.get("scientific_capabilities") == "FAIL_CLOSED_NO_WEIGHTS",
        }
        failed = sorted(name for name, ok in checks.items() if not ok)
        if failed:
            raise UpdatePostInstallError(
                "UPDATE_POST_INSTALL_PACKAGE_TRUTH_FAILED:" + ",".join(failed)
            )

        return {
            "status": "ok",
            "version": expected,
            "frozen": True,
            "scientific_capabilities": "FAIL_CLOSED_NO_WEIGHTS",
        }
    finally:
        report_path.unlink(missing_ok=True)


def _validate_health_url(url: str) -> str:
    parsed = urlparse(str(url or ""))
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise UpdatePostInstallError("UPDATE_POST_INSTALL_HEALTH_URL_NOT_LOOPBACK")
    if parsed.path != "/health" or parsed.params or parsed.query or parsed.fragment:
        raise UpdatePostInstallError("UPDATE_POST_INSTALL_HEALTH_URL_INVALID")
    return parsed.geturl()


def wait_runtime_health(
    *,
    health_url: str = DEFAULT_HEALTH_URL,
    timeout: float = 60.0,
    poll_interval: float = 1.0,
) -> dict[str, str]:
    """Wait for the local runtime and DB health gate after package self-test."""
    url = _validate_health_url(health_url)
    deadline = time.monotonic() + max(1.0, float(timeout))
    interval = max(0.05, float(poll_interval))
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "DigitalCrown-Updater/1"},
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=2) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if (
                    response.status == 200
                    and isinstance(payload, dict)
                    and payload.get("status") == "ok"
                    and payload.get("db") == "ok"
                ):
                    return {"status": "ok", "db": "ok"}
        except Exception as exc:  # runtime may still be starting
            last_error = exc
        time.sleep(interval)

    raise UpdatePostInstallError("UPDATE_POST_INSTALL_RUNTIME_HEALTH_FAILED") from last_error


def verify_post_install(
    executable: Path | str,
    *,
    expected_version: str,
    report_dir: Path,
    health_url: str = DEFAULT_HEALTH_URL,
    package_timeout: float = 120.0,
    health_timeout: float = 60.0,
) -> dict[str, Any]:
    package = verify_package_self_test(
        executable,
        expected_version=expected_version,
        report_dir=report_dir,
        timeout=package_timeout,
    )
    health = wait_runtime_health(health_url=health_url, timeout=health_timeout)
    return {
        "status": "ok",
        "version": package["version"],
        "package_self_test": "passed",
        "runtime_health": health,
        "scientific_capabilities": package["scientific_capabilities"],
    }
