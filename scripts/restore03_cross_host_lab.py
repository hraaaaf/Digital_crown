#!/usr/bin/env python3
"""RESTORE-03 cross-host synthetic portability LAB (not a real cabinet restore).

Source and target run in independent processes on different hosts. Only an
encrypted .dcbundle and non-sensitive evidence JSON cross the host boundary.
No real patient data, clinic credentials or machine-bound secrets are used.
Does not test packaged GuidedRestore apply, smoke, rollback, NAS or SMB.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import secrets
import sqlite3
import sys
import types
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "RESTORE03_SYNTHETIC_ONLY_NO_PHYSICAL_DR_GO"
SECRET_ENV = "RESTORE03_TEST_MIGRATION_SECRET"
BUNDLE_NAME = "restore03-SYNTHETIC.dcbundle"
SOURCE_RECORD = "restore03-source-evidence.json"


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def machine_pseudonym() -> str:
    # Never expose a machine hostname or MAC in test evidence.
    material = f"{platform.node()}|{uuid.getnode()}|{platform.system()}".encode()
    return digest_bytes(material)


def new_dir(path: Path) -> Path:
    if path.exists() or path.is_symlink():
        raise RuntimeError("LAB_DIRECTORY_MUST_BE_NEW")
    if not path.is_absolute() or not path.parent.is_dir() or path.parent.is_symlink():
        raise RuntimeError("LAB_DIRECTORY_INVALID_PARENT")
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    return path


def test_secret() -> str:
    value = os.environ.get(SECRET_ENV, "")
    if len(value.strip().encode("utf-8")) < 16:
        raise RuntimeError("TEST_MIGRATION_SECRET_REQUIRED")
    if any(os.getenv(name) for name in ("DATABASE_URL", "SQLCIPHER_KEY_HEX")):
        raise RuntimeError("CLINIC_DATABASE_ENV_NOT_ALLOWED")
    return value


def load_slice():
    # Exact lightweight import boundary from scripts/portability_p3_check.py.
    def package(name: str, path: Path):
        mod = types.ModuleType(name)
        mod.__path__ = [str(path)]
        mod.__package__ = name
        sys.modules[name] = mod
        if "." in name:
            parent, child = name.rsplit(".", 1)
            setattr(sys.modules[parent], child, mod)

    def load(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError("MODULE_UNAVAILABLE")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        if "." in name:
            parent, child = name.rsplit(".", 1)
            setattr(sys.modules[parent], child, mod)
        spec.loader.exec_module(mod)
        return mod

    package("backend", ROOT / "backend")
    package("backend.core", ROOT / "backend" / "core")
    package("backend.services", ROOT / "backend" / "services")
    load("backend.core.platform", ROOT / "backend" / "core" / "platform.py")
    load("backend.core.paths", ROOT / "backend" / "core" / "paths.py")
    load("backend.core.media_paths", ROOT / "backend" / "core" / "media_paths.py")
    backup = load("backend.services.backup_service", ROOT / "backend" / "services" / "backup_service.py")
    archive = load("backend.services.guided_restore_archive", ROOT / "backend" / "services" / "guided_restore_archive.py")
    bundle = load("backend.services.cabinet_bundle", ROOT / "backend" / "services" / "cabinet_bundle.py")
    return backup.BackupService, archive, bundle.CabinetBundleService


def setup_synthetic_environment(work: Path):
    if any(os.environ.get(key) for key in ("CABINET_MASTER_KEY_HEX", "DIGITALCROWN_USER_DATA_DIR")):
        raise RuntimeError("CLINIC_KEY_OR_APPDATA_ENV_NOT_ALLOWED")
    os.environ["DIGITALCROWN_USER_DATA_DIR"] = str(work / "lab-appdata")
    os.environ["CABINET_MASTER_KEY_HEX"] = secrets.token_hex(32)
    os.environ["CABINET_PORT"] = "8005"


def create_db(path: Path, marker: str):
    with sqlite3.connect(str(path)) as conn:
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
        conn.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, nom TEXT)")
        conn.execute("CREATE TABLE truth (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO truth VALUES (1, ?)", (marker,))
        conn.execute("PRAGMA user_version = 63")
        conn.commit()


def read_db_marker(path: Path) -> tuple[str, int]:
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        return (
            conn.execute("SELECT value FROM truth WHERE id=1").fetchone()[0],
            int(conn.execute("PRAGMA user_version").fetchone()[0]),
        )


def source(out: Path):
    secret = test_secret()
    new_dir(out)
    work = new_dir(out / "lab-private")
    setup_synthetic_environment(work)
    _, _, service = load_slice()
    token = "RESTORE03_SYNTHETIC_" + secrets.token_hex(6)
    db = work / "synthetic.db"
    create_db(db, token)
    media = new_dir(work / "media")
    (media / "radios").mkdir()
    (media / "documents").mkdir()
    payloads = {
        "radios/SYNTHETIC.txt": b"SYNTHETIC_RADIO_NOT_CLINICAL",
        "documents/SYNTHETIC.txt": b"SYNTHETIC_DOCUMENT_NOT_CLINICAL",
    }
    for name, data in payloads.items():
        (media / name).write_bytes(data)
    bundle = out / BUNDLE_NAME
    result = service.create_bundle(bundle, secret, database_path=db, media_root=media)
    evidence = {
        "marker": MARKER,
        "source_machine_hash": machine_pseudonym(),
        "source_os": platform.system(),
        "runner": "github_actions" if os.getenv("GITHUB_ACTIONS") == "true" else "unattested",
        "bundle_name": BUNDLE_NAME,
        "bundle_sha256": sha256_file(bundle),
        "fixture_token": token,
        "db_user_version": 63,
        "media_sha256": {name: digest_bytes(data) for name, data in payloads.items()},
        "physical_second_pc": "NOT_RUN",
        "guided_restore_apply": "NOT_RUN",
        "nas_smb": "NOT_RUN",
    }
    assert evidence["bundle_sha256"] == result["sha256"]
    (out / SOURCE_RECORD).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    import shutil
    shutil.rmtree(work)
    assert {f.name for f in out.iterdir()} == {BUNDLE_NAME, SOURCE_RECORD}
    print(MARKER + " SOURCE_BUNDLE_CREATED_SHA256=" + evidence["bundle_sha256"])


def target(input_dir: Path, out: Path, require_windows: bool):
    secret = test_secret()
    if require_windows and platform.system() != "Windows":
        raise RuntimeError("TARGET_NOT_WINDOWS")
    evidence_file, bundle = input_dir / SOURCE_RECORD, input_dir / BUNDLE_NAME
    assert evidence_file.is_file() and bundle.is_file(), "TRANSFER_INCOMPLETE"
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert evidence.get("marker") == MARKER, "SOURCE_NOT_SYNTHETIC"
    assert evidence.get("source_machine_hash") != machine_pseudonym(), "HOST_NOT_DISTINCT"
    assert evidence.get("bundle_sha256") == sha256_file(bundle), "TRANSFER_HASH_MISMATCH"
    new_dir(out)
    setup_synthetic_environment(out)
    backup, archive, service = load_slice()
    restore = out / "local-guided-restore-SYNTHETIC.zip"
    service.to_local_guided_restore_archive(bundle, secret, restore, active_engine=("sqlite", "pysqlite"))
    with zipfile.ZipFile(restore, "r") as local:
        manifest = json.loads(local.read("manifest.json"))
        assert manifest["format"] == "digital-crown-guided-restore"
        assert manifest["media"]["included"] is True
        enc_db = local.read("database.db.enc")
        assert digest_bytes(enc_db) == manifest["database"]["sha256"]
        plain_db = out / "verified-synthetic.db"
        plain_db.write_bytes(backup._get_or_create_key().decrypt(enc_db))
        observed = read_db_marker(plain_db)
        assert observed == (evidence["fixture_token"], evidence["db_user_version"])
        enc_media = out / "encrypted-media-SYNTHETIC.bin"
        enc_media.write_bytes(local.read("media.zip.enc"))
        assert sha256_file(enc_media) == manifest["media"]["sha256"]
    extracted = out / "extracted-SYNTHETIC"
    archive._extract_encrypted_media(enc_media, extracted)
    for name, expected in evidence["media_sha256"].items():
        assert sha256_file(extracted / name) == expected, "MEDIA_HASH_MISMATCH"
    wrong = out / "wrong-secret-must-not-exist.zip"
    try:
        service.to_local_guided_restore_archive(bundle, secret + "-WRONG", wrong, active_engine=("sqlite", "pysqlite"))
    except ValueError:
        assert not wrong.exists(), "WRONG_SECRET_CREATED_RESTORE"
    else:
        raise AssertionError("WRONG_SECRET_ACCEPTED")
    output = {
        "marker": MARKER,
        "target_os": platform.system(),
        "target_machine_hash": machine_pseudonym(),
        "hosts_distinct": True,
        "transfer_hash_ok": True,
        "guided_restore_archive_conversion": True,
        "sqlite_integrity_check": "ok",
        "database_oracle": "PASS",
        "media_oracle": "PASS",
        "wrong_secret": "REFUSED",
        "physical_second_pc": "NOT_ATTESTED",
        "packaged_guided_restore_apply": "NOT_RUN",
        "nas_smb": "NOT_RUN",
    }
    # Only non-sensitive proof remains; test keys and plaintext are destroyed.
    import shutil
    for path in (restore, plain_db, enc_media):
        path.unlink(missing_ok=True)
    shutil.rmtree(extracted)
    shutil.rmtree(out / "lab-appdata", ignore_errors=True)
    (out / "restore03-target-evidence.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    assert {f.name for f in out.iterdir()} == {"restore03-target-evidence.json"}
    print(MARKER + " TARGET_CONVERSION_ORACLES_PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="phase", required=True)
    a = subs.add_parser("source")
    a.add_argument("--output", type=Path, required=True)
    b = subs.add_parser("target")
    b.add_argument("--input", type=Path, required=True)
    b.add_argument("--output", type=Path, required=True)
    b.add_argument("--require-windows", action="store_true")
    args = parser.parse_args()
    try:
        if args.phase == "source":
            source(args.output)
        else:
            target(args.input, args.output, args.require_windows)
    except Exception as exc:
        print("RESTORE03_LAB_FAIL:" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
