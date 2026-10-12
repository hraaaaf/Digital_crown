"""LOT06-A: encrypted, restartable, disabled-by-default hot-folder collector.

NO patient inference, server write or server acknowledgement is implemented.
The server-side authorization/idempotency gate is a separate integration step.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import re
import secrets
import sqlite3
import stat
import tempfile
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


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

    def __post_init__(self):
        if not ID.fullmatch(self.cabinet) or not ID.fullmatch(self.workstation):
            raise GatewayError("invalid cabinet/workstation")
        if self.category not in {"PHOTO", "RADIOGRAPH"}:
            raise GatewayError("explicit category required")
        if len(self.key) != 32:
            raise GatewayError("a 256-bit spool key is mandatory")
        if not 0 < self.max_bytes <= MAX_BYTES:
            raise GatewayError("invalid size limit")
        w, p = Path(self.watch).absolute(), Path(self.private).absolute()
        if w == p or w in p.parents or p in w.parents:
            raise GatewayError("watch and private paths must be disjoint")
        if (w.is_symlink() or not w.is_dir() or p.is_symlink() or
                w.resolve(strict=True) != w or p.resolve(strict=False) != p):
            raise GatewayError("unsafe watch/private root or symlink ancestor")
        p.mkdir(parents=True, exist_ok=True)


class HotFolder:
    def __init__(self, config: Config):
        self.config = config
        self._observed = {}
        self.private = Path(config.private).absolute()
        self.spool = self.private / "spool"
        if self.spool.is_symlink():
            raise GatewayError("spool symlink rejected")
        self.spool.mkdir(mode=0o700, exist_ok=True)
        if os.name != "nt":
            os.chmod(self.private, 0o700)
            os.chmod(self.spool, 0o700)
        self.db_file = self.private / "acquisitions.sqlite3"
        if self.db_file.is_symlink():
            raise GatewayError("database symlink rejected")
        with self._db() as db:
            db.executescript("""
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
            );
            CREATE TABLE IF NOT EXISTS audit(
                id INTEGER PRIMARY KEY,
                item_id INTEGER NOT NULL,
                event TEXT NOT NULL,
                at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS device_scope(
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                cabinet TEXT NOT NULL,
                workstation TEXT NOT NULL
            );
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

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.db_file, timeout=10)
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _identity(self, digest, source_filename, modified_ns):
        # Opaque per-capture metadata: never persist/display the source filename.
        source_hash = hashlib.sha256(
            source_filename.encode("utf-8", "surrogatepass")
        ).hexdigest()
        parts = [self.config.cabinet, self.config.workstation,
                 self.config.category, digest, source_hash, modified_ns]
        return hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()

    def _aad(self, identity):
        return ("DC06A|" + self.config.cabinet + "|" +
                self.config.workstation + "|" + identity).encode()

    def _read(self, path, initial):
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            signature = lambda st: (st.st_size, st.st_mtime_ns, st.st_ctime_ns)
            if not stat.S_ISREG(opened.st_mode) or signature(opened) != initial:
                raise GatewayError("source changed")
            with os.fdopen(fd, "rb", closefd=False) as src:
                data = src.read(self.config.max_bytes + 1)
            after = os.fstat(fd)
        finally:
            os.close(fd)
        final = path.lstat()
        if (signature(after) != initial or signature(final) != initial or
                not stat.S_ISREG(final.st_mode) or len(data) != initial[0]):
            raise GatewayError("source changed during read")
        return data

    def _decrypt(self, blob, identity, digest):
        target = self.spool / blob
        if target.is_symlink() or not target.is_file():
            raise GatewayError("spool missing or symlink")
        data = target.read_bytes()
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

    def scan_once(self):
        outcome = dict(staged=0, quarantine=0, duplicate=0, unstable=0, rejected=0)
        for path in sorted(Path(self.config.watch).iterdir()):
            if path.is_symlink() or path.name.startswith("."):
                outcome["rejected"] += 1
                continue
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= self.config.max_bytes:
                outcome["rejected"] += 1
                continue
            signature = (info.st_size, info.st_mtime_ns, info.st_ctime_ns)
            token = str(path)
            if self._observed.get(token) != signature:
                self._observed[token] = signature
                outcome["unstable"] += 1
                continue
            try:
                content = self._read(path, signature)
            except (GatewayError, OSError):
                self._observed.pop(token, None)
                outcome["unstable"] += 1
                continue
            digest = hashlib.sha256(content).hexdigest()
            identity = self._identity(digest, path.name, signature[1])
            mime = sniff(content)
            accepted = mime is not None and path.suffix.lower() in SUPPORTED[mime]
            state = "PENDING_CONFIRMATION" if accepted else "QUARANTINED"
            blob = identity + ".dc6"
            with self._db() as db:
                db.execute("BEGIN IMMEDIATE")
                previous = db.execute(
                    "SELECT blob,digest FROM items WHERE dedup_key=?", (identity,)
                ).fetchone()
                if previous:
                    self._decrypt(previous[0], identity, previous[1])
                    outcome["duplicate"] += 1
                    continue
                self._store(blob, identity, content, digest)
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
