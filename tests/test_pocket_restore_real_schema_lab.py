"""CPV2-02C J6: real-schema SQLCipher + Pocket receipts + both PDF trees.

Isolated FUE ONLY. Production portable-bundle conversion, guided-restore
preflight and worker DB/media swap+rescue primitives on disposable fixtures.
NEVER call GuidedRestoreWorker.run/request_apply or touch real cabinet data.
"""
from __future__ import annotations

import hashlib
import secrets
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlcipher3 import dbapi2 as cipher

from backend import models
from backend.core.paths import AppPaths
from backend.core.runtime_safety import database_target_fingerprint
from backend.services.cabinet_bundle import CabinetBundleService, _export_sqlcipher_plaintext
from backend.services.guided_restore import GuidedRestoreService
from backend.services.guided_restore_archive import _directory_digest
from backend.services.guided_restore_worker import GuidedRestoreWorker
from backend.services.mobile_document_archive_forensics import inspect_archive_receipt_read_only
from backend.services.mobile_document_archive_receipts import (
    MobileDocumentArchiveReceipt,
    PocketReceiptBase,
    claim_archive_intent,
    complete_archive_in_current_transaction,
    read_scoped_receipt,
)

OWNER = 97801
PATIENT = 97802
DEVICE = "fictional-pocket-paired"
PDF = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n"
UNRESOLVED_PDF = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%unresolved-test-only\n%%EOF\n"


def _engine(db_file: Path, sqlcipher_passphrase: str):
    def create():
        conn = cipher.connect(str(db_file), check_same_thread=False, timeout=12)
        conn.execute("PRAGMA key = '" + sqlcipher_passphrase + "'")
        conn.execute("SELECT count(*) FROM sqlite_master")
        return conn

    return create_engine(
        "sqlite:///" + str(db_file), creator=create, poolclass=NullPool,
    )


def _db_args(key: str) -> dict:
    return dict(
        tenant_id=OWNER, actor_id=OWNER, device_id=DEVICE, key=key,
        patient_id=PATIENT, document_type="certificat", request_sha256="a" * 64,
    )


def test_portable_sqlcipher_actual_archive_receipt_both_media_trees_and_rollback(
    tmp_path, monkeypatch,
):
    """Real DocumentArchive, durable receipt, portable conversion and manual rollback."""
    vault = tmp_path / "fixture-only-private-vault"
    vault.mkdir(mode=0o700)
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: vault))
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SECRET_KEY", "fixture-only-authentication-key-not-for-cabinet")
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "74" * 32)
    passphrase = secrets.token_hex(32)
    monkeypatch.setenv("SQLCIPHER_KEY_HEX", passphrase)
    assert not GuidedRestoreService.runtime_apply_supported()

    original_db = tmp_path / "disposable-source.sqlcipher"
    engine = _engine(original_db, passphrase)
    models.Base.metadata.create_all(
        engine,
        tables=[models.User.__table__, models.Patient.__table__, models.DocumentArchive.__table__],
    )
    PocketReceiptBase.metadata.create_all(engine)
    complete_key, unresolved_key = str(uuid.uuid4()), str(uuid.uuid4())
    canonical = "archives/97802/certificat/2026/11/fictional-certified.pdf"
    historical = "documents/2026/11/fictional-certified.pdf"
    orphan_canonical = "archives/97802/certificat/2026/11/fictional-unresolved.pdf"
    orphan_legacy = "documents/2026/11/fictional-unresolved.pdf"
    media_source = tmp_path / "fixture-media-source"
    for relative, content in (
        (canonical, PDF), (historical, PDF),
        (orphan_canonical, UNRESOLVED_PDF), (orphan_legacy, UNRESOLVED_PDF),
    ):
        path = media_source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    initial_media_digest = _directory_digest(media_source)
    assert initial_media_digest["files"] == 4

    with Session(engine) as db:
        db.add(models.User(
            id=OWNER, email="fictional@example.invalid",
            hashed_password="not-valid-test-login", role=models.UserRole.DENTISTE,
        ))
        db.add(models.Patient(
            id=PATIENT, employer_id=OWNER, nom="FICTIF", prenom="TEST",
            sexe="F", date_naissance=datetime(1999, 1, 1),
        ))
        db.commit()
        complete, created = claim_archive_intent(db, **_db_args(complete_key))
        assert created and complete.state == "PROCESSING"
        unresolved, created = claim_archive_intent(db, **_db_args(unresolved_key))
        assert created and unresolved.state == "PROCESSING"
        document = models.DocumentArchive(
            patient_id=PATIENT, uploaded_by_id=OWNER,
            document_type=models.DocumentType.CERTIFICAT,
            filename="fictional-certified.pdf", original_filename="fictional-certified.pdf",
            document_group_id=str(uuid.uuid4()), version_number=1,
            is_latest_version=True, file_hash=hashlib.sha256(PDF).hexdigest(),
            file_size=len(PDF), file_path="static/" + canonical,
            status=models.DocumentStatus.ACTIF, clinical_data={}, tags=[],
        )
        db.add(document)
        db.flush()
        original_document_id = document.id
        db.info["_mobile_document_archive_receipt_id"] = complete.id
        complete_archive_in_current_transaction(db, archive=document)
        db.commit()
    engine.dispose()
    assert original_db.read_bytes()[:16] != b"SQLite format 3\x00"
    with sqlite3.connect(original_db) as plain:
        with pytest.raises(sqlite3.DatabaseError):
            plain.execute("SELECT name FROM sqlite_master").fetchall()

    # Actual production portable-bundle exporter + guided restore conversion.
    portable_plain = tmp_path / "fictional-portable-source.sqlite"
    _export_sqlcipher_plaintext(original_db, portable_plain, passphrase)
    assert portable_plain.read_bytes().startswith(b"SQLite format 3\x00")
    portable = tmp_path / "fictional-export.dcbundle"
    secret = secrets.token_urlsafe(32)
    bundle = CabinetBundleService.create_bundle(
        portable, secret, database_path=portable_plain, media_root=media_source,
    )
    assert bundle["media_file_count"] == 4
    assert PDF not in portable.read_bytes() and UNRESOLVED_PDF not in portable.read_bytes()
    guided_package = tmp_path / "fictional-guided-restore.zip"
    converted = CabinetBundleService.to_local_guided_restore_archive(
        portable, secret, guided_package,
        active_engine=("sqlite", "pysqlcipher"),
    )
    assert converted["media_file_count"] == 4
    preflight = GuidedRestoreService.preflight_file(
        guided_package, original_name="fictional-guided-restore.zip",
        active_engine=("sqlite", "pysqlcipher"), owner_employer_id=OWNER,
    )
    assert preflight["status"] == "preflight_ready"
    assert preflight["compatible"] and preflight["restore_media"]
    assert preflight["media_file_count"] == 4 and not preflight["errors"]
    job = GuidedRestoreService.get_job(preflight["restore_id"])
    GuidedRestoreService._verify_staged_job(job)
    staging = GuidedRestoreService.job_dir(preflight["restore_id"])
    assert job["owner_employer_id"] == OWNER

    # Apply on a disposable target with exact production worker primitives.
    target_db = tmp_path / "isolated-target.sqlcipher"
    shutil.copyfile(original_db, target_db)
    raw = cipher.connect(str(target_db))
    try:
        raw.execute("PRAGMA key = '" + passphrase + "'")
        raw.execute("CREATE TABLE old_state_only(marker TEXT NOT NULL)")
        raw.execute("INSERT INTO old_state_only(marker) VALUES ('RESCUE_ONLY')")
        raw.commit()
    finally:
        raw.close()
    rescue_database_dir = tmp_path / "db-rescue"
    rescued = GuidedRestoreWorker._rescue_database(target_db, rescue_database_dir)
    assert "clinical_vault.db" in rescued
    GuidedRestoreWorker._verify_database_rescue(rescue_database_dir, "pysqlcipher")
    restored_media = tmp_path / "isolated-target-media"
    restored_media.mkdir()
    (restored_media / "preexisting-test.txt").write_bytes(b"original fake media")
    original_target_media_digest = _directory_digest(restored_media)
    rescued_media = tmp_path / "media-rescue"
    GuidedRestoreWorker._apply_database(
        staging / "database.enc", target_db, "pysqlcipher",
    )
    GuidedRestoreWorker._apply_media(
        staging / "media.enc", restored_media, rescued_media,
        original_target_media_digest,
    )
    assert _directory_digest(restored_media) == initial_media_digest
    assert _directory_digest(rescued_media) == original_target_media_digest
    assert not (restored_media / "preexisting-test.txt").exists()
    for relative, expected in (
        (canonical, PDF), (historical, PDF),
        (orphan_canonical, UNRESOLVED_PDF), (orphan_legacy, UNRESOLVED_PDF),
    ):
        assert (restored_media / relative).read_bytes() == expected

    db_url = "sqlite:///" + str(target_db)
    monkeypatch.setenv(
        "DIGITALCROWN_ISOLATION_DB_FINGERPRINT", database_target_fingerprint(db_url),
    )
    restored_engine = _engine(target_db, passphrase)
    try:
        with Session(restored_engine) as db:
            assert db.scalar(select(func.count()).select_from(models.DocumentArchive)) == 1
            assert db.scalar(select(func.count()).select_from(MobileDocumentArchiveReceipt)) == 2
            doc = db.get(models.DocumentArchive, original_document_id)
            assert doc is not None and doc.patient_id == PATIENT
            assert doc.file_path == "static/" + canonical
            assert doc.file_hash == hashlib.sha256((restored_media / canonical).read_bytes()).hexdigest()
            assert doc.file_hash == hashlib.sha256((restored_media / historical).read_bytes()).hexdigest()
            scope = dict(tenant_id=OWNER, actor_id=OWNER, device_id=DEVICE)
            completed = read_scoped_receipt(db, **scope, key=complete_key)
            pending = read_scoped_receipt(db, **scope, key=unresolved_key)
            assert completed.archive_id == doc.id and completed.state == "COMPLETED"
            assert pending.archive_id is None and pending.state == "PROCESSING"
            assert inspect_archive_receipt_read_only(
                db, **scope, key=complete_key, media_root=restored_media,
            )["decision"] == "EXISTING_ARCHIVE_VERIFIED"
            pending_verdict = inspect_archive_receipt_read_only(
                db, **scope, key=unresolved_key, media_root=restored_media,
            )
            assert pending_verdict == {
                "receipt_state": "PROCESSING", "verified_archive": False,
                "automatic_replay_allowed": False, "decision": "HOLD_FOR_MANUAL_REVIEW",
            }
            existing, claimed = claim_archive_intent(db, **_db_args(unresolved_key))
            assert not claimed and existing.id == pending.id
            assert db.scalar(select(func.count()).select_from(models.DocumentArchive)) == 1
    finally:
        restored_engine.dispose()

    # Real rescue primitives return both DB and media to their pre-restore state.
    GuidedRestoreWorker._rollback_media(restored_media, rescued_media)
    GuidedRestoreWorker._restore_database_from_rescue(target_db, rescue_database_dir)
    assert _directory_digest(restored_media) == original_target_media_digest
    assert (restored_media / "preexisting-test.txt").read_bytes() == b"original fake media"
    check = cipher.connect(str(target_db))
    try:
        check.execute("PRAGMA key = '" + passphrase + "'")
        assert check.execute("SELECT marker FROM old_state_only").fetchone()[0] == "RESCUE_ONLY"
        assert check.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        check.close()

    # Modified live media must fail closed: no silent overwrite or orphan deletion.
    (restored_media / "preexisting-test.txt").write_bytes(b"new fake media mutation")
    with pytest.raises(RuntimeError, match="Médias modifiés"):
        GuidedRestoreWorker._apply_media(
            staging / "media.enc", restored_media, rescued_media,
            original_target_media_digest,
        )
    assert (restored_media / "preexisting-test.txt").read_bytes() == b"new fake media mutation"
    assert not rescued_media.exists()
