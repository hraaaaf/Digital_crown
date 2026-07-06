from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent


def load_backend_env(override: bool = True) -> Path:
    """Load backend env vars, preferring an untracked local file."""
    candidates = (
        BASE_DIR / ".env.local",
        BASE_DIR / ".env",
    )

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
