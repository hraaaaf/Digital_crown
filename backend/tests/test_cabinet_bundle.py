import io
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService
from backend.services.cabinet_bundle import (
    CabinetBundleService,
    _encrypt_plaintext_sqlcipher,
    _export_sqlcipher_plaintext,
)
from backend.services.guided_restore import GuidedRestoreService
from backend.services.guided_restore_archive import _extract_encrypted_media

SECRET = "migration phrase strong enough 2026"


def _patch_appdata(monkeypatch, path: Path):
    path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: path))


def _make_db(path: Path, value: str = "portable", user_version: int = 37) -> Path:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
    conn.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, nom TEXT)")
    conn.execute("CREATE TABLE truth (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT INTO truth(value) VALUES (?)", (value,))
    conn.execute(f"PRAGMA user_version = {user_version}")
    conn.commit()
    conn.close()
    return path


def _read_truth(path: Path) -> tuple[str, int]:
    conn = sqlite3.connect(str(path))
    try:
        value = str(conn.execute("SELECT value FROM truth LIMIT 1").fetchone()[0])
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        return value, version
    finally:
        conn.close()


def test_portable_bundle_round_trip_to_existing_guided_restore(tmp_path, monkeypatch):
    appdata = tmp_path / "destination"
    _patch_appdata(monkeypatch, appdata)
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "11" * 32)
    monkeypatch.setenv("SECRET_KEY", "SOURCE_SECRET_MUST_NOT_TRAVEL_123456789")
    monkeypatch.setenv("CABINET_PORT", "8123")

    source_db = _make_db(tmp_path / "source.db", "after-migration", 41)
    source_media = tmp_path / "source-media"
    (source_media / "radios").mkdir(parents=True)
    (source_media / "radios" / "pano.jpg").write_bytes(b"pano-bytes")
    (source_media / "docs").mkdir()
    (source_media / "docs" / "note.pdf").write_bytes(b"pdf-bytes")

    bundle = tmp_path / "cabinet.dcbundle"
    created = CabinetBundleService.create_bundle(
        bundle,
        SECRET,
        database_path=source_db,
        media_root=source_media,
    )
    assert created["size_bytes"] > 0
    assert created["media_file_count"] == 2

    raw = bundle.read_bytes()
    assert b"SOURCE_SECRET_MUST_NOT_TRAVEL_123456789" not in raw
    assert ("11" * 32).encode() not in raw

    local_restore = tmp_path / "local-restore.zip"
    converted = CabinetBundleService.to_local_guided_restore_archive(
        bundle,
        SECRET,
        local_restore,
        active_engine=("sqlite", "pysqlite"),
    )
    assert converted["media_file_count"] == 2
    assert converted["config"]["portable_runtime_preferences"]["cabinet_port"] == 8123
    assert ".env" in converted["machine_bound_excluded"]
    assert "backup.key" in converted["machine_bound_excluded"]
    assert "license_vault.bin" in converted["machine_bound_excluded"]

    with zipfile.ZipFile(local_restore, "r") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["media"]["storage_format"] == "aesgcm-stream-v1"
        db_enc = tmp_path / "database.db.enc"
        db_enc.write_bytes(archive.read("database.db.enc"))
        decrypted = tmp_path / "database.db"
        decrypted.write_bytes(BackupService._get_or_create_key().decrypt(db_enc.read_bytes()))
        assert _read_truth(decrypted) == ("after-migration", 41)

        media_enc = tmp_path / "media.zip.enc"
        media_enc.write_bytes(archive.read("media.zip.enc"))
        restored_media = tmp_path / "restored-media"
        _extract_encrypted_media(media_enc, restored_media)
        assert (restored_media / "radios" / "pano.jpg").read_bytes() == b"pano-bytes"
        assert (restored_media / "docs" / "note.pdf").read_bytes() == b"pdf-bytes"

    preflight = GuidedRestoreService.preflight_file(
        local_restore,
        original_name="cabinet.dcbundle",
        active_engine=("sqlite", "pysqlite"),
        owner_employer_id=7,
    )
    assert preflight["compatible"] is True
    assert preflight["restore_database"] is True
    assert preflight["restore_media"] is True
    assert preflight["media_file_count"] == 2


def test_wrong_secret_and_tampering_fail_closed(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "22" * 32)
    source_db = _make_db(tmp_path / "source.db")
    empty_media = tmp_path / "media"
    empty_media.mkdir()
    bundle = tmp_path / "cabinet.dcbundle"
    CabinetBundleService.create_bundle(bundle, SECRET, database_path=source_db, media_root=empty_media)

    with pytest.raises(ValueError, match="incorrecte|altéré"):
        CabinetBundleService.to_local_guided_restore_archive(
            bundle,
            "definitely wrong migration phrase",
            tmp_path / "wrong.zip",
            active_engine=("sqlite", "pysqlite"),
        )

    tampered = tmp_path / "tampered.dcbundle"
    with zipfile.ZipFile(bundle, "r") as src, zipfile.ZipFile(tampered, "w", zipfile.ZIP_STORED) as dst:
        manifest = json.loads(src.read("manifest.json"))
        manifest["source"]["os"] = "tampered-os"
        dst.writestr("manifest.json", json.dumps(manifest, sort_keys=True, separators=(",", ":")))
        dst.writestr("payload.enc", src.read("payload.enc"))
    with pytest.raises(ValueError, match="incorrecte|altéré"):
        CabinetBundleService.to_local_guided_restore_archive(
            tampered,
            SECRET,
            tmp_path / "tampered.zip",
            active_engine=("sqlite", "pysqlite"),
        )


def test_outer_bundle_has_only_manifest_and_ciphertext(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "33" * 32)
    monkeypatch.setenv("SECRET_KEY", "TOP_SECRET_VALUE_NOT_EXPORTED_987654321")
    source_db = _make_db(tmp_path / "source.db")
    media = tmp_path / "media"
    media.mkdir()
    bundle = tmp_path / "cabinet.dcbundle"
    CabinetBundleService.create_bundle(bundle, SECRET, database_path=source_db, media_root=media)

    with zipfile.ZipFile(bundle, "r") as archive:
        assert set(archive.namelist()) == {"manifest.json", "payload.enc"}
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["format"] == "digital-crown-cabinet-bundle"
        assert manifest["version"] == 1
        assert manifest["kdf"]["name"] == "scrypt"
        assert manifest["kdf"]["n"] == 2**17
        assert manifest["cipher"]["name"] == "AES-256-GCM"
        assert manifest["machine_bound_excluded"] == [
            ".env", "backup.key", "license_vault.bin", "runtime locks", "logs", "caches"
        ]
    raw = bundle.read_bytes()
    assert b"TOP_SECRET_VALUE_NOT_EXPORTED_987654321" not in raw
    assert ("33" * 32).encode() not in raw


def test_streaming_media_archive_detects_tamper(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "44" * 32)
    source_db = _make_db(tmp_path / "source.db")
    media = tmp_path / "media"
    media.mkdir()
    (media / "large.bin").write_bytes(b"x" * (3 * 1024 * 1024 + 123))
    bundle = tmp_path / "cabinet.dcbundle"
    CabinetBundleService.create_bundle(bundle, SECRET, database_path=source_db, media_root=media)
    local_restore = tmp_path / "local.zip"
    CabinetBundleService.to_local_guided_restore_archive(
        bundle, SECRET, local_restore, active_engine=("sqlite", "pysqlite")
    )
    with zipfile.ZipFile(local_restore, "r") as archive:
        media_enc = tmp_path / "media.enc"
        media_enc.write_bytes(archive.read("media.zip.enc"))
    data = bytearray(media_enc.read_bytes())
    data[len(data) // 2] ^= 0x01
    media_enc.write_bytes(bytes(data))
    with pytest.raises(ValueError, match="AES-GCM invalide|incompatible"):
        _extract_encrypted_media(media_enc, tmp_path / "should-not-exist")
    assert not (tmp_path / "should-not-exist").exists()


def test_sqlcipher_portable_conversion_preserves_user_version(tmp_path):
    sqlcipher = pytest.importorskip("sqlcipher3.dbapi2")
    plain = _make_db(tmp_path / "plain.db", "cipher-value", 52)
    encrypted = tmp_path / "encrypted.db"
    key = "ab" * 32
    _encrypt_plaintext_sqlcipher(plain, encrypted, key)
    exported = tmp_path / "exported.db"
    _export_sqlcipher_plaintext(encrypted, exported, key)
    assert _read_truth(exported) == ("cipher-value", 52)
