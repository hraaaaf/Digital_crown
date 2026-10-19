"""LOT05.7-J phase 2: REAL SQLCipher WAL copy laboratory, never clinical apply.

This helper is not imported by any runtime route or worker. A temporary lab
root is mandatory. The only replace operation targets CURRENT.json inside
the synthetic root, never clinical_vault.db, media, or licence files.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import uuid

_FLAG = "LOT05J2_NATIVE_SQLCIPHER_FAKE_ONLY"
_FILES = ("snapshot.db", "vault-fake.bin", "media-fake/a.fake", "media-fake/b.fake")
_NAME = re.compile(r"g_[a-f0-9]{32}\Z")
_KEY = re.compile(r"[a-f0-9]{64}\Z")


class J2Denied(PermissionError):
    """Sanitized fail-closed diagnostic; never expose patient values."""


def _guard(root: Path, owner: object, key: object) -> None:
    if os.environ.get(_FLAG) != "1":
        raise J2Denied("LAB_DISABLED")
    if (not isinstance(root, Path) or not root.is_absolute()
            or not root.name.startswith("lot05j2_fake_")
            or not root.is_dir() or root.is_symlink()):
        raise J2Denied("FAKE_ROOT_REQUIRED")
    if type(owner) is not int or owner <= 0:
        raise J2Denied("EXPLICIT_FAKE_OWNER_REQUIRED")
    if type(key) is not str or not _KEY.fullmatch(key):
        raise J2Denied("EPHEMERAL_FAKE_KEY_REQUIRED")


def _regular(path: Path, parent: Path) -> None:
    if (path.is_symlink() or parent.is_symlink() or not path.is_file()
            or not stat.S_ISREG(path.stat().st_mode)
            or path.resolve(strict=True).parent != parent.resolve(strict=True)):
        raise J2Denied("FAKE_COMPONENT_REDIRECTED")


def _hash(path: Path) -> dict:
    size = 0
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            size += len(block)
            if size > 128 * 1024 * 1024:
                raise J2Denied("FAKE_COMPONENT_TOO_LARGE")
            digest.update(block)
    if size <= 0:
        raise J2Denied("FAKE_COMPONENT_EMPTY")
    return {"size": size, "sha256": digest.hexdigest()}


def _files(directory: Path) -> dict:
    all_paths = set()
    for entry in directory.rglob("*"):
        if entry.is_symlink():
            raise J2Denied("SYMLINK_IN_BUNDLE")
        if entry.is_file():
            all_paths.add(entry.relative_to(directory).as_posix())
        elif not entry.is_dir():
            raise J2Denied("UNEXPECTED_COMPONENT")
    if all_paths != set(_FILES):
        raise J2Denied("FAKE_COMPONENT_SET_INVALID")
    result = {}
    for name in _FILES:
        p = directory / name
        _regular(p, p.parent)
        result[name] = _hash(p)
    return result


def _sqlcipher_conn(path: Path, key: str):
    from sqlcipher3 import dbapi2
    db = dbapi2.connect(str(path))
    try:
        # Matches the REAL SQLCipher fake fixture used in LOT05.7-E/I.
        db.execute("PRAGMA key = '" + key + "'")
        if not db.execute("PRAGMA cipher_version").fetchone()[0]:
            raise J2Denied("NATIVE_SQLCIPHER_REQUIRED")
        return db
    except BaseException:
        db.close()
        raise


def _validate_snapshot(path: Path, key: str) -> None:
    try:
        with closing(_sqlcipher_conn(path, key)) as db:
            if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise J2Denied("SQLCIPHER_INTEGRITY_INVALID")
            # Required entirely synthetic test table, not clinical schema.
            if db.execute("SELECT count(*) FROM fake_truth").fetchone()[0] != 1:
                raise J2Denied("FAKE_ROW_COUNT_INVALID")
    except J2Denied:
        raise
    except Exception as exc:
        raise J2Denied("SQLCIPHER_SNAPSHOT_UNREADABLE") from exc


def _check_generation(directory: Path, manifest: dict, key: str) -> None:
    if type(manifest) is not dict or set(manifest) != set(_FILES):
        raise J2Denied("MANIFEST_INVALID")
    if _files(directory) != manifest:
        raise J2Denied("FAKE_GENERATION_CORRUPTED")
    snapshot = directory / "snapshot.db"
    if snapshot.read_bytes()[:16] == b"SQLite format 3\x00":
        raise J2Denied("UNENCRYPTED_SNAPSHOT")
    _validate_snapshot(snapshot, key)


def fake_current(root: Path, *, owner: object, key: object):
    _guard(root, owner, key)
    base = root.resolve(strict=True)
    pointer = root / "CURRENT.json"
    _regular(pointer, root)
    try:
        record = json.loads(pointer.read_text(encoding="utf-8"))
        if (set(record) != {"version", "fake_owner", "generation", "manifest"}
                or record["version"] != 1 or record["fake_owner"] != owner
                or type(record["generation"]) is not str
                or not _NAME.fullmatch(record["generation"])):
            raise J2Denied("POINTER_INVALID")
        versions = root / "versions"
        if versions.is_symlink() or versions.resolve(strict=True).parent != base:
            raise J2Denied("VERSIONS_REDIRECTED")
        directory = versions / record["generation"]
        if (directory.is_symlink() or not directory.is_dir()
                or directory.resolve(strict=True).parent != versions.resolve(strict=True)):
            raise J2Denied("GENERATION_REDIRECTED")
        _check_generation(directory, record["manifest"], key)
        return directory, record
    except J2Denied:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise J2Denied("GENERATION_UNVERIFIABLE") from exc


def fake_publish(root: Path, source, *, owner: object, expected_owner: object,
                 key: object, fail_at: str | None = None) -> dict:
    _guard(root, owner, key)
    # Comparing two caller-supplied FAKE identities is only a laboratory
    # exercise. A real authenticated/SCM principal MUST be proved separately.
    if (type(expected_owner) is not int or expected_owner <= 0
            or owner != expected_owner):
        raise J2Denied("FAKE_OWNER_MISMATCH")
    from sqlcipher3 import dbapi2
    if not isinstance(source, dbapi2.Connection):
        raise J2Denied("REAL_SQLCIPHER_SOURCE_REQUIRED")
    input_dir = root / "inputs"
    base = root.resolve(strict=True)
    if (input_dir.is_symlink() or not input_dir.is_dir()
            or input_dir.resolve(strict=True).parent != base):
        raise J2Denied("FAKE_INPUT_DIR_REQUIRED")
    source_db = input_dir / "source.db"
    _regular(source_db, input_dir)
    try:
        source_files = source.execute("PRAGMA database_list").fetchall()
        if (len(source_files) != 1 or
                Path(source_files[0][2]).resolve(strict=True) != source_db.resolve(strict=True)):
            raise J2Denied("SQLCIPHER_SOURCE_PATH_MISMATCH")
        if source.execute("SELECT count(*) FROM fake_truth").fetchone()[0] != 1:
            raise J2Denied("FAKE_ROW_COUNT_INVALID")
    except J2Denied:
        raise
    except Exception as exc:
        raise J2Denied("SOURCE_UNVERIFIABLE") from exc

    versions = root / "versions"
    versions.mkdir(exist_ok=True)
    if versions.is_symlink() or versions.resolve(strict=True).parent != base:
        raise J2Denied("VERSIONS_REDIRECTED")
    token = uuid.uuid4().hex
    stage = versions / (".stage-" + token)
    final = versions / ("g_" + token)
    stage.mkdir(mode=0o700)
    (stage / "media-fake").mkdir()
    try:
        snapshot = stage / "snapshot.db"
        with closing(_sqlcipher_conn(snapshot, key)) as dest:
            source.backup(dest)
            mode = dest.execute("PRAGMA journal_mode=DELETE").fetchone()
            if not mode or str(mode[0]).lower() != "delete":
                raise J2Denied("SQLCIPHER_STAGED_WAL_NOT_CLOSED")
            dest.commit()
        # Force physical SQLCipher snapshot validation before copying assets.
        _validate_snapshot(snapshot, key)
        with snapshot.open("r+b") as handle:
            os.fsync(handle.fileno())
        if fail_at == "after_snapshot":
            raise J2Denied("INJECTED_AFTER_SNAPSHOT")
        for name in _FILES[1:]:
            src = input_dir / name
            if (src.parent.is_symlink()
                    or not src.resolve(strict=True).is_relative_to(input_dir.resolve(strict=True))):
                raise J2Denied("ASSET_REDIRECTED")
            _regular(src, src.parent)
            before = _hash(src)
            destination = stage / name
            shutil.copyfile(src, destination)
            if _hash(src) != before or _hash(destination) != before:
                raise J2Denied("ASSET_CHANGED_DURING_COPY")
            with destination.open("r+b") as handle:
                os.fsync(handle.fileno())
        if fail_at == "after_assets":
            raise J2Denied("INJECTED_AFTER_ASSETS")
        manifest = _files(stage)
        _check_generation(stage, manifest, key)
        if fail_at == "before_rename":
            raise J2Denied("INJECTED_BEFORE_RENAME")
        os.rename(stage, final)  # new, unique FAKE directory only
        record = {"version": 1, "fake_owner": owner,
                  "generation": final.name, "manifest": manifest}
        if fail_at == "after_rename":
            raise J2Denied("INJECTED_AFTER_RENAME")
        pointer = root / "CURRENT.json"
        if pointer.exists():
            fake_current(root, owner=owner, key=key)
        if pointer.is_symlink():
            raise J2Denied("POINTER_REDIRECTED")
        temp = root / (".current-" + token + ".tmp")
        try:
            with temp.open("xb") as handle:
                handle.write(json.dumps(record, sort_keys=True).encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, pointer)  # FAKE pointer only; no clinical assets
        finally:
            temp.unlink(missing_ok=True)
        return record
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def fake_clone(root: Path, destination: Path, *, owner: object, key: object):
    _guard(root, owner, key)
    if (not isinstance(destination, Path) or destination.parent != root
            or destination.name != "offline-recovery" or destination.exists()):
        raise J2Denied("ISOLATED_CLONE_REQUIRED")
    source, record = fake_current(root, owner=owner, key=key)
    try:
        shutil.copytree(source, destination)
        _check_generation(destination, record["manifest"], key)
    except Exception:
        if destination.exists():
            shutil.rmtree(destination)
        raise
    return destination


def inspect_windows_boundary():
    """Real runner observation only; never a proof of SCM or authority."""
    if os.name != "nt":
        return {"os": os.name, "whoami_observed": False,
                "scm_service_attested": False, "clinical_apply_allowed": False}
    principal = subprocess.run(["whoami.exe", "/user"], capture_output=True,
                               text=True, timeout=15)
    scm = subprocess.run(["sc.exe", "query", "DigitalCrown_J2_NONEXISTENT_FAKE"],
                         capture_output=True, text=True, timeout=15)
    if principal.returncode != 0:
        raise J2Denied("WINDOWS_TOKEN_INSPECTION_UNAVAILABLE")
    # The synthetic service is deliberately NOT installed on GitHub runners.
    if scm.returncode == 0:
        raise J2Denied("UNEXPECTED_FAKE_SERVICE")
    return {"os": "nt", "whoami_observed": True, "scm_service_attested": False,
            "clinical_apply_allowed": False}


def require_real_windows_worker_attestation(*_args, **_kwargs):
    """No SCM Service SID + DACL evidence is wired to production. DENY all."""
    raise J2Denied("SCM_SERVICE_SID_NOT_ATTESTED")
