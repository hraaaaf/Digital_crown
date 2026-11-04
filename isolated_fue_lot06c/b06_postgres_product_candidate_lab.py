"""B06-4C: ISOLATED PostgreSQL transaction candidate, never imported by product.

PostgreSQL product persistence is NOT approved. Only CI's synthetic/loopback
dc06_b06_ci database may execute this module. The real SQLCipher-only product
continues to refuse PostgreSQL in all environments.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import secrets
import time

from sqlalchemy import insert, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from backend.models_media_core import ClinicalAsset
from backend.services.clinical_asset_service import create_clinical_asset
from backend.services.clinical_asset_storage import store_clinical_asset_bytes
from backend.services.imaging_acquisition_durable_v15 import (
    DurableCaptureDenied, _receipt, _signature, _verify_receipt, audit,
    outbox, receipts,
)


def _isolated(engine):
    url = make_url(str(engine.url))
    if not (
        os.environ.get("ENVIRONMENT") == "test"
        and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
        and os.environ.get("DC06_B06_PG_LAB_ONLY") == "1"
        and url.drivername == "postgresql+psycopg"
        and url.host == "127.0.0.1"
        and url.port == 5432
        and url.database == "dc06_b06_ci"
        and url.username == "dc06_synthetic"
    ):
        raise DurableCaptureDenied("PG_PRODUCT_CANDIDATE_TEST_ONLY")
    # Prevent a lookalike connection URL or altered search_path from escaping
    # the disposable per-test schema. Revalidate on every operation.
    with engine.connect() as conn:
        ident = conn.exec_driver_sql(
            "SELECT current_database(), current_user, current_schema()"
        ).one()
    if (ident[0], ident[1]) != ("dc06_b06_ci", "dc06_synthetic") or not (
        ident[2].startswith("dc06_b06_lab_")
    ):
        raise DurableCaptureDenied("PG_PRODUCT_CANDIDATE_WRONG_SCHEMA")


def _lab_schema(db):
    conn = db.connection()
    for table in (receipts, audit, outbox, ClinicalAsset.__table__):
        row = conn.exec_driver_sql(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema=current_schema() AND table_name=%s",
            (table.name,),
        ).scalar_one()
        if row != 1:
            raise DurableCaptureDenied("PG_PRODUCT_SCHEMA_NOT_APPROVED")
    # Fixture has 9 anti-mutation triggers (including TRUNCATE). Nothing is
    # installed or repaired by this runtime code.
    for table in (receipts, audit, outbox):
        names = set(conn.exec_driver_sql(
            "SELECT tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname=current_schema() AND c.relname=%s "
            "AND t.tgenabled='O' AND NOT t.tgisinternal",
            (table.name,),
        ).scalars())
        part = table.name.replace("dc06_b06_product_", "")
        expected = {f"dc06_b06_{part}_{op}_lock"
                    for op in ("update", "delete", "truncate")}
        if not expected.issubset(names):
            raise DurableCaptureDenied("PG_PRODUCT_SCHEMA_NOT_APPROVED")
    # Lab-only additive foreign-key contract, including tenant+patient
    # cross-binding and receipt audit/outbox references.
    fks = set(conn.exec_driver_sql(
        "SELECT conname FROM pg_constraint c "
        "JOIN pg_namespace n ON n.oid=c.connamespace "
        "WHERE n.nspname=current_schema() AND c.contype='f'"
    ).scalars())
    if not {
        "dc06_b06_lab_asset_fk", "dc06_b06_lab_tenant_patient_fk",
        "dc06_b06_lab_receipt_audit_fk", "dc06_b06_lab_receipt_outbox_fk",
    }.issubset(fks):
        raise DurableCaptureDenied("PG_PRODUCT_SCHEMA_NOT_APPROVED")


def is_committed(engine, *, tenant, station, capture):
    _isolated(engine)
    with Session(engine) as db:
        _lab_schema(db)
        return _receipt(db, tenant=tenant, station=station, capture=capture) is not None


def receipt_for(engine, *, tenant, station, capture, patient, staff, digest,
                media_root=None):
    _isolated(engine)
    with Session(engine) as db:
        _lab_schema(db)
        row = _receipt(db, tenant=tenant, station=station, capture=capture)
        if row is None or any(row[k] != v for k, v in (
            ("patient", patient), ("staff", staff), ("digest", digest)
        )):
            raise DurableCaptureDenied("PG_PRODUCT_ACK_SCOPE_DENIED")
        return _verify_receipt(db, row, media_root)


def commit_capture(engine, *, tenant, station, capture, patient, staff, digest,
                   media, validate_locked, category, media_root=None, fail_at=None):
    _isolated(engine)
    if fail_at not in (None, "after_asset", "after_receipt", "after_audit"):
        raise DurableCaptureDenied("PG_PRODUCT_INVALID_FAILPOINT")
    if not isinstance(media, bytes) or not media or category not in (
        "PHOTO", "RADIOGRAPH",
    ) or hashlib.sha256(media).hexdigest() != digest:
        raise DurableCaptureDenied("PG_PRODUCT_INVALID_MEDIA")
    with Session(engine, expire_on_commit=False) as db:
        try:
            # PostgreSQL transaction-scoped lock serializes equal capture IDs
            # before staff/patient validation, without volatile process mutex.
            key = f"{tenant}:{station}:{capture}".encode("utf-8")
            lock = int.from_bytes(hashlib.sha256(key).digest()[:8],
                                  "big", signed=True)
            db.connection().exec_driver_sql(
                "SELECT pg_advisory_xact_lock(%s)", (lock,),
            )
            _lab_schema(db)
            validate_locked(db)
            prior = _receipt(db, tenant=tenant, station=station, capture=capture)
            if prior is not None:
                if (prior["patient"], prior["staff"], prior["digest"],
                        prior["byte_size"]) != (patient, staff, digest, len(media)):
                    raise DurableCaptureDenied("PG_PRODUCT_REPLAY_CONFLICT")
                found = _verify_receipt(db, prior, media_root)
                db.commit()
                return found
            asset = create_clinical_asset(
                db, employer_id=tenant, patient_id=patient, asset_type=category,
                source_kind="DEVICE_CAPTURE", created_by=staff,
                source_ref=f"DC06:{station}:{capture}", mime_type="image/png",
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
                "receipt_id": "LAB-DC06-" + secrets.token_hex(16),
                "committed_at": int(time.time()),
            }
            signature = _signature(row)
            db.execute(insert(receipts).values(**row, signature=signature))
            if fail_at == "after_receipt":
                raise DurableCaptureDenied("INJECTED_TRANSACTION_ROLLBACK")
            db.execute(insert(audit).values(
                receipt_id=row["receipt_id"],
                event="STAFF_APPROVED_MEDIA_COMMITTED",
            ))
            if fail_at == "after_audit":
                raise DurableCaptureDenied("INJECTED_TRANSACTION_ROLLBACK")
            db.execute(insert(outbox).values(
                receipt_id=row["receipt_id"], event="MEDIA_ACK_AVAILABLE",
            ))
            ack = _verify_receipt(db, {**row, "signature": signature}, media_root)
            db.commit()
            return ack
        except BaseException:
            db.rollback()
            raise
