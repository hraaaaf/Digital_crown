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
    ):
        raise DurableCaptureDenied("PG_PRODUCT_CANDIDATE_TEST_ONLY")
    # Strict loopback/CI-only candidate. B06-4D-C additionally permits a real
    # NO-SUPERUSER LOGIN named after the *current disposable schema*; never
    # accept an arbitrary PG account or a production/cabinet identifier.
    with engine.connect() as conn:
        ident = conn.exec_driver_sql(
            "SELECT current_database(), session_user, current_user, current_schema()"
        ).one()
        schema = ident[3]
        expected_runtime = f"{schema}_runtime"
        if not (
            ident[0] == "dc06_b06_ci"
            and schema.startswith("dc06_b06_lab_")
            and len(schema) == len("dc06_b06_lab_") + 16
            and all(c in "0123456789abcdef" for c in schema[len("dc06_b06_lab_"):])
            and ident[1] == ident[2] == url.username
            and url.username in ("dc06_synthetic", expected_runtime)
        ):
            raise DurableCaptureDenied("PG_PRODUCT_CANDIDATE_WRONG_SCHEMA")
        if url.username == expected_runtime:
            role = conn.exec_driver_sql(
                "SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole "
                "FROM pg_roles WHERE rolname=%s", (expected_runtime,),
            ).one_or_none()
            if role is None or tuple(role) != (True, False, False, False):
                raise DurableCaptureDenied("PG_PRODUCT_CANDIDATE_UNSAFE_RUNTIME_ROLE")
            create = conn.exec_driver_sql(
                "SELECT has_schema_privilege(%s, %s, 'CREATE')",
                (expected_runtime, schema),
            ).scalar_one()
            if create:
                raise DurableCaptureDenied("PG_PRODUCT_CANDIDATE_RUNTIME_ROLE_CAN_DDL")


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
    # Trigger names alone are not an immutability guarantee: an attacker
    # with DDL privilege could replace the function with RETURN NEW while
    # preserving all nine trigger names. Fail closed on operation, timing,
    # function namespace, definer mode and the exact approved denial body.
    # This is *LAB-only* verification, not a migration or product activation.
    expected_body = (
        "BEGIN RAISE EXCEPTION 'DC06_B06_LEDGER_IMMUTABLE'; END"
    )
    for table in (receipts, audit, outbox):
        rows = conn.exec_driver_sql(
            "SELECT t.tgname, t.tgtype, f.proname, fn.nspname, "
            "f.prosrc, f.prosecdef "
            "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_proc f ON f.oid=t.tgfoid "
            "JOIN pg_namespace fn ON fn.oid=f.pronamespace "
            "WHERE n.nspname=current_schema() AND c.relname=%s "
            "AND t.tgenabled='O' AND NOT t.tgisinternal",
            (table.name,),
        ).all()
        found = {row[0]: row[1:] for row in rows}
        part = table.name.replace("dc06_b06_product_", "")
        for op, flag, row_level in (
            ("update", 16, True), ("delete", 8, True),
            ("truncate", 32, False),
        ):
            name = f"dc06_b06_{part}_{op}_lock"
            record = found.get(name)
            # PostgreSQL tgtype: ROW=1, BEFORE=2, UPDATE=16,
            # DELETE=8, TRUNCATE=32.
            expected_type = 2 | flag | (1 if row_level else 0)
            if record is None or (
                record[0] != expected_type
                or record[1] != "dc06_b06_lab_immutable"
                or record[2] != conn.exec_driver_sql(
                    "SELECT current_schema()"
                ).scalar_one()
                or " ".join(record[3].split()) != expected_body
                or record[4] is not False
            ):
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
