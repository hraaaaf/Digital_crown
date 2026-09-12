import os
import uuid

import pytest
from sqlalchemy import create_engine, event, inspect, text

from backend import database


POSTGRES_URL = os.getenv("CABINET_COMPAT_POSTGRES_URL", "").strip()
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="CABINET_COMPAT_POSTGRES_URL is required for PostgreSQL cabinet compatibility certification",
)


def test_legacy_cabinet_schema_is_reconciled_additively_on_postgresql():
    schema = f"cabinet_compat_{uuid.uuid4().hex[:12]}"
    admin_engine = create_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))

    test_engine = create_engine(POSTGRES_URL)

    @event.listens_for(test_engine, "connect")
    def _set_search_path(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute(f'SET search_path TO "{schema}"')
        cursor.close()

    try:
        with test_engine.begin() as conn:
            conn.execute(text("CREATE TYPE paiementstatut AS ENUM ('EN_ATTENTE', 'PAYE', 'PARTIEL')"))
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR(255) NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE appointments (
                    id INTEGER PRIMARY KEY,
                    patient_id INTEGER,
                    datetime_start TIMESTAMP NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    employer_id INTEGER NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE actes (
                    id INTEGER PRIMARY KEY,
                    statut_paiement paiementstatut NOT NULL
                )
            """))
            conn.execute(text("INSERT INTO users (id, email) VALUES (1, 'owner@test.local')"))
            conn.execute(text("""
                INSERT INTO appointments
                    (id, patient_id, datetime_start, duration_minutes, employer_id)
                VALUES
                    (42, 7, '2026-09-01 09:00:00', 30, 1)
            """))
            conn.execute(text("INSERT INTO actes (id, statut_paiement) VALUES (9, 'PARTIEL')"))

        database.migrate_appointment_columns(bind=test_engine)
        database.migrate_payment_status_enum(bind=test_engine)
        # Second pass proves startup idempotence on the reconciled schema.
        database.migrate_appointment_columns(bind=test_engine)
        database.migrate_payment_status_enum(bind=test_engine)

        inspector = inspect(test_engine)
        columns = {column["name"]: column for column in inspector.get_columns("appointments")}
        indexes = {index["name"] for index in inspector.get_indexes("appointments")}
        foreign_keys = inspector.get_foreign_keys("appointments")

        assert "praticien_id" in columns
        assert columns["praticien_id"]["nullable"] is True
        assert "ix_appointments_praticien_id" in indexes
        assert any(
            fk.get("constrained_columns") == ["praticien_id"]
            and fk.get("referred_table") == "users"
            and str((fk.get("options") or {}).get("ondelete", "")).upper() == "SET NULL"
            for fk in foreign_keys
        )

        with test_engine.connect() as conn:
            appointment = conn.execute(text("""
                SELECT id, patient_id, employer_id, duration_minutes, praticien_id
                FROM appointments
                WHERE id = 42
            """)).mappings().one()
            enum_labels = conn.execute(text("""
                SELECT e.enumlabel
                FROM pg_type t
                JOIN pg_enum e ON e.enumtypid = t.oid
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE n.nspname = current_schema()
                  AND t.typname = 'paiementstatut'
                ORDER BY e.enumsortorder
            """)).scalars().all()
            existing_act_status = conn.execute(text(
                "SELECT statut_paiement::text FROM actes WHERE id = 9"
            )).scalar_one()

        assert dict(appointment) == {
            "id": 42,
            "patient_id": 7,
            "employer_id": 1,
            "duration_minutes": 30,
            "praticien_id": None,
        }
        assert enum_labels == ["EN_ATTENTE", "PAYE", "PARTIEL", "A_ENCAISSER"]
        assert existing_act_status == "PARTIEL"
    finally:
        test_engine.dispose()
        with admin_engine.connect() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin_engine.dispose()
