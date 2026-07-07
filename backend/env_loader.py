from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent


def _appdata_env_path() -> Path | None:
    """Chemin du .env cabinet posé à l'installation (%APPDATA%/DigitalCrown/.env).

    Utilisé par le build EXE : l'exécutable n'embarque AUCUN fichier .env
    (jamais de secrets dans le binaire distribué) — la configuration réelle du
    cabinet vit dans %APPDATA%, posée par la procédure d'installation
    (docs/CABINET_ONPREM_GUIDE.md §3-4).
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "DigitalCrown" / ".env"
    return Path.home() / ".config" / "DigitalCrown" / ".env"


def load_backend_env(override: bool = True) -> Path:
    """Load backend env vars, preferring an explicit or untracked local file.

    Ordre de priorité :
    1. DIGITALCROWN_ENV_FILE (chemin explicite — services/installations)
    2. backend/.env.local (dev, non versionné)
    3. backend/.env (base versionnée, placeholders)
    4. %APPDATA%/DigitalCrown/.env (cabinet on-premise — seul candidat
       existant en mode EXE frozen, où aucun .env n'est embarqué)
    """
    explicit = os.getenv("DIGITALCROWN_ENV_FILE", "").strip()
    candidates = [Path(explicit)] if explicit else []
    candidates += [
        BASE_DIR / ".env.local",
        BASE_DIR / ".env",
    ]
    appdata_env = _appdata_env_path()
    if appdata_env is not None:
        candidates.append(appdata_env)

    for candidate in candidates:
        if candidate.exists():
            load_dotenv(candidate, override=override)
            return candidate

    return candidates[-1]


def current_backend_env_path() -> str:
    """Return the env file path the backend should mutate/read."""
    override = os.getenv("DIGITALCROWN_ENV_FILE", "").strip()
    if override:
        return override

    local_env = BASE_DIR / ".env.local"
    if local_env.exists():
        return str(local_env)

    return str(BASE_DIR / ".env")
