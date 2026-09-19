import os
import sys


def _verify_frozen_release_certification() -> None:
    """Fail closed before any first-boot write when a packaged build is not installable."""
    if not getattr(sys, "frozen", False):
        return

    from pathlib import Path
    from backend.release_certification import verify_installable_release_identity

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    verify_installable_release_identity(bundle_root)


def _first_boot_bootstrap() -> None:
    """Create the persistent cabinet environment on first packaged launch.

    This runs before importing ``backend.main`` so cabinet secrets exist before
    settings/database initialization. Development launches remain untouched.
    """
    if not getattr(sys, "frozen", False):
        return

    from pathlib import Path
    from backend.core.paths import AppPaths
    from backend.core.platform import get_platform_adapter

    explicit_env = os.getenv("DIGITALCROWN_ENV_FILE", "").strip()
    env_path = Path(explicit_env) if explicit_env else AppPaths.get_env_path()
    if env_path.exists():
        return

    if "--initialize-new-cabinet" not in sys.argv:
        raise RuntimeError(
            "SECURITE : aucun environnement cabinet existant n'a été trouvé. "
            "Une mise à jour ne doit jamais créer silencieusement une nouvelle base. "
            "Utilisez DIGITALCROWN_ENV_FILE pour un cabinet existant ou "
            "--initialize-new-cabinet uniquement pour une installation neuve."
        )

    import secrets
    import socket

    def _detect_lan_ip() -> str | None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return None

    # First boot is loopback-only. LAN exposure is enabled later only through
    # the explicit HTTPS/certificate contract.
    origins = "http://127.0.0.1:8005"

    env_content = (
        "# Généré automatiquement au premier démarrage — ne pas modifier à la main,\n"
        "# ne jamais partager ce fichier (contient des secrets uniques à ce poste).\n"
        "ENVIRONMENT=cabinet\n"
        f"SECRET_KEY={secrets.token_hex(32)}\n"
        f"CABINET_MASTER_KEY_HEX={secrets.token_hex(32)}\n"
        f"ALLOWED_ORIGINS={origins}\n"
        "CABINET_HOST=127.0.0.1\n"
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


# Order is security-sensitive: INSTALLABLE identity is checked before any env/data write.
_verify_frozen_release_certification()
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


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_runtime_network():
    """Resolve a fail-closed local/LAN transport contract for the packaged runtime."""
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    host = os.environ.get("CABINET_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = int(os.environ.get("CABINET_PORT", "8005"))
    https_enabled = _truthy_env("DIGITALCROWN_ENABLE_HTTPS")
    cert_file = os.environ.get("DIGITALCROWN_TLS_CERT_FILE", "").strip()
    key_file = os.environ.get("DIGITALCROWN_TLS_KEY_FILE", "").strip()

    loopback_hosts = {"127.0.0.1", "localhost", "::1"}
    if https_enabled:
        if not cert_file or not key_file:
            raise RuntimeError("SECURITE : HTTPS cabinet exige DIGITALCROWN_TLS_CERT_FILE et DIGITALCROWN_TLS_KEY_FILE.")
        if not os.path.isfile(cert_file) or not os.path.isfile(key_file):
            raise RuntimeError("SECURITE : certificat/clé TLS cabinet introuvable.")
    elif env in {"cabinet", "production"} and host not in loopback_hosts:
        raise RuntimeError(
            "SECURITE : exposition réseau cabinet/production refusée sans HTTPS explicite ; "
            "utilisez 127.0.0.1 ou configurez TLS."
        )

    return host, port, https_enabled, cert_file, key_file


def main() -> int:
    multiprocessing.freeze_support()
    _load_launcher_environment()
    host, port, https_enabled, cert_file, key_file = _resolve_runtime_network()
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
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            ssl_certfile=cert_file if https_enabled else None,
            ssl_keyfile=key_file if https_enabled else None,
        )
        return 0
    finally:
        if instance_lock is not None:
            instance_lock.release()


if __name__ == "__main__":
    raise SystemExit(main())
