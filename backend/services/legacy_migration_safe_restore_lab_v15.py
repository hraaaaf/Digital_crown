"""LOT05.7-J: disposable copy-generation recovery LAB. Never a clinical restore.

All outputs remain under a named synthetic TemporaryDirectory.  The only
publication is a pointer to a COMPLETE immutable generation.  No active
database, Windows service, user vault, or media directory is overwritten.
The caller-supplied owner is NOT an authenticated request/SCM identity.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import uuid
from contextlib import closing
from pathlib import Path

FIXED_COMPONENTS = ("snapshot.db", "license_fake.bin",
                    "media-fake/scan.fake", "media-fake/invoice.fake")
_GENERATION = re.compile(r"g_[a-f0-9]{32}\Z")


class FakeRecoveryDenied(PermissionError):
    pass


def _root(root: Path) -> Path:
    if (not isinstance(root, Path) or not root.is_absolute()
            or not root.name.startswith("lot05j_fake_")
            or root.is_symlink() or not root.is_dir()):
        raise FakeRecoveryDenied("SYNTHETIC_ROOT_REQUIRED")
    return root.resolve(strict=True)


def _regular(path: Path, parent: Path) -> None:
    if (path.is_symlink() or path.parent.is_symlink() or not path.is_file()
            or path.resolve(strict=True).parent != parent.resolve(strict=True)
            or not stat.S_ISREG(path.stat().st_mode)):
        raise FakeRecoveryDenied("COMPONENT_PATH_DENIED")


def _digest(path: Path) -> dict[str, object]:
    h = hashlib.sha256()
    length = 0
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            length += len(part)
            if length > 128 * 1024 * 1024:
                raise FakeRecoveryDenied("COMPONENT_TOO_LARGE")
            h.update(part)
    if not length:
        raise FakeRecoveryDenied("EMPTY_COMPONENT")
    return {"sha256": h.hexdigest(), "size": length}


def _write_synced(path: Path, content: bytes) -> None:
    with path.open("xb") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())


def _manifest(directory: Path) -> dict:
    # A generation must contain precisely the expected files: even an extra
    # SQLite -wal/-shm sidecar would make the published bundle ambiguous.
    observed = set()
    for candidate in directory.rglob("*"):
        if candidate.is_symlink():
            raise FakeRecoveryDenied("LINKED_GENERATION_COMPONENT")
        if candidate.is_file():
            observed.add(candidate.relative_to(directory).as_posix())
        elif not candidate.is_dir():
            raise FakeRecoveryDenied("UNEXPECTED_GENERATION_COMPONENT")
    if observed != set(FIXED_COMPONENTS):
        raise FakeRecoveryDenied("EXTRA_OR_MISSING_GENERATION_COMPONENT")
    entries = {}
    for name in FIXED_COMPONENTS:
        p = directory / name
        _regular(p, p.parent)
        entries[name] = _digest(p)
    return {"version": 1, "fake_components": entries}


def _verify(directory: Path, manifest: dict) -> None:
    if not isinstance(manifest, dict) or set(manifest) != {"version", "fake_components"}:
        raise FakeRecoveryDenied("MANIFEST_INVALID")
    if manifest["version"] != 1 or set(manifest["fake_components"]) != set(FIXED_COMPONENTS):
        raise FakeRecoveryDenied("MANIFEST_COMPONENT_SET_INVALID")
    if _manifest(directory) != manifest:
        raise FakeRecoveryDenied("GENERATION_INCOMPLETE_OR_TAMPERED")
    # In addition to byte parity, the copied SQLite snapshot must open and pass integrity.
    try:
        conn = sqlite3.connect(f"file:{(directory / 'snapshot.db').as_posix()}?mode=ro", uri=True)
        try:
            if conn.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise FakeRecoveryDenied("SQLITE_SNAPSHOT_INTEGRITY_FAILED")
        finally:
            conn.close()
    except sqlite3.DatabaseError as exc:
        raise FakeRecoveryDenied("SQLITE_SNAPSHOT_UNREADABLE") from exc


def _owner(request_owner: object, expected_owner: object) -> int:
    if (type(request_owner) is not int or request_owner <= 0
            or type(expected_owner) is not int or expected_owner <= 0
            or request_owner != expected_owner):
        raise FakeRecoveryDenied("TRUSTED_OWNER_REQUIRED")
    return request_owner


def _pointer(root: Path) -> Path:
    p = root / "CURRENT.json"
    if p.is_symlink():
        raise FakeRecoveryDenied("POINTER_LINK_DENIED")
    return p


def read_fake_current(root: Path, *, request_owner: object, expected_owner: object) -> tuple[Path, dict]:
    base = _root(root)
    owner = _owner(request_owner, expected_owner)
    pointer = _pointer(root)
    if not pointer.is_file():
        raise FakeRecoveryDenied("NO_COMPLETE_GENERATION")
    _regular(pointer, base)
    try:
        record = json.loads(pointer.read_text("utf-8"))
        if (set(record) != {"version", "owner", "generation", "manifest"}
                or record["version"] != 1 or record["owner"] != owner
                or not isinstance(record["generation"], str)
                or not _GENERATION.fullmatch(record["generation"])):
            raise FakeRecoveryDenied("POINTER_INVALID")
        generation_root = root / "generations"
        if generation_root.is_symlink() or generation_root.resolve(strict=True).parent != base:
            raise FakeRecoveryDenied("GENERATION_ROOT_REDIRECTED")
        directory = generation_root / record["generation"]
        if (not directory.is_dir() or directory.is_symlink()
                or directory.resolve(strict=True).parent != generation_root.resolve(strict=True)):
            raise FakeRecoveryDenied("GENERATION_REDIRECTED")
        _verify(directory, record["manifest"])
        return directory, record
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise FakeRecoveryDenied("CURRENT_GENERATION_UNVERIFIABLE") from exc


def publish_fake_snapshot(
    root: Path, source_conn: sqlite3.Connection, *,
    request_owner: object, expected_owner: object, fail_at: str | None = None,
) -> dict:
    """Stage a consistent SQLite WAL snapshot and FAKE media/vault; publish last.

    Source is an actual sqlite3 connection opened by caller to
    root/inputs/clinical.db. SQLite backup API snapshots committed WAL state.
    Not a SQLCipher/Windows SCM production implementation.
    """
    base = _root(root)
    owner = _owner(request_owner, expected_owner)
    if not isinstance(source_conn, sqlite3.Connection):
        raise FakeRecoveryDenied("TRUSTED_FAKE_CONNECTION_REQUIRED")
    inputs = root / "inputs"
    if inputs.is_symlink() or inputs.resolve(strict=True).parent != base:
        raise FakeRecoveryDenied("INPUT_PARENT_REDIRECTED")
    db_path = inputs / "clinical.db"
    _regular(db_path, inputs)
    try:
        db_files = source_conn.execute("PRAGMA database_list").fetchall()
        if len(db_files) != 1 or Path(db_files[0][2]).resolve(strict=True) != db_path.resolve(strict=True):
            raise FakeRecoveryDenied("SOURCE_CONNECTION_SCOPE_DENIED")
    except sqlite3.DatabaseError as exc:
        raise FakeRecoveryDenied("SOURCE_CONNECTION_UNVERIFIABLE") from exc

    generations = root / "generations"
    generations.mkdir(exist_ok=True)
    if generations.is_symlink() or generations.resolve(strict=True).parent != base:
        raise FakeRecoveryDenied("GENERATION_ROOT_REDIRECTED")
    nonce = uuid.uuid4().hex
    stage = generations / (".stage-" + nonce)
    final = generations / ("g_" + nonce)
    stage.mkdir(mode=0o700)
    (stage / "media-fake").mkdir()
    try:
        snapshot = stage / "snapshot.db"
        # sqlite3.Connection context managers do NOT close on exit: on Windows
        # keeping this handle open prevents cleanup/rename of the snapshot.
        with closing(sqlite3.connect(str(snapshot))) as dest:
            source_conn.backup(dest)
            # The backup API captures committed WAL changes. Convert the
            # OFFLINE destination to DELETE journal mode to ensure a
            # self-contained, exact one-file generation with no sidecars.
            mode = dest.execute("PRAGMA journal_mode=DELETE").fetchone()
            if not mode or str(mode[0]).lower() != "delete":
                raise FakeRecoveryDenied("STAGED_SNAPSHOT_JOURNAL_NOT_CLOSED")
            dest.commit()
        # SQLite creates journal sidecars as needed. Require no live output WAL.
        if Path(str(snapshot) + "-wal").exists() or Path(str(snapshot) + "-shm").exists():
            raise FakeRecoveryDenied("OUTPUT_SIDECAR_UNEXPECTED")
        _regular(snapshot, stage)
        with snapshot.open("r+b") as f:
            os.fsync(f.fileno())
        if fail_at == "after_db":
            raise FakeRecoveryDenied("INJECTED_AFTER_DB")
        for name in FIXED_COMPONENTS[1:]:
            src = inputs / name
            if src.parent.is_symlink() or src.resolve(strict=True).is_relative_to(inputs.resolve(strict=True)) is False:
                raise FakeRecoveryDenied("INPUT_COMPONENT_REDIRECTED")
            _regular(src, src.parent)
            before = _digest(src)
            dest = stage / name
            shutil.copyfile(src, dest)
            _regular(dest, dest.parent)
            if _digest(src) != before or _digest(dest) != before:
                raise FakeRecoveryDenied("SOURCE_CHANGED_DURING_COPY")
            with dest.open("r+b") as f:
                os.fsync(f.fileno())
        if fail_at == "after_media":
            raise FakeRecoveryDenied("INJECTED_AFTER_MEDIA")
        manifest = _manifest(stage)
        _verify(stage, manifest)
        if fail_at == "before_publish":
            raise FakeRecoveryDenied("INJECTED_BEFORE_PUBLISH")
        os.rename(stage, final)   # unique version, never the active DB
        record = {"version": 1, "owner": owner,
                  "generation": final.name, "manifest": manifest}
        if fail_at == "after_generation":
            raise FakeRecoveryDenied("INJECTED_AFTER_GENERATION")
        old = _pointer(root)
        if old.exists():
            read_fake_current(root, request_owner=owner, expected_owner=owner)
        temporary_pointer = root / (".current-" + nonce + ".tmp")
        try:
            _write_synced(temporary_pointer,
                          json.dumps(record, sort_keys=True).encode("utf-8"))
            os.replace(temporary_pointer, old)  # pointer only, not clinical files
        finally:
            temporary_pointer.unlink(missing_ok=True)
        return record
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def clone_current_into_new_fake_dir(root: Path, destination: Path, *,
                                    request_owner: object, expected_owner: object) -> Path:
    base = _root(root)
    _owner(request_owner, expected_owner)
    if (not isinstance(destination, Path) or destination.parent != root
            or destination.name != "isolated-recovery" or destination.exists()):
        raise FakeRecoveryDenied("NEW_ISOLATED_DESTINATION_REQUIRED")
    directory, record = read_fake_current(
        root, request_owner=request_owner, expected_owner=expected_owner)
    # copytree itself can raise AFTER creating partial output: always discard it.
    try:
        shutil.copytree(directory, destination)
        _verify(destination, record["manifest"])
    except Exception:
        if destination.exists():
            shutil.rmtree(destination)
        raise
    return destination
