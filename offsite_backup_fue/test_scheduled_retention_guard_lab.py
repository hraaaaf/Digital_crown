"""Run the actual scheduled_backup.run AST in a dependency-free LAB harness.

The heavyweight backend package is not imported. These are *not* evidence
of a real Windows Task Scheduler service or a remote NAS; this exercises
the exact run-function body with controlled synthetic DB/media outputs.
"""
import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import uuid


_SCHEDULED_SRC = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "scheduled_backup.py"


def _load_run_in_lab(tmp_path, *, db_status="SUCCESS", media_status="SUCCESS",
                     offsite_status="SUCCESS", offsite_db=True, offsite_media=True):
    root = tmp_path / "scheduled"
    origin = ast.parse(_SCHEDULED_SRC.read_text(encoding="utf-8"), filename=str(_SCHEDULED_SRC))
    run_nodes = [node for node in origin.body if isinstance(node, ast.FunctionDef) and node.name == "run"]
    assert len(run_nodes) == 1
    module = ast.fix_missing_locations(ast.Module(body=run_nodes, type_ignores=[]))
    retention_spy = Mock(return_value=[])
    manifest_spy = Mock()
    db_file = "db_backup_test.sql.enc" if db_status == "SUCCESS" else None
    media_file = "media_backup_test.zip.enc" if media_status == "SUCCESS" else None
    env = {
        "uuid": uuid, "datetime": datetime,
        "SCHEDULED_ROOT": root, "OFFSITE_DIR": str(tmp_path / "fake_remote"),
        "_check_execution_provenance": lambda: {"status": "OK", "violations": {}},
        "_acquire_lock": lambda: (True, ""), "_release_lock": lambda: None,
        "_run_db_backup": lambda timestamp: {"status": db_status, "backup_filename": db_file,
            "checksum": "f" * 64 if db_file else None, "size_bytes": 2},
        "_run_media_backup": lambda timestamp: {"status": media_status, "backup_filename": media_file,
            "checksum": "e" * 64 if media_file else None, "size_bytes": 2, "file_count": 1},
        "_run_offsite_copy": lambda manifest: {"status": offsite_status,
            "db_copied": offsite_db, "media_copied": offsite_media,
            "error_code": None, "error_message": None, "duration_seconds": 0.0},
        "_apply_retention_all": lambda dry_run: [],
        "_apply_retention_all_offsite": retention_spy,
        "_write_manifest": manifest_spy,
        "logger": SimpleNamespace(warning=lambda *args: None),
    }
    exec(compile(module, str(_SCHEDULED_SRC), "exec"), env)
    return env["run"], retention_spy, manifest_spy


def test_medium_retention_skipped_when_offsite_copy_failed(tmp_path):
    run, retention, _manifest = _load_run_in_lab(tmp_path, offsite_status="FAILED",
                                                  offsite_db=False, offsite_media=False)
    result = run(apply_retention=True)
    assert result["overall_status"] == "SUCCESS"
    assert result["offsite_status"] == "FAILED"
    retention.assert_not_called()


def test_medium_retention_skipped_when_offsite_copy_partial(tmp_path):
    run, retention, _manifest = _load_run_in_lab(tmp_path, offsite_status="PARTIAL",
                                                  offsite_db=False, offsite_media=True)
    result = run(apply_retention=True)
    assert result["overall_status"] == "SUCCESS"
    retention.assert_not_called()


def test_medium_retention_skipped_when_status_claims_success_without_db(tmp_path):
    run, retention, _manifest = _load_run_in_lab(tmp_path, offsite_status="SUCCESS",
                                                  offsite_db=False, offsite_media=True)
    result = run(apply_retention=True)
    assert result["offsite_db_copied"] is False
    retention.assert_not_called()


def test_medium_retention_skipped_when_local_db_failed(tmp_path):
    run, retention, _manifest = _load_run_in_lab(tmp_path, db_status="FAILED",
                                                  offsite_status="SUCCESS",
                                                  offsite_db=True, offsite_media=True)
    result = run(apply_retention=True)
    assert result["overall_status"] == "PARTIAL"
    retention.assert_not_called()


def test_medium_retention_allowed_only_after_complete_local_and_offsite_success(tmp_path):
    run, retention, _manifest = _load_run_in_lab(tmp_path)
    result = run(apply_retention=True)
    assert result["overall_status"] == "SUCCESS"
    assert result["offsite_status"] == "SUCCESS"
    retention.assert_called_once_with(str(tmp_path / "fake_remote"), dry_run=False)


def test_medium_retention_dry_run_never_deletes(tmp_path):
    run, retention, _manifest = _load_run_in_lab(tmp_path)
    result = run(apply_retention=False)
    assert result["overall_status"] == "SUCCESS"
    retention.assert_called_once_with(str(tmp_path / "fake_remote"), dry_run=True)
