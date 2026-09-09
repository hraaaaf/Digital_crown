import hashlib
import json
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService
from backend.services.update_db_rollback import UpdateDatabaseRollback, UpdateDatabaseRollbackError


JOB_ID = "a" * 32


def _make_case(tmp_path: Path, monkeypatch, *, rescue_name: str = "rescue/db_backup_test.db.enc"):
    user_data = tmp_path / "user-data"
    user_data.mkdir()
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: user_data))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "test-sqlcipher-passphrase")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    key = Fernet.generate_key()
    (user_data / "backup.key").write_bytes(key)
    cipher = Fernet(key)

    job_dir = user_data / "updates" / "jobs" / JOB_ID
    (job_dir / "rescue").mkdir(parents=True)
    rescue = job_dir / "rescue" / "db_backup_test.db.enc"
    rescue.write_bytes(cipher.encrypt(b"valid-sqlcipher"))
    job = {
        "schema": 1,
        "job_id": JOB_ID,
        "platform": "windows",
        "worker_contract": "windows-inno-v1",
        "apply_certified": True,
        "status": "database_rolling_back",
        "worker_result": "rollback_failed",
        "rollback": "failed",
        "rollback_failure_reason": "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED",
        "database_rollback": "running",
        "rescue_backup_filename": rescue_name,
        "rescue_backup_sha256": hashlib.sha256(rescue.read_bytes()).hexdigest(),
    }
    job_path = job_dir / "job.json"
    job_path.write_text(json.dumps(job), encoding="utf-8")
    return user_data, job_dir, job_path, rescue


def _fake_verify(path: Path, passphrase: str) -> None:
    assert passphrase == "test-sqlcipher-passphrase"
    if Path(path).read_bytes() != b"valid-sqlcipher":
        raise RuntimeError("invalid sqlcipher payload")


def test_db_rollback_restores_verified_sqlcipher_and_quarantines_active_family(tmp_path, monkeypatch):
    user_data, job_dir, job_path, _ = _make_case(tmp_path, monkeypatch)
    target = user_data / "clinical_vault.db"
    target.write_bytes(b"old-db")
    Path(str(target) + "-wal").write_bytes(b"old-wal")
    Path(str(target) + "-shm").write_bytes(b"old-shm")
    monkeypatch.setattr(BackupService, "_verify_sqlcipher_file", staticmethod(_fake_verify))

    report = UpdateDatabaseRollback.execute(job_path)

    assert report["status"] == "success"
    assert report["replay_safe"] is True
    assert target.read_bytes() == b"valid-sqlcipher"
    assert not Path(str(target) + "-wal").exists()
    assert not Path(str(target) + "-shm").exists()
    quarantine = job_dir / "rescue" / "pre-db-rollback"
    assert (quarantine / "clinical_vault.db").read_bytes() == b"old-db"
    assert (quarantine / "clinical_vault.db-wal").read_bytes() == b"old-wal"
    assert (quarantine / "clinical_vault.db-shm").read_bytes() == b"old-shm"
    state = json.loads((job_dir / "rescue" / "db-rollback-state.json").read_text(encoding="utf-8"))
    assert state["phase"] == "restored"
    assert state["quarantine_sha256"]["database"] == hashlib.sha256(b"old-db").hexdigest()
    persisted = json.loads((job_dir / "db-rollback-report.json").read_text(encoding="utf-8"))
    assert persisted["status"] == "success"


def test_db_rollback_replay_preserves_original_quarantine(tmp_path, monkeypatch):
    user_data, job_dir, job_path, _ = _make_case(tmp_path, monkeypatch)
    target = user_data / "clinical_vault.db"
    target.write_bytes(b"original-before-crash")
    Path(str(target) + "-wal").write_bytes(b"original-wal")
    monkeypatch.setattr(BackupService, "_verify_sqlcipher_file", staticmethod(_fake_verify))

    first = UpdateDatabaseRollback.execute(job_path)
    quarantine = job_dir / "rescue" / "pre-db-rollback"
    first_db = (quarantine / "clinical_vault.db").read_bytes()
    first_wal = (quarantine / "clinical_vault.db-wal").read_bytes()
    first_hashes = dict(first["quarantine_sha256"])

    # Simulate a crash after replacement/report, followed by runtime mutation before retry.
    target.write_bytes(b"valid-sqlcipher")
    second = UpdateDatabaseRollback.execute(job_path)

    assert second["status"] == "success"
    assert second["replay_safe"] is True
    assert second["quarantine_sha256"] == first_hashes
    assert (quarantine / "clinical_vault.db").read_bytes() == first_db == b"original-before-crash"
    assert (quarantine / "clinical_vault.db-wal").read_bytes() == first_wal == b"original-wal"
    assert target.read_bytes() == b"valid-sqlcipher"


def test_db_rollback_refuses_direct_cli_without_orchestrator_authorization(tmp_path, monkeypatch):
    user_data, _, job_path, _ = _make_case(tmp_path, monkeypatch)
    target = user_data / "clinical_vault.db"
    target.write_bytes(b"old-db")
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload["status"] = "rollback_failed"
    payload["database_rollback"] = "required_but_not_wired"
    job_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_NOT_AUTHORIZED"):
        UpdateDatabaseRollback.execute(job_path)
    assert target.read_bytes() == b"old-db"


def test_db_rollback_refuses_uncertified_or_wrong_worker_contract(tmp_path, monkeypatch):
    _, _, job_path, _ = _make_case(tmp_path, monkeypatch)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload["apply_certified"] = False
    job_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_NOT_AUTHORIZED"):
        UpdateDatabaseRollback.execute(job_path)

    payload["apply_certified"] = True
    payload["worker_contract"] = "other-worker"
    job_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_NOT_AUTHORIZED"):
        UpdateDatabaseRollback.execute(job_path)


def test_db_rollback_checksum_mismatch_leaves_active_db_untouched(tmp_path, monkeypatch):
    user_data, _, job_path, _ = _make_case(tmp_path, monkeypatch)
    target = user_data / "clinical_vault.db"
    target.write_bytes(b"old-db")
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload["rescue_backup_sha256"] = "0" * 64
    job_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_RESCUE_SHA256_MISMATCH"):
        UpdateDatabaseRollback.execute(job_path)
    assert target.read_bytes() == b"old-db"


def test_db_rollback_missing_backup_key_fails_without_generating_one(tmp_path, monkeypatch):
    user_data, _, job_path, _ = _make_case(tmp_path, monkeypatch)
    key_path = user_data / "backup.key"
    key_path.unlink()

    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_BACKUP_KEY_MISSING"):
        UpdateDatabaseRollback.execute(job_path)
    assert not key_path.exists()


def test_db_rollback_rejects_postgres_and_sql_rescue(tmp_path, monkeypatch):
    _, _, job_path, _ = _make_case(tmp_path, monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql://cabinet@example.invalid/digitalcrown")
    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_POSTGRES_UNSUPPORTED"):
        UpdateDatabaseRollback.execute(job_path)

    monkeypatch.delenv("DATABASE_URL", raising=False)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload["rescue_backup_filename"] = "rescue/db_backup_test.sql.enc"
    job_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_RESCUE_PATH_INVALID"):
        UpdateDatabaseRollback.execute(job_path)


def test_db_rollback_rejects_rescue_path_traversal(tmp_path, monkeypatch):
    _, _, job_path, _ = _make_case(tmp_path, monkeypatch)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload["rescue_backup_filename"] = "rescue/../escape.db.enc"
    job_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_RESCUE_PATH_INVALID"):
        UpdateDatabaseRollback.execute(job_path)


def test_db_rollback_rejects_job_outside_canonical_update_root(tmp_path, monkeypatch):
    user_data = tmp_path / "user-data"
    user_data.mkdir()
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: user_data))
    outside = tmp_path / JOB_ID
    outside.mkdir()
    job_path = outside / "job.json"
    job_path.write_text(json.dumps({"schema": 1, "job_id": JOB_ID}), encoding="utf-8")
    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_JOB_PATH_INVALID"):
        UpdateDatabaseRollback.execute(job_path)


def test_db_rollback_restores_original_family_if_post_replace_validation_fails(tmp_path, monkeypatch):
    user_data, _, job_path, _ = _make_case(tmp_path, monkeypatch)
    target = user_data / "clinical_vault.db"
    target.write_bytes(b"old-db")
    Path(str(target) + "-wal").write_bytes(b"old-wal")
    calls = {"count": 0}

    def fail_after_replace(path: Path, passphrase: str) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("post-replace verification failed")
        if calls["count"] == 3 and Path(path).read_bytes() != b"old-db":
            raise RuntimeError("old database was not restored")

    monkeypatch.setattr(BackupService, "_verify_sqlcipher_file", staticmethod(fail_after_replace))
    with pytest.raises(UpdateDatabaseRollbackError, match="UPDATE_DB_ROLLBACK_RESTORED_DB_INVALID"):
        UpdateDatabaseRollback.execute(job_path)
    assert target.read_bytes() == b"old-db"
    assert Path(str(target) + "-wal").read_bytes() == b"old-wal"


def test_db_rollback_run_persists_fail_closed_report(tmp_path, monkeypatch):
    _, job_dir, job_path, _ = _make_case(tmp_path, monkeypatch)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload["rescue_backup_sha256"] = "f" * 64
    job_path.write_text(json.dumps(payload), encoding="utf-8")

    assert UpdateDatabaseRollback.run(job_path) == 4
    report = json.loads((job_dir / "db-rollback-report.json").read_text(encoding="utf-8"))
    assert report == {
        "schema": 1,
        "status": "failed",
        "error_code": "UPDATE_DB_ROLLBACK_RESCUE_SHA256_MISMATCH",
    }
