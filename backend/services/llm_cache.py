import hashlib
import time
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TTL_SECONDS = 300  # 5 minutes


class LLMCache:
    """Thread-safe in-memory LLM response cache with TTL eviction."""

    def __init__(self):
        self._store: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def _make_key(self, model: str, prompt: str) -> str:
        return hashlib.sha256(f"{model}||{prompt}".encode("utf-8")).hexdigest()

    def get(self, model: str, prompt: str) -> Optional[str]:
        key = self._make_key(model, prompt)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, ts = entry
            if time.time() - ts > TTL_SECONDS:
                del self._store[key]
                return None
            logger.debug("LLMCache: HIT key=%s", key[:12])
            return value

    def set(self, model: str, prompt: str, value: str) -> None:
        key = self._make_key(model, prompt)
        with self._lock:
            self._store[key] = (value, time.time())
            self._evict()

    def _evict(self) -> None:
        now = time.time()
        expired = [k for k, (_, ts) in self._store.items() if now - ts > TTL_SECONDS]
        for k in expired:
            del self._store[k]

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def stats(self) -> dict:
        with self._lock:
            return {"size": len(self._store), "ttl_seconds": TTL_SECONDS}


llm_cache = LLMCache()
