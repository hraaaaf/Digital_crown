#!/usr/bin/env python3
"""LOT05 J7 FUE-G: real run.py process, real SQLCipher/WAL/media restore on disposable Windows VM.

NOT a packaged installable .exe, clinic PC, production deployment or clinical migration.
All database/media/keys stay inside a fresh GitHub runner temp directory and are deleted.
Only process launch invocation is adapted to run.py, because the release executable is
deliberately unavailable before INSTALLABLE_CERTIFIED. Real worker restore, HTTP /health,
process exit and Windows SQLCipher files are exercised (no fake HTTP responder).
"""
from __future__ import annotations

from contextlib import closing
import argparse
import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from restore03_windows_native_runtime_lab import _env_and_target, _subprocess

MARKER = "LOT05_J7_FUEG_REAL_RUNPY_SQLCIPHER_RESTART_ROLLBACK_FAKE_ONLY"
PROOF_NAME = "lot05-j7-fueg-windows-verdict.json"
FAKE_OWNER = 77001


def check(value, message):
    if not value:
        raise AssertionError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_truth(db: Path, key: str) -> str:
    from sqlcipher3 import dbapi2 as sqlcipher
    with closing(sqlcipher.connect(str(db))) as conn:
        conn.execute("PRAGMA key = '" + key + "'")
        check(conn.execute("PRAGMA integrity_check").fetchone() == ("ok",), "DB_INTEGRITY")
        return conn.execute("SELECT value FROM FUE_ONLY_truth WHERE id=1").fetchone()[0]


def crash_commit_wal(db: Path, key: str) -> None:
    code = (
        "import os,sys; from sqlcipher3 import dbapi2 as c; "
        "d=c.connect(sys.argv[1]); d.execute(\"PRAGMA key = '\"+sys.argv[2]+\"'\"); "
        "d.execute('PRAGMA journal_mode=WAL'); d.execute('PRAGMA wal_autocheckpoint=0'); "
        "d.execute('CREATE TABLE FUE_ONLY_truth(id INTEGER PRIMARY KEY,value TEXT)'); "
        "d.execute(\"INSERT INTO FUE_ONLY_truth VALUES (1,'BEFORE_FAKE')\"); "
        "d.commit(); os._exit(0)"
    )
    p = subprocess.run([sys.executable, "-B", "-c", code, str(db), key],
                       cwd=ROOT, capture_output=True, timeout=30)
    check(p.returncode == 0, "WAL_CHILD_CRASH_EXIT")
    wal = Path(str(db) + "-wal")
    check(wal.exists() and wal.stat().st_size > 0, "COMMITTED_WAL_NOT_FOUND")


def health(port: int, timeout: float, process=None) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            return False
        try:
            with urlopen("http://127.0.0.1:%d/health" % port, timeout=2) as r:
                content = json.loads(r.read().decode("utf-8"))
                if r.status == 200 and content.get("status") == "ok" and content.get("db") == "ok":
                    return True
        except Exception:
            pass
        time.sleep(0.75)
    return False


def launch(env: dict[str, str], work: Path, label: str):
    log = (work / (label + "-private.log")).open("wb")
    proc = subprocess.Popen([sys.executable, "-u", "run.py"], cwd=ROOT, env=env,
                            stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log.close()
    return proc


def stop(proc):
    if proc.poll() is None:
        proc.kill()  # real sudden termination on disposable VM, never a cabinet PID
    proc.wait(timeout=15)
    check(proc.poll() is not None, "REAL_APP_PROCESS_NOT_STOPPED")


def bundle(work: Path, db: Path, key: str, marker: str, files: dict[str, bytes]) -> Path:
    from sqlcipher3 import dbapi2 as sqlcipher
    from backend.services.backup_service import BackupService
    from backend.services import guided_restore_archive as archive
    candidate = work / ("FAKE_candidate_" + marker + ".db")
    BackupService._export_sqlcipher_snapshot(db, candidate, key)
    with closing(sqlcipher.connect(str(candidate))) as conn:
        conn.execute("PRAGMA key = '" + key + "'")
        conn.execute("UPDATE FUE_ONLY_truth SET value=? WHERE id=1", (marker,))
        conn.commit()
    snapshot = work / ("FAKE_snapshot_" + marker + ".db")
    BackupService._export_sqlcipher_snapshot(candidate, snapshot, key)
    enc_db = work / ("FAKE_" + marker + ".db.enc")
    BackupService._encrypt_file_atomic(snapshot, enc_db, BackupService._get_or_create_key())
    media_archive = io.BytesIO()
    with zipfile.ZipFile(media_archive, "w", zipfile.ZIP_DEFLATED) as out:
        for name, content in files.items():
            out.writestr(name, content)
    media_encrypted = archive._master_cipher().encrypt(media_archive.getvalue())
    info = {
        "format": "digital-crown-guided-restore", "version": 1,
        "created_at": "2026-11-09T19:00:00Z",
        "database": {"filename": "fake-database.db.enc", "sha256": sha(enc_db),
                     "encryption": "backup_key", "engine": "sqlite"},
        "media": {"included": True, "filename": "fake-media.zip.enc",
                  "sha256": hashlib.sha256(media_encrypted).hexdigest(),
                  "encryption": "master_key"},
    }
    result = work / ("FAKE_" + marker + "_package.zip")
    with zipfile.ZipFile(result, "w", zipfile.ZIP_STORED) as out:
        out.writestr("manifest.json", json.dumps(info))
        out.writestr("fake-database.db.enc", enc_db.read_bytes())
        out.writestr("fake-media.zip.enc", media_encrypted)
    for disposable in (candidate, snapshot, enc_db):
        disposable.unlink(missing_ok=True)
    return result


def prepare(package: Path, target: Path):
    from backend.services.guided_restore import GuidedRestoreService as Service
    result = Service.preflight_file(package, original_name=package.name,
                                    active_engine=("sqlite", "pysqlcipher"),
                                    owner_employer_id=FAKE_OWNER)
    check(result["status"] == "preflight_ready", "PREFLIGHT_NOT_READY")
    prep = Service.prepare(result["restore_id"], owner_employer_id=FAKE_OWNER)
    check(prep["status"] == "prepared", "PREPARE_NOT_READY")
    job = Service.get_job(result["restore_id"])
    check(job["prepared_rescue_db_sha256"] and job["prepared_media_digest"], "RESCUE_NOT_VERIFIED")
    job["status"] = "scheduled"  # Frozen-only request_apply cannot be called from source checkout.
    job["target_db_path"] = str(target)
    Service._write_job(job)
    return result["restore_id"]


def main():
    check(os.name == "nt" and os.getenv("GITHUB_ACTIONS") == "true", "GITHUB_WINDOWS_ONLY")
    check(bool(os.getenv("RUNNER_TEMP")), "RUNNER_TEMP_REQUIRED")
    check(bool(os.getenv("EXACT_HEAD")), "EXACT_HEAD_REQUIRED")
    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    check(actual_sha == os.environ["EXACT_HEAD"], "WRONG_HEAD")
    check(not any(os.getenv(k) for k in (
        "DATABASE_URL", "DIGITALCROWN_USER_DATA_DIR", "DIGITALCROWN_ENV_FILE",
        "SQLCIPHER_KEY_HEX", "CABINET_MASTER_KEY_HEX", "MEDIA_ROOT"
    )), "INHERITED_CABINET_ENV_REFUSED")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    evidence = args.output.absolute()
    root = Path(os.environ["RUNNER_TEMP"]).resolve()
    check(evidence.parent.resolve() == root and not evidence.exists(), "NON_VIRGIN_RUNNER_OUTPUT")
    evidence.mkdir()
    work = evidence / "FAKE_PRIVATE_WORK"
    work.mkdir()
    procs = []
    verdict = None
    try:
        env, db, port = _env_and_target(work)
        os.environ.update(env)
        from backend.services.backup_service import BackupService
        from backend.services.guided_restore import GuidedRestoreService as Service
        from backend.services.guided_restore_worker import GuidedRestoreWorker as Worker
        from backend import database
        media = Path(env["MEDIA_ROOT"])
        media.mkdir(parents=True, exist_ok=False)
        _subprocess("FAKE_alembic", [sys.executable, "-m", "alembic", "upgrade", "head"], env, work)
        check(db.is_file(), "REAL_SQLCIPHER_SCHEMA_NOT_CREATED")
        first = launch(env, work, "FAKE_live_before")
        procs.append(first)
        check(health(port, 110, first), "REAL_INITIAL_RUNPY_HEALTH_FAILED")
        (media / "FAKE_before.bin").write_bytes(b"FAKE_BEFORE_NOT_A_PATIENT")
        crash_commit_wal(db, env["SQLCIPHER_KEY_HEX"])
        check(Path(str(db) + "-wal").stat().st_size > 0, "WAL_NOT_RETAINED")
        before_package = bundle(work, db, env["SQLCIPHER_KEY_HEX"], "AFTER_FAKE",
                                {"radios/FAKE_AFTER.bin": b"FAKE_RADIO_NO_PATIENT",
                                 "documents/FAKE_AFTER.bin": b"FAKE_DOC_NO_PATIENT"})
        # Real backup to a NEW verified SQLCipher clone, while /health is running.
        original_backup = BackupService.backup_active_database()
        check(original_backup["status"] == "SUCCESS", "REAL_BACKUPSERVICE_BACKUP_FAILED")
        encrypted = Path(env["DIGITALCROWN_USER_DATA_DIR"]) / "backups" / original_backup["backup_filename"]
        check(sha(encrypted) == original_backup["checksum"], "ENCRYPTED_BACKUP_SHA_MISMATCH")
        clone = work / "FAKE_original_backup_clone.db"
        BackupService.restore_backup(encrypted, clone, verify_sqlcipher=True,
                                     passphrase=env["SQLCIPHER_KEY_HEX"])
        check(read_truth(clone, env["SQLCIPHER_KEY_HEX"]) == "BEFORE_FAKE", "VERIFIED_BACKUP_WRONG")
        good_id = prepare(before_package, db)
        database.engine.dispose()
        stop(first)
        import backend.services.guided_restore_worker as worker_module
        # ONLY launcher path is adapted: the installed signed EXE is NOT available.
        # Each returned process actually executes the real source entrypoint run.py.
        launches = []
        def launch_real(_exe):
            proc = launch(env, work, "FAKE_real_restart_" + str(len(launches)))
            launches.append(proc)
            procs.append(proc)
            return proc
        Worker._launch_app = staticmethod(launch_real)
        check(not Worker._pid_alive(first.pid), "PARENT_EXIT_NOT_REAL")
        check(Worker.run(good_id, first.pid, executable="SOURCE_ONLY_NOT_FROZEN") == 0,
              "REAL_RESTORE_AND_RESTART_FAILED")
        check(Service.get_job(good_id)["status"] == "success", "REAL_RESTORE_JOB_NOT_SUCCESS")
        check(health(port, 30, launches[-1]), "REAL_POST_RESTORE_HTTP_NOT_HEALTHY")
        check(read_truth(db, env["SQLCIPHER_KEY_HEX"]) == "AFTER_FAKE", "REAL_RESTORE_MARKER_WRONG")
        check((media / "radios/FAKE_AFTER.bin").read_bytes() == b"FAKE_RADIO_NO_PATIENT",
              "RESTORED_FAKE_MEDIA_MISSING")
        check(not (media / "FAKE_before.bin").exists(), "OLD_MEDIA_NOT_REPLACED")
        # Negative: a real run.py startup is deliberately denied by a short secret.
        # The real HTTP health probe must fail, triggering genuine worker rollback.
        failing_package = bundle(work, db, env["SQLCIPHER_KEY_HEX"], "FAILED_FAKE",
                                 {"radios/FAKE_FAILED.bin": b"FAKE_FAILED_MEDIA"})
        bad_id = prepare(failing_package, db)
        database.engine.dispose()
        stop(launches[-1])
        check(not Worker._pid_alive(launches[-1].pid), "SECOND_PARENT_EXIT_NOT_REAL")
        failed_once = [False]
        def launch_with_real_failure(_exe):
            bad = not failed_once[0]
            failed_once[0] = True
            broken = env.copy()
            if bad:
                broken["SECRET_KEY"] = "too_short_to_start"
            proc = launch(broken, work, "FAKE_negative_restart_" + str(len(procs)))
            launches.append(proc)
            procs.append(proc)
            return proc
        Worker._launch_app = staticmethod(launch_with_real_failure)
        original_smoke = Worker._smoke_check
        Worker._smoke_check = staticmethod(
            lambda timeout=60: original_smoke(timeout=9 if failed_once[0] and len(launches) == 2 else 110))
        exit_code = Worker.run(bad_id, launches[0].pid, executable="SOURCE_ONLY_NOT_FROZEN")
        check(exit_code == 2, "REAL_HEALTH_FAILURE_DID_NOT_ROLLBACK")
        check(Service.get_job(bad_id)["status"] == "rolled_back", "ROLLBACK_STATE_NOT_WRITTEN")
        check(health(port, 35, launches[-1]), "REAL_ROLLBACK_RESTART_NOT_HEALTHY")
        check(read_truth(db, env["SQLCIPHER_KEY_HEX"]) == "AFTER_FAKE", "ROLLBACK_DB_NOT_RESTORED")
        check((media / "radios/FAKE_AFTER.bin").read_bytes() == b"FAKE_RADIO_NO_PATIENT",
              "ROLLBACK_MEDIA_NOT_RESTORED")
        check(not (media / "radios/FAKE_FAILED.bin").exists(), "FAILED_MEDIA_REMAINS")
        verdict = {
            "marker": MARKER, "head_sha": actual_sha, "platform": "windows",
            "runtime": "REAL_RUNPY_SOURCE_PROCESS_NOT_FROZEN_EXE",
            "app_start_stop_real": True, "http_health_real": True,
            "native_sqlcipher_wal_commit_and_crash": True,
            "backupservice_encrypted_clone_verified": True,
            "guided_restore_worker_success_restart_real": True,
            "guided_restore_worker_http_failure_rollback_restart_real": True,
            "database_and_media_invariants": "PASSED",
            "test_data": "SYNTHETIC_ONLY", "clinical_import_permitted": False,
            "physical_cabinet_touched": False, "production_deployed": False,
            "signed_installable_executable_verified": False,
        }
    finally:
        for proc in procs:
            try:
                if proc.poll() is None:
                    stop(proc)
            except Exception:
                pass
        try:
            database.engine.dispose()
        except Exception:
            pass
        shutil.rmtree(work, ignore_errors=True)
    if verdict is None:
        raise AssertionError("NO_VERDICT")
    (evidence / PROOF_NAME).write_text(json.dumps(verdict, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    check({p.name for p in evidence.iterdir()} == {PROOF_NAME}, "PRIVATE_ARTIFACT_ESCAPE")
    print(MARKER + " PASS exact_sha=" + actual_sha[:10])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("LOT05_J7_FUEG_FAIL:" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2) from None
