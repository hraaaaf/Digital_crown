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
    """Explicit, isolated first boot after installable verification."""
    if not getattr(sys, "frozen", False):
        return
    from pathlib import Path
    from backend.core.paths import AppPaths
    from backend.core.platform import get_platform_adapter, PlatformAdapter
    explicit_env = os.getenv("DIGITALCROWN_ENV_FILE", "").strip()
    if not explicit_env or not Path(explicit_env).is_absolute():
        raise RuntimeError("Packaged cabinet requires an explicit absolute environment profile")
    env_path = Path(explicit_env)
    if env_path.exists():
        if "--initialize-new-cabinet" in sys.argv:
            raise RuntimeError("Existing configuration refused for new-cabinet initialization")
        return
    if "--initialize-new-cabinet" not in sys.argv:
        raise RuntimeError("Une mise à jour ne doit jamais créer silencieusement une nouvelle base. Select the existing explicit environment.")
    names = ("DIGITALCROWN_USER_DATA_DIR", "DIGITALCROWN_CONFIG_DIR",
             "DIGITALCROWN_RUNTIME_DIR", "DIGITALCROWN_LOG_DIR", "DIGITALCROWN_ENV_FILE")
    paths = {}
    for name in names:
        value = os.getenv(name, "").strip()
        if not value or not Path(value).is_absolute():
            raise RuntimeError("New cabinet requires five explicit absolute isolated paths")
        paths[name] = Path(value).resolve()
    data = paths["DIGITALCROWN_USER_DATA_DIR"]
    root = data.parent
    directories = [paths[name] for name in names[:-1]]
    if data.name != "data" or len(set(directories)) != 4 or any(path.parent != root for path in directories):
        raise RuntimeError("New cabinet requires distinct data/config/runtime/log directories in its dedicated root")
    if paths["DIGITALCROWN_ENV_FILE"].parent != paths["DIGITALCROWN_CONFIG_DIR"]:
        raise RuntimeError("New cabinet environment must be in its config directory")
    if root == PlatformAdapter(environ={}).user_data_dir().resolve():
        raise RuntimeError("Historical default cabinet namespace forbidden")
    if any(path.exists() and (not path.is_dir() or any(path.iterdir())) for path in directories):
        raise RuntimeError("New cabinet requires empty isolated directories")
    if root.exists() and any(path.resolve() not in directories for path in root.iterdir()):
        raise RuntimeError("New cabinet root contains unrelated existing files")
    import secrets
    import uuid
    content = "ENVIRONMENT=cabinet\nDEBUG=false\nCABINET_HOST=127.0.0.1\nALLOWED_ORIGINS=http://127.0.0.1:8005\n"
    for name in ("SECRET_KEY", "PAIRING_CODE_PEPPER", "CABINET_MASTER_KEY_HEX", "SQLCIPHER_KEY_HEX", "MOBILE_PAIRING_KEY_HEX"):
        content += f"{name}={secrets.token_hex(32)}\n"
    content += f"DIGITALCROWN_INSTANCE_ID={uuid.uuid4()}\n"
    content += f'DATABASE_URL="sqlite:///{(data / "clinical_vault.db").as_posix()}"\n'
    content += f'MEDIA_ROOT="{(data / "media").as_posix()}"\n'
    for name, path in paths.items():
        content += f'{name}="{path.as_posix()}"\n'
    # Exclusive creation prevents two initializations from replacing each other's keys.
    get_platform_adapter().ensure_private_directory(env_path.parent)
    descriptor = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _provision_new_cabinet_interactively() -> bool:
    """Native secret input works with the packaged console=False executable."""
    import tkinter
    from tkinter import simpledialog, messagebox
    from backend.core.new_cabinet_setup import provision_new_cabinet
    window = tkinter.Tk()
    window.withdraw()
    try:
        email = simpledialog.askstring("Digital Crown", "Adresse email du propriétaire :", parent=window)
        if not email:
            return False
        password = simpledialog.askstring("Digital Crown", "Mot de passe (12 caractères minimum) :", show="*", parent=window)
        confirmation = simpledialog.askstring("Digital Crown", "Confirmez le mot de passe :", show="*", parent=window)
        if not password or password != confirmation:
            messagebox.showerror("Digital Crown", "Création annulée : mots de passe absents ou différents.", parent=window)
            return False
        provision_new_cabinet(email, password, resume="--resume-new-cabinet-setup" in sys.argv)
        messagebox.showinfo("Digital Crown", "Propriétaire créé. La licence et l'enrôlement du poste restent à effectuer par le parcours authentifié.", parent=window)
        return True
    finally:
        window.destroy()


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


def _select_cabinet_env_profile() -> None:
    """Profile argument is selected only after the release identity is verified."""
    if "--cabinet-env-file" in sys.argv:
        from pathlib import Path
        index = sys.argv.index("--cabinet-env-file")
        if index + 1 >= len(sys.argv) or not Path(sys.argv[index + 1]).is_absolute():
            raise RuntimeError("An absolute cabinet environment file is required")
        os.environ["DIGITALCROWN_ENV_FILE"] = sys.argv[index + 1]


def _load_launcher_environment() -> None:
    """Load the canonical env before resolving cabinet host/port or acquiring runtime state."""
    from backend.env_loader import load_backend_env

    load_backend_env(override=bool(getattr(sys, 'frozen', False)))


# Order is security-sensitive: INSTALLABLE identity is checked before any env/data write.
_verify_frozen_release_certification()
_select_cabinet_env_profile()
_first_boot_bootstrap()
if getattr(sys, "frozen", False):
    _load_launcher_environment()
_setup_frozen_logging()
_maybe_run_guided_restore_worker()

import multiprocessing
import threading

import uvicorn


def _resolve_runtime_network():
    """Compatibility wrapper over the canonical V1.5-01 transport contract."""
    from backend.core.cabinet_topology import resolve_cabinet_network

    contract = resolve_cabinet_network()
    return (
        contract.host,
        contract.port,
        contract.https_enabled,
        contract.cert_file,
        contract.key_file,
    )


def main() -> int:
    multiprocessing.freeze_support()
    _load_launcher_environment()
    if '--provision-new-cabinet' in sys.argv:
        return 0 if _provision_new_cabinet_interactively() else 1
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
