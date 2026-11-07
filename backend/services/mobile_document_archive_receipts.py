"""Pocket document archive receipts — opt-in, local SQL/SQLCipher contract.

The mapped table is intentionally imported lazily by Pocket archive routes.
No production schema is created or migrated by importing this module. Cabinet
activation requires an explicitly approved additive schema migration.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import DateTime, Integer, String, UniqueConstraint, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class PocketReceiptBase(DeclarativeBase):
    """Separate metadata: cabinet Base.metadata.create_all cannot migrate it."""
    pass


class MobileDocumentArchiveReceipt(PocketReceiptBase):
    __tablename__ = "mobile_document_archive_receipts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "actor_id", "device_id", "idempotency_key",
            name="uq_mobile_document_archive_intent",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False)
    patient_id: Mapped[int] = mapped_column(Integer, nullable=False)
    document_type: Mapped[str] = mapped_column(String(24), nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    archive_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    archive_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


def normalize_intent_key(value: str) -> str:
    """Never silently accept an empty, malformed or noncanonical operation key."""
    try:
        key = uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise HTTPException(status_code=422, detail="Identifiant d'archivage UUID invalide.") from exc
    if key.version != 4 or str(key) != str(value).lower():
        raise HTTPException(status_code=422, detail="Identifiant d'archivage UUIDv4 requis.")
    return str(key)


def payload_sha256(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assert_receipt_schema(db: Session) -> None:
    """Never create tables in a request or migrate a cabinet implicitly."""
    try:
        inspector = inspect(db.get_bind())
        table = MobileDocumentArchiveReceipt.__tablename__
        if not inspector.has_table(table):
            raise HTTPException(
                status_code=503,
                detail="Archivage Pocket désactivé : migration du registre non autorisée.",
            )
        # A table by this name is NOT proof of the approved migration.
        # An absent UNIQUE(scope, UUID) could create two clinical documents
        # when concurrent devices or network retries arrive.
        columns = {column["name"] for column in inspector.get_columns(table)}
        required = {column.name for column in MobileDocumentArchiveReceipt.__table__.columns}
        unique_scope = {"tenant_id", "actor_id", "device_id", "idempotency_key"}
        constraints = inspector.get_unique_constraints(table)
        indexes = inspector.get_indexes(table)
        enforce_unique = any(
            set(item.get("column_names") or ()) == unique_scope
            for item in (*constraints, *indexes)
            if item.get("unique", True)
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Registre d'archivage indisponible.") from exc
    if not required.issubset(columns) or not enforce_unique:
        raise HTTPException(
            status_code=503,
            detail="Registre d'archivage incomplet : activation refusée.",
        )


def read_scoped_receipt(
    db: Session, *, tenant_id: int, actor_id: int, device_id: str, key: str,
) -> MobileDocumentArchiveReceipt | None:
    assert_receipt_schema(db)
    return db.query(MobileDocumentArchiveReceipt).filter_by(
        tenant_id=tenant_id, actor_id=actor_id, device_id=device_id, idempotency_key=key,
    ).first()


def claim_archive_intent(
    db: Session, *, tenant_id: int, actor_id: int, device_id: str,
    key: str, patient_id: int, document_type: str, request_sha256: str,
) -> tuple[MobileDocumentArchiveReceipt, bool]:
    """INSERT-first durable claim: DB UNIQUE constraint elects one writer.

    Starting with SELECT would allow both SQLite sessions to acquire read
    snapshots and deadlock when upgrading to a write. INSERT ON CONFLICT is
    atomic on SQLite/SQLCipher and PostgreSQL, then we read after commit.
    """
    assert_receipt_schema(db)
    dialect = db.get_bind().dialect.name
    if dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    elif dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        raise HTTPException(status_code=503, detail="Dialecte de reçu non certifié.")

    values = dict(
        id=str(uuid.uuid4()), tenant_id=tenant_id, actor_id=actor_id,
        device_id=device_id, idempotency_key=key, patient_id=patient_id,
        document_type=document_type, request_sha256=request_sha256,
        state="PROCESSING", created_at=datetime.utcnow(),
    )
    statement = insert(MobileDocumentArchiveReceipt).values(**values)
    statement = statement.on_conflict_do_nothing(
        index_elements=["tenant_id", "actor_id", "device_id", "idempotency_key"],
    )
    try:
        outcome = db.execute(statement)
        created = outcome.rowcount == 1
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Registre d'archivage momentanément indisponible.") from exc

    existing = read_scoped_receipt(
        db, tenant_id=tenant_id, actor_id=actor_id, device_id=device_id, key=key,
    )
    if existing is None:
        raise HTTPException(status_code=503, detail="Reçu d'archivage non récupérable.")
    if (
        existing.patient_id != patient_id
        or existing.document_type != document_type
        or existing.request_sha256 != request_sha256
    ):
        raise HTTPException(status_code=409, detail="Clé d'archivage déjà liée à un contenu différent.")
    return existing, created

def complete_archive_in_current_transaction(
    db: Session, *, archive: object,
) -> None:
    """Receipt and DocumentArchive must be committed atomically in ONE SQL tx."""
    receipt_id = db.info.get("_mobile_document_archive_receipt_id")
    if receipt_id is None:
        return

    row = db.get(MobileDocumentArchiveReceipt, receipt_id)
    if (
        row is None or row.state != "PROCESSING"
        or row.patient_id != getattr(archive, "patient_id", None)
        or row.actor_id != getattr(archive, "uploaded_by_id", None)
    ):
        raise RuntimeError("Archivage Pocket : reçu d'intention incompatible.")
    if not getattr(archive, "id", None) or not getattr(archive, "file_hash", None):
        raise RuntimeError("Archivage Pocket : PDF/ligne canonique non confirmés.")

    row.archive_id = archive.id
    row.archive_sha256 = archive.file_hash
    row.state = "COMPLETED"
    row.completed_at = datetime.utcnow()
    db.flush()


def mark_unresolved_for_manual_review(db: Session, receipt_id: str) -> None:
    """No replay after an uncertain error; do not override an already committed result."""
    db.rollback()
    row = db.get(MobileDocumentArchiveReceipt, receipt_id)
    if row is not None and row.state == "PROCESSING":
        row.state = "REVIEW_REQUIRED"
        db.commit()
