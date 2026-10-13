"""Alembic-only guard for append-only print audit/evidence tables.

Versioned schema DDL and the genuinely-empty DB baselines BOTH invoke this
helper. No application startup, HTTP route or print worker may call it.

These triggers reject UPDATE/DELETE, plus PostgreSQL TRUNCATE, by ordinary SQL roles. PostgreSQL
database superusers/DDL owners can still remove a trigger, so this is NOT an
independent tamper-proof ledger or a replacement for DB backups/access audit.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection

PROTECTED_PRINT_AUDITS = (
    "station_print_config_audit",
    "station_print_claim_events",
    "station_print_device_evidence",
    "station_print_uncertain_reviews",
)

# The following SQL uses only hard-coded internal table and trigger names.
def install_append_only_print_audit_guards(connection: Connection) -> None:
    dialect = connection.dialect.name
    if dialect == "postgresql":
        connection.execute(text("""
            CREATE OR REPLACE FUNCTION dc_reject_print_audit_mutation()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                RAISE EXCEPTION 'DC_PRINT_AUDIT_APPEND_ONLY'
                    USING ERRCODE = '23514';
            END
            $$
        """))
        for table in PROTECTED_PRINT_AUDITS:
            for operation in ("UPDATE", "DELETE"):
                name = f"dc_immutable_{table}_{operation.lower()}"
                connection.execute(text(
                    f'CREATE OR REPLACE TRIGGER "{name}" '
                    f'BEFORE {operation} ON "{table}" FOR EACH ROW '
                    'EXECUTE FUNCTION dc_reject_print_audit_mutation()'
                ))
            connection.execute(text(
                f'CREATE OR REPLACE TRIGGER "dc_immutable_{table}_truncate" '
                f'BEFORE TRUNCATE ON "{table}" FOR EACH STATEMENT '
                'EXECUTE FUNCTION dc_reject_print_audit_mutation()'
            ))
            # PUBLIC should not have DML rights even if an operator
            # accidentally grants them later. Real runtime roles must be
            # independently provisioned by the DB administrator.
            connection.execute(text(
                f'REVOKE UPDATE, DELETE, TRUNCATE ON TABLE "{table}" FROM PUBLIC'
            ))
    elif dialect == "sqlite":
        for table in PROTECTED_PRINT_AUDITS:
            for operation in ("UPDATE", "DELETE"):
                name = f"dc_immutable_{table}_{operation.lower()}"
                connection.execute(text(
                    f'CREATE TRIGGER IF NOT EXISTS "{name}" BEFORE {operation} '
                    f'ON "{table}" BEGIN '
                    "SELECT RAISE(ABORT, 'DC_PRINT_AUDIT_APPEND_ONLY'); END"
                ))
    else:
        raise RuntimeError("PRINT_AUDIT_GUARD_DIALECT_UNSUPPORTED")


def remove_append_only_print_audit_guards(connection: Connection) -> None:
    """Only for explicit Alembic downgrade/rehearsal, never a runtime command."""
    dialect = connection.dialect.name
    if dialect not in ("postgresql", "sqlite"):
        raise RuntimeError("PRINT_AUDIT_GUARD_DIALECT_UNSUPPORTED")
    for table in PROTECTED_PRINT_AUDITS:
        for operation in ("UPDATE", "DELETE"):
            name = f"dc_immutable_{table}_{operation.lower()}"
            if dialect == "postgresql":
                connection.execute(text(f'DROP TRIGGER IF EXISTS "{name}" ON "{table}"'))
            else:
                connection.execute(text(f'DROP TRIGGER IF EXISTS "{name}"'))
    if dialect == "postgresql":
        for table in PROTECTED_PRINT_AUDITS:
            connection.execute(text(
                f'DROP TRIGGER IF EXISTS "dc_immutable_{table}_truncate" ON "{table}"'
            ))
        connection.execute(text(
            "DROP FUNCTION IF EXISTS dc_reject_print_audit_mutation()"
        ))
