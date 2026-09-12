"""Additive P3 provenance fields for the canonical local DocumentArchive model.

The cabinet runtime does not automatically execute the full Alembic chain. This module
therefore attaches the fields to SQLAlchemy metadata and registers an idempotent
`MetaData.before_create` compatibility migration. Existing document rows are never
backfilled: NULL keeps the truthful meaning "historical provenance not recorded".
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, event, inspect, text

from backend.services.document_provenance_context import get_document_author_practitioner_id


_INSTALLED = False


def _attach_columns() -> None:
    from backend.models import DocumentArchive

    if "author_practitioner_id" not in DocumentArchive.__table__.c:
        DocumentArchive.author_practitioner_id = Column(
            "author_practitioner_id",
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        )
    if "signed_by_practitioner_id" not in DocumentArchive.__table__.c:
        DocumentArchive.signed_by_practitioner_id = Column(
            "signed_by_practitioner_id",
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        )
    if "signed_at" not in DocumentArchive.__table__.c:
        DocumentArchive.signed_at = Column("signed_at", DateTime, nullable=True)


def _migrate_existing_document_archives(_metadata, connection, **_kwargs) -> None:
    """Add nullable provenance columns to an existing cabinet DB before create_all."""
    inspector = inspect(connection)
    if not inspector.has_table("document_archives"):
        return

    existing = {column["name"] for column in inspector.get_columns("document_archives")}
    timestamp_type = "TIMESTAMP" if connection.dialect.name == "postgresql" else "DATETIME"
    definitions = {
        "author_practitioner_id": "INTEGER REFERENCES users(id) ON DELETE SET NULL",
        "signed_by_practitioner_id": "INTEGER REFERENCES users(id) ON DELETE SET NULL",
        "signed_at": timestamp_type,
    }
    for column_name, column_type in definitions.items():
        if column_name in existing:
            continue
        connection.execute(text(
            f"ALTER TABLE document_archives ADD COLUMN {column_name} {column_type}"
        ))

    migrated = {
        column["name"]
        for column in inspect(connection).get_columns("document_archives")
    }
    missing = set(definitions) - migrated
    if missing:
        raise RuntimeError(
            "Critical document provenance schema mismatch: missing "
            + ", ".join(sorted(missing))
        )


def _apply_author_before_insert(_mapper, _connection, target) -> None:
    author_id = get_document_author_practitioner_id()
    if author_id is not None:
        target.author_practitioner_id = author_id


def _apply_author_before_update(_mapper, _connection, target) -> None:
    """A regenerated file gets the current author and loses any stale signature proof."""
    author_id = get_document_author_practitioner_id()
    if author_id is None:
        return

    state = inspect(target)
    file_changed = state.attrs.file_hash.history.has_changes()
    if not file_changed:
        return

    target.author_practitioner_id = author_id
    target.signed_by_practitioner_id = None
    target.signed_at = None


def install_document_provenance_p3() -> None:
    """Install P3 metadata, response contracts, migration and provenance hooks."""
    global _INSTALLED
    if _INSTALLED:
        return

    from backend.models import Base, DocumentArchive
    from backend.schemas.document_provenance_p3 import install_document_provenance_schema_contracts

    _attach_columns()
    install_document_provenance_schema_contracts()
    event.listen(Base.metadata, "before_create", _migrate_existing_document_archives)
    event.listen(DocumentArchive, "before_insert", _apply_author_before_insert)
    event.listen(DocumentArchive, "before_update", _apply_author_before_update)
    _INSTALLED = True
