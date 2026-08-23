import os
import time
import json
import threading
from fastapi import HTTPException, Request, status
from typing import Dict, Tuple

LIMIT_WINDOW = 600
MAX_ATTEMPTS = 5

_lock = threading.Lock()
_store_path = os.path.join(os.path.dirname(__file__), ".rate_limit_store.json")


def _load() -> Dict[str, Tuple[int, float]]:
    try:
        if os.path.exists(_store_path):
            with open(_store_path, "r") as f:
                raw = json.load(f)
                return {k: tuple(v) for k, v in raw.items()}
    except Exception:
        pass
    return {}


def _save(data: Dict[str, Tuple[int, float]]):
    try:
        with open(_store_path, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def check_rate_limit(request: Request, scope: str = "auth"):
    client_ip = request.client.host if request.client else "unknown"
    key = f"{scope}:{client_ip}"
    now = time.time()

    with _lock:
        attempts = _load()
        attempts = {k: v for k, v in attempts.items() if now - v[1] <= LIMIT_WINDOW}
        if key in attempts:
            count, first_time = attempts[key]
            if now - first_time > LIMIT_WINDOW:
                attempts[key] = (1, now)
            elif count >= MAX_ATTEMPTS:
                retry_after = int(LIMIT_WINDOW - (now - first_time))
                _save(attempts)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Trop de tentatives. Réessayez dans {retry_after} secondes.",
                    headers={"Retry-After": str(retry_after)},
                )
            else:
                attempts[key] = (count + 1, first_time)
        else:
            attempts[key] = (1, now)
        _save(attempts)
