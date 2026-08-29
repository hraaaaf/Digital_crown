import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.core.paths import AppPaths
from backend.core.platform import PlatformAdapter
from backend.services.backup_service import BackupService
from backend.services.macos_update_apply import MacOSUpdateApplyService
from backend.services.macos_update_db_rollback import MacOSUpdateDatabaseRollback
from backend.services.macos_update_worker import MacOSUpdateWorker
from backend.services.update_apply import CONFIRMATION_TOKEN, UpdateApplyService
from backend.services.update_dispatch import UpdateApplyDispatchService
from backend.services.update_engine import UpdateEngine, UpdatePreparationError
from backend.services.update_recovery import UpdateRecoveryService


def _patch_data(monkeypatch, tmp_path):
    data = tmp_path / "appdata"
    data.mkdir()
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: data))
    return data


def _prepared_macos_job(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    artifact = tmp_path / "DigitalCrown-1.0.1-arm64.dmg"
    artifact.write_bytes(b"notarized-dmg-candidate")
    artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    verified = {
        "schema": 1,
        "sequence": 2,
        "version": "1.0.1",
        "manifest_sha256": "b" * 64,
        "target": {
            "os": "macos",
            "arch": "arm64",
            "filename": artifact.name,
            "size_bytes": artifact.stat().st_size,
            "sha256": artifact_sha,
            "url": "https://updates.example.invalid/DigitalCrown-1.0.1-arm64.dmg",
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
        staticmethod(lambda: {"status": "SUCCESS", "backup_filename": rescue.name, "checksum": rescue_sha}),
    )
    return UpdateEngine.prepare_update(verified, artifact_path=artifact), data


def test_macos_runtime_gate_requires_frozen_cabinet_and_macos(monkeypatch):
    monkeypatch.setattr(
        "backend.services.macos_update_apply.get_platform_adapter",
        lambda: PlatformAdapter(system_name="Darwin"),
    )
    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    monkeypatch.setattr("backend.services.macos_update_apply.sys.frozen", True, raising=False)
    assert MacOSUpdateApplyService.runtime_apply_supported() is True
    monkeypatch.setattr(
        "backend.services.macos_update_apply.get_platform_adapter",
        lambda: PlatformAdapter(system_name="Windows"),
    )
    assert MacOSUpdateApplyService.runtime_apply_supported() is False


def test_dispatch_preserves_windows_and_routes_macos(monkeypatch):
    monkeypatch.setattr(UpdateEngine, "get_job", classmethod(lambda cls, job_id: {"platform": "windows"}))
    monkeypatch.setattr(
        UpdateApplyService,
        "request_apply",
        classmethod(lambda cls, job_id, confirmation: {"path": "windows"}),
    )
    assert UpdateApplyDispatchService.request_apply("a" * 32, CONFIRMATION_TOKEN)["path"] == "windows"
    monkeypatch.setattr(UpdateEngine, "get_job", classmethod(lambda cls, job_id: {"platform": "macos"}))
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "request_apply",
        classmethod(lambda cls, job_id, confirmation: {"path": "macos"}),
    )
    assert UpdateApplyDispatchService.request_apply("b" * 32, CONFIRMATION_TOKEN)["path"] == "macos"


def test_macos_apply_requires_distribution_proof_then_schedules_rescue_worker(monkeypatch, tmp_path):
    job, data = _prepared_macos_job(monkeypatch, tmp_path)
    install_app = tmp_path / "Applications" / "DigitalCrown.app"
    installed_exe = install_app / "Contents" / "MacOS" / "DigitalCrown"
    installed_exe.parent.mkdir(parents=True)
    installed_exe.write_bytes(b"current")
    monkeypatch.setattr(MacOSUpdateApplyService, "runtime_apply_supported", staticmethod(lambda: True))
    monkeypatch.setattr(MacOSUpdateApplyService, "_installed_app", staticmethod(lambda: install_app))
    monkeypatch.setattr(MacOSUpdateApplyService, "_current_version", classmethod(lambda cls: "1.0.0"))
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_health_url",
        staticmethod(lambda: "http://127.0.0.1:8005/health"),
    )
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_verify_app_bundle",
        classmethod(lambda cls, app, expected_version: {"version": expected_version}),
    )
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_verify_macos_distribution",
        classmethod(
            lambda cls, dmg, expected_version: {
                "bundle_id": "com.saninova.digitalcrown",
                "version": expected_version,
                "developer_id": "valid",
                "hardened_runtime": "valid",
                "secure_timestamp": "valid",
                "notarization": "stapled",
                "gatekeeper": "valid",
            }
        ),
    )

    def fake_snapshot(cls, stored_job, app):
        job_dir = data / "updates" / "jobs" / stored_job["job_id"]
        rescue_app = job_dir / "rescue" / "program" / "DigitalCrown.app"
        rescue_exe = rescue_app / "Contents" / "MacOS" / "DigitalCrown"
        rescue_exe.parent.mkdir(parents=True)
        rescue_exe.write_bytes(b"rescue-exe")
        manifest = job_dir / "rescue" / "program-manifest.json"
        manifest.write_text("[]", encoding="utf-8")
        return rescue_app, hashlib.sha256(manifest.read_bytes()).hexdigest()

    monkeypatch.setattr(MacOSUpdateApplyService, "_snapshot_current_app", classmethod(fake_snapshot))
    launched = []
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_launch_detached_worker",
        staticmethod(lambda executable, job_path, parent_pid: launched.append((executable, job_path, parent_pid))),
    )
    monkeypatch.setattr(MacOSUpdateApplyService, "_schedule_parent_exit", classmethod(lambda cls: None))
    result = MacOSUpdateApplyService.request_apply(job["job_id"], CONFIRMATION_TOKEN)
    stored = UpdateEngine.get_job(job["job_id"])
    assert result["status"] == "scheduled"
    assert stored["apply_certified"] is True
    assert stored["worker_contract"] == "macos-dmg-v1"
    assert stored["recovery_contract"] == "macos-interruption-v1"
    assert stored["macos_notarization"] == "stapled"
    assert stored["macos_gatekeeper"] == "valid"
    assert stored["current_version"] == "1.0.0"
    assert stored["install_app"] == str(install_app)
    assert len(launched) == 1
    assert launched[0][0].name == "DigitalCrown"


def test_macos_distribution_failure_never_certifies_apply(monkeypatch, tmp_path):
    job, _ = _prepared_macos_job(monkeypatch, tmp_path)
    install_app = tmp_path / "Applications" / "DigitalCrown.app"
    (install_app / "Contents" / "MacOS").mkdir(parents=True)
    monkeypatch.setattr(MacOSUpdateApplyService, "runtime_apply_supported", staticmethod(lambda: True))
    monkeypatch.setattr(MacOSUpdateApplyService, "_installed_app", staticmethod(lambda: install_app))
    monkeypatch.setattr(MacOSUpdateApplyService, "_current_version", classmethod(lambda cls: "1.0.0"))
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_verify_app_bundle",
        classmethod(lambda cls, app, expected_version: {"version": expected_version}),
    )
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_verify_macos_distribution",
        classmethod(
            lambda cls, dmg, expected_version: (_ for _ in ()).throw(
                UpdatePreparationError("UPDATE_MACOS_STAPLE_INVALID")
            )
        ),
    )
    with pytest.raises(UpdatePreparationError, match="STAPLE_INVALID"):
        MacOSUpdateApplyService.request_apply(job["job_id"], CONFIRMATION_TOKEN)
    stored = UpdateEngine.get_job(job["job_id"])
    assert stored["status"] == "prepared"
    assert stored["apply_certified"] is False


def test_macos_worker_requires_exact_loopback_health_path_and_newer_semver():
    assert MacOSUpdateWorker._validated_health_url("http://127.0.0.1:8005/health") == "http://127.0.0.1:8005/health"
    with pytest.raises(UpdatePreparationError, match="HEALTH_URL_NOT_LOOPBACK"):
        MacOSUpdateWorker._validated_health_url("http://127.0.0.1:8005/other/health")
    with pytest.raises(UpdatePreparationError, match="HEALTH_URL_NOT_LOOPBACK"):
        MacOSUpdateWorker._validated_health_url("https://127.0.0.1:8005/health")
    assert MacOSUpdateWorker._semver("1.0.1", "BAD") > MacOSUpdateWorker._semver("1.0.0", "BAD")
    with pytest.raises(UpdatePreparationError, match="BAD"):
        MacOSUpdateWorker._semver("1.0", "BAD")


def test_macos_recovery_contract_is_eligible():
    job = {
        "schema": 1,
        "platform": "macos",
        "worker_contract": "macos-dmg-v1",
        "recovery_contract": "macos-interruption-v1",
        "apply_certified": True,
        "status": "applying",
    }
    assert UpdateRecoveryService._eligible(job) is True
    job["recovery_contract"] = "wrong"
    assert UpdateRecoveryService._eligible(job) is False


def test_macos_recovery_accepts_replay_safe_db_failure():
    job = {
        "schema": 1,
        "platform": "macos",
        "worker_contract": "macos-dmg-v1",
        "recovery_contract": "macos-interruption-v1",
        "apply_certified": True,
        "status": "rollback_failed",
        "worker_result": "rollback_failed",
        "rollback": "failed",
        "database_rollback": "failed",
        "rollback_failure_reason": "UPDATE_MACOS_DB_ROLLBACK_RUNTIME_HEALTH_FAILED",
    }
    assert UpdateRecoveryService._eligible(job) is True


def test_macos_recovery_rejects_incoherent_db_state():
    job = {
        "schema": 1,
        "platform": "macos",
        "worker_contract": "macos-dmg-v1",
        "recovery_contract": "macos-interruption-v1",
        "apply_certified": True,
        "status": "database_rolling_back",
        "worker_result": "install_verified",
        "rollback": "not_needed",
        "database_rollback": "running",
        "rollback_failure_reason": "UPDATE_MACOS_PACKAGE_ROLLBACK_HEALTH_FAILED",
    }
    assert UpdateRecoveryService._eligible(job) is False
    assert MacOSUpdateWorker._database_recovery_authorized(job) is False


def test_macos_db_rollback_authorization_is_platform_specific():
    job = {
        "platform": "macos",
        "worker_contract": "macos-dmg-v1",
        "apply_certified": True,
        "status": "database_rolling_back",
        "worker_result": "rollback_failed",
        "rollback": "failed",
        "rollback_failure_reason": "UPDATE_MACOS_PACKAGE_ROLLBACK_HEALTH_FAILED",
        "database_rollback": "running",
    }
    MacOSUpdateDatabaseRollback._require_authorized_rollback_state(job)
    job["worker_contract"] = "windows-inno-v1"
    with pytest.raises(Exception, match="UPDATE_DB_ROLLBACK_NOT_AUTHORIZED"):
        MacOSUpdateDatabaseRollback._require_authorized_rollback_state(job)


def test_macos_apply_cleanup_failure_never_rolls_back(monkeypatch, tmp_path):
    install_parent = tmp_path / "Applications"
    install_parent.mkdir()
    install_app = install_parent / "DigitalCrown.app"
    install_app.mkdir()
    staged = install_parent / ".DigitalCrown.app.update-test"
    staged.mkdir()
    rescue_app = tmp_path / "rescue" / "DigitalCrown.app"
    rescue_app.mkdir(parents=True)
    job_id = "c" * 32
    side_backup = MacOSUpdateWorker._side_backup(
        {"install_parent": install_parent},
        job_id,
    )
    context = {
        "artifact": tmp_path / "candidate.dmg",
        "rescue_app": rescue_app,
        "install_app": install_app,
        "install_parent": install_parent,
        "health_url": "http://127.0.0.1:8005/health",
        "health_timeout": 60,
        "current_version": "1.0.0",
        "target_version": "1.0.1",
    }
    job = {"job_id": job_id, "status": "scheduled"}

    monkeypatch.setattr(MacOSUpdateWorker, "_wait_parent_exit", staticmethod(lambda parent_pid, timeout=30.0: None))
    monkeypatch.setattr(MacOSUpdateWorker, "_self_test", classmethod(lambda cls, app, version, report_dir: None))
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_verify_macos_distribution",
        classmethod(lambda cls, artifact, expected_version: {"status": "valid"}),
    )
    monkeypatch.setattr(
        MacOSUpdateWorker,
        "_stage_target",
        classmethod(lambda cls, ctx, worker_job_id, report_dir: staged),
    )
    monkeypatch.setattr(
        MacOSUpdateWorker,
        "_launch_runtime",
        staticmethod(lambda app: SimpleNamespace(pid=4242)),
    )
    monkeypatch.setattr(MacOSUpdateWorker, "_wait_health", staticmethod(lambda url, timeout: None))
    monkeypatch.setattr(MacOSUpdateWorker, "_save", classmethod(lambda cls, stored_job: None))
    monkeypatch.setattr(MacOSUpdateWorker, "_finalize_target", classmethod(lambda cls, job_path, ctx: None))
    rollback_calls = []
    monkeypatch.setattr(
        MacOSUpdateWorker,
        "_rollback",
        classmethod(lambda cls, job_path, ctx, stored_job, failure: rollback_calls.append(failure) or 2),
    )

    import shutil

    real_rmtree = shutil.rmtree

    def fail_only_post_finalize_cleanup(path, *args, **kwargs):
        if Path(path) == side_backup:
            raise OSError("cleanup failure after durable finalization")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(
        "backend.services.macos_update_worker.shutil.rmtree",
        fail_only_post_finalize_cleanup,
    )

    result = MacOSUpdateWorker._apply(tmp_path / "job.json", context, job, 1234)
    assert result == 0
    assert rollback_calls == []
    assert side_backup.is_dir()


def test_macos_recovery_resumes_database_rollback_without_package_retry(monkeypatch, tmp_path):
    context = {
        "install_app": tmp_path / "DigitalCrown.app",
        "health_url": "http://127.0.0.1:8005/health",
        "health_timeout": 60,
    }
    job = {
        "job_id": "d" * 32,
        "status": "database_rolling_back",
        "worker_result": "rollback_failed",
        "rollback": "failed",
        "database_rollback": "running",
        "rollback_failure_reason": "UPDATE_MACOS_PACKAGE_ROLLBACK_HEALTH_FAILED",
    }
    events = []
    monkeypatch.setattr(MacOSUpdateWorker, "_wait_parent_exit", staticmethod(lambda parent_pid, timeout=30.0: None))
    monkeypatch.setattr(
        MacOSUpdateWorker,
        "_finish_database_rollback",
        classmethod(lambda cls, job_path, ctx, stored_job: events.append("db") or 2),
    )
    monkeypatch.setattr(
        MacOSUpdateWorker,
        "_rollback",
        classmethod(
            lambda cls, job_path, ctx, stored_job, failure: (_ for _ in ()).throw(
                AssertionError("package rollback must not restart during DB recovery")
            )
        ),
    )

    result = MacOSUpdateWorker._recover(tmp_path / "job.json", context, job, 4321)
    assert result == 2
    assert events == ["db"]
