"""B06-3 candidate: SQLCipher-only, transactionally durable capture ledger.

This module does NOT migrate/create product tables and does not activate clinic
ingress. A trusted server bootstrap must explicitly enable it after schema
approval. Test fixtures may provision the schema on an isolated SQLCipher file.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select
from sqlalchemy.orm import Session

from backend.models_media_core import ClinicalAsset
from backend.services.clinical_asset_service import create_clinical_asset
from backend.services.clinical_asset_storage import (
    read_clinical_asset_bytes, store_clinical_asset_bytes,
)

metadata = MetaData()
receipts = Table(
    "dc06_b06_product_receipts", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("station", String(64), primary_key=True),
    Column("capture", Integer, primary_key=True),
    Column("patient", Integer, nullable=False),
    Column("staff", Integer, nullable=False),
    Column("digest", String(64), nullable=False),
    Column("byte_size", Integer, nullable=False),
    Column("asset_id", Integer, nullable=False, unique=True),
    Column("receipt_id", String(64), nullable=False, unique=True),
    Column("committed_at", Integer, nullable=False),
    Column("signature", String(128), nullable=False),
)
audit = Table(
    "dc06_b06_product_audit", metadata,
    Column("receipt_id", String(64), primary_key=True),
    Column("event", String(48), nullable=False),
)
outbox = Table(
    "dc06_b06_product_outbox", metadata,
    Column("receipt_id", String(64), primary_key=True),
    Column("event", String(48), nullable=False),
)
SCHEMA_TABLES = (receipts, audit, outbox)

# Operator migration proposal, not executed at startup. A table-name-only
# existence check is insufficient: an incomplete or writable ledger could
# produce a seemingly verified ACK without durable audit immutability.
LEDGER_IMMUTABILITY_TRIGGERS = {
    f"dc06_b06_{kind}_{action.lower()}_lock": (
        f"CREATE TRIGGER dc06_b06_{kind}_{action.lower()}_lock "
        f"BEFORE {action} ON dc06_b06_product_{kind} "
        f"BEGIN SELECT RAISE(ABORT, 'DC06_B06_LEDGER_IMMUTABLE'); END"
    )
    for kind in ("receipts", "audit", "outbox")
    for action in ("UPDATE", "DELETE")
}


class DurableCaptureDenied(RuntimeError):
    """Public caller must return a sanitized failure, never a partial ACK."""


def _signer():
    raw = os.environ.get("CABINET_MASTER_KEY_HEX", "")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", raw):
        raise DurableCaptureDenied("DURABLE_SIGNER_UNAVAILABLE")
    seed = HKDF(
        algorithm=hashes.SHA256(), length=32,
        salt=b"dc06-b06-receipt-signature-v1",
        info=b"ed25519-cabinet-acquisition-receipt",
    ).derive(bytes.fromhex(raw))
    return Ed25519PrivateKey.from_private_bytes(seed)


def _payload(row: dict) -> bytes:
    fields = ("tenant", "station", "capture", "patient", "staff",
              "digest", "byte_size", "asset_id", "receipt_id", "committed_at")
    return json.dumps(
        {"schema": "dc06-b06-ack-v1", **{k: row[k] for k in fields}},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")


def _signature(row: dict) -> str:
    return _signer().sign(_payload(row)).hex()


def _sqlcipher(db: Session) -> None:
    try:
        value = db.connection().exec_driver_sql("PRAGMA cipher_version").scalar()
    except Exception as exc:
        raise DurableCaptureDenied("DURABLE_SQLCIPHER_REQUIRED") from exc
    if not value or db.get_bind().dialect.name != "sqlite":
        raise DurableCaptureDenied("DURABLE_SQLCIPHER_REQUIRED")


def _schema(db: Session) -> None:
    """Read-only, fail-closed verification of the *exact* approved ledger.

    No DDL, trigger repair, implicit Alembic upgrade or migration occurs here.
    A future operator migration must independently install this schema.
    """
    connection = db.connection()
    for table in SCHEMA_TABLES:
        name = table.name  # fixed literal declared server-side
        rows = connection.exec_driver_sql(f'PRAGMA table_info("{name}")').all()
        expected = {column.name: column for column in table.columns}
        if len(rows) != len(expected) or {row[1] for row in rows} != set(expected):
            raise DurableCaptureDenied("DURABLE_SCHEMA_NOT_APPROVED")
        for row in rows:
            col = expected[row[1]]
            if bool(row[3]) != (not col.nullable):
                raise DurableCaptureDenied("DURABLE_SCHEMA_NOT_APPROVED")
        required_pk = tuple(column.name for column in table.primary_key.columns)
        actual_pk = tuple(row[1] for row in sorted(
            (item for item in rows if item[5]), key=lambda item: item[5],
        ))
        if actual_pk != required_pk:
            raise DurableCaptureDenied("DURABLE_SCHEMA_NOT_APPROVED")

    # Exactly one ClinicalAsset and one receipt ID per ledger entry, independently
    # of the tuple primary key (tenant, station, opaque capture ID).
    unique_index_columns = set()
    for info in connection.exec_driver_sql(
        'PRAGMA index_list("dc06_b06_product_receipts")'
    ).all():
        # A partial UNIQUE index only constrains rows matching its WHERE
        # predicate, so it cannot protect all patient-capture receipts.
        # SQLite PRAGMA index_list column 4 is the 'partial' flag.
        if info[2] and len(info) > 4 and not info[4]:
            idx_name = info[1].replace('"', '""')
            unique_index_columns.add(tuple(
                col[2] for col in connection.exec_driver_sql(
                    f'PRAGMA index_info("{idx_name}")'
                ).all()
            ))
    if not {("asset_id",), ("receipt_id",)}.issubset(unique_index_columns):
        raise DurableCaptureDenied("DURABLE_SCHEMA_NOT_APPROVED")

    def _canonical(sql: str) -> str:
        return re.sub(r"\s+", " ", sql.strip()).lower()

    rows = connection.exec_driver_sql(
        "SELECT name,sql FROM sqlite_master WHERE type='trigger'"
    ).all()
    triggers = {name: sql for name, sql in rows}
    for name, sql in LEDGER_IMMUTABILITY_TRIGGERS.items():
        if name not in triggers or _canonical(triggers[name] or "") != _canonical(sql):
            raise DurableCaptureDenied("DURABLE_SCHEMA_NOT_APPROVED")


def _receipt(db: Session, *, tenant: int, station: str, capture: int):
    return db.execute(select(receipts).where(
        receipts.c.tenant == tenant,
        receipts.c.station == station,
        receipts.c.capture == capture,
    )).mappings().first()


def _verify_receipt(db: Session, record, media_root: Path | None) -> dict:
    if record is None:
        raise DurableCaptureDenied("DURABLE_RECEIPT_NOT_FOUND")
    row = dict(record)
    if (
        db.execute(select(audit.c.event).where(
            audit.c.receipt_id == row["receipt_id"],
        )).scalar_one_or_none() != "STAFF_APPROVED_MEDIA_COMMITTED"
        or db.execute(select(outbox.c.event).where(
            outbox.c.receipt_id == row["receipt_id"],
        )).scalar_one_or_none() != "MEDIA_ACK_AVAILABLE"
    ):
        raise DurableCaptureDenied("DURABLE_RECEIPT_INCOMPLETE")
    try:
        _signer().public_key().verify(bytes.fromhex(row["signature"]), _payload(row))
    except Exception as exc:
        raise DurableCaptureDenied("DURABLE_RECEIPT_SIGNATURE_DENIED") from exc
    asset = db.get(ClinicalAsset, row["asset_id"])
    if (
        asset is None or asset.employer_id != row["tenant"]
        or asset.patient_id != row["patient"]
        or asset.source_kind != "DEVICE_CAPTURE"
        or asset.sha256 != row["digest"] or asset.byte_size != row["byte_size"]
        or asset.source_ref != f"DC06:{row['station']}:{row['capture']}"
    ):
        raise DurableCaptureDenied("DURABLE_ASSET_BINDING_DENIED")
    try:
        media = read_clinical_asset_bytes(
            db, employer_id=row["tenant"], patient_id=row["patient"],
            asset_id=row["asset_id"], media_root=media_root,
        )
    except Exception as exc:
        raise DurableCaptureDenied("DURABLE_MEDIA_INTEGRITY_DENIED") from exc
    if hashlib.sha256(media).hexdigest() != row["digest"] or len(media) != row["byte_size"]:
        raise DurableCaptureDenied("DURABLE_MEDIA_INTEGRITY_DENIED")
    pub = _signer().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()
    return {
        "schema_version": "dc06-b06-ack-v1",
        "status": "DURABLE_MEDIA_ACK",
        "receipt_id": row["receipt_id"],
        "signature": row["signature"],
        "signer_public_key": pub,
        "asset_id": row["asset_id"],
        "capture_id": row["capture"],
        "capture_digest": row["digest"],
        "patient_id": row["patient"],
        "clinical_receipt_authorized": False,
        "patient_assigned": True,
        "media_published": True,
    }


def receipt_for(
    engine, *, tenant: int, station: str, capture: int,
    patient: int, staff: int, digest: str, media_root: Path | None = None,
) -> dict:
    with Session(engine) as db:
        _sqlcipher(db)
        _schema(db)
        record = _receipt(db, tenant=tenant, station=station, capture=capture)
        if (record is None or record["patient"] != patient or
                record["staff"] != staff or record["digest"] != digest):
            raise DurableCaptureDenied("DURABLE_RECEIPT_SCOPE_DENIED")
        return _verify_receipt(db, record, media_root)


def is_committed(engine, *, tenant: int, station: str, capture: int) -> bool:
    with Session(engine) as db:
        _sqlcipher(db)
        _schema(db)
        return _receipt(db, tenant=tenant, station=station, capture=capture) is not None


def commit_capture(
    engine, *, tenant: int, station: str, capture: int,
    patient: int, staff: int, digest: str, media: bytes,
    validate_locked, category: str, media_root: Path | None = None,
    fail_at: str | None = None,
) -> dict:
    """One writer lock: patient/staff check, encrypted C2 blob, ledger, audit, ACK.

    On failure the SQLCipher transaction rolls back. An encrypted unreferenced
    blob may survive an aborted transaction; no patient asset/ACK may survive.
    """
    if fail_at is not None and not (
        os.environ.get("ENVIRONMENT") == "test"
        and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
        and fail_at in ("after_asset", "after_receipt", "after_audit")
    ):
        raise DurableCaptureDenied("DURABLE_FAILPOINT_NOT_AUTHORIZED")
    if (category not in ("PHOTO", "RADIOGRAPH")
            or not isinstance(media, bytes) or not media
            or hashlib.sha256(media).hexdigest() != digest):
        raise DurableCaptureDenied("DURABLE_MEDIA_DIGEST_DENIED")
    with Session(engine, expire_on_commit=False) as db:
        try:
            _sqlcipher(db)
            _schema(db)
            # A writer lock is required before re-reading the current authority.
            db.rollback()
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            _sqlcipher(db)
            _schema(db)
            validate_locked(db)
            prior = _receipt(db, tenant=tenant, station=station, capture=capture)
            if prior is not None:
                if (prior["patient"] != patient or prior["staff"] != staff
                        or prior["digest"] != digest or prior["byte_size"] != len(media)):
                    raise DurableCaptureDenied("DURABLE_CAPTURE_REPLAY_CONFLICT")
                result = _verify_receipt(db, prior, media_root)
                db.commit()
                return result
            asset = create_clinical_asset(
                db, employer_id=tenant, patient_id=patient,
                asset_type=category,
                source_kind="DEVICE_CAPTURE", created_by=staff,
                source_ref=f"DC06:{station}:{capture}",
                mime_type="image/png",
                provenance_json={
                    "ingestion_channel": "DC06_NATIVE_STAFF_REVIEW",
                    "workstation_id": station, "capture_id": capture,
                },
            )
            store_clinical_asset_bytes(
                db, employer_id=tenant, patient_id=patient,
                asset_id=asset.id, content=media, media_root=media_root,
            )
            if fail_at == "after_asset":
                raise DurableCaptureDenied("INJECTED_TRANSACTION_ROLLBACK")
            row = {
                "tenant": tenant, "station": station, "capture": capture,
                "patient": patient, "staff": staff, "digest": digest,
                "byte_size": len(media), "asset_id": asset.id,
                "receipt_id": "DC06-" + secrets.token_hex(16),
                "committed_at": int(time.time()),
            }
            db.execute(insert(receipts).values(**row, signature=_signature(row)))
            if fail_at == "after_receipt":
                raise DurableCaptureDenied("INJECTED_TRANSACTION_ROLLBACK")
            db.execute(insert(audit).values(
                receipt_id=row["receipt_id"], event="STAFF_APPROVED_MEDIA_COMMITTED",
            ))
            if fail_at == "after_audit":
                raise DurableCaptureDenied("INJECTED_TRANSACTION_ROLLBACK")
            db.execute(insert(outbox).values(
                receipt_id=row["receipt_id"], event="MEDIA_ACK_AVAILABLE",
            ))
            result = _verify_receipt(
                db, {**row, "signature": _signature(row)}, media_root,
            )
            db.commit()
            return result
        except BaseException:
            db.rollback()
            raise
