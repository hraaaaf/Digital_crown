"""Isolated first-boot and process identity regression; no real installation."""
import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace
import socket
from unittest.mock import patch
import pytest
from dotenv import dotenv_values
from backend.core.runtime_supervisor import RuntimeSupervisor

ROOT = Path(__file__).resolve().parents[1]

def bootstrap(monkeypatch, tmp_path):
    root = tmp_path / "new-instance"
    for name, folder in (("USER_DATA", "data"), ("CONFIG", "config"), ("RUNTIME", "runtime"), ("LOG", "logs")):
        monkeypatch.setenv("DIGITALCROWN_" + name + "_DIR", str(root / folder))
    monkeypatch.setenv("DIGITALCROWN_ENV_FILE", str(root / "config" / ".env"))
    tree = ast.parse((ROOT / "run.py").read_text(encoding="utf-8"))
    definition = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_first_boot_bootstrap")
    namespace = {"os": os, "sys": SimpleNamespace(frozen=True, argv=["DigitalCrown.exe", "--initialize-new-cabinet"])}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), str(ROOT / "run.py"), "exec"), namespace)
    return namespace["_first_boot_bootstrap"], root

def test_bootstrap_creates_independent_secrets_and_exact_isolated_paths(monkeypatch, tmp_path):
    function, root = bootstrap(monkeypatch, tmp_path)
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "b" * 64)
    function()
    env = root / "config" / ".env"
    config = dotenv_values(env)
    keys = [config[name] for name in ("SECRET_KEY", "PAIRING_CODE_PEPPER", "CABINET_MASTER_KEY_HEX", "SQLCIPHER_KEY_HEX", "MOBILE_PAIRING_KEY_HEX")]
    assert len(set(keys)) == 5
    assert all(len(bytes.fromhex(key)) == 32 and key != "b" * 64 for key in keys)
    assert config["DATABASE_URL"] == "sqlite:///" + (root / "data" / "clinical_vault.db").as_posix()
    assert config["MEDIA_ROOT"] == (root / "data" / "media").as_posix()
    assert config["DIGITALCROWN_INSTANCE_ID"]
    before = env.read_bytes()
    with pytest.raises(RuntimeError, match="Existing configuration"):
        function()
    assert env.read_bytes() == before
    assert not (root / "data" / "clinical_vault.db").exists()

def test_missing_isolation_override_refuses_before_configuration_write(monkeypatch, tmp_path):
    function, root = bootstrap(monkeypatch, tmp_path)
    monkeypatch.delenv("DIGITALCROWN_RUNTIME_DIR")
    with pytest.raises(RuntimeError, match="five explicit"):
        function()
    assert not (root / "config" / ".env").exists()

def test_bootstrap_refuses_nonempty_old_directory(monkeypatch, tmp_path):
    function, root = bootstrap(monkeypatch, tmp_path)
    old = root / "data" / "fictitious-old.db"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"fictitious preserved content")
    with pytest.raises(RuntimeError, match="empty isolated"):
        function()
    assert old.read_bytes() == b"fictitious preserved content"
    assert not (root / "config" / ".env").exists()

def test_new_instance_refuses_port_occupied_by_any_backend(monkeypatch, tmp_path):
    monkeypatch.setenv("DIGITALCROWN_INSTANCE_ID", "fictitious-new-instance")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        supervisor = RuntimeSupervisor(occupied.getsockname()[1], runtime_dir=tmp_path / "runtime")
        with pytest.raises(RuntimeError, match="already occupied"):
            supervisor.claim_or_focus_existing()
        # Refusal released the acquired lock.
        lock = supervisor.try_acquire_instance()
        assert lock is not None
        lock.release()

@pytest.mark.parametrize("identity,expected", [(None, False), ("fictitious-old", False), ("fictitious-new", True)])
def test_readiness_requires_correct_instance_identity(monkeypatch, tmp_path, identity, expected):
    monkeypatch.setenv("DIGITALCROWN_INSTANCE_ID", "fictitious-new")
    supervisor = RuntimeSupervisor(8005, runtime_dir=tmp_path / "runtime")
    payload = {"status": "ok", "db": "ok", "instance_id": identity}
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def getcode(self): return 200
        def read(self): return json.dumps(payload).encode()
    with patch("backend.core.runtime_supervisor.urlopen", return_value=Response()):
        assert supervisor.is_ready() is expected

def test_windows_installer_namespace_is_distinct_and_never_deletes_global_task():
    source = (ROOT / "installer" / "DigitalCrown.iss").read_text(encoding="utf-8")
    assert "AppId=DigitalCrown-{#CabinetInstanceId}" in source
    assert "CloseApplications=no" in source
    assert "8F1B6C1E-6C7E-4B7B-9C7C-7E6C1E6C7E6C" not in source
    assert "/delete /tn" not in source

def test_frozen_launcher_refuses_implicit_historical_environment(monkeypatch, tmp_path):
    function, root = bootstrap(monkeypatch, tmp_path)
    monkeypatch.delenv("DIGITALCROWN_ENV_FILE")
    with pytest.raises(RuntimeError, match="explicit absolute"):
        function()
    assert not root.exists()

def test_competing_first_boot_cannot_replace_winning_environment(monkeypatch, tmp_path):
    function, root = bootstrap(monkeypatch, tmp_path)
    env = root / "config" / ".env"
    original_open = os.open
    winner = b"fictitious winning environment, never overwrite"
    def interleaved_open(path, flags, mode=0o777, *args, **kwargs):
        if Path(path) == env and flags & os.O_EXCL:
            env.write_bytes(winner)
        return original_open(path, flags, mode, *args, **kwargs)
    monkeypatch.setattr(os, "open", interleaved_open)
    with pytest.raises(FileExistsError):
        function()
    assert env.read_bytes() == winner

def test_installer_does_not_create_a_shortcut_without_an_explicit_profile():
    source = (ROOT / "installer" / "DigitalCrown.iss").read_text(encoding="utf-8")
    icons = source.split("[Icons]",1)[1].split("[Run]",1)[0]
    assert not any(line.strip().startswith("Name:") for line in icons.splitlines())

def test_release_verification_precedes_profile_loading_and_logging():
    source = (ROOT / "run.py").read_text(encoding="utf-8")
    calls = source[source.index("# Order is security-sensitive"):source.index("import multiprocessing")]
    assert calls.index("_verify_frozen_release_certification()") < calls.index("_select_cabinet_env_profile()")
    assert calls.index("_first_boot_bootstrap()") < calls.index("_load_launcher_environment()") < calls.index("_setup_frozen_logging()")

def test_explicit_missing_environment_cannot_fall_back_to_old_configuration(monkeypatch, tmp_path):
    from backend import env_loader
    monkeypatch.setenv("DIGITALCROWN_ENV_FILE", str(tmp_path / "missing" / ".env"))
    def old_lookup():
        raise AssertionError("historical environment fallback was reached")
    monkeypatch.setattr(env_loader, "_appdata_env_path", old_lookup)
    with pytest.raises(RuntimeError, match="fallback forbidden"):
        env_loader.load_backend_env(override=True)
