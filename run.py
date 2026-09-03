import os
import sys


def _first_boot_bootstrap() -> None:
    """Create the persistent cabinet environment on first packaged launch.

    This runs before importing ``backend.main`` so cabinet secrets exist before
    settings/database initialization. Development launches remain untouched.
    """
    if not getattr(sys, "frozen", False):
        return

    from backend.core.paths import AppPaths
    from backend.core.platform import get_platform_adapter

    env_path = AppPaths.get_env_path()
    if env_path.exists():
        return

    import secrets
    import socket

    def _detect_lan_ip() -> str | None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return None

    origins = "http://127.0.0.1:8005"
    lan_ip = _detect_lan_ip()
    if lan_ip:
        origins += f",http://{lan_ip}:8005"

    env_content = (
        "# Généré automatiquement au premier démarrage — ne pas modifier à la main,\n"
        "# ne jamais partager ce fichier (contient des secrets uniques à ce poste).\n"
        "ENVIRONMENT=cabinet\n"
        f"SECRET_KEY={secrets.token_hex(32)}\n"
        f"CABINET_MASTER_KEY_HEX={secrets.token_hex(32)}\n"
        f"ALLOWED_ORIGINS={origins}\n"
    )
    get_platform_adapter().atomic_write_text(env_path, env_content)


def _setup_frozen_logging() -> None:
    """Redirect packaged-app logs to the platform-owned log directory."""
    if not getattr(sys, "frozen", False):
        return

    import logging
    from logging.handlers import RotatingFileHandler
    from backend.core.paths import AppPaths

    log_dir = AppPaths.get_log_dir()
    handler = RotatingFileHandler(
        log_dir / "digitalcrown.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    def _log_uncaught_exception(exc_type, exc_value, exc_tb):
        logging.getLogger("uncaught").critical(
            "Exception non interceptée — arrêt de l'application",
            exc_info=(exc_type, exc_value, exc_tb),
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _log_uncaught_exception


def _maybe_run_sec1_package_self_test() -> None:
    """Exercise signed-license verification from the frozen executable itself.

    The key pair is generated in memory for this diagnostic invocation only. It
    is never a production trust anchor and is never written to disk. The command
    is intentionally side-effect free with respect to cabinet data/config.
    """
    prefix = "--sec1-package-self-test="
    report_arg = next((arg[len(prefix):] for arg in sys.argv[1:] if arg.startswith(prefix)), None)
    if report_arg is None and "--sec1-package-self-test" not in sys.argv[1:]:
        return
    if not getattr(sys, "frozen", False):
        raise SystemExit(64)

    import base64
    import json
    from datetime import datetime, timedelta, timezone
    from pathlib import Path

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

    from backend.license_security import (
        LICENSE_AUDIENCE,
        LICENSE_ISSUER,
        LICENSE_SCHEMA_VERSION,
        LicenseSecurityError,
        sign_license,
        verify_license,
    )

    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    now = datetime.now(timezone.utc)
    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_raw = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    key_id = "sec1-package-ephemeral"
    cabinet_id = "sec1-package-self-test-cabinet"
    claims = {
        "schema_version": LICENSE_SCHEMA_VERSION,
        "issuer": LICENSE_ISSUER,
        "audience": LICENSE_AUDIENCE,
        "license_id": "sec1-package-self-test",
        "cabinet_id": cabinet_id,
        "created_by_user_id": 1,
        "policy_version": "sec1-package-self-test-v1",
        "license_type": "PAID",
        "status": "ACTIVE",
        "issued_at": (now - timedelta(seconds=1)).isoformat(),
        "not_before": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(days=1)).isoformat(),
        "release_channel": "stable",
        "feature_set": "GOLD",
        "max_devices": 1,
    }
    token = sign_license(claims, _b64url(private_raw), key_id)
    trusted = {key_id: _b64url(public_raw)}
    verified = verify_license(token, trusted, expected_cabinet_id=cabinet_id, now=now)
    valid_signature_accepted = verified.license_id == "sec1-package-self-test"

    encoded_header, encoded_payload, encoded_signature = token.split(".")
    payload = json.loads(base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4)).decode("utf-8"))
    payload["feature_set"] = "ELITE"
    tampered_payload = _b64url(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    tampered_token = f"{encoded_header}.{tampered_payload}.{encoded_signature}"
    tampered_payload_rejected = False
    try:
        verify_license(tampered_token, trusted, expected_cabinet_id=cabinet_id, now=now)
    except LicenseSecurityError:
        tampered_payload_rejected = True

    report = {
        "frozen_executable": True,
        "valid_signature_accepted": valid_signature_accepted,
        "tampered_payload_rejected": tampered_payload_rejected,
        "key_material": "ephemeral-memory-only",
    }
    report_path = Path(report_arg or os.environ.get("DIGITALCROWN_SEC1_REPORT", "sec1-package-self-test.json"))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2), encoding="utf-8")
    raise SystemExit(0 if valid_signature_accepted and tampered_payload_rejected else 1)


def _maybe_run_guided_restore_worker() -> None:
    """Run the restore worker before importing the FastAPI runtime."""
    if len(sys.argv) < 2 or sys.argv[1] != "--guided-restore-worker":
        return

    import argparse

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--guided-restore-worker", dest="restore_id", required=True)
    parser.add_argument("--parent-pid", dest="parent_pid", type=int, required=True)
    args = parser.parse_args(sys.argv[1:])

    from backend.services.guided_restore_worker import GuidedRestoreWorker

    raise SystemExit(GuidedRestoreWorker.run(args.restore_id, args.parent_pid, sys.executable))


_maybe_run_sec1_package_self_test()
_first_boot_bootstrap()
_setup_frozen_logging()
_maybe_run_guided_restore_worker()

import multiprocessing
import threading

import uvicorn


def _load_launcher_environment() -> None:
    """Load the canonical env before resolving cabinet host/port or acquiring runtime state."""
    from backend.env_loader import load_backend_env

    load_backend_env(override=False)
    if os.environ.get("ENVIRONMENT", "development").lower() in ("development", "local", "test"):
        load_backend_env(override=True)


def _resolve_host_port():
    """Resolve the listen address according to the application environment."""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    default_host = "0.0.0.0" if env == "cabinet" else "127.0.0.1"
    host = os.environ.get("CABINET_HOST", default_host)
    port = int(os.environ.get("CABINET_PORT", "8005"))
    return host, port


def main() -> int:
    multiprocessing.freeze_support()
    _load_launcher_environment()
    host, port = _resolve_host_port()
    instance_lock = None

    if getattr(sys, "frozen", False):
        from backend.core.runtime_supervisor import RuntimeSupervisor

        supervisor = RuntimeSupervisor(port)
        suppress_browser = os.environ.get("DIGITALCROWN_RESTORE_RESTART") == "1"
        instance_lock = supervisor.claim_or_focus_existing(open_existing=not suppress_browser)
        if instance_lock is None:
            return 0
        if not suppress_browser:
            threading.Thread(
                target=supervisor.open_ui_when_ready,
                kwargs={"timeout": 120.0},
                daemon=True,
            ).start()

    from backend.main import app

    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
        return 0
    finally:
        if instance_lock is not None:
            instance_lock.release()


if __name__ == "__main__":
    raise SystemExit(main())
