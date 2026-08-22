from __future__ import annotations

import ast
import os
import stat
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.core.paths import AppPaths
from backend.core.platform import PlatformAdapter


REPO_ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BOUNDARY = (REPO_ROOT / "backend" / "core" / "platform.py").resolve()


def test_windows_paths_preserve_current_cabinet_contract(tmp_path):
    adapter = PlatformAdapter(
        system_name="Windows",
        environ={"APPDATA": str(tmp_path / "Roaming")},
        home=tmp_path / "home",
    )
    expected = tmp_path / "Roaming" / "DigitalCrown"
    assert adapter.kind == "windows"
    assert adapter.user_data_dir() == expected
    assert adapter.config_dir() == expected
    assert adapter.log_dir() == expected / "logs"
    assert adapter.runtime_dir() == expected / "runtime"
    assert adapter.cabinet_env_path() == expected / ".env"
    assert adapter.autostart_strategy == "task_scheduler"


def test_macos_uses_native_application_support_and_logs(tmp_path):
    adapter = PlatformAdapter(system_name="Darwin", environ={}, home=tmp_path)
    app_support = tmp_path / "Library" / "Application Support" / "DigitalCrown"
    assert adapter.kind == "macos"
    assert adapter.user_data_dir() == app_support
    assert adapter.config_dir() == app_support
    assert adapter.runtime_dir() == app_support / "runtime"
    assert adapter.log_dir() == tmp_path / "Library" / "Logs" / "DigitalCrown"
    assert adapter.cabinet_env_path() == app_support / ".env"
    assert adapter.autostart_strategy == "launch_agent"


def test_linux_dev_fallback_remains_under_config(tmp_path):
    adapter = PlatformAdapter(system_name="Linux", environ={}, home=tmp_path)
    expected = tmp_path / ".config" / "DigitalCrown"
    assert adapter.user_data_dir() == expected
    assert adapter.config_dir() == expected
    assert adapter.log_dir() == expected / "logs"
    assert adapter.runtime_dir() == expected / "runtime"


def test_explicit_path_overrides_are_platform_neutral(tmp_path):
    adapter = PlatformAdapter(
        system_name="Darwin",
        environ={
            "DIGITALCROWN_USER_DATA_DIR": str(tmp_path / "data"),
            "DIGITALCROWN_CONFIG_DIR": str(tmp_path / "config"),
            "DIGITALCROWN_LOG_DIR": str(tmp_path / "logs"),
            "DIGITALCROWN_RUNTIME_DIR": str(tmp_path / "runtime"),
        },
        home=tmp_path / "ignored",
    )
    assert adapter.user_data_dir() == tmp_path / "data"
    assert adapter.config_dir() == tmp_path / "config"
    assert adapter.log_dir() == tmp_path / "logs"
    assert adapter.runtime_dir() == tmp_path / "runtime"


def test_app_paths_delegate_to_platform_adapter(tmp_path):
    adapter = PlatformAdapter(system_name="Darwin", environ={}, home=tmp_path)
    with patch("backend.core.paths.get_platform_adapter", return_value=adapter):
        assert AppPaths.get_user_data_dir() == tmp_path / "Library" / "Application Support" / "DigitalCrown"
        assert AppPaths.get_config_dir() == tmp_path / "Library" / "Application Support" / "DigitalCrown"
        assert AppPaths.get_log_dir() == tmp_path / "Library" / "Logs" / "DigitalCrown"
        assert AppPaths.get_runtime_dir() == tmp_path / "Library" / "Application Support" / "DigitalCrown" / "runtime"


def test_env_loader_falls_back_to_platform_owned_config(tmp_path, monkeypatch):
    from backend import env_loader

    cabinet_env = tmp_path / "config" / ".env"
    cabinet_env.parent.mkdir(parents=True)
    cabinet_env.write_text("P1_PLATFORM_PROBE=from-platform\n", encoding="utf-8")
    monkeypatch.delenv("DIGITALCROWN_ENV_FILE", raising=False)
    monkeypatch.delenv("P1_PLATFORM_PROBE", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")

    with (
        patch.object(env_loader, "BASE_DIR", tmp_path / "missing-backend"),
        patch.object(env_loader, "_appdata_env_path", return_value=cabinet_env),
    ):
        loaded = env_loader.load_backend_env(override=True)

    assert loaded == cabinet_env
    assert os.environ["P1_PLATFORM_PROBE"] == "from-platform"


def test_atomic_write_creates_private_file(tmp_path):
    adapter = PlatformAdapter(system_name="Linux", environ={}, home=tmp_path)
    target = tmp_path / "private" / ".env"
    adapter.atomic_write_text(target, "SECRET_KEY=test\n")
    assert target.read_text(encoding="utf-8") == "SECRET_KEY=test\n"
    if os.name != "nt":
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
        assert stat.S_IMODE(target.parent.stat().st_mode) == 0o700


def test_open_uri_is_centralized():
    adapter = PlatformAdapter(system_name="Darwin", environ={}, home="/tmp")
    with patch("backend.core.platform.webbrowser.open", return_value=True) as opener:
        assert adapter.open_uri("http://127.0.0.1:8005") is True
    opener.assert_called_once_with("http://127.0.0.1:8005")


def test_detached_process_options_are_centralized():
    windows = PlatformAdapter(system_name="Windows", environ={}, home="C:/Users/Test")
    windows_kwargs = windows.detached_process_kwargs()
    assert windows_kwargs["close_fds"] is True
    assert int(windows_kwargs["creationflags"]) != 0
    assert "start_new_session" not in windows_kwargs

    posix = PlatformAdapter(system_name="Darwin", environ={}, home="/tmp")
    posix_kwargs = posix.detached_process_kwargs()
    assert posix_kwargs == {"close_fds": True, "start_new_session": True}


def test_windows_pid_probe_is_centralized():
    adapter = PlatformAdapter(system_name="Windows", environ={}, home="C:/Users/Test")
    result = SimpleNamespace(returncode=0, stdout='"DigitalCrown.exe","4321","Console","1","10,000 K"\n')
    with patch("backend.core.platform.subprocess.run", return_value=result) as runner:
        assert adapter.is_process_alive(4321) is True
    command = runner.call_args.args[0]
    assert command[0] == "tasklist"
    assert "PID eq 4321" in command


def test_posix_pid_probe_uses_signal_zero():
    adapter = PlatformAdapter(system_name="Darwin", environ={}, home="/tmp")
    with patch("backend.core.platform.os.kill", return_value=None) as kill:
        assert adapter.is_process_alive(4321) is True
    kill.assert_called_once_with(4321, 0)
    assert adapter.is_process_alive(0) is False


def test_shared_runtime_has_no_unmanaged_os_branching():
    """Only backend/core/platform.py may know concrete OS APIs/commands."""
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
    offenders: list[str] = []

    candidates = [REPO_ROOT / "run.py"]
    candidates.extend((REPO_ROOT / "backend").rglob("*.py"))

    for path in candidates:
        resolved = path.resolve()
        if resolved == PLATFORM_BOUNDARY:
            continue
        relative = resolved.relative_to(REPO_ROOT)
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
                if node.value.lower() in {value.lower() for value in forbidden_constants}:
                    offenders.append(f"{relative}:{node.lineno} OS token {node.value!r}")

    assert offenders == [], "Unmanaged OS integration:\n" + "\n".join(offenders)
