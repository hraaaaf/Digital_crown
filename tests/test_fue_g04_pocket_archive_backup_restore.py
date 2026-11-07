"""CPV2-02C: real SQLCipher backup/restore with Pocket receipt + encrypted media.

G04 automatically includes tests/test_fue_g04*.py on Windows and Ubuntu.
All data and all keys are fictitious; no production DB, migrations, or media.
These tests exercise EXISTING BackupService and GuidedRestoreArchive APIs.
"""
from __future__ import annotations

import hashlib
import io
import os
import secrets
import sqlite3
import uuid
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlcipher3 import dbapi2 as cipher

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService
from backend.services.guided_restore_archive import (
    _encrypt_streaming_media_archive,
    _extract_encrypted_media,
)
from backend.services.mobile_document_archive_receipts import (
    MobileDocumentArchiveReceipt,
    PocketReceiptBase,
    claim_archive_intent,
    complete_archive_in_current_transaction,
    read_scoped_receipt,
)

SCOPE = dict(tenant_id=91301, actor_id=91302, device_id="synthetic-paired-91303")
PATIENT = 91304
PDF = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n"
DIGEST = hashlib.sha256(PDF).hexdigest()

lab_meta = MetaData()
archive_links = Table(
    "synthetic_archive_links", lab_meta,
    Column("id", Integer, primary_key=True),
    Column("patient_id", Integer, nullable=False),
    Column("actor_id", Integer, nullable=False),
    Column("file_hash", String(64), nullable=False),
    Column("file_path", String(250), nullable=False),
)


def _open_cipher(path: Path, passphrase: str):
    connection = cipher.connect(str(path), timeout=12, check_same_thread=False)
    # Printed keys in CI logs are forbidden. Passphrases are generated and
    # remain entirely inside the disposable pytest process.
    connection.execute("PRAGMA key = '" + passphrase + "'")
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
    return connection


def _engine(path: Path, passphrase: str):
    # URL retains the actual isolated on-disk location; creator enforces
    # SQLCipher encryption on EVERY connection rather than using pysqlite.
    return create_engine(
        "sqlite:///" + str(path),
        creator=lambda: _open_cipher(path, passphrase),
        poolclass=NullPool,
    )


def _args(key: str):
    return dict(**SCOPE, key=key, patient_id=PATIENT,
                document_type="certificat", request_sha256="f" * 64)


@pytest.fixture
def synthetic_lab(tmp_path, monkeypatch):
    user_data = tmp_path / "isolated-vault"
    user_data.mkdir(mode=0o700)
    monkeypatch.setattr(
        AppPaths, "get_user_data_dir", staticmethod(lambda: user_data),
    )
    # Existing GuidedRestoreArchive streaming media encryption, with a
    # separate fictitious media master from the SQLCipher passphrase.
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "77" * 32)
    monkeypatch.setenv("SECRET_KEY", "fictitious-pocket-recovery-auth-key-32characters")
    passphrase = secrets.token_hex(32)
    source = tmp_path / "synthetic-only-source.db"
    engine = _engine(source, passphrase)
    PocketReceiptBase.metadata.create_all(engine)
    lab_meta.create_all(engine)
    pdf_root = tmp_path / "synthetic-media"
    (pdf_root / "archives").mkdir(parents=True)
    (pdf_root / "archives" / "fictional-certificate.pdf").write_bytes(PDF)

    completed_key, pending_key = str(uuid.uuid4()), str(uuid.uuid4())
    with Session(engine) as session:
        completed, fresh = claim_archive_intent(session, **_args(completed_key))
        assert fresh and completed.state == "PROCESSING"
        pending, fresh = claim_archive_intent(session, **_args(pending_key))
        assert fresh and pending.state == "PROCESSING"

        # Actual SQL receipt + synthetic link are committed atomically.
        session.info["_mobile_document_archive_receipt_id"] = completed.id
        new_doc = session.execute(archive_links.insert().values(
            patient_id=PATIENT, actor_id=SCOPE["actor_id"],
            file_hash=DIGEST, file_path="static/archives/fictional-certificate.pdf",
        ))
        document_id = new_doc.inserted_primary_key[0]
        complete_archive_in_current_transaction(
            session, archive=SimpleNamespace(
                id=document_id, patient_id=PATIENT,
                uploaded_by_id=SCOPE["actor_id"], file_hash=DIGEST,
            ),
        )
        session.commit()

    # Verify source is genuinely encrypted (not a renamed SQLite plaintext DB).
    assert source.read_bytes()[:16] != b"SQLite format 3\\x00"
    with pytest.raises(sqlite3.DatabaseError):
        with sqlite3.connect(source) as plain:
            plain.execute("SELECT name FROM sqlite_master").fetchall()

    # Existing production SQLCipher export -> Fernet atomic encrypted backup.
    snapshot = tmp_path / "synthetic-snapshot.db"
    BackupService._export_sqlcipher_snapshot(source, snapshot, passphrase)
    suite = BackupService._get_or_create_key()
    backup = tmp_path / "synthetic-database.db.enc"
    BackupService._encrypt_file_atomic(snapshot, backup, suite)
    assert backup.read_bytes() != snapshot.read_bytes()
    assert not backup.read_bytes().startswith(b"SQLite format 3")

    # Existing GuidedRestoreArchive media encryption is a separate operation:
    # database-only backup DOES NOT imply media was captured.
    media_zip = tmp_path / "synthetic-media.zip"
    with zipfile.ZipFile(media_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(
            pdf_root / "archives" / "fictional-certificate.pdf",
            arcname="archives/fictional-certificate.pdf",
        )
    media_backup = tmp_path / "synthetic-media.zip.enc"
    _encrypt_streaming_media_archive(media_zip, media_backup)
    assert PDF not in media_backup.read_bytes()

    engine.dispose()
    yield {
        "root": tmp_path, "source": source, "snapshot": snapshot,
        "db_backup": backup, "media_backup": media_backup,
        "passphrase": passphrase, "completed": completed_key,
        "processing": pending_key, "document_id": document_id,
    }


def test_restored_sqlcipher_receipt_keeps_exactly_one_archive_and_processing_lock(synthetic_lab):
    lab = synthetic_lab
    # Synthetic disaster: intentionally destroy ONLY fixture originals after
    # both encrypted backups have been successfully produced.
    lab["source"].write_bytes(b"FICTIONAL_LOST_SOURCE_DATA")
    (lab["root"] / "synthetic-media" / "archives" / "fictional-certificate.pdf").unlink()

    restored = lab["root"] / "restored-synthetic-only.db"
    BackupService.restore_backup(
        lab["db_backup"], restored, verify_sqlcipher=True,
        passphrase=lab["passphrase"],
    )
    assert restored.is_file()
    assert restored.read_bytes()[:16] != b"SQLite format 3\\x00"

    # SQLCipher integrity on a fresh native connection.
    with _open_cipher(restored, lab["passphrase"]) as raw:
        assert raw.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    engine = _engine(restored, lab["passphrase"])
    try:
        with Session(engine) as session:
            complete = read_scoped_receipt(
                session, **SCOPE, key=lab["completed"],
            )
            processing = read_scoped_receipt(
                session, **SCOPE, key=lab["processing"],
            )
            assert complete.state == "COMPLETED"
            assert complete.archive_id == lab["document_id"]
            assert complete.archive_sha256 == DIGEST
            assert processing.state == "PROCESSING" and processing.archive_id is None
            assert session.query(func.count(MobileDocumentArchiveReceipt.id)).scalar() == 2
            row = session.execute(select(archive_links)).one()
            assert row.patient_id == PATIENT and row.actor_id == SCOPE["actor_id"]
            assert row.file_hash == DIGEST and row.file_path.startswith("static/archives/")

            # Restoring does not create an authorization to replay.
            prior, created = claim_archive_intent(session, **_args(lab["completed"]))
            assert not created and prior.archive_id == lab["document_id"]
            unresolved, created = claim_archive_intent(session, **_args(lab["processing"]))
            assert not created and unresolved.state == "PROCESSING"
            assert session.query(func.count(archive_links.c.id)).scalar() == 1
    finally:
        engine.dispose()

    # A restored database without media is NOT a restored clinical document.
    media_dest = lab["root"] / "restored-media"
    assert not (media_dest / "archives" / "fictional-certificate.pdf").exists()
    _extract_encrypted_media(lab["media_backup"], media_dest)
    recovered_pdf = media_dest / "archives" / "fictional-certificate.pdf"
    assert recovered_pdf.read_bytes() == PDF
    assert hashlib.sha256(recovered_pdf.read_bytes()).hexdigest() == DIGEST


def test_wrong_key_or_corrupt_encrypted_backup_never_overwrites_destination(synthetic_lab):
    lab = synthetic_lab
    existing = lab["root"] / "never-overwrite.db"
    original_marker = b"EXISTING_SYNTHETIC_DESTINATION_MUST_BE_PRESERVED"
    existing.write_bytes(original_marker)
    with pytest.raises(Exception):
        BackupService.restore_backup(
            lab["db_backup"], existing, verify_sqlcipher=True,
            passphrase="definitely-the-wrong-sqlcipher-passphrase",
        )
    assert existing.read_bytes() == original_marker

    damaged = lab["root"] / "tampered-db.enc"
    encrypted = bytearray(lab["db_backup"].read_bytes())
    encrypted[len(encrypted) // 2] ^= 0x01
    damaged.write_bytes(bytes(encrypted))
    with pytest.raises(Exception):
        BackupService.restore_backup(
            damaged, existing, verify_sqlcipher=True,
            passphrase=lab["passphrase"],
        )
    assert existing.read_bytes() == original_marker

    corrupt_media = lab["root"] / "tampered-media.enc"
    ciphertext = bytearray(lab["media_backup"].read_bytes())
    ciphertext[len(ciphertext) // 2] ^= 0x01
    corrupt_media.write_bytes(bytes(ciphertext))
    media_target = lab["root"] / "never-extract-corrupt-media"
    with pytest.raises(Exception):
        _extract_encrypted_media(corrupt_media, media_target)
    assert not media_target.exists()
