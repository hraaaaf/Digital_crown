"""P2-F01: disposable synthetic quiescent snapshot oracle; NOT production backup.

Only the cooperating Bridge LAB owner lock excludes writers. Untrusted same-SID
processes, SQLCipher, native Windows SCM and crash-safe key custody are unproved.
"""
from contextlib import closing
from pathlib import Path
import hashlib
import hmac
import json
import re
import shutil
import sqlite3
import stat
import tempfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tools.imaging_gateway.bridge_background_lab import make_lab_collector
from tools.imaging_gateway.gateway import _is_unsafe_path_component
from tools.imaging_gateway.owner_lock_lab import LabOwnerLockError

WITNESS = ".acquisitions-initialized-v1"
SIGNATURE = b"DC6_ACQUISITIONS_INITIALIZED_V1\n"
FIXTURE = ".digitalcrown-imaging-lab-only"
FIXTURE_SIGNATURE = "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n"


class B02SnapshotError(RuntimeError):
    pass


def _root(path):
    source = Path(path).absolute()
    temp = Path(tempfile.gettempdir()).resolve(strict=True)
    if temp not in source.resolve(strict=True).parents:
        raise B02SnapshotError("B02_TEMP_ONLY")
    here = source
    while here != temp:
        if _is_unsafe_path_component(here) or temp not in (here.parent, *here.parent.parents):
            raise B02SnapshotError("B02_REPARSE_OR_ESCAPE")
        here = here.parent
    return source


def _hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def _inventory(root, expected):
    folder = root / "spool"
    if not folder.is_dir() or _is_unsafe_path_component(folder):
        raise B02SnapshotError("B02_SPOOL_MISSING")
    entries = {p.name for p in folder.iterdir()}
    if entries != expected:
        raise B02SnapshotError("B02_SPOOL_SET_MISMATCH")
    result = {}
    for name in sorted(entries):
        p = folder / name
        meta = p.lstat()
        if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1 or _is_unsafe_path_component(p):
            raise B02SnapshotError("B02_SPOOL_UNSAFE")
        result[name] = [_hash(p), meta.st_size]
    return result


def _inspect(snapshot, key):
    dbpath, witness = snapshot / "acquisitions.sqlite3", snapshot / WITNESS
    if (not dbpath.is_file() or _is_unsafe_path_component(dbpath) or
            not witness.is_file() or _is_unsafe_path_component(witness) or
            witness.read_bytes() != SIGNATURE):
        raise B02SnapshotError("B02_INCOMPLETE")
    with closing(sqlite3.connect(dbpath.as_uri() + "?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise B02SnapshotError("B02_SQLITE_INTEGRITY")
        if db.execute("SELECT cabinet,workstation FROM device_scope WHERE singleton=1").fetchone() != ("lab_cabinet", "lab_station"):
            raise B02SnapshotError("B02_SCOPE")
        rows = db.execute("SELECT dedup_key,blob,digest,size FROM items ORDER BY id").fetchall()
    expected = {row[1] for row in rows}
    if len(expected) != len(rows):
        raise B02SnapshotError("B02_DUPLICATE")
    inventory = _inventory(snapshot, expected)
    for identity, blob, digest, size in rows:
        if (not re.fullmatch(r"[0-9a-f]{64}", identity) or
                blob != identity + ".dc6" or
                not re.fullmatch(r"[0-9a-f]{64}", digest) or
                type(size) is not int or not 0 < size <= 50 * 1024 * 1024):
            raise B02SnapshotError("B02_BAD_ROW")
        cipher = (snapshot / "spool" / blob).read_bytes()
        if not cipher.startswith(b"DC6A") or not 33 <= len(cipher) <= size + 32:
            raise B02SnapshotError("B02_BAD_BLOB")
        try:
            clear = AESGCM(key).decrypt(cipher[4:16], cipher[16:],
                   ("DC06A|lab_cabinet|lab_station|" + identity).encode())
        except Exception:
            raise B02SnapshotError("B02_AUTHENTICATION_FAILED") from None
        if len(clear) != size or hashlib.sha256(clear).hexdigest() != digest:
            raise B02SnapshotError("B02_DIGEST")
    return {"version": 1, "db": _hash(dbpath), "witness": _hash(witness),
            "spool": inventory, "rows": len(rows)}


def verify_snapshot(snapshot, key):
    """Read-only, keyed manifest and ciphertext check; no restore side effects."""
    if type(key) is not bytes or len(key) != 32:
        raise B02SnapshotError("B02_KEY")
    folder = _root(snapshot)
    raw = (folder / "manifest.json").read_bytes()
    mac = (folder / "manifest.hmac").read_text(encoding="ascii").strip()
    correct = hmac.new(key, b"B02_LAB|" + raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(correct, mac):
        raise B02SnapshotError("B02_MANIFEST_AUTH")
    if json.loads(raw) != _inspect(folder, key):
        raise B02SnapshotError("B02_MANIFEST_MISMATCH")
    return True


def snapshot_quiescent_lab(root, destination, key):
    """Require a stopped/cooperative Bridge, then publish verified archive only."""
    if type(key) is not bytes or len(key) != 32:
        raise B02SnapshotError("B02_KEY")
    fixture = _root(root)
    if (fixture / FIXTURE).read_text(encoding="utf-8") != FIXTURE_SIGNATURE:
        raise B02SnapshotError("B02_FIXTURE")
    target = Path(destination).absolute()
    if (not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", target.name) or
            target.parent != fixture / "snapshots" or target.exists()):
        raise B02SnapshotError("B02_DESTINATION")
    private = fixture / "private"
    if not all((private / name).exists() for name in
               ("acquisitions.sqlite3", "spool", WITNESS)):
        raise B02SnapshotError("B02_SOURCE_INCOMPLETE")
    env = {"DC_V15_06_BRIDGE_LAB": "1", "ENVIRONMENT": "test",
           "DIGITALCROWN_ISOLATED_RUNTIME": "true",
           "DC_V15_06_BRIDGE_LAB_ROOT": str(fixture),
           "DC_V15_06_BRIDGE_LAB_KEY_HEX": key.hex()}
    try:
        collector, owner = make_lab_collector(env, acquire_owner=True)
    except LabOwnerLockError:
        raise B02SnapshotError("B02_ACTIVE_BRIDGE") from None
    with owner:
        with collector._db() as live:
            blobs = {row[0] for row in live.execute("SELECT blob FROM items")}
        before = _inventory(private, blobs)
        snapshots = fixture / "snapshots"
        snapshots.mkdir(mode=0o700, exist_ok=True)
        if _is_unsafe_path_component(snapshots):
            raise B02SnapshotError("B02_UNSAFE_SNAPSHOT_ROOT")
        stage = Path(tempfile.mkdtemp(prefix=".b02-partial-", dir=snapshots))
        try:
            with collector._db() as live:
                with closing(sqlite3.connect(stage / "acquisitions.sqlite3")) as saved:
                    live.backup(saved)
            shutil.copytree(private / "spool", stage / "spool")
            shutil.copy2(private / WITNESS, stage / WITNESS)
            if _inventory(private, blobs) != before:
                raise B02SnapshotError("B02_SOURCE_CHANGED")
            descriptor = _inspect(stage, key)
            raw = json.dumps(descriptor, sort_keys=True, separators=(",", ":")).encode()
            (stage / "manifest.json").write_bytes(raw)
            (stage / "manifest.hmac").write_text(
                hmac.new(key, b"B02_LAB|" + raw, hashlib.sha256).hexdigest(),
                encoding="ascii")
            verify_snapshot(stage, key)
            if target.exists():
                raise B02SnapshotError("B02_DESTINATION_RACE")
            stage.rename(target)  # same filesystem; not a durability guarantee
            return target
        finally:
            if stage.exists():
                shutil.rmtree(stage)
