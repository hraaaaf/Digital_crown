import os
import time
import json
import threading
from fastapi import HTTPException, Request, status
from typing import Dict, Tuple

LIMIT_WINDOW = 600   # 10 minutes
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

def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    with _lock:
        attempts = _load()
        # Purge expired entries
        attempts = {ip: v for ip, v in attempts.items() if now - v[1] <= LIMIT_WINDOW}

        if client_ip in attempts:
            count, first_time = attempts[client_ip]
            if now - first_time > LIMIT_WINDOW:
                attempts[client_ip] = (1, now)
            elif count >= MAX_ATTEMPTS:
                retry_after = int(LIMIT_WINDOW - (now - first_time))
                _save(attempts)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Trop de tentatives de connexion. Réessayez dans {retry_after} secondes.",
                    headers={"Retry-After": str(retry_after)}
                )
            else:
                attempts[client_ip] = (count + 1, first_time)
        else:
            attempts[client_ip] = (1, now)

        _save(attempts)
