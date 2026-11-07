#!/usr/bin/env python3
"""RESTORE-03 P4 normal rebind across two Windows GitHub runners (synthetic LAB).

A exports an encrypted portable DB/media bundle with real SQLAlchemy model
tables. B uses the real GuidedRestore worker and real P4/token revocation code,
but a synthetic SQLAlchemy session binding and a stand-in HTTP health service.
No actual installed cabinet, physical PC, real patient or clinical GO.
"""
from __future__ import annotations

import argparse
import importlib
from contextlib import closing
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

from restore03_cross_host_lab import (
    MARKER, ROOT, SOURCE_RECORD, create_db, load_slice, machine_pseudonym,
    new_dir, read_db_marker, setup_synthetic_environment, sha256_file,
    test_secret,
)
from restore03_remote_windows_worker_lab import (
    TEST_HEALTH_SERVER, fresh_port, load_restore_classes,
)

BUNDLE_NAME = "restore03-SYNTHETIC-P4.dcbundle"
REPORT_NAME = "restore03-p4-normal-success-evidence.json"
OWNER_ID = 7
CLINIC_ID = "synthetic-p4-windows-crosshost"
BEFORE_MARKER = "RESTORE03_P4_B_BEFORE"
AFTER_MARKER = "RESTORE03_P4_A_AFTER"
BEFORE_MEDIA = b"SYNTHETIC_BEFORE_NOT_CLINICAL"
RADIO_MEDIA = b"SYNTHETIC_RADIO_NOT_CLINICAL"
DOC_MEDIA = b"SYNTHETIC_DOCUMENT_NOT_CLINICAL"
VAULT_SENTINEL = b"SYNTHETIC_PRE_EXISTING_VAULT_NOT_A_CLINICAL_LICENSE"
TABLES = ("users", "cabinet_configs", "revoked_tokens",
          "zka_pairing_tokens", "mobile_paired_devices")


def enforce_isolation() -> None:
    if os.name != "nt" or os.getenv("GITHUB_ACTIONS") != "true":
        raise RuntimeError("ISOLATED_GITHUB_WINDOWS_ONLY")
    if any(os.getenv(k) for k in (
        "DATABASE_URL", "SQLCIPHER_KEY_HEX", "CABINET_MASTER_KEY_HEX",
        "DIGITALCROWN_USER_DATA_DIR", "MEDIA_ROOT",
    )):
        raise RuntimeError("CLINICAL_ENVIRONMENT_FORBIDDEN")
    test_secret()


def models_and_sqlalchemy():
    # load_slice() establishes a lightweight namespace without backend app startup.
    models = importlib.import_module("backend.models")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    return models, create_engine, sessionmaker


def source(output: Path) -> None:
    enforce_isolation()
    new_dir(output)
    work = new_dir(output / "synthetic-private")
    setup_synthetic_environment(work)
    _, _, cabinet_bundle = load_slice()
    models, create_engine, _ = models_and_sqlalchemy()
    db = work / "source-p4.db"
    engine = create_engine("sqlite:///" + db.as_posix())
    try:
        selected = [getattr(models, name).__table__ for name in (
            "User", "CabinetConfig", "RevokedToken", "ZKAPairingToken", "MobilePairedDevice"
        )]
        models.Base.metadata.create_all(engine, tables=selected)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE TABLE patients (id INTEGER PRIMARY KEY, nom TEXT)")
            conn.exec_driver_sql("CREATE TABLE truth (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
            conn.exec_driver_sql("INSERT INTO truth VALUES (1, ?)", (AFTER_MARKER,))
            conn.exec_driver_sql("PRAGMA user_version = 63")
            conn.execute(models.User.__table__.insert().values(
                id=OWNER_ID, email="p4-synthetic@example.invalid",
                hashed_password="SYNTHETIC_NO_AUTH", is_licensed=True,
                license_expires_at=now + timedelta(days=90),
            ))
            conn.execute(models.CabinetConfig.__table__.insert().values(
                owner_id=OWNER_ID, clinic_id=CLINIC_ID,
                nom_cabinet="SYNTHETIC_ONLY_NOT_A_CABINET",
            ))
            conn.execute(models.ZKAPairingToken.__table__.insert().values(
                token="synthetic-p4-pending-code", employer_id=OWNER_ID,
                user_id=OWNER_ID, public_id="synthetic-p4",
                master_key="SYNTHETIC_NOT_A_SECRET",
                expires_at=now + timedelta(minutes=30),
            ))
            conn.execute(models.MobilePairedDevice.__table__.insert().values(
                device_id="synthetic-p4-device", user_id=OWNER_ID,
                employer_id=OWNER_ID, client_public_key_hex="ab" * 65,
                refresh_jti="synthetic-p4-refresh-jti",
            ))
    finally:
        engine.dispose()
    assert read_db_marker(db) == (AFTER_MARKER, 63)
    with closing(sqlite3.connect(str(db))) as check:
        names = {row[0] for row in check.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        assert set(TABLES).issubset(names)
        assert check.execute("SELECT is_licensed FROM users WHERE id=7").fetchone() == (1,)
    media = new_dir(work / "media")
    (media / "radios").mkdir()
    (media / "documents").mkdir()
    (media / "radios" / "SYNTHETIC.txt").write_bytes(RADIO_MEDIA)
    (media / "documents" / "SYNTHETIC.txt").write_bytes(DOC_MEDIA)
    bundle = output / BUNDLE_NAME
    result = cabinet_bundle.create_bundle(
        bundle, test_secret(), database_path=db, media_root=media)
    assert result["sha256"] == sha256_file(bundle)
    evidence = {
        "marker": MARKER, "scenario": "P4_NORMAL_SQLALCHEMY_REAL_MODELS",
        "source_os": "Windows", "source_machine_hash": machine_pseudonym(),
        "bundle_sha256": sha256_file(bundle), "bundle_name": BUNDLE_NAME,
        "synthetic_only": True,
    }
    shutil.rmtree(work)
    (output / SOURCE_RECORD).write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    assert {p.name for p in output.iterdir()} == {BUNDLE_NAME, SOURCE_RECORD}
    print("RESTORE03_P4_SOURCE_ENCRYPTED_SYNTHETIC_BUNDLE_PASS")


def target(input_dir: Path, output: Path) -> None:
    enforce_isolation()
    evidence = json.loads((input_dir / SOURCE_RECORD).read_text(encoding="utf-8"))
    assert evidence["marker"] == MARKER
    assert evidence["source_os"] == "Windows"
    assert evidence["scenario"] == "P4_NORMAL_SQLALCHEMY_REAL_MODELS"
    assert evidence["source_machine_hash"] != machine_pseudonym()
    bundle = input_dir / BUNDLE_NAME
    assert bundle.is_file() and evidence["bundle_sha256"] == sha256_file(bundle)
    new_dir(output)
    work = new_dir(output / "synthetic-private")
    setup_synthetic_environment(work)
    appdata = Path(os.environ["DIGITALCROWN_USER_DATA_DIR"])
    media = work / "synthetic-media"
    media.mkdir()
    os.environ["MEDIA_ROOT"] = str(media)
    os.environ["ENVIRONMENT"] = "restore03_synthetic_ci"
    port = fresh_port()
    os.environ["CABINET_PORT"] = str(port)
    backups, _, portable = load_slice()
    service, worker = load_restore_classes()
    models, create_engine, sessionmaker = models_and_sqlalchemy()
    converted = work / "portable-guided.zip"
    portable.to_local_guided_restore_archive(
        bundle, test_secret(), converted, active_engine=("sqlite", "pysqlite"))
    assert converted.is_file()

    db = appdata / "clinical_vault.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    create_db(db, BEFORE_MARKER)
    (media / "before.txt").write_bytes(BEFORE_MEDIA)
    vault = appdata / "license_vault.bin"
    vault.write_bytes(VAULT_SENTINEL)
    assert read_db_marker(db) == (BEFORE_MARKER, 63)
    rescue_path = appdata / "backups" / "synthetic-before.db.enc"

    def backup_before():
        rescue_path.parent.mkdir(parents=True, exist_ok=True)
        backups._encrypt_and_save(db, rescue_path, backups._get_or_create_key())
        return {
            "status": "SUCCESS", "backup_filename": rescue_path.name,
            "checksum": sha256_file(rescue_path),
            "engine": "sqlite", "size_bytes": rescue_path.stat().st_size,
        }

    backups.backup_active_database = staticmethod(backup_before)
    candidate = service.preflight_file(
        converted, original_name="synthetic-p4-portable-guided.zip",
        active_engine=("sqlite", "pysqlite"))
    assert candidate["compatible"] is True and candidate["restore_media"] is True
    prepared = service.prepare(candidate["restore_id"])
    assert prepared["status"] == "prepared"
    job = service.get_job(candidate["restore_id"])
    assert job["prepared_rescue_db_sha256"]
    job["status"] = "scheduled"
    service._write_job(job)

    # Exercise the genuine P4 ORM/revocation code on the restored file.
    # Only the database *binding* is laboratory-scoped; it is not app startup.
    database = types.ModuleType("backend.database")
    database.engine = create_engine(
        "sqlite:///" + db.as_posix(), connect_args={"check_same_thread": False})
    database.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=database.engine)
    sys.modules["backend.database"] = database
    sys.modules["backend"].database = database
    sys.modules["backend"].models = models
    security = importlib.import_module("backend.security")
    security.token_blacklist._mobile_cutoffs.clear()

    worker._wait_parent_exit = classmethod(lambda cls, pid, timeout=20.0: None)
    original_smoke = worker._smoke_check
    worker._smoke_check = staticmethod(lambda timeout=60: original_smoke(timeout=5.0))
    health_server = work / "synthetic-health-server.py"
    health_server.write_text(TEST_HEALTH_SERVER, encoding="utf-8")
    processes = []

    def launch_stand_in(_executable):
        proc = subprocess.Popen(
            [sys.executable, "-u", str(health_server), str(port), str(db), str(media),
             AFTER_MARKER, "radios/SYNTHETIC.txt", RADIO_MEDIA.decode("ascii"), "pass"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        processes.append(proc)
        return proc

    worker._launch_app = staticmethod(launch_stand_in)
    try:
        result_code = worker.run(
            candidate["restore_id"], parent_pid=999999,
            executable="SYNTHETIC_STANDIN_NOT_INSTALLED_CABINET")
        final = service.get_job(candidate["restore_id"])
        assert result_code == 0, "NORMAL_P4_REBIND_FAILED_OR_ROLLED_BACK"
        assert final["status"] == "success"
        assert final["smoke_check"] == "passed" and final["rollback"] == "not_needed"
        p4 = final["portability_rebind"]
        assert p4["cabinet_count"] == 1
        assert p4["licence_revalidation_required"] is True
        assert p4["mobile_access_revoked"] is True
        assert p4["cabinets"] == [{
            "owner_id": OWNER_ID, "clinic_id": CLINIC_ID,
            "mobile_access_revoked": True,
        }]
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)
        database.engine.dispose()

    # Independent fresh-connection persistence oracle AFTER P4 disposed its engine.
    assert read_db_marker(db) == (AFTER_MARKER, 63)
    assert (media / "radios" / "SYNTHETIC.txt").read_bytes() == RADIO_MEDIA
    assert (media / "documents" / "SYNTHETIC.txt").read_bytes() == DOC_MEDIA
    assert not (media / "before.txt").exists()
    assert not vault.exists(), "DESTINATION_LICENSE_VAULT_NOT_REMOVED"
    with closing(sqlite3.connect(str(db))) as check:
        assert check.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        owner = check.execute(
            "SELECT is_licensed, license_expires_at FROM users WHERE id=?", (OWNER_ID,)
        ).fetchone()
        assert owner == (0, None), "REVALIDATION_STATE_NOT_PERSISTED"
        config = check.execute(
            "SELECT clinic_id FROM cabinet_configs WHERE owner_id=?", (OWNER_ID,)
        ).fetchone()
        assert config == (CLINIC_ID,), "CLINIC_ID_CHANGED"
        markers = check.execute(
            "SELECT jti FROM revoked_tokens WHERE jti LIKE ?",
            (f"mobile-epoch:{OWNER_ID}:%",),
        ).fetchall()
        assert len(markers) == 1, "MOBILE_CUTOFF_NOT_PERSISTED"
        assert check.execute(
            "SELECT COUNT(*) FROM zka_pairing_tokens WHERE employer_id=?",
            (OWNER_ID,),
        ).fetchone() == (0,), "PENDING_PAIRING_NOT_REVOKED"
        device = check.execute(
            "SELECT revoked_at FROM mobile_paired_devices WHERE employer_id=?",
            (OWNER_ID,),
        ).fetchone()
        assert device and device[0] is not None, "MOBILE_DEVICE_NOT_REVOKED"

    result = {
        "marker": "RESTORE03_P4_NORMAL_REAL_FUNCTION_SYNTHETIC_ONLY",
        "tested_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_os": "Windows", "target_os": "Windows",
        "distinct_runners_by_machine_pseudonym": True,
        "bundle_integrity": "PASS",
        "db_original_and_media_applied": "PASS",
        "license_rebind_normal_execution": "PASS",
        "owner_license_unlicensed_after_reopen": "PASS",
        "licence_revalidation_required": True,
        "mobile_cutoff_persisted_after_reopen": "PASS",
        "pairing_tokens_invalidated": "PASS",
        "paired_device_revoked": "PASS",
        "vault_from_old_machine_removed": "PASS",
        "db_integrity_after_reopen": "PASS",
        "http_health": "STAND_IN_ONLY",
        "database_binding": "SYNTHETIC_REAL_SQLALCHEMY_NOT_PACKAGED_APP_STARTUP",
        "actual_p4_code": True,
        "real_patients": False, "frozen_exe": False,
        "physical_second_pc": False, "nas_smb_real": False,
        "clinical_go": False,
    }
    shutil.rmtree(work)
    if appdata.exists():
        shutil.rmtree(appdata)
    (output / REPORT_NAME).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    assert {p.name for p in output.iterdir()} == {REPORT_NAME}
    print("RESTORE03_P4_NORMAL_REBIND_PERSISTENCE_CROSSHOST_SYNTHETIC_PASS")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=("source", "target"))
    p.add_argument("--input", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.phase == "source":
            source(args.output)
        else:
            if args.input is None:
                raise RuntimeError("TRANSFER_INPUT_REQUIRED")
            target(args.input, args.output)
    except Exception as exc:
        # Only error class is surfaced, never local DB paths, patient or secrets.
        print("RESTORE03_P4_LAB_FAIL:" + type(exc).__name__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
