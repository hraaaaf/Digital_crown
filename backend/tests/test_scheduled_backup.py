"""Tests for the SCHEDULED-TASK-BACKUP-REPLACE-1 orchestrator."""
import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.scripts import scheduled_backup as sb

# Captured before the autouse fixture below patches sb._check_execution_provenance
# for every other test -- TestExecutionProvenance tests the real implementation.
_real_check_execution_provenance = sb._check_execution_provenance


@pytest.fixture(autouse=True)
def _isolated_runtime_root(tmp_path, monkeypatch):
    """Every test gets its own throwaway SCHEDULED_ROOT -- never touches the real
    DigitalCrown-Runtime tree. Also bypasses the execution-provenance check by
    default (status OK) since the test suite itself always runs from the repo --
    provenance detection has its own dedicated tests below."""
    root = tmp_path / "scheduled"
    monkeypatch.setattr(sb, "SCHEDULED_ROOT", root)
    monkeypatch.setattr(sb, "LOCK_PATH", root / ".backup.lock")
    monkeypatch.setattr(
        sb, "_check_execution_provenance",
        lambda: {"status": "OK", "cwd": str(root), "python_executable": "x",
                  "repo_root_checked": str(sb.REPO_ROOT), "violations": {}},
    )
    yield root


class TestLock:
    def test_acquire_lock_when_free(self):
        acquired, reason = sb._acquire_lock()
        assert acquired is True
        assert sb.LOCK_PATH.exists()

    def test_acquire_lock_refused_when_held_by_live_process(self):
        sb.LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {"pid": 999999, "host": "x", "started_at_epoch": time.time(), "started_at": "now"}
        sb.LOCK_PATH.write_text(json.dumps(payload), encoding="utf-8")

        with patch.object(sb, "_pid_alive", return_value=True):
            acquired, reason = sb._acquire_lock()

        assert acquired is False
        assert "Verrou actif" in reason

    def test_stale_lock_dead_pid_is_overwritten(self):
        sb.LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {"pid": 999999, "host": "x", "started_at_epoch": time.time(), "started_at": "now"}
        sb.LOCK_PATH.write_text(json.dumps(payload), encoding="utf-8")

        with patch.object(sb, "_pid_alive", return_value=False):
            acquired, reason = sb._acquire_lock()

        assert acquired is True

    def test_stale_lock_too_old_is_overwritten_even_if_pid_alive(self):
        sb.LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        old_epoch = time.time() - (sb.LOCK_MAX_AGE_SECONDS + 60)
        payload = {"pid": 123, "host": "x", "started_at_epoch": old_epoch, "started_at": "old"}
        sb.LOCK_PATH.write_text(json.dumps(payload), encoding="utf-8")

        with patch.object(sb, "_pid_alive", return_value=True):
            acquired, reason = sb._acquire_lock()

        assert acquired is True

    def test_release_lock_removes_file(self):
        sb._acquire_lock()
        assert sb.LOCK_PATH.exists()
        sb._release_lock()
        assert not sb.LOCK_PATH.exists()


class TestOrchestrationStatus:
    def _run_with(self, db_result, media_result, engine="postgresql"):
        with patch("backend.services.backup_service.BackupService._detect_engine", return_value=(engine, "psycopg2")), \
             patch("backend.services.backup_service.BackupService._backup_postgres", return_value=db_result), \
             patch("backend.scripts.backup_media._build_media_archive", return_value=media_result):
            return sb.run(apply_retention=False, dry_run=False)

    def test_both_success_gives_overall_success(self):
        db = {"status": "SUCCESS", "backup_filename": "db.enc", "size_bytes": 10, "checksum": "a"}
        media = {"status": "SUCCESS", "backup_filename": "media.enc", "size_bytes": 20, "file_count": 3, "checksum": "b"}
        manifest = self._run_with(db, media)
        assert manifest["overall_status"] == "SUCCESS"
        assert manifest["lock_status"] == "ACQUIRED"

    def test_db_success_media_failed_gives_partial(self):
        db = {"status": "SUCCESS", "backup_filename": "db.enc", "size_bytes": 10, "checksum": "a"}
        media = {"status": "FAILED", "backup_filename": None, "size_bytes": 0, "file_count": 0,
                  "checksum": None, "error_code": "SOURCE_NOT_FOUND", "error_message": "x"}
        manifest = self._run_with(db, media)
        assert manifest["overall_status"] == "PARTIAL"

    def test_db_failed_media_success_gives_partial_never_success(self):
        """A DB-only or media-only outcome must never be reported as a complete
        SUCCESS -- media coverage is now mandatory per doctrine."""
        db = {"status": "FAILED", "backup_filename": None, "size_bytes": 0, "checksum": None,
              "error_code": "PG_DUMP_FAILED", "error_message": "x"}
        media = {"status": "SUCCESS", "backup_filename": "media.enc", "size_bytes": 20, "file_count": 3, "checksum": "b"}
        manifest = self._run_with(db, media)
        assert manifest["overall_status"] == "PARTIAL"

    def test_both_failed_gives_failed(self):
        db = {"status": "FAILED", "backup_filename": None, "size_bytes": 0, "checksum": None,
              "error_code": "PG_DUMP_FAILED", "error_message": "x"}
        media = {"status": "FAILED", "backup_filename": None, "size_bytes": 0, "file_count": 0,
                  "checksum": None, "error_code": "SOURCE_NOT_FOUND", "error_message": "y"}
        manifest = self._run_with(db, media)
        assert manifest["overall_status"] == "FAILED"

    def test_unsupported_engine_never_calls_pg_dump_backup(self):
        with patch("backend.services.backup_service.BackupService._detect_engine", return_value=("sqlite", "pysqlcipher")), \
             patch("backend.services.backup_service.BackupService._backup_postgres") as mock_pg, \
             patch("backend.scripts.backup_media._build_media_archive", return_value={
                 "status": "SUCCESS", "backup_filename": "m.enc", "size_bytes": 1, "file_count": 1, "checksum": "c"
             }):
            manifest = sb.run(apply_retention=False, dry_run=False)

        mock_pg.assert_not_called()
        assert manifest["db_status"] == "SKIPPED_UNSUPPORTED_ENGINE"

    def test_lock_held_skips_everything_and_reports_failed(self):
        sb.LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {"pid": 999999, "host": "x", "started_at_epoch": time.time(), "started_at": "now"}
        sb.LOCK_PATH.write_text(json.dumps(payload), encoding="utf-8")

        with patch.object(sb, "_pid_alive", return_value=True), \
             patch("backend.services.backup_service.BackupService._backup_postgres") as mock_pg:
            manifest = sb.run(apply_retention=False, dry_run=False)

        mock_pg.assert_not_called()
        assert manifest["lock_status"] == "SKIPPED_LOCKED"
        assert manifest["overall_status"] == "FAILED"

    def test_dry_run_never_calls_real_backups(self):
        with patch("backend.services.backup_service.BackupService._backup_postgres") as mock_pg, \
             patch("backend.scripts.backup_media._build_media_archive") as mock_media:
            manifest = sb.run(apply_retention=False, dry_run=True)

        mock_pg.assert_not_called()
        mock_media.assert_not_called()
        assert manifest["overall_status"] == "SKIPPED_DRY_RUN"


class TestManifestAndLogs:
    def test_manifest_and_latest_written(self):
        db = {"status": "SUCCESS", "backup_filename": "db.enc", "size_bytes": 10, "checksum": "a"}
        media = {"status": "SUCCESS", "backup_filename": "media.enc", "size_bytes": 20, "file_count": 3, "checksum": "b"}
        with patch("backend.services.backup_service.BackupService._detect_engine", return_value=("postgresql", "psycopg2")), \
             patch("backend.services.backup_service.BackupService._backup_postgres", return_value=db), \
             patch("backend.scripts.backup_media._build_media_archive", return_value=media):
            manifest = sb.run(apply_retention=False, dry_run=False)

        manifests_dir = sb.SCHEDULED_ROOT / "manifests"
        specific = manifests_dir / f"manifest_{manifest['run_id']}.json"
        latest = manifests_dir / "latest.json"
        assert specific.exists()
        assert latest.exists()
        assert json.loads(latest.read_text())["run_id"] == manifest["run_id"]

    def test_no_secrets_in_manifest_or_log(self):
        # _backup_postgres/_build_media_archive already guarantee their own
        # error_message never contains a secret (tested in test_backups.py) --
        # this test guards the orchestrator's manifest/log writer itself, so a
        # future change to _write_manifest() can't accidentally start dumping
        # raw exception objects or env vars.
        db = {"status": "FAILED", "backup_filename": None, "size_bytes": 0, "checksum": None,
              "error_code": "PG_DUMP_FAILED", "error_message": "pg_dump failed (code 1)"}
        media = {"status": "FAILED", "backup_filename": None, "size_bytes": 0, "file_count": 0,
                  "checksum": None, "error_code": "SOURCE_NOT_FOUND", "error_message": "Dossier média introuvable"}
        with patch("backend.services.backup_service.BackupService._detect_engine", return_value=("postgresql", "psycopg2")), \
             patch("backend.services.backup_service.BackupService._backup_postgres", return_value=db), \
             patch("backend.scripts.backup_media._build_media_archive", return_value=media):
            manifest = sb.run(apply_retention=False, dry_run=False)

        manifest_text = (sb.SCHEDULED_ROOT / "manifests" / "latest.json").read_text()
        log_files = list((sb.SCHEDULED_ROOT / "logs").glob("run_*.log"))
        log_text = "\n".join(f.read_text() for f in log_files)
        assert "CABINET_MASTER_KEY_HEX" not in manifest_text
        assert "postgresql://" not in manifest_text
        assert "postgresql://" not in log_text


class TestRetention:
    def _make_file(self, d: Path, name: str, age_days: float):
        d.mkdir(parents=True, exist_ok=True)
        f = d / name
        f.write_bytes(b"x")
        mtime = time.time() - age_days * 86400
        import os
        os.utime(f, (mtime, mtime))
        return f

    def test_dry_run_lists_candidates_but_deletes_nothing(self):
        db_dir = sb.SCHEDULED_ROOT / "db"
        for i in range(6):
            self._make_file(db_dir, f"db_backup_{i}.sql.enc", age_days=40 + i)

        report = sb._apply_retention(db_dir, "db_backup_", ".sql.enc", retention_days=30, dry_run=True)

        assert len(report["candidates"]) > 0
        assert report["deleted"] == []
        assert len(list(db_dir.glob("db_backup_*.sql.enc"))) == 6  # rien supprimé

    def test_real_retention_never_drops_below_min_backups_to_keep(self):
        db_dir = sb.SCHEDULED_ROOT / "db"
        for i in range(6):
            self._make_file(db_dir, f"db_backup_{i}.sql.enc", age_days=100 + i)  # tous très vieux

        with patch.object(sb, "MIN_BACKUPS_TO_KEEP", 3):
            report = sb._apply_retention(db_dir, "db_backup_", ".sql.enc", retention_days=30, dry_run=False)

        remaining = list(db_dir.glob("db_backup_*.sql.enc"))
        assert len(remaining) == 3  # plancher respecté même si tout est "vieux"

    def test_retention_never_touches_files_outside_its_prefix(self):
        db_dir = sb.SCHEDULED_ROOT / "db"
        unrelated = self._make_file(db_dir, "not_a_backup_file.txt", age_days=999)
        for i in range(4):
            self._make_file(db_dir, f"db_backup_{i}.sql.enc", age_days=100)

        with patch.object(sb, "MIN_BACKUPS_TO_KEEP", 1):
            sb._apply_retention(db_dir, "db_backup_", ".sql.enc", retention_days=30, dry_run=False)

        assert unrelated.exists()

    def test_manual_and_in_app_backup_dirs_never_touched(self):
        """Retention is scoped to scheduled/ only -- never backend/backups/ nor
        %APPDATA%/DigitalCrown/backups/."""
        db_dir = sb.SCHEDULED_ROOT / "db"
        self._make_file(db_dir, "db_backup_x.sql.enc", age_days=100)
        # _apply_retention only ever receives paths under SCHEDULED_ROOT in run() --
        # this test documents/enforces that invariant at the call-site level.
        with patch("backend.services.backup_service.BackupService._detect_engine", return_value=("postgresql", "psycopg2")), \
             patch("backend.services.backup_service.BackupService._backup_postgres", return_value={
                 "status": "SUCCESS", "backup_filename": "d.enc", "size_bytes": 1, "checksum": "a"}), \
             patch("backend.scripts.backup_media._build_media_archive", return_value={
                 "status": "SUCCESS", "backup_filename": "m.enc", "size_bytes": 1, "file_count": 1, "checksum": "b"}), \
             patch.object(sb, "_apply_retention", wraps=sb._apply_retention) as spy:
            sb.run(apply_retention=True, dry_run=False)

        for call in spy.call_args_list:
            called_dir = str(call.args[0])
            assert str(sb.SCHEDULED_ROOT) in called_dir


class TestExecutionProvenance:
    """SCHEDULED-BACKUP-RELEASE-EXECUTION-FIX-1 -- the orchestrator must refuse to
    run if its own code (or the backup modules it depends on) was loaded from the
    mutable working repo instead of an immutable release."""

    def test_violation_detected_when_repo_root_matches_real_module_location(self, monkeypatch):
        # In the test suite itself, every module genuinely is loaded from the repo --
        # so pointing REPO_ROOT at the real repo must report a violation for all 5.
        import backend.scripts.scheduled_backup as real_sb
        real_repo_root = Path(real_sb.__file__).resolve().parents[2]
        monkeypatch.setattr(sb, "REPO_ROOT", real_repo_root)

        result = _real_check_execution_provenance()

        assert result["status"] == "VIOLATION"
        assert set(result["violations"].keys()) == {
            "scheduled_backup", "backup_service", "backup_db", "backup_media", "database",
        }

    def test_ok_when_repo_root_does_not_match_actual_module_location(self, monkeypatch, tmp_path):
        # Point REPO_ROOT at an unrelated path -- simulates running from a release,
        # since none of the real module files live under tmp_path.
        monkeypatch.setattr(sb, "REPO_ROOT", tmp_path / "not-the-repo")

        result = _real_check_execution_provenance()

        assert result["status"] == "OK"
        assert result["violations"] == {}

    def test_result_reports_cwd_and_python_executable_for_diagnostics(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sb, "REPO_ROOT", tmp_path / "not-the-repo")
        result = _real_check_execution_provenance()
        assert "cwd" in result
        assert "python_executable" in result
        # sys.executable pointing at the repo's venv is never itself a violation --
        # only backend.* module __file__ locations are checked.
        assert "python_executable" not in result["violations"]

    def test_run_refuses_and_never_acquires_lock_on_provenance_violation(self, monkeypatch):
        monkeypatch.setattr(
            sb, "_check_execution_provenance",
            lambda: {"status": "VIOLATION", "cwd": "x", "python_executable": "y",
                      "repo_root_checked": "z", "violations": {"database": "/repo/backend/database.py"}},
        )
        with patch.object(sb, "_acquire_lock") as mock_lock:
            manifest = sb.run(apply_retention=False, dry_run=False)

        mock_lock.assert_not_called()
        assert manifest["overall_status"] == "FAILED"
        assert manifest["error_code"] == "EXECUTION_PROVENANCE_VIOLATION"
        assert manifest["provenance_status"] == "VIOLATION"

    def test_run_proceeds_normally_when_provenance_ok(self):
        # Uses the autouse fixture's default OK bypass -- dry_run keeps it cheap.
        manifest = sb.run(apply_retention=False, dry_run=True)
        assert manifest["provenance_status"] == "OK"
        assert manifest["overall_status"] == "SKIPPED_DRY_RUN"
