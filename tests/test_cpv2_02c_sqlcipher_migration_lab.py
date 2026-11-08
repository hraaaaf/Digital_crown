"""CPV2-02C: offline additive SQLCipher migration rehearsal, fictional-only.

No application migration endpoint, cabinet DB, real patients or media.
The optional independent-review step is not required to execute this lab.
"""
from __future__ import annotations

import hashlib
import secrets
import shutil
import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlcipher3 import dbapi2 as cipher

from backend.services.mobile_document_archive_receipts import (
    MobileDocumentArchiveReceipt, assert_receipt_schema, claim_archive_intent,
)

LEGACY_MARKER = "FICTIONAL_OLD_RECORD_NOT_A_PATIENT"
SCOPE = dict(tenant_id=94001, actor_id=94002, device_id="fictional-pocket-device")


def _engine(path: Path, key: str):
    def open_cipher():
        db = cipher.connect(str(path), timeout=2, check_same_thread=False)
        db.execute("PRAGMA key = '" + key + "'")  # secrets.token_hex only
        db.execute("PRAGMA busy_timeout = 250")
        db.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return db
    return create_engine("sqlite:///" + str(path), creator=open_cipher, poolclass=NullPool)


@pytest.fixture
def old_encrypted_fixture(tmp_path):
    path, key = tmp_path / "fictional-old-cabinet.db", secrets.token_hex(32)
    engine = _engine(path, key)
    with engine.connect() as c:
        c.exec_driver_sql("BEGIN IMMEDIATE")
        c.exec_driver_sql("CREATE TABLE legacy_patients (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)")
        c.exec_driver_sql("INSERT INTO legacy_patients VALUES (1, ?)", (LEGACY_MARKER,))
        c.exec_driver_sql("PRAGMA user_version = 63")
        c.commit()
    engine.dispose()
    assert path.read_bytes()[:16] != b"SQLite format 3\x00"
    with pytest.raises(sqlite3.DatabaseError):
        with sqlite3.connect(str(path)) as plain:
            plain.execute("SELECT count(*) FROM sqlite_master").fetchone()
    return path, key


def _oracle(engine):
    with engine.connect() as c:
        assert c.exec_driver_sql("PRAGMA integrity_check").scalar_one() == "ok"
        assert c.exec_driver_sql("PRAGMA user_version").scalar_one() == 63
        assert c.exec_driver_sql("SELECT marker FROM legacy_patients WHERE id=1").scalar_one() == LEGACY_MARKER


def _disabled(engine):
    with Session(engine) as session:
        with pytest.raises(HTTPException) as err:
            assert_receipt_schema(session)
        assert err.value.status_code == 503


def _dba_fixture_only(engine):
    """Manual, scoped, rollback-capable SQL transaction on an isolated fixture.

    Never make this function reachable from the Pocket runtime or CLI.
    """
    with engine.connect() as c:
        if inspect(c).has_table(MobileDocumentArchiveReceipt.__tablename__):
            raise RuntimeError("EXISTING_RECEIPT_TABLE_REQUIRES_MANUAL_RECONCILIATION")
        c.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            MobileDocumentArchiveReceipt.__table__.create(c, checkfirst=False)
            c.commit()
        except BaseException:
            c.rollback()
            raise


def test_additive_migration_preserves_legacy_and_allows_unique_durable_lock(old_encrypted_fixture):
    path, key = old_encrypted_fixture
    before_backup = path.with_suffix(".pre-migration.enc")
    shutil.copy2(path, before_backup)  # only after closing fixture's SQLCipher connections
    original_sha = hashlib.sha256(before_backup.read_bytes()).hexdigest()
    engine = _engine(path, key)
    _oracle(engine)
    _disabled(engine)
    assert not inspect(engine).has_table(MobileDocumentArchiveReceipt.__tablename__)
    _dba_fixture_only(engine)
    with Session(engine) as session:
        assert_receipt_schema(session)
    _oracle(engine)
    assert {c["name"] for c in inspect(engine).get_columns(MobileDocumentArchiveReceipt.__tablename__)} == {
        column.name for column in MobileDocumentArchiveReceipt.__table__.columns
    }
    intent = dict(**SCOPE, key=str(uuid.uuid4()), patient_id=94003,
                  document_type="certificat", request_sha256="a" * 64)
    with Session(engine) as session:
        receipt, created = claim_archive_intent(session, **intent)
        assert created and receipt.state == "PROCESSING" and receipt.archive_id is None
        receipt_id = receipt.id
    with Session(engine) as session:
        prior, created = claim_archive_intent(session, **intent)
        assert not created and prior.id == receipt_id
        with pytest.raises(HTTPException) as error:
            claim_archive_intent(session, **{**intent, "request_sha256": "b" * 64})
        assert error.value.status_code == 409
    engine.dispose()

    assert hashlib.sha256(before_backup.read_bytes()).hexdigest() == original_sha
    restored = path.with_suffix(".restored-before.db")
    shutil.copy2(before_backup, restored)
    original = _engine(restored, key)
    _oracle(original)
    _disabled(original)
    assert not inspect(original).has_table(MobileDocumentArchiveReceipt.__tablename__)
    original.dispose()

    reopened = _engine(path, key)
    _oracle(reopened)
    with Session(reopened) as session:
        old, created = claim_archive_intent(session, **intent)
        assert not created and old.state == "PROCESSING" and old.archive_id is None
    reopened.dispose()


def test_operator_cancellation_rolls_back_new_table(old_encrypted_fixture):
    path, key = old_encrypted_fixture
    engine = _engine(path, key)
    with engine.connect() as c:
        c.exec_driver_sql("BEGIN IMMEDIATE")
        MobileDocumentArchiveReceipt.__table__.create(c, checkfirst=False)
        assert inspect(c).has_table(MobileDocumentArchiveReceipt.__tablename__)
        c.rollback()  # synthetic operator cancellation before COMMIT
    _oracle(engine)
    _disabled(engine)
    assert not inspect(engine).has_table(MobileDocumentArchiveReceipt.__tablename__)
    engine.dispose()


def test_incomplete_existing_schema_is_not_repaired_implicitly(old_encrypted_fixture):
    path, key = old_encrypted_fixture
    engine = _engine(path, key)
    with engine.begin() as c:
        c.exec_driver_sql(
            "CREATE TABLE mobile_document_archive_receipts "
            "(id VARCHAR(36) PRIMARY KEY, tenant_id INTEGER NOT NULL)"
        )
    _disabled(engine)
    with pytest.raises(RuntimeError, match="EXISTING_RECEIPT_TABLE"):
        _dba_fixture_only(engine)
    assert {c["name"] for c in inspect(engine).get_columns("mobile_document_archive_receipts")} == {
        "id", "tenant_id"
    }
    _oracle(engine)
    engine.dispose()


def test_wrong_key_preserves_original_encrypted_copy(old_encrypted_fixture):
    path, key = old_encrypted_fixture
    original = hashlib.sha256(path.read_bytes()).hexdigest()
    wrong = _engine(path, secrets.token_hex(32))
    with pytest.raises(cipher.DatabaseError):
        with wrong.connect() as c:
            c.exec_driver_sql("SELECT count(*) FROM sqlite_master")
    wrong.dispose()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original
    valid = _engine(path, key)
    _oracle(valid)
    _disabled(valid)
    valid.dispose()


def test_scope_uniqueness_present_in_real_sqlcipher(old_encrypted_fixture):
    path, key = old_encrypted_fixture
    engine = _engine(path, key)
    _dba_fixture_only(engine)
    unique = inspect(engine).get_unique_constraints(MobileDocumentArchiveReceipt.__tablename__)
    assert any(set(c["column_names"]) == {
        "tenant_id", "actor_id", "device_id", "idempotency_key"
    } for c in unique)
    _oracle(engine)
    engine.dispose()
