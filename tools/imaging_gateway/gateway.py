"""LOT06-A: encrypted, restartable, disabled-by-default hot-folder collector.

NO patient inference, server write or server acknowledgement is implemented.
The server-side authorization/idempotency gate is a separate integration step.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import errno
import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import sqlite3
import stat
import tempfile
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tools.imaging_gateway.media_validation import validated_mime
from tools.imaging_gateway.windows_scoped_read_lab import directory_identity, open_relative_read
from tools.imaging_gateway.windows_scoped_spool_lab import write_ciphertext
from tools.imaging_gateway.sqlite_boundary_lab import SQLiteBoundaryError, inspect_sqlite_boundary


class GatewayError(RuntimeError):
    pass


SUPPORTED = {
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/webp": {".webp"},
    "application/pdf": {".pdf"},
}
ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_BYTES = 50 * 1024 * 1024
DEFAULT_SPOOL_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_QUEUE_ITEMS = 1000
DEFAULT_FREE_RESERVE_BYTES = 64 * 1024 * 1024
_MAX_SPOOL_BYTES = 16 * 1024 ** 4


class StorageBackpressure(GatewayError):
    """Local capacity gate; neither source nor confirmed media are removed."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _is_disk_full(error):
    return (
        getattr(error, "errno", None) in (errno.ENOSPC, getattr(errno, "EDQUOT", -1))
        or getattr(error, "winerror", None) in (39, 112)
        or getattr(error, "sqlite_errorcode", None) == sqlite3.SQLITE_FULL
    )



def _is_unsafe_path_component(path: Path) -> bool:
    """Detect symlinks and NTFS junction/reparse points, including Python 3.11.

    This initial check does not replace kernel-handle/ACL confinement in a
    future supported clinical capture driver.
    """
    try:
        meta = path.lstat()
    except FileNotFoundError:
        return False
    return (
        stat.S_ISLNK(meta.st_mode)
        or (os.name == "nt" and bool(
            getattr(meta, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ))
    )

def sniff(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    return None


@dataclass(frozen=True)
class Config:
    cabinet: str
    workstation: str
    watch: Path
    private: Path
    key: bytes
    category: str = "PHOTO"
    max_bytes: int = MAX_BYTES
    require_ready_manifest: bool = False
    max_spool_bytes: int = DEFAULT_SPOOL_BYTES
    max_queue_items: int = DEFAULT_QUEUE_ITEMS
    min_free_bytes: int = DEFAULT_FREE_RESERVE_BYTES

    def __post_init__(self):
        if not ID.fullmatch(self.cabinet) or not ID.fullmatch(self.workstation):
            raise GatewayError("invalid cabinet/workstation")
        if self.category not in {"PHOTO", "RADIOGRAPH"}:
            raise GatewayError("explicit category required")
        if type(self.require_ready_manifest) is not bool:
            raise GatewayError("invalid ready-manifest mode")
        if (type(self.max_spool_bytes) is not int or
                not 1 <= self.max_spool_bytes <= _MAX_SPOOL_BYTES or
                type(self.max_queue_items) is not int or
                not 1 <= self.max_queue_items <= 100_000 or
                type(self.min_free_bytes) is not int or
                not 0 <= self.min_free_bytes <= _MAX_SPOOL_BYTES):
            raise GatewayError("invalid local capacity policy")
        if len(self.key) != 32:
            raise GatewayError("a 256-bit spool key is mandatory")
        if not 0 < self.max_bytes <= MAX_BYTES:
            raise GatewayError("invalid size limit")
        w, p = Path(self.watch).absolute(), Path(self.private).absolute()
        if w == p or w in p.parents or p in w.parents:
            raise GatewayError("watch and private paths must be disjoint")
        # Windows may canonicalize harmless 8.3 paths, drive casing and volume aliases.
        # Check actual symbolic links instead of rejecting differing path spellings.
        ancestors = (*w.parents, *p.parents)
        if (not w.is_dir() or
                any(_is_unsafe_path_component(item) for item in (w, p, *ancestors))):
            raise GatewayError("unsafe watch/private root or symlink ancestor")
        # Reparse points must not make resolved watch and private overlap.
        resolved_w, resolved_p = w.resolve(strict=True), p.resolve(strict=False)
        if (resolved_w == resolved_p or resolved_w in resolved_p.parents or
                resolved_p in resolved_w.parents):
            raise GatewayError("watch and private canonical paths overlap")
        p.mkdir(parents=True, exist_ok=True)
        if _is_unsafe_path_component(p):
            raise GatewayError("unsafe private root after creation")


class HotFolder:
    def __init__(self, config: Config):
        self.config = config
        self._observed = {}
        self._last_capacity_issue = None  # diagnostic only; no patient/file info
        self.private = Path(config.private).absolute()
        self.spool = self.private / "spool"
        if _is_unsafe_path_component(self.spool):
            raise GatewayError("spool symlink rejected")
        self.spool.mkdir(mode=0o700, exist_ok=True)
        if os.name != "nt":
            os.chmod(self.private, 0o700)
            os.chmod(self.spool, 0o700)
        self.db_file = self.private / "acquisitions.sqlite3"
        if _is_unsafe_path_component(self.db_file):
            raise GatewayError("database symlink rejected")
        self._watch_identity = self._directory_identity(Path(config.watch))
        self._windows_watch_identity = directory_identity(config.watch)
        self._private_identity = self._directory_identity(self.private)
        self._windows_private_identity = directory_identity(self.private)
        self._db_file_identity = None  # Pinned after first authorized open.
        self._spool_identity = self._directory_identity(self.spool)
        self._windows_spool_identity = directory_identity(self.spool)
        with self._db() as db:
            # executescript() commits DDL in autocommit mode and can leave an
            # incomplete ledger when later schema/scope validation fails.
            # Keep ALL first-boot schema and device_scope writes atomic.
            db.execute("BEGIN IMMEDIATE")
            db.execute("""
            CREATE TABLE IF NOT EXISTS items(
                            id INTEGER PRIMARY KEY,
                            dedup_key TEXT NOT NULL UNIQUE,
                            digest TEXT NOT NULL,
                            size INTEGER NOT NULL,
                            mime TEXT,
                            category TEXT NOT NULL,
                            state TEXT NOT NULL,
                            blob TEXT NOT NULL,
                            retries INTEGER NOT NULL DEFAULT 0,
                            due INTEGER,
                            created_at INTEGER NOT NULL
                        )
            """)
            db.execute("""
            CREATE TABLE IF NOT EXISTS audit(
                            id INTEGER PRIMARY KEY,
                            item_id INTEGER NOT NULL,
                            event TEXT NOT NULL,
                            at INTEGER NOT NULL
                        )
            """)
            db.execute("""
            CREATE TABLE IF NOT EXISTS device_scope(
                            singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                            cabinet TEXT NOT NULL,
                            workstation TEXT NOT NULL
                        )
            """)
            db.execute(
                "INSERT OR IGNORE INTO device_scope(singleton,cabinet,workstation) VALUES(1,?,?)",
                (config.cabinet, config.workstation),
            )
            active = db.execute(
                "SELECT cabinet,workstation FROM device_scope WHERE singleton=1"
            ).fetchone()
            if active != (config.cabinet, config.workstation):
                raise GatewayError("state directory belongs to another cabinet/workstation")

    def _sqlite_guard(self):
        """Best-effort LAB gate; path-based SQLite VFS still needs OS ACLs."""
        self._assert_live_directories()
        try:
            found = inspect_sqlite_boundary(
                self.private, self.db_file, self._private_identity,
                self._windows_private_identity,
            )
        except SQLiteBoundaryError as error:
            raise GatewayError("SQLite LAB boundary rejected: " + str(error)) from None
        if (self._db_file_identity is not None
                and found.get("") != self._db_file_identity):
            raise GatewayError("SQLite LAB database identity changed")
        return found

    @staticmethod
    def _reject_changed_sidecars(previous, current):
        """Detect observed WAL/SHM/journal replacement within ONE connection.

        Absence/recreation between snapshots and sub-check races remain possible;
        this does NOT turn the path-based SQLite VFS into a secure sandbox.
        """
        for suffix in ("-wal", "-shm", "-journal"):
            if (suffix in previous and suffix in current
                    and previous[suffix] != current[suffix]):
                raise GatewayError("SQLite LAB sidecar changed during connection")

    @contextmanager
    def _db(self):
        before = self._sqlite_guard()
        # After initial trusted creation, NEVER silently recreate a missing
        # database. A disappeared DB is an integrity incident, not a blank
        # cabinet. SQLite URI mode=rw refuses implicit file creation.
        # This is fail-closed recovery, NOT race-free Windows VFS confinement.
        if self._db_file_identity is None:
            db = sqlite3.connect(self.db_file, timeout=10)
        else:
            db = sqlite3.connect(self.db_file.as_uri() + "?mode=rw",
                                 timeout=10, uri=True)
        try:
            # Even a successful sqlite3.connect might have followed a swapped
            # root; reject any now-observable substitution before executing SQL.
            after = self._sqlite_guard()
            self._reject_changed_sidecars(before, after)
            if before.get("") is not None and after.get("") != before[""]:
                raise GatewayError("SQLite LAB database switched during open")
            if after.get("") is None:
                raise GatewayError("SQLite LAB database missing after open")
            if self._db_file_identity is None:
                self._db_file_identity = after[""]
            locations = db.execute("PRAGMA database_list").fetchall()
            expected = os.path.normcase(str(self.db_file.absolute()))
            if (len(locations) != 1 or locations[0][1] != "main"
                    or os.path.normcase(os.path.abspath(locations[0][2])) != expected):
                raise GatewayError("SQLite LAB unexpected database attachment/path")
            # Do not silently downgrade from WAL to rollback journaling.
            mode = db.execute("PRAGMA journal_mode=WAL").fetchone()
            if not mode or str(mode[0]).lower() != "wal":
                raise GatewayError("SQLite LAB WAL mode unavailable")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA temp_store=MEMORY")
            # Only trusted setup may configure durability and journal policy.
            # This connection-level authorizer is defense in depth, NOT a
            # filesystem ACL or a Windows handle-relative SQLite VFS.
            forbidden = {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
            protected_pragmas = {
                "writable_schema", "journal_mode", "trusted_schema",
                "temp_store", "synchronous", "locking_mode",
                "wal_autocheckpoint", "journal_size_limit", "cache_size",
                "mmap_size", "read_uncommitted", "secure_delete",
                "page_size", "auto_vacuum",
            }
            # These PRAGMAs can alter data/files even when no value is passed.
            side_effect_pragmas = {
                "wal_checkpoint", "incremental_vacuum", "optimize",
            }
            def authorize(action, arg1, arg2, db_name, trigger):
                if action in forbidden:
                    return sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_PRAGMA:
                    name = str(arg1).lower()
                    if (name in side_effect_pragmas or
                            (name in protected_pragmas and arg2 is not None)):
                        return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            db.set_authorizer(authorize)
            verified = self._sqlite_guard()
            self._reject_changed_sidecars(after, verified)
            yield db
            # All fallible policy checks must happen BEFORE the durable
            # commit. A post-commit guard can report failure even though the
            # transaction was already saved and rollback cannot undo it.
            precommit = self._sqlite_guard()
            self._reject_changed_sidecars(verified, precommit)
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _source_signature(st):
        return (st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_dev, st.st_ino)

    @staticmethod
    def _directory_identity(path):
        meta = path.stat()
        return (meta.st_dev, meta.st_ino)

    def _assert_live_directories(self):
        """Best-effort fail-closed check for roots replaced after initialization.

        This catches deterministic junction and directory swaps between polls.
        It does not close a kernel-level Windows rename race during I/O;
        supported hardware must use secure directory handles/ACLs or isolation.
        """
        for root, expected in (
            (Path(self.config.watch), self._watch_identity),
            (self.private, self._private_identity),
            (self.spool, self._spool_identity),
        ):
            if (not root.is_dir() or _is_unsafe_path_component(root) or
                    self._directory_identity(root) != expected or
                    any(_is_unsafe_path_component(parent) for parent in root.parents)):
                raise GatewayError("imaging root replaced or unsafe")

    def _identity(self, digest, path, signature):
        # Replayed captures retain identity; distinct file generations do not coalesce.
        # Source path and file metadata never enter the local ledger in plaintext.
        parts = [self.config.cabinet, self.config.workstation,
                 self.config.category, digest, str(path.absolute()), list(signature)]
        raw = json.dumps(parts, separators=(",", ":")).encode()
        return hmac.new(self.config.key, raw, hashlib.sha256).hexdigest()

    def _aad(self, identity):
        return ("DC06A|" + self.config.cabinet + "|" +
                self.config.workstation + "|" + identity).encode()

    def _read(self, path, initial):
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = (open_relative_read(self.config.watch, path.name, self._windows_watch_identity)
              if os.name == "nt" else os.open(path, flags))
        try:
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode) or self._source_signature(opened) != initial:
                raise GatewayError("source changed")
            with os.fdopen(fd, "rb", closefd=False) as src:
                data = src.read(self.config.max_bytes + 1)
            after = os.fstat(fd)
        finally:
            os.close(fd)
        final = path.lstat()
        if (self._source_signature(after) != initial or self._source_signature(final) != initial or
                not stat.S_ISREG(final.st_mode) or len(data) != initial[0]):
            raise GatewayError("source changed during read")
        return data

    def _ready_manifest(self, path):
        """Optional *producer* completion claim. Not a device authorization.

        A .ready sidecar must be a plain, stable, small JSON file with exactly
        version/size/sha256. No symlinks or arbitrary directories are followed.
        Missing, malformed or racing manifests simply prevent staging.
        """
        marker = path.with_name(path.name + ".ready")
        try:
            before = marker.lstat()
            if (not stat.S_ISREG(before.st_mode) or
                    not 0 < before.st_size <= 256 or
                    before.st_nlink != 1):
                return None
            flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
            fd = (open_relative_read(self.config.watch, marker.name, self._windows_watch_identity)
                  if os.name == "nt" else os.open(marker, flags))
            try:
                opened = os.fstat(fd)
                if (not stat.S_ISREG(opened.st_mode) or
                        opened.st_nlink != 1 or
                        self._source_signature(opened) != self._source_signature(before)):
                    return None
                with os.fdopen(fd, "rb", closefd=False) as reader:
                    raw = reader.read(257)
                after = os.fstat(fd)
            finally:
                os.close(fd)
            final = marker.lstat()
            if (self._source_signature(after) != self._source_signature(before) or
                    self._source_signature(final) != self._source_signature(before) or
                    not stat.S_ISREG(final.st_mode) or len(raw) != before.st_size):
                return None
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or set(obj) != {"version", "size", "sha256"}:
                return None
            if type(obj["version"]) is not int or obj["version"] != 1:
                return None
            if type(obj["size"]) is not int or not 0 < obj["size"] <= self.config.max_bytes:
                return None
            digest = obj["sha256"]
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                return None
            return (digest, obj["size"], self._source_signature(before))
        except (OSError, ValueError, UnicodeError, TypeError):
            return None

    def _decrypt(self, blob, identity, digest):
        target = self.spool / blob
        if target.is_symlink() or not target.is_file():
            raise GatewayError("spool missing or symlink")
        # No unbounded allocation if a local actor plants a huge spool file.
        if not 33 <= target.stat().st_size <= self.config.max_bytes + 32:
            raise GatewayError("spool size invalid")
        if os.name == "nt":
            fd = open_relative_read(self.spool, blob, self._windows_spool_identity)
            try:
                with os.fdopen(fd, "rb", closefd=False) as reader:
                    data = reader.read(self.config.max_bytes + 33)
            finally:
                os.close(fd)
        else:
            data = target.read_bytes()
        if len(data) > self.config.max_bytes + 32:
            raise GatewayError("spool size changed")
        if not data.startswith(b"DC6A") or len(data) < 33:
            raise GatewayError("spool corrupted")
        try:
            clear = AESGCM(self.config.key).decrypt(data[4:16], data[16:], self._aad(identity))
        except Exception as error:
            raise GatewayError("spool authentication failed") from error
        if hashlib.sha256(clear).hexdigest() != digest:
            raise GatewayError("spool digest mismatch")
        return clear

    def _store(self, blob, identity, content, digest):
        dest = self.spool / blob
        if dest.is_symlink():
            raise GatewayError("unsafe spool destination")
        if dest.exists():
            self._decrypt(blob, identity, digest)
            return
        nonce = secrets.token_bytes(12)
        encrypted = b"DC6A" + nonce + AESGCM(self.config.key).encrypt(
            nonce, content, self._aad(identity))
        if os.name == "nt":
            # Temp creation and atomic rename are both relative to the same
            # verified native directory handle. No path-based os.replace.
            write_ciphertext(self.spool, blob, encrypted, self._windows_spool_identity)
            return
        fd, tmp = tempfile.mkstemp(prefix=".partial-", dir=self.spool)
        try:
            if os.name != "nt":
                os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as output:
                output.write(encrypted)
                output.flush()
                os.fsync(output.fileno())
            if dest.exists() or dest.is_symlink():
                raise GatewayError("spool collision")
            os.replace(tmp, dest)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def _spool_usage(self, db):
        """Count actual on-disk bytes, including crash-orphan and partial files.

        Never delete untracked bytes automatically: retain for forensic recovery.
        """
        registered = {row[0] for row in db.execute("SELECT blob FROM items")}
        occupied = 0
        orphan_bytes = 0
        orphan_count = 0
        file_count = 0
        # Close the directory handle on *all* exits, including fail-closed
        # rejections (symlinks, hardlinks and file-count backpressure).
        with os.scandir(self.spool) as entries:
            for entry in entries:
                file_count += 1
                if file_count > 100_000:
                    raise StorageBackpressure("SPOOL_DIRECTORY_LIMIT")
                # Windows DirEntry.stat() can omit the NTFS hardlink count.
                # os.stat(path, follow_symlinks=False) performs a full file query,
                # preserving the ability to refuse observed hardlinks and symlinks.
                meta = os.stat(entry.path, follow_symlinks=False)
                if not stat.S_ISREG(meta.st_mode) or meta.st_nlink > 1:
                    raise GatewayError("unsafe spool entry")
                occupied += meta.st_size
                if entry.name not in registered:
                    orphan_count += 1
                    orphan_bytes += meta.st_size
        return {
            "spool_bytes": occupied,
            "orphan_files": orphan_count,
            "orphan_bytes": orphan_bytes,
        }

    def _check_capacity(self, db, incoming_size, blob):
        if db.execute("SELECT COUNT(*) FROM items").fetchone()[0] >= self.config.max_queue_items:
            raise StorageBackpressure("QUEUE_ITEM_LIMIT")
        used = self._spool_usage(db)["spool_bytes"]
        # If the ciphertext was durably renamed before a prior DB crash,
        # a matching capture may reuse that orphan without counting it twice.
        additional = 0 if (self.spool / blob).exists() else incoming_size + 32
        if used + additional > self.config.max_spool_bytes:
            raise StorageBackpressure("SPOOL_BYTE_LIMIT")
        free = shutil.disk_usage(self.spool).free
        if free < additional + self.config.min_free_bytes:
            raise StorageBackpressure("DISK_RESERVE_LIMIT")

    def storage_health(self):
        """Explicit no-PHI operational diagnostics. No file names/paths/digests."""
        with self._db() as db:
            raw_counts = db.execute(
                "SELECT state,COUNT(*) FROM items GROUP BY state"
            ).fetchall()
            # SQL states are not user-facing strings. Never leak a corrupt or
            # attacker-injected state value through --health/--operations.
            allowed = {"PENDING_CONFIRMATION", "QUARANTINED",
                       "RETRY_PENDING", "BLOCKED"}
            counts = {}
            for raw_state, count in raw_counts:
                name = raw_state if raw_state in allowed else "UNRECOGNIZED_STATE"
                counts[name] = counts.get(name, 0) + count
            queued = sum(counts.values())
            usage = self._spool_usage(db)
            free = shutil.disk_usage(self.spool).free
        limited = (
            self._last_capacity_issue is not None or
            "UNRECOGNIZED_STATE" in counts or
            queued >= self.config.max_queue_items or
            usage["spool_bytes"] >= self.config.max_spool_bytes or
            free < self.config.min_free_bytes
        )
        return {
            "state": "BACKPRESSURE" if limited else "READY",
            "queued_items": queued,
            "states": counts,
            "spool_bytes": usage["spool_bytes"],
            "orphan_files": usage["orphan_files"],
            "orphan_bytes": usage["orphan_bytes"],
            "free_bytes": free,
            "max_spool_bytes": self.config.max_spool_bytes,
            "max_queue_items": self.config.max_queue_items,
            "min_free_bytes": self.config.min_free_bytes,
            "last_capacity_issue": self._last_capacity_issue,
        }

    def _previous_ready_capture(self, path, signature, ready):
        """Cheap indexed replay check, without rereading or decrypting content.

        This is only for captures already verified against a producer manifest.
        read_verified() remains the cryptographic integrity gate before use.
        """
        if ready is None or ready[1] != signature[0]:
            return False
        identity = self._identity(ready[0], path, signature)
        with self._db() as db:
            previous = db.execute(
                "SELECT blob,digest,size FROM items WHERE dedup_key=?", (identity,)
            ).fetchone()
        if previous is None:
            return False
        blob, digest, size = previous
        if digest != ready[0] or size != ready[1]:
            raise GatewayError("existing acquisition ledger mismatch")
        target = self.spool / blob
        if _is_unsafe_path_component(target) or not target.is_file():
            raise GatewayError("previous spool missing or unsafe")
        stored_size = target.stat().st_size
        if not 33 <= stored_size <= size + 32:
            raise GatewayError("previous spool size invalid")
        if (self._source_signature(path.lstat()) != signature or
                self._ready_manifest(path) != ready):
            return False
        return True

    def scan_once(self):
        self._assert_live_directories()
        outcome = dict(staged=0, quarantine=0, duplicate=0, unstable=0, rejected=0,
                       deferred=0)
        self._last_capacity_issue = None
        for path in sorted(Path(self.config.watch).iterdir()):
            if self.config.require_ready_manifest and path.name.endswith(".ready"):
                continue  # Completion metadata is not an acquisition.
            if path.is_symlink() or path.name.startswith("."):
                outcome["rejected"] += 1
                continue
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= self.config.max_bytes:
                outcome["rejected"] += 1
                continue
            signature = self._source_signature(info)
            token = str(path)
            if self._observed.get(token) != signature:
                self._observed[token] = signature
                outcome["unstable"] += 1
                continue
            ready_before = self._ready_manifest(path) if self.config.require_ready_manifest else None
            if self.config.require_ready_manifest and ready_before is None:
                outcome["unstable"] += 1
                continue
            if self.config.require_ready_manifest:
                try:
                    if self._previous_ready_capture(path, signature, ready_before):
                        outcome["duplicate"] += 1
                        continue
                except (OSError, ValueError):
                    outcome["unstable"] += 1
                    continue
            self._assert_live_directories()
            try:
                content = self._read(path, signature)
            except (GatewayError, OSError):
                self._observed.pop(token, None)
                outcome["unstable"] += 1
                continue
            # Reject a source-root swap that happened *during* the read.
            self._assert_live_directories()
            digest = hashlib.sha256(content).hexdigest()
            if self.config.require_ready_manifest:
                ready_after = self._ready_manifest(path)
                if (ready_before != ready_after or
                        ready_before[0] != digest or ready_before[1] != len(content)):
                    outcome["unstable"] += 1
                    continue
            identity = self._identity(digest, path, signature)
            mime = sniff(content)
            accepted = (mime is not None and path.suffix.lower() in SUPPORTED[mime]
                        and validated_mime(content, mime))
            state = "PENDING_CONFIRMATION" if accepted else "QUARANTINED"
            blob = identity + ".dc6"
            try:
                with self._db() as db:
                    db.execute("BEGIN IMMEDIATE")
                    previous = db.execute(
                        "SELECT blob,digest FROM items WHERE dedup_key=?", (identity,)
                    ).fetchone()
                    if previous:
                        self._decrypt(previous[0], identity, previous[1])
                        outcome["duplicate"] += 1
                        continue
                    # Reserve under the SQLite writer lock, including physical
                    # orphans from an earlier interrupted file-to-DB commit.
                    self._assert_live_directories()
                    self._check_capacity(db, len(content), blob)
                    self._store(blob, identity, content, digest)
                    self._assert_live_directories()
                    item = db.execute(
                        """INSERT INTO items
                        (dedup_key,digest,size,mime,category,state,blob,created_at)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (identity, digest, len(content), mime, self.config.category,
                         state, blob, int(time.time())),
                    )
                    db.execute(
                        "INSERT INTO audit(item_id,event,at) VALUES(?,?,?)",
                        (item.lastrowid, state, int(time.time())),
                    )
            except StorageBackpressure as error:
                self._last_capacity_issue = error.code
                outcome["deferred"] += 1
                continue
            except (OSError, sqlite3.OperationalError) as error:
                if not _is_disk_full(error):
                    raise
                # The DB transaction rolled back; original file stays untouched.
                # Never synthesize CONFIRMED or silently drop an acquisition.
                self._last_capacity_issue = "DISK_FULL"
                outcome["deferred"] += 1
                continue
            outcome["staged" if accepted else "quarantine"] += 1
        return outcome

    def items(self):
        """Minimal diagnostics: no patient, appointment or source filename."""
        with self._db() as db:
            rows = db.execute(
                "SELECT id,digest,size,mime,category,state,retries FROM items ORDER BY id"
            ).fetchall()
        keys = ("id", "digest", "size", "mime", "category", "state", "retries")
        return [dict(zip(keys, row)) for row in rows]

    def read_verified(self, item_id):
        """Internal read primitive, not a patient binding or a server receipt."""
        with self._db() as db:
            row = db.execute(
                "SELECT dedup_key,blob,digest FROM items WHERE id=?", (item_id,)
            ).fetchone()
        if row is None:
            raise GatewayError("unknown item")
        return self._decrypt(row[1], row[0], row[2])

    def record_transport_failure(self, item_id, now):
        """Durable bounded retry bookkeeping; never grants upload permission."""
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT retries,state FROM items WHERE id=?", (item_id,)).fetchone()
            if row is None or row[1] not in {"PENDING_CONFIRMATION", "RETRY_PENDING"}:
                raise GatewayError("retry not allowed")
            retries = row[0] + 1
            state = "BLOCKED" if retries > 6 else "RETRY_PENDING"
            due = None if state == "BLOCKED" else now + min(3600, 2 ** retries)
            db.execute(
                "UPDATE items SET retries=?,state=?,due=? WHERE id=?",
                (retries, state, due, item_id),
            )
            db.execute(
                "INSERT INTO audit(item_id,event,at) VALUES(?,?,?)",
                (item_id, state, now),
            )

    def audit(self, item_id):
        with self._db() as db:
            return [row[0] for row in db.execute(
                "SELECT event FROM audit WHERE item_id=? ORDER BY id", (item_id,)
            )]
