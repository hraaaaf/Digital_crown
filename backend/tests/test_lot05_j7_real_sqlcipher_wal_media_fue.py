"""LOT05 J7: real SQLCipher/WAL + BackupService + GuidedRestore clone FUE.

The only fixture is entirely fabricated, lives in pytest tmp_path, and cannot
accept a cabinet path, database record, license, network endpoint, or patient
input. Never set a real Cabinet environment or invoke request_apply.

Real SQLCipher disk I/O, WAL crash persistence and production backup/restore
methods are exercised. APP EXIT / LAUNCH / HEALTH are *mocked* by design:
this is not a physical cabinet restart or clinical migration certification.
"""
from __future__ import annotations

import hashlib
from contextlib import closing
import io
import json
import os
import subprocess
import sys
import types
import zipfile
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from sqlcipher3 import dbapi2 as sqlcipher  # REQUIRED; no importorskip/skip

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService
from backend.services.guided_restore import GuidedRestoreService
from backend.services.guided_restore_worker import GuidedRestoreWorker
from backend.services import guided_restore_archive as archive
from backend.services import guided_restore_worker as worker_module


FAKE_SQLCIPHER_KEY = "22" * 32
FAKE_MASTER_KEY = "11" * 32
FAKE_OWNER_ID = 77001

# subprocess ends via os._exit() after a SQLCipher COMMIT, deliberately leaving
# uncheckpointed WAL: a reproducible approximation of a sudden process death.
_CRASH_CREATE = r"""
from sqlcipher3 import dbapi2 as sqlcipher
import os,sys
path,key,value=sys.argv[1:]
conn=sqlcipher.connect(path)
conn.execute("PRAGMA key = '" + key + "'")
assert conn.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower()=="wal"
conn.execute("PRAGMA wal_autocheckpoint=0")
conn.executescript('''
CREATE TABLE users(id INTEGER PRIMARY KEY, email TEXT);
CREATE TABLE patients(id INTEGER PRIMARY KEY, nom TEXT);
CREATE TABLE truth(id INTEGER PRIMARY KEY, value TEXT);
''')
conn.execute("INSERT INTO users VALUES (1,'fake-owner@example.invalid')")
conn.execute("INSERT INTO patients VALUES (1,'FAKE_ONLY')")
conn.execute("INSERT INTO truth VALUES (1,?)",(value,))
conn.commit()
conn.execute("INSERT INTO truth VALUES (2,'WAL_COMMITTED_FAKE_ONLY')")
conn.commit()
assert conn.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
assert os.path.getsize(path+"-wal")>0
os._exit(0)
"""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _crash_committed_database(path: Path, value: str) -> None:
    assert str(path.name).startswith("FAKE_") or path.name == "clinical_vault.db"
    result = subprocess.run(
        [sys.executable, "-B", "-c", _CRASH_CREATE,
         str(path), FAKE_SQLCIPHER_KEY, value],
        check=False, capture_output=True, text=True, timeout=25,
    )
    assert result.returncode == 0, result.stderr[-1200:]
    wal = Path(str(path) + "-wal")
    assert path.is_file() and wal.is_file() and wal.stat().st_size > 0



def _crash_refresh_wal(path: Path) -> None:
    """Leave a committed but uncheckpointed WAL after preparation, no value change."""
    code = (
        "from sqlcipher3 import dbapi2 as c\n"
        "import os,sys\n"
        "db=c.connect(sys.argv[1]); "
        "db.execute(\"PRAGMA key = '\"+sys.argv[2]+\"'\"); "
        "db.execute('PRAGMA journal_mode=WAL'); "
        "db.execute('PRAGMA wal_autocheckpoint=0'); "
        "db.execute('CREATE TABLE IF NOT EXISTS FAKE_ONLY_WAL_MARKER(marker TEXT)'); "
        "db.execute(\"INSERT INTO FAKE_ONLY_WAL_MARKER VALUES ('WAL_ONLY_FAKE')\"); "
        "db.commit(); os._exit(0)\n"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", code, str(path), FAKE_SQLCIPHER_KEY],
        capture_output=True, text=True, timeout=25,
    )
    assert result.returncode == 0, result.stderr[-1200:]
    wal = Path(str(path) + "-wal")
    assert wal.exists() and wal.stat().st_size > 0

def _read_truth(path: Path) -> list[str]:
    with closing(sqlcipher.connect(str(path))) as db:
        db.execute("PRAGMA key = '" + FAKE_SQLCIPHER_KEY + "'")
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='patients'"
        ).fetchone() == ("patients",)
        return [v[0] for v in db.execute("SELECT value FROM truth ORDER BY id")]


def _make_restore_package(lab, *, tamper_db=False) -> Path:
    """Real verified SQLCipher export + real Fernet encryption + media archive."""
    snapshot = lab["tmp"] / "FAKE_snapshot.db"
    BackupService._export_sqlcipher_snapshot(
        lab["candidate"], snapshot, FAKE_SQLCIPHER_KEY
    )
    assert _read_truth(snapshot) == ["AFTER_FAKE", "WAL_COMMITTED_FAKE_ONLY"]
    encrypted_db = lab["tmp"] / "FAKE_candidate.db.enc"
    BackupService._encrypt_file_atomic(
        snapshot, encrypted_db, BackupService._get_or_create_key()
    )
    plaintext_snapshot_sha = _sha(snapshot)
    assert plaintext_snapshot_sha != _sha(lab["candidate"])
    snapshot.unlink()

    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as out:
        out.writestr("fake-images/AFTER_FAKE_RADIO.bin", b"FAKE_NEW_IMAGE_NO_PATIENT")
        out.writestr("fake-documents/AFTER_FAKE_NOTE.bin", b"FAKE_NEW_NOTE_NO_PATIENT")
    encrypted_media = archive._master_cipher().encrypt(data.getvalue())
    cipher_bytes = bytearray(encrypted_db.read_bytes())
    db_manifest_hash = hashlib.sha256(cipher_bytes).hexdigest()
    if tamper_db:
        cipher_bytes[-1] = (cipher_bytes[-1] + 1) % 255
    manifest = {
        "format": "digital-crown-guided-restore",
        "version": 1,
        "created_at": "2026-11-09T16:00:00Z",
        "database": {
            "filename": "fake-database.db.enc",
            "sha256": db_manifest_hash,
            "encryption": "backup_key",
            "engine": "sqlite",
        },
        "media": {
            "included": True,
            "filename": "fake-media.zip.enc",
            "sha256": hashlib.sha256(encrypted_media).hexdigest(),
            "encryption": "master_key",
        },
    }
    path = lab["tmp"] / ("FAKE_tampered_restore.zip" if tamper_db else "FAKE_restore.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as out:
        out.writestr("manifest.json", json.dumps(manifest))
        out.writestr("fake-database.db.enc", bytes(cipher_bytes))
        out.writestr("fake-media.zip.enc", encrypted_media)
    assert path.exists()
    return path


@pytest.fixture
def lab(tmp_path: Path, monkeypatch):
    appdata = tmp_path / "FAKE_only_appdata"
    appdata.mkdir()
    monkeypatch.setattr(
        AppPaths, "get_user_data_dir", staticmethod(lambda: appdata)
    )
    monkeypatch.setenv("SQLCIPHER_KEY_HEX", FAKE_SQLCIPHER_KEY)
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", FAKE_MASTER_KEY)
    monkeypatch.setenv("SECRET_KEY", "33" * 32)
    monkeypatch.setenv("ENVIRONMENT", "test")
    # Strictly local fake media; no app HOME path or files outside tmp_path.
    media = appdata / "media"
    media.mkdir()
    (media / "FAKE_PREVIOUS.bin").write_bytes(b"FAKE_OLD_IMAGE_NO_PATIENT")
    monkeypatch.setattr(worker_module, "get_media_root", lambda: media)
    monkeypatch.setattr(
        "backend.services.guided_restore.get_media_root", lambda: media
    )
    target = appdata / "clinical_vault.db"
    candidate = tmp_path / "FAKE_candidate_source.db"
    _crash_committed_database(target, "BEFORE_FAKE")
    _crash_committed_database(candidate, "AFTER_FAKE")
    # Do not read/close the WAL crash image here: final-close may checkpoint WAL.

    # Production BackupService obtains the engine by import. Replace ONLY that
    # engine import in pytest with a fake object pointing to our temp clone.
    fake_backend_database = types.ModuleType("backend.database")
    fake_backend_database.engine = types.SimpleNamespace(
        dialect=types.SimpleNamespace(name="sqlite"),
        driver="pysqlcipher",
        url=types.SimpleNamespace(database=str(target), password=FAKE_SQLCIPHER_KEY),
    )
    monkeypatch.setitem(sys.modules, "backend.database", fake_backend_database)

    return {
        "tmp": tmp_path, "appdata": appdata, "media": media,
        "target": target, "candidate": candidate,
    }


def _prepare(lab, monkeypatch):
    archive_path = _make_restore_package(lab)
    preflight = GuidedRestoreService.preflight_file(
        archive_path, original_name="FAKE_j7_pair.zip",
        active_engine=("sqlite", "pysqlcipher"),
        owner_employer_id=FAKE_OWNER_ID,
    )
    assert preflight["status"] == "preflight_ready", preflight["errors"]
    prepared = GuidedRestoreService.prepare(
        preflight["restore_id"], owner_employer_id=FAKE_OWNER_ID
    )
    assert prepared["status"] == "prepared"
    job = GuidedRestoreService.get_job(preflight["restore_id"])
    assert job["prepared_rescue_db_sha256"] and job["prepared_media_digest"]
    backups = list((lab["appdata"] / "backups").glob("db_backup_*.db.enc"))
    assert backups and backups[0].stat().st_size > 0
    rescue = lab["tmp"] / "FAKE_prepared_safety_clone.db"
    BackupService.restore_backup(
        backups[0], rescue,
        verify_sqlcipher=True, passphrase=FAKE_SQLCIPHER_KEY,
    )
    assert _read_truth(rescue) == ["BEFORE_FAKE", "WAL_COMMITTED_FAKE_ONLY"]

    # The real product request_apply() requires a frozen Cabinet executable and
    # owner confirmation. DO NOT invoke it in a test VM; simulate scheduled
    # status as the only bypass, without launching or stopping a real app.
    job["status"] = "scheduled"
    GuidedRestoreService._write_job(job)

    monkeypatch.setattr(
        GuidedRestoreWorker, "_wait_parent_exit",
        classmethod(lambda cls, pid, timeout=20: None),
    )

    class FakeProcess:
        def poll(self): return 0
        def terminate(self): raise AssertionError("NO_PROCESS_TERMINATION_IN_FAKE_LAB")
        def wait(self, timeout=0): return 0
        def kill(self): raise AssertionError("NO_PROCESS_KILL_IN_FAKE_LAB")

    monkeypatch.setattr(
        GuidedRestoreWorker, "_launch_app",
        staticmethod(lambda executable: FakeProcess()),
    )
    return preflight["restore_id"]


def test_j7_real_sqlcipher_crash_wal_preserved_through_verified_backup(lab):
    """Production BackupService uses SQLCipher export, not raw main-file copy."""
    target = lab["target"]
    assert Path(str(target) + "-wal").stat().st_size > 0
    result = BackupService.backup_active_database()
    assert result["status"] == "SUCCESS", result.get("error_code")
    ciphertext = lab["appdata"] / "backups" / result["backup_filename"]
    assert result["checksum"] == _sha(ciphertext)
    assert not ciphertext.read_bytes().startswith(b"SQLite format 3")
    clone = lab["tmp"] / "FAKE_RESTORED_CLONE.db"
    BackupService.restore_backup(
        ciphertext, clone,
        verify_sqlcipher=True, passphrase=FAKE_SQLCIPHER_KEY,
    )
    assert _read_truth(clone) == ["BEFORE_FAKE", "WAL_COMMITTED_FAKE_ONLY"]
    assert not list(lab["appdata"].rglob(".tmp_*sqlcipher_snapshot.db"))


def test_j7_real_guided_restore_sqlcipher_plus_media_success(lab, monkeypatch):
    restore_id = _prepare(lab, monkeypatch)
    _crash_refresh_wal(lab["target"])
    monkeypatch.setattr(
        GuidedRestoreWorker, "_smoke_check",
        staticmethod(lambda timeout=60: True),
    )
    result = GuidedRestoreWorker.run(
        restore_id, parent_pid=0, executable="FAKE_ONLY_NO_EXECUTION"
    )
    final = GuidedRestoreService.get_job(restore_id)
    assert result == 0
    assert final["status"] == "success"
    assert _read_truth(lab["target"]) == ["AFTER_FAKE", "WAL_COMMITTED_FAKE_ONLY"]
    assert not (lab["media"] / "FAKE_PREVIOUS.bin").exists()
    assert (lab["media"] / "fake-images" / "AFTER_FAKE_RADIO.bin").read_bytes() == \
        b"FAKE_NEW_IMAGE_NO_PATIENT"
    assert (lab["media"] / "fake-documents" / "AFTER_FAKE_NOTE.bin").read_bytes() == \
        b"FAKE_NEW_NOTE_NO_PATIENT"
    assert _read_truth(lab["candidate"]) == ["AFTER_FAKE", "WAL_COMMITTED_FAKE_ONLY"]


def test_j7_real_guided_restore_smoke_fail_restores_wal_and_media(lab, monkeypatch):
    restore_id = _prepare(lab, monkeypatch)
    _crash_refresh_wal(lab["target"])
    checks = iter([False, True])  # first app failed, rollback app healthy
    monkeypatch.setattr(
        GuidedRestoreWorker, "_smoke_check",
        staticmethod(lambda timeout=60: next(checks)),
    )
    result = GuidedRestoreWorker.run(
        restore_id, parent_pid=0, executable="FAKE_ONLY_NO_EXECUTION"
    )
    final = GuidedRestoreService.get_job(restore_id)
    assert result == 2
    assert final["status"] == "rolled_back"
    assert final["rollback"] == "passed"
    assert _read_truth(lab["target"]) == ["BEFORE_FAKE", "WAL_COMMITTED_FAKE_ONLY"]
    # Critical oracle: the COMMITTED WAL marker created *after prepare* must
    # still exist after DB+media rescue. Checking only the original truth rows
    # would falsely pass if the worker silently dropped the rescue WAL.
    with closing(sqlcipher.connect(str(lab["target"]))) as restored:
        restored.execute("PRAGMA key = '" + FAKE_SQLCIPHER_KEY + "'")
        assert restored.execute(
            "SELECT marker FROM FAKE_ONLY_WAL_MARKER"
        ).fetchone() == ("WAL_ONLY_FAKE",)
    assert (lab["media"] / "FAKE_PREVIOUS.bin").read_bytes() == \
        b"FAKE_OLD_IMAGE_NO_PATIENT"
    assert not (lab["media"] / "fake-images" / "AFTER_FAKE_RADIO.bin").exists()


def test_j7_sqlcipher_corruption_wrong_key_and_owner_fail_closed(lab, monkeypatch):
    malformed_archive = _make_restore_package(lab, tamper_db=True)
    with pytest.raises((ValueError, RuntimeError)):
        GuidedRestoreService.preflight_file(
            malformed_archive, original_name="FAKE_tampered.zip",
            active_engine=("sqlite", "pysqlcipher"),
            owner_employer_id=FAKE_OWNER_ID,
        )
    assert _read_truth(lab["target"]) == ["BEFORE_FAKE", "WAL_COMMITTED_FAKE_ONLY"]

    restore_id = _prepare(lab, monkeypatch)
    with pytest.raises(PermissionError):
        GuidedRestoreService.get_owned_job(restore_id, FAKE_OWNER_ID + 1)
    # Restore the pre-apply status to exercise the *real* frozen runtime gate.
    preapply = GuidedRestoreService.get_job(restore_id)
    preapply["status"] = "prepared"
    GuidedRestoreService._write_job(preapply)
    with pytest.raises(RuntimeError, match="exécutable cabinet"):
        GuidedRestoreService.request_apply(
            restore_id, "RESTAURER", owner_employer_id=FAKE_OWNER_ID,
        )  # deliberate NO-GO: never starts the worker
    assert GuidedRestoreService.get_job(restore_id)["status"] == "prepared"
    assert _read_truth(lab["target"]) == ["BEFORE_FAKE", "WAL_COMMITTED_FAKE_ONLY"]

    # A mismatched SQLCipher key must not publish a cloned destination.
    backup = next((lab["appdata"] / "backups").glob("db_backup_*.db.enc"))
    clone = lab["tmp"] / "FAKE_wrong_key_clone.db"
    with pytest.raises((RuntimeError, sqlcipher.DatabaseError)):
        BackupService.restore_backup(
            backup, clone, verify_sqlcipher=True, passphrase="FAKE_WRONG_KEY",
        )
    assert not clone.exists()
    assert not list(lab["tmp"].glob(".tmp_*FAKE_wrong_key_clone.db"))
    assert _read_truth(lab["target"]) == ["BEFORE_FAKE", "WAL_COMMITTED_FAKE_ONLY"]


def test_j7_generic_restore_rejects_authenticated_but_invalid_database(lab):
    """Fernet authenticity does NOT prove SQLCipher/SQLite structural validity."""
    ciphertext = lab["tmp"] / "FAKE_invalid_sqlite.db.enc"
    ciphertext.write_bytes(
        BackupService._get_or_create_key().encrypt(b"FAKE_NOT_A_DATABASE")
    )
    candidate = lab["tmp"] / "FAKE_unverified_clone.db"
    with pytest.raises(RuntimeError, match="RESTORE_FORMAT_UNVERIFIED"):
        BackupService.restore_backup(ciphertext, candidate)
    assert not candidate.exists()


def test_j7_generic_restore_refuses_any_existing_clone_target(lab):
    """A restore helper must never silently replace a possibly live target."""
    result = BackupService.backup_active_database()
    assert result["status"] == "SUCCESS"
    archive_path = lab["appdata"] / "backups" / result["backup_filename"]
    existing = lab["tmp"] / "FAKE_EXISTING_TARGET.db"
    existing.write_bytes(b"FAKE_PREEXISTING_SENTINEL")
    with pytest.raises(FileExistsError):
        BackupService.restore_backup(
            archive_path, existing,
            verify_sqlcipher=True, passphrase=FAKE_SQLCIPHER_KEY,
        )
    assert existing.read_bytes() == b"FAKE_PREEXISTING_SENTINEL"
    assert not list(lab["tmp"].glob(".tmp_*FAKE_EXISTING_TARGET.db"))
