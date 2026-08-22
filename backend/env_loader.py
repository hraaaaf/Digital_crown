from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from backend.core.paths import AppPaths


BASE_DIR = Path(__file__).resolve().parent
_WEAK_SECRETS = {
    "SET_A_REAL_SECRET_KEY_IN_ENV",
    "dev_only_secret_key_change_me",
    "default-dc-fallback-key",
    "changeme",
    "secret",
}


def _cabinet_env_path() -> Path:
    """Return the platform-owned persistent cabinet environment file."""
    return AppPaths.get_env_path()


def _appdata_env_path() -> Path:
    """Backward-compatible seam for existing cabinet integrations/tests."""
    return _cabinet_env_path()


def _enforce_cabinet_crypto_secret() -> None:
    """Fail before database import can ever use a predictable SQLCipher fallback."""
    if os.getenv("ENVIRONMENT", "development").strip().lower() != "cabinet":
        return

    dedicated = os.getenv("CABINET_MASTER_KEY_HEX", "").strip()
    shared = os.getenv("SECRET_KEY", "").strip()
    candidate = dedicated or shared
    if not candidate or candidate in _WEAK_SECRETS or len(candidate) < 32:
        raise RuntimeError(
            "SECURITE : mode cabinet refuse. Définissez CABINET_MASTER_KEY_HEX "
            "ou une SECRET_KEY forte (>= 32 caractères) avant toute ouverture de la base."
        )


def load_backend_env(override: bool = True) -> Path:
    """Load backend env vars from explicit, repository-dev, then platform config."""
    explicit = os.getenv("DIGITALCROWN_ENV_FILE", "").strip()
    candidates = [Path(explicit)] if explicit else []
    candidates += [
        BASE_DIR / ".env.local",
        BASE_DIR / ".env",
        _appdata_env_path(),
    ]

    for candidate in candidates:
        if candidate.exists():
            load_dotenv(candidate, override=override)
            _enforce_cabinet_crypto_secret()
            return candidate

    _enforce_cabinet_crypto_secret()
    return candidates[-1]


def current_backend_env_path() -> str:
    """Return the environment file path the backend should mutate/read."""
    override = os.getenv("DIGITALCROWN_ENV_FILE", "").strip()
    if override:
        return override

    if getattr(sys, "frozen", False):
        return str(_appdata_env_path())

    local_env = BASE_DIR / ".env.local"
    if local_env.exists():
        return str(local_env)

    return str(BASE_DIR / ".env")
