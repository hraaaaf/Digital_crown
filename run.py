import sys
import os


def _first_boot_bootstrap() -> None:
    """Génère %APPDATA%/DigitalCrown/.env au tout premier démarrage de l'EXE
    packagé, s'il n'existe pas encore — secrets aléatoires, jamais écrasé.

    Doit s'exécuter AVANT `from backend.main import app` : `backend/main.py`
    appelle `load_backend_env()` dès son import (niveau module), qui lit ce
    fichier s'il existe déjà. Sans ce bootstrap, un EXE fraîchement installé
    n'a aucun `.env` et `SECRET_KEY` retombe sur un placeholder faible — le
    lifespan de `backend/main.py` refuse alors de démarrer (garde-fou
    sécurité volontaire, cf. `validate_environment_invariants`).

    Ne s'exécute JAMAIS hors du build PyInstaller (`sys.frozen`) : lancer
    `python run.py` en dev garde le comportement actuel (`backend/.env` ou
    `.env.local`, `ENVIRONMENT=development` par défaut) — aucun changement
    pour les postes de développement.

    N'importe volontairement que `backend.env_loader` (aucune dépendance sur
    `backend.config`/`backend.database`) pour ne jamais déclencher la lecture
    des settings avant que ce fichier n'existe.
    """
    if not getattr(sys, "frozen", False):
        return

    from backend.env_loader import _appdata_env_path

    env_path = _appdata_env_path()
    if env_path is None or env_path.exists():
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
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(env_content, encoding="utf-8")


def _setup_frozen_logging() -> None:
    """Redirige les logs applicatifs vers un fichier quand l'EXE est packagé
    sans console (`console=False` dans `DigitalCrown.spec`)."""
    if not getattr(sys, "frozen", False):
        return

    import logging
    from logging.handlers import RotatingFileHandler
    from backend.core.paths import AppPaths

    log_dir = AppPaths.get_user_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
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
    """Exécute le worker de restauration avant tout import du runtime FastAPI.

    Le worker tourne dans un second processus du même EXE, attend l'arrêt du
    processus applicatif, applique la restauration puis relance l'EXE. Il ne
    doit donc jamais importer backend.main avant d'avoir terminé son travail.
    """
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

import uvicorn
import multiprocessing
import threading
import time
import webbrowser
from backend.main import app


def _resolve_host_port():
    """Résout l'adresse d'écoute selon l'environnement."""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    default_host = "0.0.0.0" if env == "cabinet" else "127.0.0.1"
    host = os.environ.get("CABINET_HOST", default_host)
    port = int(os.environ.get("CABINET_PORT", "8005"))
    return host, port


def open_browser(port: int):
    time.sleep(2)
    webbrowser.open(f"http://127.0.0.1:{port}")


if __name__ == '__main__':
    multiprocessing.freeze_support()

    host, port = _resolve_host_port()

    if (
        getattr(sys, 'frozen', False)
        and os.environ.get("DIGITALCROWN_RESTORE_RESTART") != "1"
    ):
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="info")
