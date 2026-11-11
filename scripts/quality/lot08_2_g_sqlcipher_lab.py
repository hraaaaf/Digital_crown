"""LOT08.2-G: three genuinely encrypted SQLCipher synthetic stores + cold recovery.

CI ONLY. Uses ephemeral random keys and wholly fabricated markers; never reads
a cabinet configuration, patient file, user profile or checked-in model asset.
Tests the SQLCipher *primitive*, not the installed Windows binary, clinical
schema, signed release, power outage, or cross-database transaction atomicity.
"""
from __future__ import annotations

from contextlib import closing
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import subprocess
import tempfile

FILES = ("auth-synthetic.db", "devices-synthetic.db", "queue-synthetic.db")
MARKER = "LOT08G_FAKE_ONLY_NO_PATIENT"
MASTER = "bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4"


class Refuse(RuntimeError):
    pass


def require_ci() -> str:
    if os.getenv("GITHUB_ACTIONS") != "true" or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
        raise Refuse("GITHUB_EPHEMERAL_ISOLATED_ONLY")
    head = os.getenv("LOT08G_SOURCE_SHA", "")
    if re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise Refuse("SOURCE_SHA_REQUIRED")
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if actual != head:
        raise Refuse("SOURCE_HEAD_MISMATCH")
    return head


def open_cipher(path: Path, key: str):
    from sqlcipher3 import dbapi2 as cipher

    if not re.fullmatch(r"[0-9a-f]{64}", key):
        raise Refuse("FAKE_KEY_INVALID")
    db = cipher.connect(str(path), timeout=10)
    try:
        db.execute("PRAGMA key = \"x'%s'\"" % key)
        version = db.execute("PRAGMA cipher_version").fetchone()
        if not version or not version[0]:
            raise Refuse("REAL_SQLCIPHER_DRIVER_MISSING")
        return db
    except BaseException:
        db.close()
        raise


def epoch_and_integrity(path: Path, key: str) -> int:
    if path.is_symlink() or not path.is_file():
        raise Refuse("SYNTHETIC_FILE_MISSING")
    try:
        with closing(open_cipher(path, key)) as db:
            if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise Refuse("CIPHER_INTEGRITY_INVALID")
            row = db.execute("SELECT epoch, marker FROM lab_epoch WHERE id=1").fetchone()
    except sqlite3.DatabaseError as exc:
        raise Refuse("BAD_ENCRYPTED_SQLITE") from exc
    except Exception as exc:
        # sqlcipher3.DatabaseError may not inherit standard-library DatabaseError.
        if isinstance(exc, Refuse):
            raise
        raise Refuse("BAD_ENCRYPTED_SQLITE") from exc
    if not row or type(row[0]) is not int or row[0] < 0 or row[1] != MARKER:
        raise Refuse("NOT_SYNTHETIC_EPOCH")
    return row[0]


def verify_bundle(root: Path, key: str) -> int:
    root = Path(root)
    if not root.is_dir() or root.is_symlink() or {p.name for p in root.iterdir()} != {*FILES, "manifest.json"}:
        raise Refuse("BUNDLE_BOUNDS_INVALID")
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise Refuse("BUNDLE_MANIFEST_INVALID") from exc
    if (
        type(manifest) is not dict
        or set(manifest) != {"scope", "epoch", "digests"}
        or manifest["scope"] != MARKER
        or type(manifest["epoch"]) is not int
        or type(manifest["digests"]) is not dict
        or set(manifest["digests"]) != set(FILES)
    ):
        raise Refuse("BUNDLE_MANIFEST_INVALID")
    epochs = []
    for name in FILES:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise Refuse("BUNDLE_FILE_INVALID")
        if sha256(path.read_bytes()).hexdigest() != manifest["digests"][name]:
            raise Refuse("ENCRYPTED_BACKUP_HASH_MISMATCH")
        epochs.append(epoch_and_integrity(path, key))
    if len(set(epochs)) != 1 or epochs[0] != manifest["epoch"]:
        raise Refuse("CROSS_STORE_EPOCH_DIVERGED")
    return epochs[0]


def cold_clone(origin: Path, destination: Path, key: str) -> int:
    """No writers exist in this disposable LAB: only copy CLOSED DB handles."""
    origin = Path(origin)
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise Refuse("RESTORE_OVERWRITE_FORBIDDEN")
    epochs = [epoch_and_integrity(origin / name, key) for name in FILES]
    if len(set(epochs)) != 1:
        raise Refuse("CROSS_STORE_EPOCH_DIVERGED")
    stage = Path(tempfile.mkdtemp(prefix=".lot08g-stage-", dir=destination.parent))
    try:
        digests = {}
        for name in FILES:
            shutil.copy2(origin / name, stage / name)
            digests[name] = sha256((stage / name).read_bytes()).hexdigest()
        (stage / "manifest.json").write_text(json.dumps({
            "scope": MARKER, "epoch": epochs[0], "digests": digests,
        }, sort_keys=True), encoding="utf-8")
        if verify_bundle(stage, key) != epochs[0]:
            raise Refuse("COLD_CLONE_INCONSISTENT")
        if destination.exists() or destination.is_symlink():
            raise Refuse("RESTORE_OVERWRITE_FORBIDDEN")
        stage.rename(destination)
        return epochs[0]
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main() -> None:
    head = require_ci()
    with tempfile.TemporaryDirectory(prefix="lot08g-ci-sqlcipher-only-") as folder:
        root = Path(folder)
        source = root / "source"
        source.mkdir()
        key = secrets.token_hex(32)
        for name in FILES:
            path = source / name
            with closing(open_cipher(path, key)) as db:
                db.execute("CREATE TABLE lab_epoch(id INTEGER PRIMARY KEY, epoch INTEGER NOT NULL, marker TEXT NOT NULL)")
                db.execute("INSERT INTO lab_epoch VALUES(1,0,?)", (MARKER,))
                db.commit()
            # Plain SQLite must NOT successfully query an encrypted file.
            if path.read_bytes()[:16] == b"SQLite format 3\x00":
                raise Refuse("SQLCIPHER_PLAINTEXT_HEADER")
            with closing(sqlite3.connect(path)) as plain:
                try:
                    plain.execute("SELECT epoch FROM lab_epoch").fetchone()
                except sqlite3.DatabaseError:
                    pass
                else:
                    raise Refuse("SQLCIPHER_PLAINTEXT_READABLE")
            try:
                epoch_and_integrity(path, secrets.token_hex(32))
            except Refuse as exc:
                if str(exc) != "BAD_ENCRYPTED_SQLITE":
                    raise
            else:
                raise Refuse("WRONG_KEY_ACCEPTED")
        destination = root / "clone"
        if cold_clone(source, destination, key) != 0 or verify_bundle(destination, key) != 0:
            raise Refuse("COLD_SQLCIPHER_RESTORE_FAILED")
        try:
            cold_clone(source, destination, key)
        except Refuse as exc:
            if str(exc) != "RESTORE_OVERWRITE_FORBIDDEN":
                raise
        else:
            raise Refuse("UNSAFE_OVERWRITE_ACCEPTED")
        # A single store advanced out of sync must block an apparently healthy backup.
        with closing(open_cipher(source / FILES[0], key)) as db:
            db.execute("UPDATE lab_epoch SET epoch=7 WHERE id=1")
            db.commit()
        try:
            cold_clone(source, root / "reject-diverged", key)
        except Refuse as exc:
            if str(exc) != "CROSS_STORE_EPOCH_DIVERGED":
                raise
        else:
            raise Refuse("DIVERGED_STORES_ACCEPTED")
        if (root / "reject-diverged").exists():
            raise Refuse("REJECTED_RESTORE_LEFT_FILES")
        # Corrupted encrypted bytes are rejected by the digest before decrypt.
        corrupt = destination / FILES[0]
        with corrupt.open("ab") as writer:
            writer.write(b"TAMPERED")
        try:
            verify_bundle(destination, key)
        except Refuse as exc:
            if str(exc) != "ENCRYPTED_BACKUP_HASH_MISMATCH":
                raise
        else:
            raise Refuse("ENCRYPTED_BACKUP_TAMPER_ACCEPTED")
    print(json.dumps({
        "lot": "08.2-G", "source_sha": head,
        "genuine_sqlcipher_version_checked": True,
        "three_synthetic_files_encrypted": True,
        "wrong_key_and_plaintext_refused": True,
        "cold_copy_verified": True,
        "overwrite_diverged_epoch_tamper_refused": True,
        "actual_installer_run": False,
        "actual_clinical_sqlcipher_restore": False,
        "release_installable_certified": False,
        "clinical_go": False,
    }, sort_keys=True))
    print("LOT08G_REAL_SQLCIPHER_THREE_DB_COLD_RESTORE_LAB_PASS")


if __name__ == "__main__":
    main()
