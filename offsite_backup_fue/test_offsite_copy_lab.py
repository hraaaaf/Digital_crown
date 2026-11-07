"""Tests for backup_offsite.copy_to_offsite() — isolated from the orchestrator
(see test_scheduled_backup.py::TestOffsiteCopy for the end-to-end wiring)."""
import hashlib

"""Dependency-light LAB test suite for encrypted offsite DB/media copy.

Load the exact production source from disk without importing the heavy backend
package or conftest fixtures. Existing backend/tests re-exports this ONE source
of tests under its normal full-suite environment; no patient data or DB is used.
"""
import importlib.util
from pathlib import Path

_SOURCE_PATH = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "backup_offsite.py"
_SPEC = importlib.util.spec_from_file_location("_dc_offsite_copy_under_test", _SOURCE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("OFFSITE_FUE_SOURCE_NOT_LOADABLE")
_SOURCE_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_SOURCE_MODULE)
copy_to_offsite = _SOURCE_MODULE.copy_to_offsite



def _write(path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def test_success_copies_both_files_and_verifies_checksum(tmp_path):
    db_source = tmp_path / "local" / "db_backup_x.sql.enc"
    media_source = tmp_path / "local" / "media_backup_x.zip.enc"
    db_checksum = _write(db_source, b"db-bytes")
    media_checksum = _write(media_source, b"media-bytes")

    dest_root = tmp_path / "nas"
    result = copy_to_offsite(db_source, db_checksum, media_source, media_checksum, dest_root)

    assert result["status"] == "SUCCESS"
    assert result["db_copied"] is True
    assert result["media_copied"] is True
    assert result["error_code"] is None
    assert (dest_root / "db" / "db_backup_x.sql.enc").read_bytes() == b"db-bytes"
    assert (dest_root / "media" / "media_backup_x.zip.enc").read_bytes() == b"media-bytes"


def test_missing_source_file_is_reported_not_raised(tmp_path):
    db_source = tmp_path / "local" / "db_backup_x.sql.enc"  # never created
    dest_root = tmp_path / "nas"

    result = copy_to_offsite(db_source, "deadbeef", None, None, dest_root)

    assert result["status"] == "FAILED"
    assert result["db_copied"] is False
    assert result["error_code"] == "DB_SOURCE_MISSING"


def test_unwritable_destination_returns_unreachable(tmp_path):
    db_source = tmp_path / "local" / "db_backup_x.sql.enc"
    db_checksum = _write(db_source, b"db-bytes")

    # A destination path whose parent segment is a regular file can never be
    # mkdir'd into — stands in for a disconnected/unreachable network share.
    blocker = tmp_path / "blocker_file"
    blocker.write_bytes(b"x")
    dest_root = blocker / "nas"

    result = copy_to_offsite(db_source, db_checksum, None, None, dest_root)

    assert result["status"] == "UNREACHABLE"
    assert result["error_code"] == "DEST_UNREACHABLE"
    assert result["db_copied"] is False


def test_checksum_mismatch_is_reported_as_failure_not_silently_accepted(tmp_path):
    db_source = tmp_path / "local" / "db_backup_x.sql.enc"
    _write(db_source, b"db-bytes")
    dest_root = tmp_path / "nas"

    result = copy_to_offsite(db_source, "wrong-checksum-does-not-match", None, None, dest_root)

    assert result["status"] == "FAILED"
    assert result["db_copied"] is False
    assert result["error_code"] == "CHECKSUM_MISMATCH"
    # Corrupted copy must never be left behind as if it were valid.
    assert not (dest_root / "db" / "db_backup_x.sql.enc").exists()


def test_partial_when_only_one_of_two_files_succeeds(tmp_path):
    db_source = tmp_path / "local" / "db_backup_x.sql.enc"
    media_source = tmp_path / "local" / "media_backup_x.zip.enc"  # never created
    db_checksum = _write(db_source, b"db-bytes")
    dest_root = tmp_path / "nas"

    result = copy_to_offsite(db_source, db_checksum, media_source, "deadbeef", dest_root)

    assert result["status"] == "PARTIAL"
    assert result["db_copied"] is True
    assert result["media_copied"] is False


def test_nothing_to_copy_when_both_sources_are_none(tmp_path):
    dest_root = tmp_path / "nas"
    result = copy_to_offsite(None, None, None, None, dest_root)

    assert result["status"] == "FAILED"
    assert result["error_code"] == "NOTHING_TO_COPY"


def test_never_raises_on_unexpected_source_type(tmp_path):
    """copy_to_offsite must degrade to a structured error, never propagate an
    exception — this is the caller's (scheduled_backup.py) primary safety net."""
    dest_root = tmp_path / "nas"
    # A directory passed where a file is expected — shutil.copy2 raises IsADirectoryError.
    weird_source = tmp_path / "a_directory"
    weird_source.mkdir()

    result = copy_to_offsite(weird_source, "deadbeef", None, None, dest_root)

    assert result["status"] == "FAILED"
    assert result["db_copied"] is False



def test_legacy_fixed_temp_filename_is_not_overwritten(tmp_path):
    """A preexisting legacy temp file must not be truncated by a new copy."""
    db_source = tmp_path / "local" / "db_backup_x.sql.enc"
    checksum = _write(db_source, b"encrypted-backup")
    db_dest = tmp_path / "nas" / "db"
    db_dest.mkdir(parents=True)
    legacy_temp = db_dest / ".tmp_db_backup_x.sql.enc"
    legacy_temp.write_bytes(b"OTHER-COPY-IN-PROGRESS")

    result = copy_to_offsite(db_source, checksum, None, None, tmp_path / "nas")

    assert result["status"] == "SUCCESS"
    assert legacy_temp.read_bytes() == b"OTHER-COPY-IN-PROGRESS"
    assert (db_dest / db_source.name).read_bytes() == b"encrypted-backup"
    assert sorted(p.name for p in db_dest.iterdir() if p.name.startswith(".tmp_")) == [legacy_temp.name]


def test_bad_checksum_preserves_existing_valid_offsite_backup(tmp_path):
    """Never publish an invalid copy or erase a previously verified archive."""
    source = tmp_path / "local" / "db_backup_x.sql.enc"
    original_checksum = _write(source, b"original-valid-encrypted-backup")
    destination = tmp_path / "nas"
    assert copy_to_offsite(source, original_checksum, None, None, destination)["status"] == "SUCCESS"

    source.write_bytes(b"CHANGED-SOURCE")
    result = copy_to_offsite(source, original_checksum, None, None, destination)

    assert result["status"] == "FAILED"
    assert result["error_code"] == "CHECKSUM_MISMATCH"
    assert (destination / "db" / source.name).read_bytes() == b"original-valid-encrypted-backup"
    assert list((destination / "db").glob(".tmp_*")) == []


def test_large_offsite_copy_rehashes_by_blocks(tmp_path, monkeypatch):
    """Do not call Path.read_bytes() on the temporary copy: bounded-memory hash."""
    from pathlib import Path

    source = tmp_path / "local" / "media_backup_x.zip.enc"
    payload = b"backup-blob" * 650000
    checksum = _write(source, payload)
    dest = tmp_path / "nas"
    original_read_bytes = Path.read_bytes

    def refuse_read_all(self):
        if self.name.startswith(".tmp_"):
            raise AssertionError("temporary offsite copy must be hashed in chunks")
        return original_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", refuse_read_all)
    result = copy_to_offsite(None, None, source, checksum, dest)

    assert result["status"] == "SUCCESS"
    assert (dest / "media" / source.name).read_bytes() == payload
    assert list((dest / "media").glob(".tmp_*")) == []
