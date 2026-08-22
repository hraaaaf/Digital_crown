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


_first_boot_bootstrap()
_setup_frozen_logging()
_maybe_run_guided_restore_worker()

import multiprocessing
import threading
import time

import uvicorn

from backend.main import app


def _resolve_host_port():
    """Resolve the listen address according to the application environment."""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    default_host = "0.0.0.0" if env == "cabinet" else "127.0.0.1"
    host = os.environ.get("CABINET_HOST", default_host)
    port = int(os.environ.get("CABINET_PORT", "8005"))
    return host, port


def open_browser(port: int):
    # P2 replaces this fixed delay with an actual readiness gate.
    from backend.core.platform import get_platform_adapter

    time.sleep(2)
    get_platform_adapter().open_uri(f"http://127.0.0.1:{port}")


if __name__ == "__main__":
    multiprocessing.freeze_support()

    host, port = _resolve_host_port()

    if (
        getattr(sys, "frozen", False)
        and os.environ.get("DIGITALCROWN_RESTORE_RESTART") != "1"
    ):
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="info")
