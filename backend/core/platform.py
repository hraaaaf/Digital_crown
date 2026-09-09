from __future__ import annotations

import os
import platform as std_platform
import subprocess
import tempfile
import webbrowser
from collections.abc import Mapping
from pathlib import Path
from typing import Any, BinaryIO


APP_NAME = "DigitalCrown"


class PlatformFileLock:
    """Process-scoped file lock released automatically when the handle closes."""

    def __init__(self, adapter: "PlatformAdapter", handle: BinaryIO) -> None:
        self._adapter = adapter
        self._handle = handle
        self._released = False

    @property
    def released(self) -> bool:
        return self._released

    def release(self) -> None:
        if self._released:
            return
        try:
            self._adapter._unlock_file(self._handle)
        finally:
            self._handle.close()
            self._released = True

    def __enter__(self) -> "PlatformFileLock":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.release()


class PlatformAdapter:
    """Single boundary for operating-system integration used by the shared core."""

    def __init__(
        self,
        *,
        system_name: str | None = None,
        environ: Mapping[str, str] | None = None,
        home: str | Path | None = None,
    ) -> None:
        self._system_name = system_name or std_platform.system()
        self._environ = os.environ if environ is None else environ
        self._home = Path.home() if home is None else Path(home)

    @property
    def kind(self) -> str:
        normalized = self._system_name.strip().lower()
        if normalized.startswith("win"):
            return "windows"
        if normalized == "darwin" or normalized.startswith("mac"):
            return "macos"
        if normalized.startswith("linux"):
            return "linux"
        return "other"

    @property
    def architecture(self) -> str:
        return std_platform.machine().strip().lower() or "unknown"

    @property
    def is_windows(self) -> bool:
        return self.kind == "windows"

    @property
    def is_macos(self) -> bool:
        return self.kind == "macos"

    @property
    def autostart_strategy(self) -> str:
        if self.is_windows:
            return "task_scheduler"
        if self.is_macos:
            return "launch_agent"
        return "unsupported"

    def _override_path(self, key: str) -> Path | None:
        value = str(self._environ.get(key, "")).strip()
        return Path(value).expanduser() if value else None

    def user_data_dir(self, app_name: str = APP_NAME) -> Path:
        override = self._override_path("DIGITALCROWN_USER_DATA_DIR")
        if override is not None:
            return override

        if self.is_windows:
            base = self._override_path("APPDATA") or self._home / "AppData" / "Roaming"
        elif self.is_macos:
            base = self._home / "Library" / "Application Support"
        else:
            base = self._override_path("XDG_CONFIG_HOME") or self._home / ".config"
        return base / app_name

    def config_dir(self, app_name: str = APP_NAME) -> Path:
        override = self._override_path("DIGITALCROWN_CONFIG_DIR")
        if override is not None:
            return override

        if self.is_windows or self.is_macos:
            return self.user_data_dir(app_name)
        base = self._override_path("XDG_CONFIG_HOME") or self._home / ".config"
        return base / app_name

    def log_dir(self, app_name: str = APP_NAME) -> Path:
        override = self._override_path("DIGITALCROWN_LOG_DIR")
        if override is not None:
            return override
        if self.is_macos:
            return self._home / "Library" / "Logs" / app_name
        return self.user_data_dir(app_name) / "logs"

    def runtime_dir(self, app_name: str = APP_NAME) -> Path:
        override = self._override_path("DIGITALCROWN_RUNTIME_DIR")
        if override is not None:
            return override
        if self.kind == "linux":
            xdg_runtime = self._override_path("XDG_RUNTIME_DIR")
            if xdg_runtime is not None:
                return xdg_runtime / app_name
        return self.user_data_dir(app_name) / "runtime"

    def cabinet_env_path(self, app_name: str = APP_NAME) -> Path:
        return self.config_dir(app_name) / ".env"

    def ensure_private_directory(self, path: str | Path) -> Path:
        directory = Path(path)
        directory.mkdir(parents=True, exist_ok=True)
        if not self.is_windows:
            try:
                directory.chmod(0o700)
            except OSError:
                pass
        return directory

    def atomic_write_text(
        self,
        path: str | Path,
        content: str,
        *,
        encoding: str = "utf-8",
        mode: int = 0o600,
    ) -> Path:
        target = Path(path)
        self.ensure_private_directory(target.parent)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding=encoding) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            if not self.is_windows:
                try:
                    temporary.chmod(mode)
                except OSError:
                    pass
            os.replace(temporary, target)
            return target
        finally:
            if temporary.exists():
                temporary.unlink(missing_ok=True)

    def open_uri(self, uri: str) -> bool:
        return bool(webbrowser.open(uri))

    def detached_process_kwargs(self) -> dict[str, Any]:
        """Return safe detached-child process options for the current platform."""
        kwargs: dict[str, Any] = {"close_fds": True}
        if self.is_windows:
            kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200
            )
        else:
            kwargs["start_new_session"] = True
        return kwargs

    def try_acquire_process_lock(self, path: str | Path) -> PlatformFileLock | None:
        """Acquire a non-blocking process lock, returning None when already held."""
        lock_path = Path(path)
        self.ensure_private_directory(lock_path.parent)
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        handle = os.fdopen(fd, "r+b", buffering=0)
        try:
            if os.fstat(handle.fileno()).st_size == 0:
                handle.write(b"\0")
            handle.seek(0)
            self._lock_file_nonblocking(handle)
        except OSError:
            handle.close()
            return None
        except Exception:
            handle.close()
            raise
        return PlatformFileLock(self, handle)

    def _lock_file_nonblocking(self, handle: BinaryIO) -> None:
        if self.is_windows:
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return

        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock_file(self, handle: BinaryIO) -> None:
        try:
            if self.is_windows:
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                return

            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass

    def is_process_alive(self, pid: int) -> bool:
        if pid <= 0:
            return False
        if self.is_windows:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                check=False,
                creationflags=creationflags,
            )
            return result.returncode == 0 and f'"{pid}"' in result.stdout

        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False


def get_platform_adapter() -> PlatformAdapter:
    """Return a fresh adapter so environment changes remain observable in tests/startup."""
    return PlatformAdapter()
