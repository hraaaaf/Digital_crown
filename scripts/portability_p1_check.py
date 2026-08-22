from __future__ import annotations

import ast
import importlib.util
import os
import stat
import sys
import tempfile
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLATFORM_FILE = ROOT / "backend" / "core" / "platform.py"
PATHS_FILE = ROOT / "backend" / "core" / "paths.py"
ENV_FILE = ROOT / "backend" / "env_loader.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_runtime_boundary():
    """Load P1 modules without executing backend/__init__.py or global test conftest."""
    backend_pkg = types.ModuleType("backend")
    backend_pkg.__path__ = [str(ROOT / "backend")]
    core_pkg = types.ModuleType("backend.core")
    core_pkg.__path__ = [str(ROOT / "backend" / "core")]
    sys.modules["backend"] = backend_pkg
    sys.modules["backend.core"] = core_pkg

    platform_mod = _load("backend.core.platform", PLATFORM_FILE)
    paths_mod = _load("backend.core.paths", PATHS_FILE)
    env_mod = _load("backend.env_loader", ENV_FILE)
    return platform_mod, paths_mod, env_mod


def _path_contracts(platform_mod, paths_mod) -> None:
    PlatformAdapter = platform_mod.PlatformAdapter
    AppPaths = paths_mod.AppPaths

    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)

        windows = PlatformAdapter(
            system_name="Windows",
            environ={"APPDATA": str(temp / "Roaming")},
            home=temp / "home",
        )
        expected_windows = temp / "Roaming" / "DigitalCrown"
        assert windows.kind == "windows"
        assert windows.user_data_dir() == expected_windows
        assert windows.config_dir() == expected_windows
        assert windows.log_dir() == expected_windows / "logs"
        assert windows.runtime_dir() == expected_windows / "runtime"
        assert windows.cabinet_env_path() == expected_windows / ".env"
        assert windows.autostart_strategy == "task_scheduler"

        macos = PlatformAdapter(system_name="Darwin", environ={}, home=temp)
        app_support = temp / "Library" / "Application Support" / "DigitalCrown"
        assert macos.kind == "macos"
        assert macos.user_data_dir() == app_support
        assert macos.config_dir() == app_support
        assert macos.runtime_dir() == app_support / "runtime"
        assert macos.log_dir() == temp / "Library" / "Logs" / "DigitalCrown"
        assert macos.cabinet_env_path() == app_support / ".env"
        assert macos.autostart_strategy == "launch_agent"

        linux = PlatformAdapter(system_name="Linux", environ={}, home=temp)
        expected_linux = temp / ".config" / "DigitalCrown"
        assert linux.user_data_dir() == expected_linux
        assert linux.config_dir() == expected_linux
        assert linux.log_dir() == expected_linux / "logs"
        assert linux.runtime_dir() == expected_linux / "runtime"

        overrides = PlatformAdapter(
            system_name="Darwin",
            environ={
                "DIGITALCROWN_USER_DATA_DIR": str(temp / "data"),
                "DIGITALCROWN_CONFIG_DIR": str(temp / "config"),
                "DIGITALCROWN_LOG_DIR": str(temp / "logs"),
                "DIGITALCROWN_RUNTIME_DIR": str(temp / "runtime"),
            },
            home=temp / "ignored",
        )
        assert overrides.user_data_dir() == temp / "data"
        assert overrides.config_dir() == temp / "config"
        assert overrides.log_dir() == temp / "logs"
        assert overrides.runtime_dir() == temp / "runtime"

        with patch("backend.core.paths.get_platform_adapter", return_value=macos):
            assert AppPaths.get_user_data_dir() == app_support
            assert AppPaths.get_config_dir() == app_support
            assert AppPaths.get_log_dir() == temp / "Library" / "Logs" / "DigitalCrown"
            assert AppPaths.get_runtime_dir() == app_support / "runtime"


def _atomic_and_process_contracts(platform_mod) -> None:
    PlatformAdapter = platform_mod.PlatformAdapter
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        adapter = PlatformAdapter(system_name="Linux", environ={}, home=temp)
        target = temp / "private" / ".env"
        adapter.atomic_write_text(target, "SECRET_KEY=test\n")
        assert target.read_text(encoding="utf-8") == "SECRET_KEY=test\n"
        if os.name != "nt":
            assert stat.S_IMODE(target.stat().st_mode) == 0o600
            assert stat.S_IMODE(target.parent.stat().st_mode) == 0o700

    macos = PlatformAdapter(system_name="Darwin", environ={}, home="/tmp")
    with patch("backend.core.platform.webbrowser.open", return_value=True) as opener:
        assert macos.open_uri("http://127.0.0.1:8005") is True
    opener.assert_called_once_with("http://127.0.0.1:8005")
    assert macos.detached_process_kwargs() == {"close_fds": True, "start_new_session": True}

    with patch("backend.core.platform.os.kill", return_value=None) as kill:
        assert macos.is_process_alive(4321) is True
    kill.assert_called_once_with(4321, 0)
    assert macos.is_process_alive(0) is False

    windows = PlatformAdapter(system_name="Windows", environ={}, home="C:/Users/Test")
    windows_kwargs = windows.detached_process_kwargs()
    assert windows_kwargs["close_fds"] is True
    assert int(windows_kwargs["creationflags"]) != 0
    assert "start_new_session" not in windows_kwargs

    result = SimpleNamespace(returncode=0, stdout='"DigitalCrown.exe","4321","Console","1","10,000 K"\n')
    with patch("backend.core.platform.subprocess.run", return_value=result) as runner:
        assert windows.is_process_alive(4321) is True
    command = runner.call_args.args[0]
    assert command[0] == "tasklist"
    assert "PID eq 4321" in command


def _env_loader_contract(env_mod) -> None:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        cabinet_env = temp / "config" / ".env"
        cabinet_env.parent.mkdir(parents=True)
        cabinet_env.write_text("P1_PLATFORM_PROBE=from-platform\n", encoding="utf-8")

        previous_explicit = os.environ.pop("DIGITALCROWN_ENV_FILE", None)
        previous_probe = os.environ.pop("P1_PLATFORM_PROBE", None)
        previous_environment = os.environ.get("ENVIRONMENT")
        os.environ["ENVIRONMENT"] = "development"
        try:
            with (
                patch.object(env_mod, "BASE_DIR", temp / "missing-backend"),
                patch.object(env_mod, "_appdata_env_path", return_value=cabinet_env),
            ):
                loaded = env_mod.load_backend_env(override=True)
            assert loaded == cabinet_env
            assert os.environ["P1_PLATFORM_PROBE"] == "from-platform"
        finally:
            if previous_explicit is not None:
                os.environ["DIGITALCROWN_ENV_FILE"] = previous_explicit
            else:
                os.environ.pop("DIGITALCROWN_ENV_FILE", None)
            if previous_probe is not None:
                os.environ["P1_PLATFORM_PROBE"] = previous_probe
            else:
                os.environ.pop("P1_PLATFORM_PROBE", None)
            if previous_environment is not None:
                os.environ["ENVIRONMENT"] = previous_environment
            else:
                os.environ.pop("ENVIRONMENT", None)


def _static_guard() -> None:
    forbidden_attributes = {("os", "name"), ("sys", "platform")}
    forbidden_calls = {("platform", "system")}
    forbidden_constants = {
        "APPDATA",
        "LOCALAPPDATA",
        "tasklist",
        "schtasks",
        "powershell",
        "powershell.exe",
    }
    lowered_constants = {value.lower() for value in forbidden_constants}
    offenders: list[str] = []

    candidates = [ROOT / "run.py"]
    candidates.extend((ROOT / "backend").rglob("*.py"))

    for path in candidates:
        resolved = path.resolve()
        if resolved == PLATFORM_FILE.resolve():
            continue
        relative = resolved.relative_to(ROOT)
        if relative.parts[:2] in {("backend", "tests"), ("backend", "scripts")}:
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if (node.value.id, node.attr) in forbidden_attributes:
                    offenders.append(f"{relative}:{node.lineno} direct {node.value.id}.{node.attr}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if (node.func.value.id, node.func.attr) in forbidden_calls:
                    offenders.append(f"{relative}:{node.lineno} direct {node.func.value.id}.{node.func.attr}()")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.lower() in lowered_constants:
                    offenders.append(f"{relative}:{node.lineno} OS token {node.value!r}")

    assert offenders == [], "Unmanaged OS integration:\n" + "\n".join(offenders)


def main() -> int:
    platform_mod, paths_mod, env_mod = _load_runtime_boundary()
    _path_contracts(platform_mod, paths_mod)
    _atomic_and_process_contracts(platform_mod)
    _env_loader_contract(env_mod)
    _static_guard()
    print(f"P1 portability check PASS on runner={platform_mod.PlatformAdapter().kind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
