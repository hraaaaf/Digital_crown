"""Additive linkage fields for insurance submissions.

No destructive migration and no backfill. Historical rows keep NULL and continue to
use the documented index-based fallback. New Honoraires rows can persist a stable
source_line_uid plus an explicit CatalogAct foreign key.
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, inspect, text


def attach_insurance_linkage_columns() -> None:
    """Attach nullable columns to the mapped Acte model at runtime."""
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


def migrate_insurance_linkage_columns(bind) -> None:
    """Idempotently add insurance linkage columns/indexes to an existing actes table."""
    attach_insurance_linkage_columns()
    inspector = inspect(bind)
    if not inspector.has_table("actes"):
        return

    existing = {column["name"] for column in inspector.get_columns("actes")}
    definitions = {
        "source_line_uid": "VARCHAR(36)",
        "catalog_act_id": "INTEGER REFERENCES catalog_acts(id) ON DELETE SET NULL",
    }

    with bind.begin() as conn:
        for name, definition in definitions.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE actes ADD COLUMN {name} {definition}"))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_actes_source_line_uid ON actes (source_line_uid)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_actes_catalog_act_id ON actes (catalog_act_id)"
        ))

    migrated = {column["name"] for column in inspect(bind).get_columns("actes")}
    missing = set(definitions) - migrated
    if missing:
        raise RuntimeError(
            "Critical insurance linkage schema mismatch: missing "
            + ", ".join(sorted(missing))
        )


def rollback_insurance_linkage_columns(bind) -> None:
    """Rollback helper for certification/tests. Never called automatically at runtime."""
    inspector = inspect(bind)
    if not inspector.has_table("actes"):
        return
    existing = {column["name"] for column in inspector.get_columns("actes")}

    with bind.begin() as conn:
        conn.execute(text("DROP INDEX IF EXISTS ix_actes_source_line_uid"))
        conn.execute(text("DROP INDEX IF EXISTS ix_actes_catalog_act_id"))
        if "catalog_act_id" in existing:
            conn.execute(text("ALTER TABLE actes DROP COLUMN catalog_act_id"))
        if "source_line_uid" in existing:
            conn.execute(text("ALTER TABLE actes DROP COLUMN source_line_uid"))
