import json
import os
import sys
from pathlib import Path


def _maybe_run_package_self_test() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "--package-self-test":
        return
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    required = [
        root / "VERSION",
        root / "frontend" / "dist" / "index.html",
        root / "backend" / "scientific_assets.json",
        root / "backend" / "templates" / "bilan_ortho_elite.html",
        root / "backend" / "static" / "assets" / "fonts" / "Outfit-Regular.ttf",
        root / "backend" / "static" / "assets" / "fonts" / "Outfit-Bold.ttf",
        root / "backend" / "data" / "cephalometry" / "measurement_definitions.yaml",
        root / "backend" / "data" / "cephalometry" / "normative_profiles.yaml",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.exists()]
    forbidden = [
        root / ".env",
        root / "backend" / ".env",
        root / "backend" / "core" / "firebase_creds.json",
    ]
    leaked = [str(path.relative_to(root)) for path in forbidden if path.exists()]
    unqualified_scientific_weights = [
        root / "backend" / "ai_models" / "panoramic_model.onnx",
        root / "backend" / "ai_models" / "cephld_cca" / "ceph_weights.pth",
        root / "backend" / "ai_models" / "model.onnx",
        root / "backend" / "ai_models" / "cephalometric_sota" / "model.onnx",
    ]
    scientific_weights_present = [
        str(path.relative_to(root)) for path in unqualified_scientific_weights if path.exists()
    ]

    scientific_policy_ok = False
    manifest_path = root / "backend" / "scientific_assets.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            assets = {item["id"]: item for item in manifest["assets"]}
            scientific_policy_ok = (
                assets["cephalo_sota"]["lifecycle"] == "deferred"
                and assets["cephalo_legacy"]["lifecycle"] == "external"
                and assets["panoramic"]["lifecycle"] == "external"
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            scientific_policy_ok = False

    status_ok = not missing and not leaked and not scientific_weights_present and scientific_policy_ok
    payload = {
        "status": "ok" if status_ok else "error",
        "frozen": bool(getattr(sys, "frozen", False)),
        "version": (root / "VERSION").read_text(encoding="utf-8").strip() if (root / "VERSION").exists() else None,
        "missing": missing,
        "forbidden_present": leaked,
        "unqualified_scientific_weights_present": scientific_weights_present,
        "scientific_manifest_policy_ok": scientific_policy_ok,
        "scientific_capabilities": "FAIL_CLOSED_NO_WEIGHTS",
    }
    print("P6_SCIENTIFIC_CAPABILITIES=FAIL_CLOSED")
    print("P6_PACKAGE_SELF_TEST=" + json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "ok" else 1)


_maybe_run_package_self_test()


def _first_boot_bootstrap() -> None:
    """Create the persistent cabinet environment on first packaged launch."""
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


def _maybe_run_guided_restore_worker() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "--guided-restore-worker":
        return

    import argparse

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--guided-restore-worker", dest="restore_id", required=True)
    parser.add_argument("--parent-pid", dest="parent_pid", type=int, required=True)
    args = parser.parse_args(sys.argv[1:])

    from backend.services.guided_restore_worker import GuidedRestoreWorker

    raise SystemExit(GuidedRestoreWorker.run(args.restore_id, args.parent_pid, sys.executable))


_first_boot_bootstrap()
_setup_frozen_logging()
_maybe_run_guided_restore_worker()

import multiprocessing
import threading
import uvicorn


def _load_launcher_environment() -> None:
    from backend.env_loader import load_backend_env

    load_backend_env(override=False)
    if os.environ.get("ENVIRONMENT", "development").lower() in ("development", "local", "test"):
        load_backend_env(override=True)


def _resolve_host_port():
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
