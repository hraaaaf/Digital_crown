import hashlib
from pathlib import Path

import pytest

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService
from backend.services.update_apply import CONFIRMATION_TOKEN, UpdateApplyService
from backend.services.update_engine import UpdateEngine, UpdatePreparationError


def _patch_data(monkeypatch, tmp_path):
    data = tmp_path / "appdata"
    data.mkdir()
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: data))
    return data


def _prepared_windows_job(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    artifact = tmp_path / "DigitalCrownSetup-1.0.1.exe"
    artifact.write_bytes(b"signed-installer-candidate")
    artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()

    verified = {
        "schema": 1,
        "sequence": 2,
        "version": "1.0.1",
        "manifest_sha256": "a" * 64,
        "target": {
            "os": "windows",
            "arch": "amd64",
            "filename": artifact.name,
            "size_bytes": artifact.stat().st_size,
            "sha256": artifact_sha,
            "url": "https://updates.example.invalid/DigitalCrownSetup-1.0.1.exe",
        },
    }

    backups = data / "backups"
    backups.mkdir()
    rescue = backups / "db_backup_test.db.enc"
    rescue.write_bytes(b"rescue")
    rescue_sha = hashlib.sha256(rescue.read_bytes()).hexdigest()
    monkeypatch.setattr(
        BackupService,
        "backup_active_database",
        staticmethod(
            lambda: {
                "status": "SUCCESS",
                "backup_filename": rescue.name,
                "checksum": rescue_sha,
            }
        ),
    )
    return UpdateEngine.prepare_update(verified, artifact_path=artifact), data


def test_production_wiring_refuses_unsigned_then_schedules_signed_job(monkeypatch, tmp_path):
    job, data = _prepared_windows_job(monkeypatch, tmp_path)
    install_dir = tmp_path / "installed"
    install_dir.mkdir()
    installed_executable = install_dir / "DigitalCrown.exe"
    installed_executable.write_bytes(b"current-package")

    monkeypatch.setattr(UpdateApplyService, "runtime_apply_supported", staticmethod(lambda: True))
    monkeypatch.setattr(UpdateApplyService, "_installed_executable", staticmethod(lambda: installed_executable))
    monkeypatch.setattr(UpdateApplyService, "_current_version", classmethod(lambda cls: "1.0.0"))
    monkeypatch.setattr(UpdateApplyService, "_health_url", staticmethod(lambda: "http://127.0.0.1:8005/health"))

    launched = []
    monkeypatch.setattr(
        UpdateApplyService,
        "_launch_detached_worker",
        classmethod(lambda cls, worker, job_path, parent_pid: launched.append((worker, job_path, parent_pid))),
    )
    monkeypatch.setattr(UpdateApplyService, "_schedule_parent_exit", classmethod(lambda cls: None))

    def reject_signature(cls, artifact):
        raise UpdatePreparationError("UPDATE_WINDOWS_AUTHENTICODE_INVALID")

    monkeypatch.setattr(UpdateApplyService, "_verify_windows_authenticode", classmethod(reject_signature))
    with pytest.raises(UpdatePreparationError, match="AUTHENTICODE_INVALID"):
        UpdateApplyService.request_apply(job["job_id"], CONFIRMATION_TOKEN)

    blocked = UpdateEngine.get_job(job["job_id"])
    assert blocked["status"] == "prepared"
    assert blocked["apply_certified"] is False
    assert blocked["apply_blocker"] == "UPDATE_WINDOWS_AUTHENTICODE_INVALID"
    assert launched == []

    monkeypatch.setattr(
        UpdateApplyService,
        "_verify_windows_authenticode",
        classmethod(
            lambda cls, artifact: {
                "status": "Valid",
                "signer_thumbprint": "A1B2",
                "timestamp_thumbprint": "C3D4",
            }
        ),
    )
    result = UpdateApplyService.request_apply(job["job_id"], CONFIRMATION_TOKEN)
    stored = UpdateEngine.get_job(job["job_id"])

    assert result["status"] == "scheduled"
    assert stored["status"] == "scheduled"
    assert stored["apply_certified"] is True
    assert stored["authenticode_status"] == "Valid"
    assert stored["authenticode_signer_thumbprint"] == "A1B2"
    assert stored["authenticode_timestamp_thumbprint"] == "C3D4"
    assert stored["worker_contract"] == "windows-inno-v1"
    assert stored["current_version"] == "1.0.0"
    assert stored["install_dir"] == str(install_dir)
    assert stored["health_url"] == "http://127.0.0.1:8005/health"

    job_dir = data / "updates" / "jobs" / job["job_id"]
    worker = job_dir / stored["worker_filename"]
    worker_core = job_dir / stored["worker_core_filename"]
    assert worker.is_file() and worker_core.is_file()
    assert hashlib.sha256(worker.read_bytes()).hexdigest() == stored["windows_update_worker.ps1_sha256"]
    assert hashlib.sha256(worker_core.read_bytes()).hexdigest() == stored["windows_update_worker_core.ps1_sha256"]
    assert len(launched) == 1
    assert launched[0][0] == worker
    assert launched[0][1] == job_dir / "job.json"
    assert isinstance(launched[0][2], int) and launched[0][2] > 0


def test_production_wiring_requires_exact_confirmation_and_runtime_gate(monkeypatch, tmp_path):
    job, _ = _prepared_windows_job(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="METTRE_A_JOUR"):
        UpdateApplyService.request_apply(job["job_id"], "UPDATE")

    monkeypatch.setattr(UpdateApplyService, "runtime_apply_supported", staticmethod(lambda: False))
    with pytest.raises(UpdatePreparationError, match="RUNTIME_APPLY_UNSUPPORTED"):
        UpdateApplyService.request_apply(job["job_id"], CONFIRMATION_TOKEN)
