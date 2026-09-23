import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Dict, Tuple

from fastapi import HTTPException, Request, status

LIMIT_WINDOW = 600
MAX_ATTEMPTS = 5

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_attempts: Dict[str, Tuple[int, float]] = {}
_loaded = False


def _store_path() -> Path:
    from backend.core.paths import AppPaths

    return AppPaths.get_runtime_dir() / "rate_limit_store.json"


def _load_once() -> None:
    global _loaded, _attempts
    if _loaded:
        return
    try:
        path = _store_path()
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            _attempts = {
                str(key): (int(value[0]), float(value[1]))
                for key, value in raw.items()
                if isinstance(value, (list, tuple)) and len(value) == 2
            }
    except Exception as exc:
        logger.warning("Rate-limit persisted state unreadable; continuing with in-memory protection: %s", type(exc).__name__)
        _attempts = {}
    finally:
        _loaded = True


def _save() -> None:
    """Best-effort persistence; in-memory enforcement remains authoritative."""
    temp: Path | None = None
    try:
        path = _store_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        temp.write_text(json.dumps(_attempts), encoding="utf-8")
        os.replace(temp, path)
    except Exception as exc:
        logger.warning("Rate-limit persistence failed; in-memory protection remains active: %s", type(exc).__name__)
    finally:
        if temp is not None:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass


def check_rate_limit(request: Request, scope: str = "auth", *, max_attempts: int = MAX_ATTEMPTS) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{scope}:{client_ip}"
    now = time.time()

    with _lock:
        _load_once()

        expired = [key for key, (_count, first_time) in _attempts.items() if now - first_time > LIMIT_WINDOW]
        for expired_key in expired:
            _attempts.pop(expired_key, None)

        count, first_time = _attempts.get(key, (0, now))
        if count >= max_attempts:
            retry_after = max(1, int(LIMIT_WINDOW - (now - first_time)))
            _save()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Trop de tentatives. Réessayez dans {retry_after} secondes.",
                headers={"Retry-After": str(retry_after)},
            )

        _attempts[key] = (count + 1, first_time)
        _save()
