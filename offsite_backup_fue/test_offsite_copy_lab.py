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

    assert result["status"] == "PARTIAL"
    assert legacy_temp.read_bytes() == b"OTHER-COPY-IN-PROGRESS"
    assert (db_dest / db_source.name).read_bytes() == b"encrypted-backup"
    assert sorted(p.name for p in db_dest.iterdir() if p.name.startswith(".tmp_")) == [legacy_temp.name]


def test_bad_checksum_preserves_existing_valid_offsite_backup(tmp_path):
    """Never publish an invalid copy or erase a previously verified archive."""
    source = tmp_path / "local" / "db_backup_x.sql.enc"
    original_checksum = _write(source, b"original-valid-encrypted-backup")
    destination = tmp_path / "nas"
    assert copy_to_offsite(source, original_checksum, None, None, destination)["status"] == "PARTIAL"

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

    assert result["status"] == "PARTIAL"
    assert (dest / "media" / source.name).read_bytes() == payload
    assert list((dest / "media").glob(".tmp_*")) == []


def test_second_valid_backup_same_name_cannot_overwrite_prior_verified_copy(tmp_path):
    """The two checksums are individually valid; a collision must never erase the earlier archive."""
    first = tmp_path / "local_a" / "db_backup_same.sql.enc"
    second = tmp_path / "local_b" / "db_backup_same.sql.enc"
    first_sum = _write(first, b"VALID-ORIGINAL-DB")
    second_sum = _write(second, b"VALID-DIFFERENT-DB")
    remote = tmp_path / "nas"
    assert copy_to_offsite(first, first_sum, None, None, remote)["status"] == "PARTIAL"
    result = copy_to_offsite(second, second_sum, None, None, remote)
    assert result["status"] == "FAILED"
    assert result["error_code"] == "DESTINATION_NAME_COLLISION"
    assert (remote / "db" / first.name).read_bytes() == b"VALID-ORIGINAL-DB"
    assert list((remote / "db").glob(".tmp_*")) == []


def test_second_identical_backup_is_idempotently_accepted(tmp_path):
    first = tmp_path / "local_a" / "db_backup_same.sql.enc"
    second = tmp_path / "local_b" / "db_backup_same.sql.enc"
    digest = _write(first, b"IDENTICAL-VALID-DB")
    _write(second, b"IDENTICAL-VALID-DB")
    remote = tmp_path / "nas"
    assert copy_to_offsite(first, digest, None, None, remote)["status"] == "PARTIAL"
    result = copy_to_offsite(second, digest, None, None, remote)
    assert result["status"] == "PARTIAL"
    assert (remote / "db" / first.name).read_bytes() == b"IDENTICAL-VALID-DB"


def test_parallel_same_filename_only_one_different_payload_may_publish(tmp_path):
    """Two processes in a shared NAS directory must not both commit different bytes."""
    from concurrent.futures import ThreadPoolExecutor
    src_a = tmp_path / "first" / "db_backup_shared.sql.enc"
    src_b = tmp_path / "second" / "db_backup_shared.sql.enc"
    hash_a = _write(src_a, b"A-ENCRYPTED-BACKUP")
    hash_b = _write(src_b, b"B-ENCRYPTED-BACKUP")
    remote = tmp_path / "nas"
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(copy_to_offsite, src_a, hash_a, None, None, remote),
            pool.submit(copy_to_offsite, src_b, hash_b, None, None, remote),
        ]
        results = [future.result() for future in futures]
    assert sorted(x["status"] for x in results) == ["FAILED", "PARTIAL"]
    assert (remote / "db" / src_a.name).read_bytes() in {b"A-ENCRYPTED-BACKUP", b"B-ENCRYPTED-BACKUP"}
    assert list((remote / "db").glob(".tmp_*")) == []


def test_missing_db_checksum_never_reports_complete_offsite_success(tmp_path):
    db = tmp_path / "local" / "db_backup.sql.enc"
    media = tmp_path / "local" / "media_backup.zip.enc"
    _write(db, b"DB")
    media_sha = _write(media, b"MEDIA")
    remote = tmp_path / "nas"
    result = copy_to_offsite(db, None, media, media_sha, remote)
    assert result["status"] == "PARTIAL"
    assert result["error_code"] == "DB_CHECKSUM_MISSING"
    assert result["db_copied"] is False
    assert result["media_copied"] is True
    assert not (remote / "db" / db.name).exists()
    assert (remote / "media" / media.name).read_bytes() == b"MEDIA"


def test_atomic_no_clobber_unavailable_never_uses_unsafe_replace(tmp_path, monkeypatch):
    """SMB/NAS without hardlink semantics must fail closed, leaving existing data untouched."""
    source = tmp_path / "local" / "db_backup.sql.enc"
    digest = _write(source, b"VALID-DB")
    remote = tmp_path / "nas"
    def deny_link(*args, **kwargs):
        raise OSError("hard links unavailable on target share")
    monkeypatch.setattr(_SOURCE_MODULE.os, "link", deny_link)
    result = copy_to_offsite(source, digest, None, None, remote)
    assert result["status"] == "FAILED"
    assert result["error_code"] == "ATOMIC_PUBLICATION_UNAVAILABLE"
    assert not (remote / "db" / source.name).exists()
    assert list((remote / "db").glob(".tmp_*")) == []


def test_media_only_copy_is_never_complete_success(tmp_path):
    media = tmp_path / "local" / "media_backup.zip.enc"
    digest = _write(media, b"MEDIA")
    result = copy_to_offsite(None, None, media, digest, tmp_path / "nas")
    assert result["status"] == "PARTIAL"
    assert result["media_copied"] is True
    assert result["db_copied"] is False
    assert result["error_code"] == "INCOMPLETE_BACKUP_PAIR"


def test_db_only_copy_is_never_complete_success(tmp_path):
    db = tmp_path / "local" / "db_backup.sql.enc"
    digest = _write(db, b"DB")
    result = copy_to_offsite(db, digest, None, None, tmp_path / "nas")
    assert result["status"] == "PARTIAL"
    assert result["media_copied"] is False
    assert result["db_copied"] is True
    assert result["error_code"] == "INCOMPLETE_BACKUP_PAIR"


def _make_symlink_or_skip(target, link, *, is_dir=True):
    import os
    import pytest
    try:
        os.symlink(target, link, target_is_directory=is_dir)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"OS cannot create synthetic symlink: {type(exc).__name__}")


def test_symlink_destination_root_does_not_escape_configured_storage(tmp_path):
    real_outside = tmp_path / "outside"
    real_outside.mkdir()
    redirect = tmp_path / "offsite_alias"
    _make_symlink_or_skip(real_outside, redirect)
    source = tmp_path / "local" / "db_backup.sql.enc"
    digest = _write(source, b"DB")
    result = copy_to_offsite(source, digest, None, None, redirect)
    assert result["status"] != "SUCCESS"
    assert result["error_code"] == "DEST_DIRECTORY_UNSAFE"
    assert list(real_outside.iterdir()) == []


def test_symlink_destination_subdir_does_not_publish_outside_root(tmp_path):
    remote = tmp_path / "nas"
    remote.mkdir()
    real_outside = tmp_path / "outside"
    real_outside.mkdir()
    _make_symlink_or_skip(real_outside, remote / "db")
    source = tmp_path / "local" / "db_backup.sql.enc"
    digest = _write(source, b"DB")
    result = copy_to_offsite(source, digest, None, None, remote)
    assert result["status"] == "FAILED"
    assert result["error_code"] == "DEST_DIRECTORY_UNSAFE"
    assert result["db_copied"] is False
    assert list(real_outside.iterdir()) == []


def test_symlinked_parent_ancestor_does_not_create_outside(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = tmp_path / "alias"
    _make_symlink_or_skip(outside, alias)
    source = tmp_path / "local" / "db_backup.sql.enc"
    digest = _write(source, b"DB")
    result = copy_to_offsite(source, digest, None, None, alias / "nas")
    assert result["status"] != "SUCCESS"
    assert result["error_code"] == "DEST_DIRECTORY_UNSAFE"
    assert not (outside / "nas").exists()


def _run_fifo_case_in_separate_process(source, checksum, remote, queue):
    result = copy_to_offsite(source, checksum, None, None, remote)
    queue.put((result["status"], result["error_code"]))


def _assert_fifo_case_nonblocking(source, checksum, remote):
    import multiprocessing
    import os
    import pytest
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO-specific regression requires POSIX filesystem")
    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    process = context.Process(target=_run_fifo_case_in_separate_process, args=(source, checksum, remote, queue))
    process.start()
    process.join(timeout=4)
    if process.is_alive():
        process.terminate()
        process.join(timeout=3)
        pytest.fail("NC-03: FIFO path caused unbounded blocking")
    assert process.exitcode == 0
    status, reason = queue.get(timeout=1)
    assert status == "FAILED"
    assert reason in {"EXISTING_BACKUP_UNSAFE_FILE_TYPE", "SOURCE_UNSAFE_FILE_TYPE"}


def test_existing_fifo_at_final_destination_does_not_block(tmp_path):
    import os
    import pytest
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO-specific regression requires POSIX")
    source = tmp_path / "local" / "db_backup.sql.enc"
    digest = _write(source, b"DB")
    remote = tmp_path / "nas"
    (remote / "db").mkdir(parents=True)
    fifo = remote / "db" / source.name
    os.mkfifo(fifo)
    _assert_fifo_case_nonblocking(source, digest, remote)
    assert fifo.exists()


def test_fifo_source_does_not_block_or_copy(tmp_path):
    import os
    import pytest
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO-specific regression requires POSIX")
    source = tmp_path / "local" / "db_backup.sql.enc"
    source.parent.mkdir(parents=True)
    os.mkfifo(source)
    _assert_fifo_case_nonblocking(source, "0" * 64, tmp_path / "nas")


def test_rev02_directory_swap_after_guard_cannot_write_outside_root(tmp_path, monkeypatch):
    """NC-02: swap the db directory after preflight, before the temp is opened."""
    import os
    import pytest
    if os.name != "posix":
        pytest.skip("POSIX pinned directory-fd implementation; Windows requires native handle audit")
    source = tmp_path / "local" / "db_backup.sql.enc"
    checksum = _write(source, b"SYNTHETIC-ENCRYPTED-DB")
    root = tmp_path / "nas"
    (root / "db").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    moved = root / "db_original"
    original_open = _SOURCE_MODULE._open_regular_readonly
    switched = {"done": False}

    def intervene(path):
        if not switched["done"]:
            switched["done"] = True
            (root / "db").rename(moved)
            os.symlink(outside, root / "db", target_is_directory=True)
        return original_open(path)

    monkeypatch.setattr(_SOURCE_MODULE, "_open_regular_readonly", intervene)
    result = copy_to_offsite(source, checksum, None, None, root)
    assert switched["done"] is True
    assert result["status"] == "FAILED"
    assert result["error_code"] == "DEST_DIRECTORY_UNSAFE"
    assert list(outside.iterdir()) == []
    assert list(moved.glob(".tmp_*")) == []


def _rev02_fifo_swap_worker(source, checksum, root, queue):
    """Separate process: old code would block reopening the swapped FIFO."""
    import os
    original = _SOURCE_MODULE.shutil.copyfileobj

    def substitute_fifo(reader, writer, length):
        original(reader, writer, length=length)
        temp_path = next((root / "db").glob(".tmp_*"))
        os.unlink(temp_path)
        os.mkfifo(temp_path)

    _SOURCE_MODULE.shutil.copyfileobj = substitute_fifo
    try:
        result = copy_to_offsite(source, checksum, None, None, root)
        queue.put((result["status"], result["error_code"]))
    finally:
        _SOURCE_MODULE.shutil.copyfileobj = original


def test_rev02_temp_path_replaced_by_fifo_does_not_block(tmp_path):
    """NC-03: hard timeout and no final publication after temp-path sabotage."""
    import multiprocessing
    import os
    import pytest
    if os.name != "posix" or not hasattr(os, "mkfifo"):
        pytest.skip("POSIX-only FIFO race; Windows has a separate residual risk")
    source = tmp_path / "local" / "db_backup.sql.enc"
    checksum = _write(source, b"SYNTHETIC-ENCRYPTED-DB")
    root = tmp_path / "nas"
    ctx = multiprocessing.get_context("fork")
    queue = ctx.Queue()
    process = ctx.Process(target=_rev02_fifo_swap_worker, args=(source, checksum, root, queue))
    process.start()
    process.join(timeout=3)
    if process.is_alive():
        process.terminate()
        process.join(timeout=3)
        pytest.fail("REV-02 NC-03: relire le temporaire par chemin provoque un FIFO bloquant")
    assert process.exitcode == 0
    status, reason = queue.get(timeout=1)
    assert status == "FAILED"
    assert reason == "TEMP_PATH_TAMPERED"
    assert not (root / "db" / source.name).exists()
