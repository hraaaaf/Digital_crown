from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService
from backend.services.update_engine import UpdateEngine, UpdatePreparationError, UpdateSecurityError, _canonical_json
from backend.services.update_windows_apply import UpdateWindowsApply


class _Adapter:
    kind = "windows"
    architecture = "amd64"

    def __init__(self, *, process_alive: bool = True, powershell: Path | None = None):
        self.process_alive = process_alive
        self.powershell = powershell
        self.launch_error: Exception | None = None
        self.last_command: list[str] | None = None

    @staticmethod
    def ensure_private_directory(path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def atomic_write_text(path, content, *, encoding="utf-8", mode=0o600):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return path

    def is_process_alive(self, pid: int) -> bool:
        return self.process_alive and pid > 0

    def windows_powershell_executable(self) -> Path:
        if self.powershell is None:
            raise FileNotFoundError("WINDOWS_POWERSHELL_51_MISSING")
        return self.powershell

    def launch_detached(self, command):
        self.last_command = [str(part) for part in command]
        if self.launch_error is not None:
            raise self.launch_error

        class _Proc:
            pid = 4242

        return _Proc()


def _signed_manifest(*, version: str, filename: str, size: int, sha256: str):
    private = Ed25519PrivateKey.generate()
    public_raw = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_b64 = base64.b64encode(public_raw).decode()
    key_id = hashlib.sha256(public_raw).hexdigest()
    now = datetime.now(timezone.utc)
    signed = {
        "schema": 1,
        "sequence": 1,
        "version": version,
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
        "targets": [{
            "os": "windows",
            "arch": "amd64",
            "filename": filename,
            "size_bytes": size,
            "sha256": sha256,
            "url": f"https://example.invalid/{filename}",
        }],
    }
    signature = base64.b64encode(private.sign(_canonical_json(signed))).decode()
    raw = json.dumps({
        "signed": signed,
        "signature": {"keyid": key_id, "algorithm": "ed25519", "sig": signature},
    }, separators=(",", ":")).encode()
    return raw, public_b64


def _setup(monkeypatch, tmp_path):
    data = tmp_path / "cabinet"
    bundle = tmp_path / "bundle"
    install = tmp_path / "program"
    scripts = bundle / "scripts"
    powershell = tmp_path / "Windows" / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    for path in (data, bundle, install, scripts, powershell.parent):
        path.mkdir(parents=True, exist_ok=True)
    (bundle / "VERSION").write_text("1.0.0", encoding="utf-8")
    (scripts / "windows_update_worker.ps1").write_text("#requires -Version 5.1\n", encoding="utf-8")
    (scripts / "windows_update_worker_core.ps1").write_text("#requires -Version 5.1\n", encoding="utf-8")
    powershell.write_bytes(b"MZ")
    executable = install / "DigitalCrown.exe"
    executable.write_bytes(b"MZ-current")

    adapter = _Adapter(powershell=powershell)
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: data))
    monkeypatch.setattr(AppPaths, "get_base_dir", staticmethod(lambda: bundle))

    import backend.services.update_windows_apply as apply_mod
    monkeypatch.setattr(apply_mod, "get_platform_adapter", lambda: adapter)
    monkeypatch.setattr(apply_mod.sys, "frozen", True, raising=False)
    monkeypatch.setattr(apply_mod.sys, "executable", str(executable))
    monkeypatch.setenv("CABINET_PORT", "18770")

    artifact = tmp_path / "DigitalCrownSetup-1.0.1.exe"
    artifact.write_bytes(b"next-installer")
    raw, public_b64 = _signed_manifest(
        version="1.0.1",
        filename=artifact.name,
        size=artifact.stat().st_size,
        sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(raw)
    monkeypatch.setenv("DIGITALCROWN_UPDATE_PUBLIC_KEY_B64", public_b64)

    backups = data / "backups"
    backups.mkdir()
    rescue = backups / "db_backup_test.db.enc"
    rescue.write_bytes(b"encrypted-rescue")
    rescue_sha = hashlib.sha256(rescue.read_bytes()).hexdigest()
    (data / "backup.key").write_bytes(b"existing-backup-key")
    monkeypatch.setattr(
        BackupService,
        "backup_active_database",
        staticmethod(lambda: {
            "engine": "sqlite",
            "status": "SUCCESS",
            "backup_filename": rescue.name,
            "size_bytes": rescue.stat().st_size,
            "checksum": rescue_sha,
        }),
    )
    return data, artifact, manifest, adapter


def test_prepare_and_schedule_signed_windows_job(monkeypatch, tmp_path):
    data, artifact, manifest, adapter = _setup(monkeypatch, tmp_path)

    prepared = UpdateWindowsApply.prepare_signed(manifest, artifact)
    assert prepared["status"] == "prepared"
    assert prepared["apply_certified"] is False
    assert prepared["signed_manifest_filename"] == "signed-manifest.json"

    scheduled = UpdateWindowsApply.schedule(prepared["job_id"], 1234)
    assert scheduled["status"] == "scheduled"
    assert scheduled["apply_certified"] is True
    assert scheduled["worker_contract"] == "windows-inno-v1"
    assert scheduled["worker_pid"] == 4242
    assert adapter.last_command is not None
    assert adapter.last_command[0] == str(adapter.powershell)

    persisted = UpdateEngine.get_job(prepared["job_id"])
    assert persisted["status"] == "scheduled"
    assert persisted["apply_certified"] is True
    assert persisted["current_version"] == "1.0.0"
    assert persisted["health_url"] == "http://127.0.0.1:18770/health"
    assert (data / "updates" / "jobs" / prepared["job_id"] / "worker" / "windows_update_worker.ps1").is_file()


def test_schedule_rejects_job_tampering_against_signed_manifest(monkeypatch, tmp_path):
    _, artifact, manifest, _ = _setup(monkeypatch, tmp_path)
    prepared = UpdateWindowsApply.prepare_signed(manifest, artifact)
    tampered = UpdateEngine.get_job(prepared["job_id"])
    tampered["artifact_sha256"] = "0" * 64
    UpdateEngine._write_job(tampered)

    with pytest.raises(UpdateSecurityError, match="SIGNED_JOB_MISMATCH"):
        UpdateWindowsApply.schedule(prepared["job_id"], 1234)


def test_schedule_rejects_missing_backup_key(monkeypatch, tmp_path):
    data, artifact, manifest, _ = _setup(monkeypatch, tmp_path)
    prepared = UpdateWindowsApply.prepare_signed(manifest, artifact)
    (data / "backup.key").unlink()

    with pytest.raises(UpdatePreparationError, match="BACKUP_KEY_MISSING"):
        UpdateWindowsApply.schedule(prepared["job_id"], 1234)


def test_worker_launch_failure_is_fail_closed_before_apply(monkeypatch, tmp_path):
    _, artifact, manifest, adapter = _setup(monkeypatch, tmp_path)
    prepared = UpdateWindowsApply.prepare_signed(manifest, artifact)
    adapter.launch_error = OSError("blocked")

    with pytest.raises(UpdatePreparationError, match="WORKER_LAUNCH_FAILED"):
        UpdateWindowsApply.schedule(prepared["job_id"], 1234)

    failed = UpdateEngine.get_job(prepared["job_id"])
    assert failed["status"] == "failed_pre_apply"
    assert failed["apply_certified"] is False
    assert failed["worker_result"] == "scheduler_launch_failed"
