"""F05-R1: prove additive Alembic upgrade preserves legacy receipts in PostgreSQL.

Never touches a cabinet or real data: asserts exact disposable CI database,
creates a dedicated PostgreSQL schema inside a transaction, then ROLLBACKs.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

assert os.environ.get("ENVIRONMENT") == "test"
assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
assert os.environ.get("PG_CERT_LAB") == "1"
assert os.environ.get("DATABASE_URL", "").startswith("postgresql+psycopg://")
assert os.environ["DATABASE_URL"].endswith("/dc_agenda_synthetic")

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text


def main() -> None:
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            version = connection.execute(text("SHOW server_version")).scalar_one()
            assert version.startswith("16."), version
            assert connection.execute(text("SELECT current_database()")).scalar_one() == "dc_agenda_synthetic"

            connection.execute(text("CREATE SCHEMA f05_r1_migration_probe"))
            connection.execute(text("SET LOCAL search_path TO f05_r1_migration_probe, public"))
            connection.execute(text(
                "CREATE TABLE patient_companion_remote_receipts ("
                "id BIGINT PRIMARY KEY, access_id INTEGER NOT NULL,"
                "message_id VARCHAR(36) NOT NULL,"
                "idempotency_key VARCHAR(36) NOT NULL,"
                "operation VARCHAR(64) NOT NULL,"
                "status VARCHAR(16) NOT NULL,"
                "response_json TEXT)"
            ))
            connection.execute(text(
                "INSERT INTO patient_companion_remote_receipts "
                "(id, access_id, message_id, idempotency_key, operation, status, response_json) "
                "VALUES (1, 9, 'old-message', 'old-idem', 'agenda.create', 'ACCEPTED', '{\"status\":\"confirmed\"}')"
            ))

            migration = Path(__file__).resolve().parents[2] / (
                "alembic/versions/f05r0000032_bind_patient_companion_receipt_intent.py"
            )
            spec = importlib.util.spec_from_file_location("f05_r1_additive_revision", migration)
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert module.down_revision == "neo000000031"
            context = MigrationContext.configure(connection)
            module.op = Operations(context)
            module.upgrade()
            row = connection.execute(text(
                "SELECT id, intent_sha256, response_json "
                "FROM patient_companion_remote_receipts WHERE id = 1"
            )).one()
            assert row.id == 1 and row.intent_sha256 is None
            assert row.response_json == '{"status":"confirmed"}'
            connection.execute(text(
                "INSERT INTO patient_companion_remote_receipts "
                "(id, access_id, message_id, idempotency_key, operation, status, intent_sha256) "
                "VALUES (2, 9, 'new-message', 'new-idem', 'agenda.create', 'ACCEPTED', :fingerprint)"
            ), {"fingerprint": "a" * 64})
            assert connection.execute(text(
                "SELECT intent_sha256 FROM patient_companion_remote_receipts WHERE id = 2"
            )).scalar_one() == "a" * 64
            print("F05_R1_PG_MIGRATION", "ADDITIVE", "LEGACY_PRESERVED",
                  "NULL_LEGACY_FAIL_CLOSED", "NEW_FINGERPRINT_WRITABLE", flush=True)
        finally:
            # A second-level synthetic schema is created and destroyed as one
            # transaction. Nothing is persisted even in the isolated CI DB.
            transaction.rollback()
    with engine.connect() as connection:
        assert connection.execute(text(
            "SELECT count(*) FROM information_schema.schemata "
            "WHERE schema_name='f05_r1_migration_probe'"
        )).scalar_one() == 0
    print("F05_R1_PG_MIGRATION_ROLLBACK", "CLEAN", flush=True)


if __name__ == "__main__":
    main()
