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
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: tmp_path))


def _make_plain_sqlite(path: Path, value: str = "restored") -> Path:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
    conn.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, nom TEXT)")
    conn.execute("CREATE TABLE truth (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT INTO truth(value) VALUES (?)", (value,))
    conn.commit()
    conn.close()
    return path


def _read_truth(path: Path) -> str:
    conn = sqlite3.connect(str(path))
    try:
        return str(conn.execute("SELECT value FROM truth LIMIT 1").fetchone()[0])
    finally:
        conn.close()


def _make_sqlite_backup(tmp_path: Path, value: str = "restored", name: str = "source.db.enc") -> Path:
    plain = _make_plain_sqlite(tmp_path / f"{name}.plain.db", value)
    encrypted = tmp_path / name
    encrypted.write_bytes(BackupService._get_or_create_key().encrypt(plain.read_bytes()))
    return encrypted


def _install_fake_verified_safety_backup(monkeypatch, appdata: Path, source_enc: Path):
    backups = appdata / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    target = backups / "prepared-current.db.enc"
    target.write_bytes(source_enc.read_bytes())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    monkeypatch.setattr(
        BackupService,
        "backup_active_database",
        staticmethod(lambda: {
            "status": "SUCCESS",
            "backup_filename": target.name,
            "checksum": digest,
            "size_bytes": target.stat().st_size,
            "engine": "sqlite",
        }),
    )


def _media_enc(monkeypatch, files: dict[str, bytes]) -> bytes:
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "11" * 32)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return archive_mod._master_cipher().encrypt(buffer.getvalue())


def _manifest_bundle(tmp_path: Path, monkeypatch, *, db_value="restored", media=None) -> Path:
    encrypted_db = _make_sqlite_backup(tmp_path, db_value, "bundle.db.enc")
    db_bytes = encrypted_db.read_bytes()
    media = media or {}
    media_bytes = _media_enc(monkeypatch, media) if media else b""
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
            "included": bool(media),
            "filename": "media.zip.enc" if media else "",
            "sha256": hashlib.sha256(media_bytes).hexdigest() if media else "",
            "encryption": "master_key" if media else None,
        },
    }
    bundle = tmp_path / "complete.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("database.db.enc", db_bytes)
        if media:
            archive.writestr("media.zip.enc", media_bytes)
    return bundle


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


def test_preflight_rejects_non_digital_crown_sqlite(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    _patch_appdata(monkeypatch, appdata)
    plain = tmp_path / "foreign.db"
    conn = sqlite3.connect(str(plain))
    conn.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    encrypted = tmp_path / "foreign.db.enc"
    encrypted.write_bytes(BackupService._get_or_create_key().encrypt(plain.read_bytes()))

    with pytest.raises(ValueError, match="Schéma Digital Crown incompatible"):
        GuidedRestoreService.preflight_file(
            encrypted,
            original_name="foreign.db.enc",
            active_engine=("sqlite", "pysqlite"),
        )


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
    bundle = _manifest_bundle(
        tmp_path,
        monkeypatch,
        media={"radios/pano.jpg": b"image", "docs/note.pdf": b"pdf"},
    )

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


def test_media_archive_allows_realistic_file_counts(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    encrypted = tmp_path / "media-many.enc"
    encrypted.write_bytes(_media_enc(monkeypatch, {f"patient/{i}.jpg": b"x" for i in range(12)}))

    assert archive_mod._inspect_encrypted_media(encrypted) == 12


def test_outer_archive_rejects_duplicate_basenames(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    bundle = tmp_path / "ambiguous.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "format": "digital-crown-guided-restore",
            "version": 1,
            "database": {"filename": "database.db.enc", "engine": "sqlite"},
        }))
        archive.writestr("one/database.db.enc", b"one")
        archive.writestr("two/database.db.enc", b"two")

    with pytest.raises(ValueError, match="noms de fichiers ambigus"):
        GuidedRestoreService.preflight_file(
            bundle,
            original_name="ambiguous.zip",
            active_engine=("sqlite", "pysqlite"),
        )


def test_prepare_is_tenant_scoped_and_revalidates_package(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    _patch_appdata(monkeypatch, appdata)
    encrypted = _make_sqlite_backup(tmp_path, "candidate")
    preflight = GuidedRestoreService.preflight_file(
        encrypted,
        original_name="cabinet.db.enc",
        active_engine=("sqlite", "pysqlite"),
        owner_employer_id=7,
    )
    safety = _make_sqlite_backup(tmp_path, "current", "safety.db.enc")
    _install_fake_verified_safety_backup(monkeypatch, appdata, safety)

    with pytest.raises(PermissionError):
        GuidedRestoreService.prepare(preflight["restore_id"], owner_employer_id=8)

    job_dir = GuidedRestoreService.job_dir(preflight["restore_id"])
    source = job_dir / "source.upload"
    original = source.read_bytes()
    source.write_bytes(original + b"tamper")
    with pytest.raises(ValueError, match="modifié"):
        GuidedRestoreService.prepare(preflight["restore_id"], owner_employer_id=7)
    source.write_bytes(original)

    prepared = GuidedRestoreService.prepare(preflight["restore_id"], owner_employer_id=7)
    assert prepared["status"] == "prepared"
    assert prepared["prepared_at"]
    job = GuidedRestoreService.get_job(preflight["restore_id"])
    assert job["prepared_rescue_db_sha256"]


def test_confirmation_is_exact_runtime_fail_closed_and_preparation_required(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    _patch_appdata(monkeypatch, appdata)
    encrypted = _make_sqlite_backup(tmp_path)
    preflight = GuidedRestoreService.preflight_file(
        encrypted,
        original_name="cabinet.db.enc",
        active_engine=("sqlite", "pysqlite"),
        owner_employer_id=7,
    )

    with pytest.raises(ValueError, match="RESTAURER"):
        GuidedRestoreService.request_apply(preflight["restore_id"], "restaurer", owner_employer_id=7)
    with pytest.raises(ValueError, match="Préparation sécurisée"):
        GuidedRestoreService.request_apply(preflight["restore_id"], "RESTAURER", owner_employer_id=7)

    safety = _make_sqlite_backup(tmp_path, "current", "safety.db.enc")
    _install_fake_verified_safety_backup(monkeypatch, appdata, safety)
    GuidedRestoreService.prepare(preflight["restore_id"], owner_employer_id=7)

    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert GuidedRestoreService.runtime_apply_supported() is False
    with pytest.raises(RuntimeError, match="exécutable cabinet"):
        GuidedRestoreService.request_apply(preflight["restore_id"], "RESTAURER", owner_employer_id=7)


def test_request_apply_dispatches_only_prepared_owned_job(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    _patch_appdata(monkeypatch, appdata)
    encrypted = _make_sqlite_backup(tmp_path)
    preflight = GuidedRestoreService.preflight_file(
        encrypted,
        original_name="cabinet.db.enc",
        active_engine=("sqlite", "pysqlite"),
        owner_employer_id=7,
    )
    safety = _make_sqlite_backup(tmp_path, "current", "safety.db.enc")
    _install_fake_verified_safety_backup(monkeypatch, appdata, safety)
    GuidedRestoreService.prepare(preflight["restore_id"], owner_employer_id=7)

    monkeypatch.setattr(GuidedRestoreService, "runtime_apply_supported", staticmethod(lambda: True))
    calls = []
    monkeypatch.setattr(
        GuidedRestoreService,
        "_launch_detached_worker",
        staticmethod(lambda restore_id, parent_pid, executable: calls.append((restore_id, parent_pid, executable))),
    )
    monkeypatch.setattr(GuidedRestoreService, "_terminate_parent_after_response", staticmethod(lambda: None))

    with pytest.raises(PermissionError):
        GuidedRestoreService.request_apply(preflight["restore_id"], "RESTAURER", owner_employer_id=8)

    result = GuidedRestoreService.request_apply(preflight["restore_id"], "RESTAURER", owner_employer_id=7)
    assert result["status"] == "scheduled"
    assert calls and calls[0][0] == preflight["restore_id"]


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


def test_media_digest_change_blocks_bascule(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    media_root = tmp_path / "media"
    media_root.mkdir()
    (media_root / "before.txt").write_bytes(b"before")
    expected = archive_mod._directory_digest(media_root)
    (media_root / "before.txt").write_bytes(b"changed")
    source_enc = tmp_path / "media.enc"
    source_enc.write_bytes(_media_enc(monkeypatch, {"after.txt": b"after"}))

    with pytest.raises(RuntimeError, match="modifiés depuis la préparation"):
        GuidedRestoreWorker._apply_media(source_enc, media_root, tmp_path / "rescue-media", expected)
    assert (media_root / "before.txt").read_bytes() == b"changed"
    assert not (media_root / "after.txt").exists()


class DummyProcess:
    def poll(self):
        return 0

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 0

    def kill(self):
        pass


def test_worker_integration_restores_temp_db_and_media(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    _patch_appdata(monkeypatch, appdata)
    media = appdata / "media"
    media.mkdir(parents=True)
    (media / "old.txt").write_bytes(b"old-media")
    target = _make_plain_sqlite(appdata / "clinical_vault.db", "before")

    bundle = _manifest_bundle(tmp_path, monkeypatch, db_value="after", media={"new.txt": b"new-media"})
    preflight = GuidedRestoreService.preflight_file(
        bundle,
        original_name="complete.zip",
        active_engine=("sqlite", "pysqlite"),
    )
    job = GuidedRestoreService.get_job(preflight["restore_id"])
    job.update(
        status="scheduled",
        target_db_path=str(target),
        prepared_media_digest=archive_mod._directory_digest(media),
    )
    GuidedRestoreService._write_job(job)

    monkeypatch.setattr(worker_mod, "get_media_root", lambda: media)
    monkeypatch.setattr(GuidedRestoreWorker, "_wait_parent_exit", classmethod(lambda cls, pid, timeout=20: None))
    monkeypatch.setattr(GuidedRestoreWorker, "_launch_app", staticmethod(lambda executable: DummyProcess()))
    monkeypatch.setattr(GuidedRestoreWorker, "_smoke_check", staticmethod(lambda timeout=60: True))

    result = GuidedRestoreWorker.run(preflight["restore_id"], parent_pid=999, executable="DigitalCrown.exe")
    final = GuidedRestoreService.get_job(preflight["restore_id"])

    assert result == 0
    assert _read_truth(target) == "after"
    assert not (media / "old.txt").exists()
    assert (media / "new.txt").read_bytes() == b"new-media"
    assert final["status"] == "success"
    assert final["smoke_check"] == "passed"


def test_worker_smoke_failure_triggers_proven_rollback(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    _patch_appdata(monkeypatch, appdata)
    media = appdata / "media"
    media.mkdir(parents=True)
    target = _make_plain_sqlite(appdata / "clinical_vault.db", "before")
    encrypted = _make_sqlite_backup(tmp_path, "restored-but-bad")
    preflight = GuidedRestoreService.preflight_file(
        encrypted,
        original_name="cabinet.db.enc",
        active_engine=("sqlite", "pysqlite"),
    )
    job = GuidedRestoreService.get_job(preflight["restore_id"])
    job.update(status="scheduled", target_db_path=str(target))
    GuidedRestoreService._write_job(job)

    monkeypatch.setattr(worker_mod, "get_media_root", lambda: media)
    monkeypatch.setattr(GuidedRestoreWorker, "_wait_parent_exit", classmethod(lambda cls, pid, timeout=20: None))
    monkeypatch.setattr(GuidedRestoreWorker, "_launch_app", staticmethod(lambda executable: DummyProcess()))
    smoke_results = iter([False, True])
    monkeypatch.setattr(GuidedRestoreWorker, "_smoke_check", staticmethod(lambda timeout=60: next(smoke_results)))

    result = GuidedRestoreWorker.run(preflight["restore_id"], parent_pid=999, executable="DigitalCrown.exe")
    final = GuidedRestoreService.get_job(preflight["restore_id"])

    assert result == 2
    assert _read_truth(target) == "before"
    assert final["status"] == "rolled_back"
    assert final["rollback"] == "passed"
    assert final["smoke_check"] == "failed"
