from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.core.platform import PlatformAdapter, PlatformFileLock, get_platform_adapter


class RuntimeSupervisor:
    """Own single-instance and readiness behavior for the packaged local runtime."""

    def __init__(
        self,
        port: int,
        *,
        adapter: PlatformAdapter | None = None,
        runtime_dir: str | Path | None = None,
        request_timeout: float = 1.5,
    ) -> None:
        if not 1 <= int(port) <= 65535:
            raise ValueError("port must be between 1 and 65535")
        self.port = int(port)
        self.adapter = adapter or get_platform_adapter()
        self.runtime_dir = Path(runtime_dir) if runtime_dir is not None else self.adapter.runtime_dir()
        self.request_timeout = max(0.1, float(request_timeout))

    @property
    def ui_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.ui_url}/health"

    @property
    def lock_path(self) -> Path:
        return self.runtime_dir / "digitalcrown.instance.lock"

    def try_acquire_instance(self) -> PlatformFileLock | None:
        return self.adapter.try_acquire_process_lock(self.lock_path)

    def is_ready(self) -> bool:
        request = Request(self.health_url, headers={"Cache-Control": "no-store"})
        try:
            with urlopen(request, timeout=self.request_timeout) as response:
                if getattr(response, "status", response.getcode()) != 200:
                    return False
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
            return False
        return payload.get("status") == "ok" and payload.get("db") == "ok"

    def wait_until_ready(self, *, timeout: float = 120.0, poll_interval: float = 0.25) -> bool:
        deadline = time.monotonic() + max(0.0, float(timeout))
        interval = max(0.01, float(poll_interval))
        while True:
            if self.is_ready():
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(interval, remaining))

    def claim_or_focus_existing(
        self,
        *,
        open_existing: bool = True,
        timeout: float = 120.0,
    ) -> PlatformFileLock | None:
        lock = self.try_acquire_instance()
        if lock is not None:
            return lock

        if not self.wait_until_ready(timeout=timeout):
            raise RuntimeError(
                "Une instance Digital Crown détient le verrou mais son runtime local ne devient pas prêt."
            )
        if open_existing:
            self.adapter.open_uri(self.ui_url)
        return None

    def open_ui_when_ready(self, *, timeout: float = 120.0) -> bool:
        if not self.wait_until_ready(timeout=timeout):
            return False
        return self.adapter.open_uri(self.ui_url)
