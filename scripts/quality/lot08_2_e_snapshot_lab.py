"""LOT08.2-E: disposable three-SQLite cross-process snapshot LAB, not clinical backup.

Cooperative writers MUST acquire the same Windows msvcrt byte-range gate (or
POSIX flock) before touching any of the three stores. A non-cooperating writer,
real service restore, hostile manifest rewrite, crash in an unfenced writer, and
power-loss durability are NOT solved here. Refuse mismatched epochs and restore
only into a fresh directory; never overwrite existing cabinet data.
"""
from __future__ import annotations

from contextlib import closing
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time

FILES = ("auth-synthetic.sqlite", "devices-synthetic.sqlite", "queue-synthetic.sqlite")
MANIFEST = "synthetic-snapshot-manifest.json"


class SnapshotLabError(RuntimeError):
    pass


class CrossProcessGate:
    """Blocking OS cross-process gate. All cooperating processes share ONE root."""

    def __init__(self, root: Path, timeout_seconds: float = 20):
        self.root = Path(root)
        self.timeout = timeout_seconds
        self.file = None

    def __enter__(self):
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise SnapshotLabError("LAB_SYMLINK_FORBIDDEN")
        self.file = (self.root / ".snapshot-cooperative.gate").open("a+b")
        self.file.seek(0, os.SEEK_END)
        if self.file.tell() == 0:
            self.file.write(b"\0")
            self.file.flush()
        deadline = time.monotonic() + self.timeout
        try:
            while True:
                try:
                    self.file.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise SnapshotLabError("LAB_GATE_TIMEOUT") from None
                    time.sleep(0.015)
        except BaseException:
            self.file.close()
            self.file = None
            raise
        return self

    def __exit__(self, *_):
        try:
            self.file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
        finally:
            self.file.close()
            self.file = None


def _path(root: Path, name: str) -> Path:
    if name not in FILES:
        raise SnapshotLabError("LAB_FILENAME_REJECTED")
    p = Path(root) / name
    if p.is_symlink() or not p.is_file():
        raise SnapshotLabError("LAB_FILE_MISSING_OR_SYMLINK")
    return p


def _epoch(p: Path) -> int:
    try:
        with closing(sqlite3.connect(p.as_uri() + "?mode=ro", uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise SnapshotLabError("LAB_SQLITE_INTEGRITY")
            if db.execute("PRAGMA foreign_key_check").fetchall():
                raise SnapshotLabError("LAB_SQLITE_FOREIGN_KEYS")
            row = db.execute("SELECT epoch, marker FROM lab_epoch WHERE id=1").fetchone()
            if not row or type(row[0]) is not int or row[0] < 0:
                raise SnapshotLabError("LAB_EPOCH_MISSING")
            if row[1] != "ONLY_SYNTHETIC_FIXTURES":
                raise SnapshotLabError("LAB_NOT_SYNTHETIC")
            return row[0]
    except sqlite3.DatabaseError as exc:
        raise SnapshotLabError("LAB_SQLITE_INVALID") from exc


def _consistent_epoch(root: Path) -> int:
    epochs = [_epoch(_path(root, name)) for name in FILES]
    if len(set(epochs)) != 1:
        raise SnapshotLabError("LAB_CROSS_STORE_EPOCH_DIVERGED")
    return epochs[0]


def create_synthetic_fixture(root: Path) -> None:
    root = Path(root)
    with CrossProcessGate(root):
        for name in FILES:
            p = root / name
            if p.exists() or p.is_symlink():
                raise SnapshotLabError("LAB_REFUSE_EXISTING_FILE")
        for name in FILES:
            with closing(sqlite3.connect(root / name)) as db:
                db.execute("CREATE TABLE lab_epoch(id INTEGER PRIMARY KEY CHECK(id=1), epoch INTEGER NOT NULL CHECK(epoch>=0), marker TEXT NOT NULL)")
                db.execute("INSERT INTO lab_epoch VALUES(1,0,'ONLY_SYNTHETIC_FIXTURES')")
                db.execute("CREATE TABLE synthetic_events(epoch INTEGER PRIMARY KEY, value TEXT NOT NULL)")
                db.commit()


def transition_synthetic(root: Path, target_epoch: int, *, fail_after: int = 0, delay: float = 0.0) -> None:
    if type(target_epoch) is not int or target_epoch < 1:
        raise SnapshotLabError("LAB_EPOCH_INVALID")
    with CrossProcessGate(root):
        previous = _consistent_epoch(root)
        if target_epoch != previous + 1:
            raise SnapshotLabError("LAB_EPOCH_NOT_NEXT")
        for i, name in enumerate(FILES, 1):
            with closing(sqlite3.connect(_path(root, name))) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT INTO synthetic_events VALUES(?,?)", (target_epoch, "SYNTHETIC_ONLY"))
                db.execute("UPDATE lab_epoch SET epoch=? WHERE id=1", (target_epoch,))
                db.commit()
            if delay:
                time.sleep(delay)
            if fail_after == i:
                raise SnapshotLabError("LAB_INJECTED_PARTIAL_COMMIT")


def _digest(p: Path) -> str:
    h = sha256()
    with p.open("rb") as source:
        while block := source.read(131072):
            h.update(block)
    return h.hexdigest()


def verify_bundle(bundle: Path) -> int:
    bundle = Path(bundle)
    if not bundle.is_dir() or bundle.is_symlink():
        raise SnapshotLabError("LAB_BUNDLE_INVALID")
    if {p.name for p in bundle.iterdir()} != set(FILES) | {MANIFEST}:
        raise SnapshotLabError("LAB_BUNDLE_CONTENTS")
    manifest_path = bundle / MANIFEST
    if manifest_path.is_symlink():
        raise SnapshotLabError("LAB_MANIFEST_SYMLINK")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SnapshotLabError("LAB_MANIFEST_INVALID") from exc
    if (
        type(manifest) is not dict
        or set(manifest) != {"schema", "epoch", "sha256"}
        or manifest["schema"] != "LOT08.2-E-SYNTHETIC-V1"
        or type(manifest["epoch"]) is not int
        or manifest["epoch"] < 0
        or type(manifest["sha256"]) is not dict
        or set(manifest["sha256"]) != set(FILES)
    ):
        raise SnapshotLabError("LAB_MANIFEST_INVALID")
    for name in FILES:
        p = _path(bundle, name)
        if type(manifest["sha256"][name]) is not str or _digest(p) != manifest["sha256"][name]:
            raise SnapshotLabError("LAB_HASH_MISMATCH")
    if _consistent_epoch(bundle) != manifest["epoch"]:
        raise SnapshotLabError("LAB_CROSS_STORE_EPOCH_DIVERGED")
    return manifest["epoch"]


def snapshot_synthetic(root: Path, archive: Path, *, fail_after: int = 0) -> int:
    root, archive = Path(root), Path(archive)
    if archive.exists() or archive.is_symlink():
        raise SnapshotLabError("LAB_ARCHIVE_EXISTS")
    archive.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".08e-snapshot-staging-", dir=archive.parent))
    try:
        with CrossProcessGate(root):
            epoch = _consistent_epoch(root)
            hashes = {}
            for i, name in enumerate(FILES, 1):
                source = _path(root, name)
                with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as db:
                    with closing(sqlite3.connect(stage / name)) as target:
                        db.backup(target)
                hashes[name] = _digest(stage / name)
                if fail_after == i:
                    raise SnapshotLabError("LAB_INJECTED_SNAPSHOT_INTERRUPTION")
            (stage / MANIFEST).write_text(json.dumps({
                "schema": "LOT08.2-E-SYNTHETIC-V1", "epoch": epoch, "sha256": hashes,
            }, sort_keys=True), encoding="utf-8")
            if verify_bundle(stage) != epoch:
                raise SnapshotLabError("LAB_SNAPSHOT_INCONSISTENT")
            if archive.exists() or archive.is_symlink():
                raise SnapshotLabError("LAB_ARCHIVE_EXISTS")
            os.rename(stage, archive)
            return epoch
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def restore_synthetic(bundle: Path, destination: Path) -> int:
    bundle, destination = Path(bundle), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise SnapshotLabError("LAB_RESTORE_REFUSE_OVERWRITE")
    epoch = verify_bundle(bundle)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".08e-restore-staging-", dir=destination.parent))
    try:
        for name in (*FILES, MANIFEST):
            shutil.copyfile(bundle / name, stage / name)
        if verify_bundle(stage) != epoch:
            raise SnapshotLabError("LAB_RESTORE_VERIFY_FAILED")
        if destination.exists() or destination.is_symlink():
            raise SnapshotLabError("LAB_RESTORE_REFUSE_OVERWRITE")
        os.rename(stage, destination)
        return epoch
    finally:
        if stage.exists():
            shutil.rmtree(stage)
