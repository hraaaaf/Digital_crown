"""Additive linkage fields for insurance submissions.

No destructive migration and no backfill. Historical rows keep NULL and continue to
use the documented index-based fallback. New Honoraires rows can persist a stable
source_line_uid plus an explicit CatalogAct foreign key.
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, event, inspect, text

_INSTALLED = False


def attach_insurance_linkage_columns() -> None:
    """Attach nullable columns to the mapped Acte model."""
    from backend.models import Acte

    if "source_line_uid" not in Acte.__table__.c:
        Acte.source_line_uid = Column("source_line_uid", String(36), nullable=True)
    if "catalog_act_id" not in Acte.__table__.c:
        Acte.catalog_act_id = Column(
            "catalog_act_id",
            Integer,
            ForeignKey("catalog_acts.id", ondelete="SET NULL"),
            nullable=True,
        )


def _migrate_existing_actes(_metadata, connection, **_kwargs) -> None:
    """Self-heal historical cabinet DBs immediately before create_all()."""
    inspector = inspect(connection)
    if not inspector.has_table("actes"):
        return

    existing = {column["name"] for column in inspector.get_columns("actes")}
    definitions = {
        "source_line_uid": "VARCHAR(36)",
        "catalog_act_id": "INTEGER REFERENCES catalog_acts(id) ON DELETE SET NULL",
    }
    for name, definition in definitions.items():
        if name not in existing:
            connection.execute(text(f"ALTER TABLE actes ADD COLUMN {name} {definition}"))

    connection.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_actes_source_line_uid ON actes (source_line_uid)"
    ))
    connection.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_actes_catalog_act_id ON actes (catalog_act_id)"
    ))

    migrated = {column["name"] for column in inspect(connection).get_columns("actes")}
    missing = set(definitions) - migrated
    if missing:
        raise RuntimeError(
            "Critical insurance linkage schema mismatch: missing "
            + ", ".join(sorted(missing))
        )


def install_insurance_linkage() -> None:
    """Install ORM columns plus the startup compatibility migration once."""
    global _INSTALLED
    if _INSTALLED:
        return

    from backend.models import Base

    attach_insurance_linkage_columns()
    event.listen(Base.metadata, "before_create", _migrate_existing_actes)
    _INSTALLED = True


def migrate_insurance_linkage_columns(bind) -> None:
    """Explicit idempotent migration helper used by certification tests/tools."""
    attach_insurance_linkage_columns()
    with bind.begin() as connection:
        _migrate_existing_actes(None, connection)


def rollback_insurance_linkage_columns(bind) -> None:
    """Rollback helper for certification/tests. Never called automatically at runtime."""
    inspector = inspect(bind)
    if not inspector.has_table("actes"):
        return
    existing = {column["name"] for column in inspector.get_columns("actes")}

    with bind.begin() as connection:
        connection.execute(text("DROP INDEX IF EXISTS ix_actes_source_line_uid"))
        connection.execute(text("DROP INDEX IF EXISTS ix_actes_catalog_act_id"))
        if "catalog_act_id" in existing:
            connection.execute(text("ALTER TABLE actes DROP COLUMN catalog_act_id"))
        if "source_line_uid" in existing:
            connection.execute(text("ALTER TABLE actes DROP COLUMN source_line_uid"))
