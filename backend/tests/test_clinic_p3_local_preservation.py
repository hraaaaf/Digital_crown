from __future__ import annotations

import hashlib
import os
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, inspect, text

from backend import models
from backend.models_document_provenance_p3 import _migrate_existing_document_archives
from backend.services import document_signature_p3 as signature_service


class _User(SimpleNamespace):
    def get_employer_id(self) -> int:
        return self.employer_id if self.employer_id is not None else self.id


class _PersistingDB:
    """Minimal adapter that persists only the P3 signature metadata under test."""

    def __init__(self, engine, doc):
        self.engine = engine
        self.doc = doc
        self.commit_count = 0
        self.refresh_count = 0

    def commit(self):
        self.commit_count += 1
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE document_archives "
                    "SET signed_by_practitioner_id = :signer, signed_at = :signed_at "
                    "WHERE id = :document_id"
                ),
                {
                    "signer": self.doc.signed_by_practitioner_id,
                    "signed_at": self.doc.signed_at,
                    "document_id": self.doc.id,
                },
            )

    def refresh(self, _obj):
        self.refresh_count += 1


def test_p3_additive_migration_and_signature_preserve_historical_archive_bytes(tmp_path, monkeypatch):
    """Rehearse P3 over a populated pre-P3 archive without rewriting historical bytes."""
    media_root = tmp_path / "media"
    relative_path = "archives/101/ORDONNANCE/2026/9/historic-preserved.pdf"
    physical_file = media_root / relative_path
    physical_file.parent.mkdir(parents=True)
    original_bytes = b"%PDF-1.4\nDIGITAL-CROWN-P3-PRESERVATION\n%%EOF\n"
    physical_file.write_bytes(original_bytes)
    original_hash = hashlib.sha256(original_bytes).hexdigest()
    original_size = len(original_bytes)
    monkeypatch.setattr(signature_service, "MEDIA_DIR", media_root)

    db_path = tmp_path / "historic-cabinet-copy.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text(
            "CREATE TABLE document_archives ("
            "id INTEGER PRIMARY KEY, "
            "patient_id INTEGER NOT NULL, "
            "file_hash TEXT NOT NULL, "
            "file_size INTEGER NOT NULL, "
            "file_path TEXT NOT NULL, "
            "status TEXT NOT NULL)"
        ))
        connection.execute(text("INSERT INTO users (id) VALUES (1)"))
        connection.execute(
            text(
                "INSERT INTO document_archives "
                "(id, patient_id, file_hash, file_size, file_path, status) "
                "VALUES (7, 101, :file_hash, :file_size, :file_path, 'ACTIF')"
            ),
            {
                "file_hash": original_hash,
                "file_size": original_size,
                "file_path": f"static/{relative_path}",
            },
        )

        before = connection.execute(text(
            "SELECT id, patient_id, file_hash, file_size, file_path, status "
            "FROM document_archives WHERE id = 7"
        )).mappings().one()

        _migrate_existing_document_archives(None, connection)
        _migrate_existing_document_archives(None, connection)

        columns = {column["name"] for column in inspect(connection).get_columns("document_archives")}
        assert {"author_practitioner_id", "signed_by_practitioner_id", "signed_at"}.issubset(columns)

        after_migration = connection.execute(text(
            "SELECT id, patient_id, file_hash, file_size, file_path, status, "
            "author_practitioner_id, signed_by_practitioner_id, signed_at "
            "FROM document_archives WHERE id = 7"
        )).mappings().one()

        assert tuple(after_migration[key] for key in before.keys()) == tuple(before.values())
        assert after_migration["author_practitioner_id"] is None
        assert after_migration["signed_by_practitioner_id"] is None
        assert after_migration["signed_at"] is None

        # Explicitly model a newly attributed P3 document. Historical rows were proven
        # above to remain NULL and are never silently backfilled.
        connection.execute(text(
            "UPDATE document_archives SET author_practitioner_id = 1 WHERE id = 7"
        ))

    assert physical_file.read_bytes() == original_bytes
    assert hashlib.sha256(physical_file.read_bytes()).hexdigest() == original_hash

    doc = SimpleNamespace(
        id=7,
        file_path=f"static/{relative_path}",
        file_hash=original_hash,
        file_size=original_size,
        status=models.DocumentStatus.ACTIF,
        author_practitioner_id=1,
        signed_by_practitioner_id=None,
        signed_at=None,
    )
    user = _User(
        id=1,
        employer_id=None,
        role=models.UserRole.DENTISTE,
        is_active=True,
        approval_status=models.ApprovalStatus.APPROVED.value,
    )
    db = _PersistingDB(engine, doc)

    signature_service.sign_document(db, doc, user)

    with engine.begin() as connection:
        signed = connection.execute(text(
            "SELECT id, patient_id, file_hash, file_size, file_path, status, "
            "author_practitioner_id, signed_by_practitioner_id, signed_at "
            "FROM document_archives WHERE id = 7"
        )).mappings().one()

    assert signed["id"] == before["id"]
    assert signed["patient_id"] == before["patient_id"]
    assert signed["file_hash"] == before["file_hash"] == original_hash
    assert signed["file_size"] == before["file_size"] == original_size
    assert signed["file_path"] == before["file_path"]
    assert signed["status"] == before["status"]
    assert signed["author_practitioner_id"] == 1
    assert signed["signed_by_practitioner_id"] == 1
    assert signed["signed_at"] is not None
    assert db.commit_count == 1
    assert db.refresh_count == 1

    assert physical_file.read_bytes() == original_bytes
    assert hashlib.sha256(physical_file.read_bytes()).hexdigest() == original_hash


def test_p3_postgres18_additive_migration_preserves_historical_row_without_backfill():
    """Exercise the same pre-P3 ALTER TABLE contract on the cabinet PostgreSQL dialect."""
    database_url = os.getenv("P3_PRESERVATION_POSTGRES_URL")
    if not database_url:
        pytest.skip("P3_PRESERVATION_POSTGRES_URL is only provided by the PostgreSQL 18 gate")

    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS document_archives CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
            connection.execute(text(
                "CREATE TABLE document_archives ("
                "id INTEGER PRIMARY KEY, "
                "patient_id INTEGER NOT NULL, "
                "file_hash TEXT NOT NULL, "
                "file_size INTEGER NOT NULL, "
                "file_path TEXT NOT NULL, "
                "status TEXT NOT NULL)"
            ))
            connection.execute(text("INSERT INTO users (id) VALUES (1)"))
            connection.execute(text(
                "INSERT INTO document_archives "
                "(id, patient_id, file_hash, file_size, file_path, status) "
                "VALUES (17, 201, 'postgres-historic-hash', 1234, "
                "'static/archives/201/historic.pdf', 'ACTIF')"
            ))

            before = connection.execute(text(
                "SELECT id, patient_id, file_hash, file_size, file_path, status "
                "FROM document_archives WHERE id = 17"
            )).mappings().one()

            _migrate_existing_document_archives(None, connection)
            _migrate_existing_document_archives(None, connection)

            after = connection.execute(text(
                "SELECT id, patient_id, file_hash, file_size, file_path, status, "
                "author_practitioner_id, signed_by_practitioner_id, signed_at "
                "FROM document_archives WHERE id = 17"
            )).mappings().one()

            assert tuple(after[key] for key in before.keys()) == tuple(before.values())
            assert after["author_practitioner_id"] is None
            assert after["signed_by_practitioner_id"] is None
            assert after["signed_at"] is None

            columns = {column["name"] for column in inspect(connection).get_columns("document_archives")}
            assert {"author_practitioner_id", "signed_by_practitioner_id", "signed_at"}.issubset(columns)
    finally:
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS document_archives CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        engine.dispose()
