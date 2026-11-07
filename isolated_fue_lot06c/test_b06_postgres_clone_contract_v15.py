"""B06-4B PostgreSQL contract FUE on a disposable, loopback CI service ONLY.

No production integration, cabinet connection, clinical media, real patient,
Alembic migration, or clinical receipt authorization is performed here.
Every test receives a disposable schema removed after the test, on a strictly
pinned synthetic-only database identity.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
import threading
import uuid

import pytest
from sqlalchemy import create_engine, func, insert, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError

from backend.services.imaging_acquisition_durable_v15 import (
    DurableCaptureDenied, audit, commit_capture, is_committed, metadata,
    outbox, receipt_for, receipts,
)

DB = "dc06_b06_ci"
USER = "dc06_synthetic"
SCHEMA_PREFIX = "dc06_b06_lab_"


def _guarded_ci_dsn() -> str:
    dsn = os.environ.get("DC06_B06_PG_TEST_DSN", "")
    if not (
        os.environ.get("ENVIRONMENT") == "test"
        and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
        and os.environ.get("DC06_B06_PG_LAB_ONLY") == "1"
        and dsn
    ):
        raise AssertionError("DC06_B06_POSTGRES_NOT_EXPLICITLY_ISOLATED")
    url = make_url(dsn)
    if not (
        url.drivername == "postgresql+psycopg"
        and url.host == "127.0.0.1"
        and url.port == 5432
        and url.database == DB
        and url.username == USER
    ):
        raise AssertionError("DC06_B06_POSTGRES_UNTRUSTED_DSN")
    return dsn


@pytest.fixture
def pg_ledger():
    dsn = _guarded_ci_dsn()
    schema = SCHEMA_PREFIX + uuid.uuid4().hex[:16]
    admin = create_engine(dsn, pool_pre_ping=True)
    # No user-supplied schema or table name in DDL.
    with admin.begin() as conn:
        assert conn.exec_driver_sql("SELECT current_database()").scalar_one() == DB
        assert conn.exec_driver_sql("SELECT current_user").scalar_one() == USER
        conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    engine = create_engine(
        dsn, connect_args={"options": f"-c search_path={schema}"},
        pool_pre_ping=True,
    )
    try:
        with engine.connect() as conn:
            assert conn.exec_driver_sql("SELECT current_schema()").scalar_one() == schema
        metadata.create_all(engine)
        # Disposable preview of PostgreSQL append-only rules, NOT a migration
        # or installed product trigger/function contract.
        with engine.begin() as conn:
            conn.exec_driver_sql(
                "CREATE FUNCTION dc06_b06_lab_immutable() RETURNS trigger "
                "LANGUAGE plpgsql AS $$ BEGIN "
                "RAISE EXCEPTION 'DC06_B06_LEDGER_IMMUTABLE'; END $$"
            )
            for table in (receipts, audit, outbox):
                for op in ("UPDATE", "DELETE", "TRUNCATE"):
                    short = table.name.replace("dc06_b06_product_", "")
                    name = f"dc06_b06_{short}_{op.lower()}_lock"
                    scope = "ROW" if op != "TRUNCATE" else "STATEMENT"
                    conn.exec_driver_sql(
                        f'CREATE TRIGGER "{name}" BEFORE {op} '
                        f'ON "{table.name}" FOR EACH {scope} '
                        "EXECUTE FUNCTION dc06_b06_lab_immutable()"
                    )
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as conn:
            assert schema.startswith(SCHEMA_PREFIX)
            conn.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        admin.dispose()


def _record(capture=91, *, tenant=1, station="synthetic-station", asset_id=500,
            receipt_id="LAB-DC06-91", digest=None):
    return {
        "tenant": tenant, "station": station, "capture": capture,
        "patient": 12, "staff": 13,
        "digest": digest or hashlib.sha256(b"LAB-ONLY-NON-CLINICAL").hexdigest(),
        "byte_size": len(b"LAB-ONLY-NON-CLINICAL"),
        "asset_id": asset_id, "receipt_id": receipt_id,
        "committed_at": 1793830000,
        # Synthetic placeholder, MUST NOT be interpreted as a valid ACK.
        "signature": "0" * 128,
    }


def _counts(engine):
    with engine.connect() as conn:
        return tuple(conn.execute(select(func.count()).select_from(t)).scalar_one()
                     for t in (receipts, audit, outbox))


def _write_bundle(conn, values):
    conn.execute(insert(receipts).values(**values))
    conn.execute(insert(audit).values(
        receipt_id=values["receipt_id"], event="STAFF_APPROVED_MEDIA_COMMITTED",
    ))
    conn.execute(insert(outbox).values(
        receipt_id=values["receipt_id"], event="MEDIA_ACK_AVAILABLE",
    ))


def test_b06_4b_pg_disposable_rollback_and_constraints(pg_ledger):
    engine = pg_ledger
    with pytest.raises(RuntimeError, match="SYNTHETIC_ROLLBACK"):
        with engine.begin() as conn:
            _write_bundle(conn, _record())
            raise RuntimeError("SYNTHETIC_ROLLBACK")
    assert _counts(engine) == (0, 0, 0)

    with engine.begin() as conn:
        _write_bundle(conn, _record())
    assert _counts(engine) == (1, 1, 1)

    for kwargs in (
        {"capture": 91, "asset_id": 501, "receipt_id": "LAB-OTHER-1"},
        {"capture": 92, "asset_id": 500, "receipt_id": "LAB-OTHER-2"},
        {"capture": 93, "asset_id": 503, "receipt_id": "LAB-DC06-91"},
    ):
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                _write_bundle(conn, _record(**kwargs))
    assert _counts(engine) == (1, 1, 1)
    print("DC06_B06_4B_PG18_CLONE_ATOMIC_ROLLBACK_AND_3_UNIQUE_KEYS_PASS")


def test_b06_4b_pg_append_only_update_delete_and_truncate(pg_ledger):
    engine = pg_ledger
    with engine.begin() as conn:
        _write_bundle(conn, _record())
    for table in (receipts, audit, outbox):
        update = ({"signature": "f" * 128} if table is receipts
                  else {"event": "FORGED"})
        for action in ("UPDATE", "DELETE", "TRUNCATE"):
            with pytest.raises(DBAPIError):
                with engine.begin() as conn:
                    if action == "UPDATE":
                        conn.execute(table.update().values(**update))
                    elif action == "DELETE":
                        conn.execute(table.delete())
                    else:
                        conn.exec_driver_sql(f'TRUNCATE TABLE "{table.name}"')
    assert _counts(engine) == (1, 1, 1)
    print("DC06_B06_4B_PG18_CLONE_APPEND_ONLY_UPDATE_DELETE_TRUNCATE_DENIED_PASS")


def test_b06_4b_pg_concurrent_duplicate_one_bundle(pg_ledger):
    engine = pg_ledger
    barrier = threading.Barrier(2)

    def compete(index):
        values = _record(capture=94, asset_id=500+index,
                         receipt_id=f"LAB-CONCURRENT-{index}")
        try:
            with engine.begin() as conn:
                barrier.wait(timeout=15)
                _write_bundle(conn, values)
            return "COMMITTED"
        except IntegrityError:
            return "DENIED"

    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks = [pool.submit(compete, i) for i in range(2)]
        outcomes = [t.result(timeout=25) for t in tasks]
    assert sorted(outcomes) == ["COMMITTED", "DENIED"]
    assert _counts(engine) == (1, 1, 1)
    print("DC06_B06_4B_PG18_CLONE_CONCURRENT_CAPTURE_SINGLE_BUNDLE_PASS")


def test_b06_4b_current_product_pg_fail_closed(pg_ledger):
    engine = pg_ledger
    with pytest.raises(DurableCaptureDenied, match="DURABLE_SQLCIPHER_REQUIRED"):
        is_committed(engine, tenant=1, station="synthetic-station", capture=99)
    with pytest.raises(DurableCaptureDenied, match="DURABLE_SQLCIPHER_REQUIRED"):
        receipt_for(engine, tenant=1, station="synthetic-station",
                    capture=99, patient=12, staff=13,
                    digest=hashlib.sha256(b"LAB-ONLY-NON-CLINICAL").hexdigest())
    media = b"LAB-ONLY-NON-CLINICAL"
    with pytest.raises(DurableCaptureDenied, match="DURABLE_SQLCIPHER_REQUIRED"):
        commit_capture(
            engine, tenant=1, station="synthetic-station", capture=99,
            patient=12, staff=13, digest=hashlib.sha256(media).hexdigest(),
            media=media, category="PHOTO",
            validate_locked=lambda _db: pytest.fail("PG authority unexpectedly called"),
        )
    assert _counts(engine) == (0, 0, 0)
    print("DC06_B06_4B_REAL_PG_SERVICE_PRODUCT_FAIL_CLOSED_ZERO_WRITES_PASS")
