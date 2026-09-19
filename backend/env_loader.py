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


def _is_strong_secret(value: str) -> bool:
    candidate = str(value or "").strip()
    return bool(candidate) and candidate not in _WEAK_SECRETS and len(candidate) >= 32


def _is_valid_master_key_hex(value: str) -> bool:
    candidate = str(value or "").strip()
    if len(candidate) != 64:
        return False
    try:
        bytes.fromhex(candidate)
    except ValueError:
        return False
    return True


def _enforce_cabinet_crypto_secret() -> None:
    """Fail closed unless JWT signing and cabinet encryption have independent strong keys."""
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    if environment not in {"cabinet", "production"}:
        return

    jwt_secret = os.getenv("SECRET_KEY", "").strip()
    if not _is_strong_secret(jwt_secret):
        raise RuntimeError(
            "SECURITE : cabinet/production refuse. SECRET_KEY doit être forte "
            "(>= 32 caractères) et ne peut pas utiliser une valeur par défaut."
        )

    master_key = os.getenv("CABINET_MASTER_KEY_HEX", "").strip()
    if not _is_valid_master_key_hex(master_key):
        raise RuntimeError(
            "SECURITE : cabinet/production refuse. CABINET_MASTER_KEY_HEX doit "
            "contenir exactement 32 octets aléatoires encodés en 64 caractères hexadécimaux."
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
