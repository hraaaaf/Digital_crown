import hashlib
import io
import json
import sqlite3
import sys
import zipfile
from pathlib import Path

import pytest

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService
import backend.services.guided_restore_archive as archive_mod
import backend.services.guided_restore_worker as worker_mod
from backend.services.guided_restore import GuidedRestoreService
from backend.services.guided_restore_worker import GuidedRestoreWorker


def _patch_appdata(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: tmp_path))


def _make_sqlite_backup(tmp_path: Path) -> Path:
    plain = tmp_path / "source.db"
    conn = sqlite3.connect(str(plain))
    conn.execute("CREATE TABLE truth (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT INTO truth(value) VALUES ('restored')")
    conn.commit()
    conn.close()
    encrypted = tmp_path / "source.db.enc"
    encrypted.write_bytes(BackupService._get_or_create_key().encrypt(plain.read_bytes()))
    return encrypted


def _media_enc(monkeypatch, files: dict[str, bytes]) -> bytes:
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "11" * 32)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return archive_mod._master_cipher().encrypt(buffer.getvalue())


def test_preflight_legacy_db_is_read_only_and_preserves_media(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    active = tmp_path / "active.db"
    active.write_bytes(b"ACTIVE-UNCHANGED")
    encrypted = _make_sqlite_backup(tmp_path)

    result = GuidedRestoreService.preflight_file(
        encrypted,
        original_name="cabinet.db.enc",
        active_engine=("sqlite", "pysqlite"),
    )

    assert result["compatible"] is True
    assert result["restore_database"] is True
    assert result["restore_media"] is False
    assert result["preserved"] == ["Médias actuels"]
    assert active.read_bytes() == b"ACTIVE-UNCHANGED"


def test_preflight_rejects_tampered_encrypted_db(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    encrypted = _make_sqlite_backup(tmp_path)
    data = bytearray(encrypted.read_bytes())
    data[-5] ^= 0xFF
    encrypted.write_bytes(bytes(data))

    with pytest.raises(ValueError, match="invalide|incompatible"):
        GuidedRestoreService.preflight_file(
            encrypted,
            original_name="tampered.db.enc",
            active_engine=("sqlite", "pysqlite"),
        )


def test_manifest_archive_restores_db_and_media_contract(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    encrypted_db = _make_sqlite_backup(tmp_path)
    media_bytes = _media_enc(monkeypatch, {"radios/pano.jpg": b"image", "docs/note.pdf": b"pdf"})
    db_bytes = encrypted_db.read_bytes()
    manifest = {
        "format": "digital-crown-guided-restore",
        "version": 1,
        "created_at": "2026-08-21T22:00:00Z",
        "database": {
            "filename": "database.db.enc",
            "sha256": hashlib.sha256(db_bytes).hexdigest(),
            "encryption": "backup_key",
            "engine": "sqlite",
        },
        "media": {
            "included": True,
            "filename": "media.zip.enc",
            "sha256": hashlib.sha256(media_bytes).hexdigest(),
            "encryption": "master_key",
        },
    }
    bundle = tmp_path / "complete.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("database.db.enc", db_bytes)
        archive.writestr("media.zip.enc", media_bytes)

    result = GuidedRestoreService.preflight_file(
        bundle,
        original_name="complete.zip",
        active_engine=("sqlite", "pysqlite"),
    )

    assert result["compatible"] is True
    assert result["restore_media"] is True
    assert result["media_file_count"] == 2
    assert result["backup_created_at"] == "2026-08-21T22:00:00Z"


def test_outer_archive_path_traversal_is_blocked(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    bundle = tmp_path / "evil.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("../manifest.json", "{}")

    with pytest.raises(ValueError, match="chemin interne non sûr"):
        GuidedRestoreService.preflight_file(
            bundle,
            original_name="evil.zip",
            active_engine=("sqlite", "pysqlite"),
        )


def test_manifest_checksum_mismatch_is_blocked(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    encrypted_db = _make_sqlite_backup(tmp_path).read_bytes()
    manifest = {
        "format": "digital-crown-guided-restore",
        "version": 1,
        "database": {
            "filename": "database.db.enc",
            "sha256": "0" * 64,
            "encryption": "backup_key",
            "engine": "sqlite",
        },
        "media": {"included": False},
    }
    bundle = tmp_path / "bad-checksum.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("database.db.enc", encrypted_db)

    with pytest.raises(ValueError, match="Checksum base de données invalide"):
        GuidedRestoreService.preflight_file(
            bundle,
            original_name="bad-checksum.zip",
            active_engine=("sqlite", "pysqlite"),
        )


def test_inner_media_path_traversal_is_blocked(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    encrypted = tmp_path / "media.enc"
    encrypted.write_bytes(_media_enc(monkeypatch, {"../escape.txt": b"nope"}))

    with pytest.raises(ValueError, match="chemin interne non sûr"):
        archive_mod._inspect_encrypted_media(encrypted)


def test_confirmation_is_exact_and_runtime_is_fail_closed(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    job = {
        "restore_id": "a" * 32,
        "status": "preflight_ready",
        "compatible": True,
        "steps": [],
    }
    GuidedRestoreService._write_job(job)

    with pytest.raises(ValueError, match="RESTAURER"):
        GuidedRestoreService.request_apply(job["restore_id"], "restaurer")

    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert GuidedRestoreService.runtime_apply_supported() is False
    with pytest.raises(RuntimeError, match="exécutable cabinet"):
        GuidedRestoreService.request_apply(job["restore_id"], "RESTAURER")


def test_database_rescue_keeps_wal_and_rollback_removes_stale_shm(tmp_path):
    target = tmp_path / "clinical_vault.db"
    target.write_bytes(b"db-before")
    Path(str(target) + "-wal").write_bytes(b"wal-before")
    Path(str(target) + "-shm").write_bytes(b"shm-before")
    rescue = tmp_path / "rescue"

    rescued = GuidedRestoreWorker._rescue_database(target, rescue)
    assert rescued == ["clinical_vault.db", "clinical_vault.db-wal"]

    target.write_bytes(b"db-after")
    Path(str(target) + "-wal").write_bytes(b"wal-after")
    Path(str(target) + "-shm").write_bytes(b"shm-after")
    GuidedRestoreWorker._restore_database_from_rescue(target, rescue)

    assert target.read_bytes() == b"db-before"
    assert Path(str(target) + "-wal").read_bytes() == b"wal-before"
    assert not Path(str(target) + "-shm").exists()


def test_worker_smoke_failure_triggers_proven_rollback(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    _patch_appdata(monkeypatch, appdata)
    media = appdata / "media"
    media.mkdir(parents=True)
    target = appdata / "clinical_vault.db"
    target.write_bytes(b"before")

    restore_id = "b" * 32
    job = {
        "restore_id": restore_id,
        "status": "scheduled",
        "compatible": True,
        "active_driver": "pysqlite",
        "target_db_path": str(target),
        "restore_media": False,
        "steps": [],
    }
    directory = GuidedRestoreService.job_dir(restore_id)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "database.enc").write_bytes(b"placeholder")
    GuidedRestoreService._write_job(job)

    monkeypatch.setattr(worker_mod, "get_media_root", lambda: media)
    monkeypatch.setattr(GuidedRestoreWorker, "_wait_parent_exit", classmethod(lambda cls, pid, timeout=20: None))

    def fake_apply(source, destination, driver):
        destination.write_bytes(b"restored-but-bad")

    monkeypatch.setattr(GuidedRestoreWorker, "_apply_database", staticmethod(fake_apply))

    class DummyProcess:
        def poll(self):
            return 0

        def terminate(self):
            pass

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

    monkeypatch.setattr(GuidedRestoreWorker, "_launch_app", staticmethod(lambda executable: DummyProcess()))
    smoke_results = iter([False, True])
    monkeypatch.setattr(GuidedRestoreWorker, "_smoke_check", staticmethod(lambda timeout=60: next(smoke_results)))

    result = GuidedRestoreWorker.run(restore_id, parent_pid=999, executable="DigitalCrown.exe")
    final = GuidedRestoreService.get_job(restore_id)

    assert result == 2
    assert target.read_bytes() == b"before"
    assert final["status"] == "rolled_back"
    assert final["rollback"] == "passed"
    assert final["smoke_check"] == "failed"
