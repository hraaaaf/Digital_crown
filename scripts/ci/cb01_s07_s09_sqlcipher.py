"""CI-only encrypted SQLCipher S07/S09 write-lock and revision guard proof.

Creates a brand new temporary encrypted database from scratch and destroys it.
Runs production SQLite lock/overlap/DDL on independent SQLCipher connections.
Not a full runtime API test and not a cabinet key/database migration test.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event

if os.environ.get("GITHUB_ACTIONS") != "true":
    raise RuntimeError("REFUSED: CI only")
if os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
    raise RuntimeError("REFUSED: isolated runtime required")
head = os.environ.get("CB01_SOURCE_HEAD", "")
if (len(head) != 40 or any(c not in "0123456789abcdef" for c in head)
        or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != head):
    raise RuntimeError("REFUSED: exact HEAD required")

from sqlalchemy import (Column, DateTime, Integer, MetaData, String, Table,
                        create_engine, select, update)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlcipher3 import dbapi2 as cipher

# Same *production* SQLite lock, exact-overlap and trigger/index functions.
# Import only these source files, not the unrelated application startup graph.
from importlib.util import module_from_spec, spec_from_file_location
repo_root = Path(__file__).resolve().parents[2]
def load(path, name):
    spec = spec_from_file_location(name, repo_root / path)
    assert spec is not None and spec.loader is not None
    m = module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

locks = load("backend/services/agenda_transaction_lock.py", "cb01_cipher_lock")
interval = load("backend/services/agenda_interval_overlap.py", "cb01_cipher_interval")
ddl = load("backend/core/appointment_revision_ddl.py", "cb01_cipher_ddl")
key = secrets.token_hex(32)
tenant, doctor = 910001, 910009
slot = datetime(2027, 3, 10, 10, 0)
duration = 30

with tempfile.TemporaryDirectory(prefix="cb01-ci-sqlcipher-") as tmp:
    filename = Path(tmp) / "new-encrypted-lab.db"
    def dbapi_connect():
        conn = cipher.connect(str(filename), timeout=7, check_same_thread=False)
        conn.execute("PRAGMA key = \"x'%s'\"" % key)
        result = conn.execute("PRAGMA cipher_version").fetchone()
        if result is None or not result[0]:
            conn.close()
            raise RuntimeError("REFUSED: SQLCipher encryption unavailable")
        conn.execute("PRAGMA busy_timeout = 7000")
        return conn
    engine = create_engine("sqlite://", creator=dbapi_connect, poolclass=NullPool)
    metadata = MetaData()
    appointments = Table("appointments", metadata,
        Column("id", Integer, primary_key=True),
        Column("employer_id", Integer, nullable=False),
        Column("praticien_id", Integer, nullable=True),
        Column("resource_id", Integer, nullable=True),
        Column("datetime_start", DateTime, nullable=False),
        Column("duration_minutes", Integer, nullable=False),
        Column("status", String(35), nullable=False),
        Column("scheduling_type", String(32), nullable=False),
        Column("deleted_at", DateTime, nullable=True),
        Column("clinical_revision", Integer, nullable=False, server_default="0"),
    )
    with engine.begin() as conn:
        metadata.create_all(conn)
        ddl.install_appointment_revision_guard(conn)
        ddl.install_appointment_overlap_index(conn)

    assert filename.exists() and filename.read_bytes()[:16] != b"SQLite format 3\x00", (
        "REFUSED: plaintext SQLite header")
    # Proof the same path cannot be opened using the normal sqlite3 driver.
    with sqlite3.connect(str(filename)) as plain:
        try:
            plain.execute("SELECT name FROM sqlite_master").all()
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("SQLCIPHER_PLAINTEXT_READABLE")

    def conflict_ids(session, target):
        end = target + timedelta(minutes=duration)
        rows = session.execute(select(
            appointments.c.id, appointments.c.datetime_start,
            appointments.c.duration_minutes,
        ).where(
            appointments.c.employer_id == tenant,
            appointments.c.praticien_id == doctor,
            appointments.c.deleted_at.is_(None),
            appointments.c.status == "PREVU",
            appointments.c.scheduling_type == "EXACT_TIME",
            appointments.c.datetime_start < end,
            interval.indexed_end_after(session, target),
        )).all()
        return [int(row.id) for row in rows if interval.exact_half_open_overlap(
            row.datetime_start, row.duration_minutes, target, end)]

    first_lock = Event()
    second_ready = Event()
    second_acquired = Event()
    release = Event()
    def first_writer():
        with Session(engine) as session:
            locks.lock_cabinet_booking(session, tenant)
            first_lock.set()
            assert release.wait(12), "first writer wait expired"
            assert not conflict_ids(session, slot)
            session.execute(appointments.insert().values(
                employer_id=tenant, praticien_id=doctor, datetime_start=slot,
                duration_minutes=duration, status="PREVU",
                scheduling_type="EXACT_TIME"))
            session.commit()
            return "FIRST_COMMITTED"
    def second_writer():
        with Session(engine) as session:
            second_ready.set()
            try:
                locks.lock_cabinet_booking(session, tenant)
            except OperationalError as e:
                session.rollback()
                if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                    raise
                return "SECOND_DB_LOCK_REFUSED"
            second_acquired.set()
            ids = conflict_ids(session, slot)
            assert len(ids) == 1, "SQLCIPHER_SECOND_WRITER_MISSED_COMMIT"
            session.rollback()
            return "SECOND_CONFLICT_REJECTED"
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            future1 = pool.submit(first_writer)
            assert first_lock.wait(10)
            future2 = pool.submit(second_writer)
            assert second_ready.wait(10)
            assert not second_acquired.wait(0.2), "SQLCIPHER_WRITER_BYPASSED_LOCK"
            release.set()
            outcomes = [future1.result(timeout=25), future2.result(timeout=25)]
    finally:
        release.set()
    assert outcomes[0] == "FIRST_COMMITTED"
    assert outcomes[1] in ("SECOND_CONFLICT_REJECTED", "SECOND_DB_LOCK_REFUSED")
    with Session(engine) as session:
        rows = session.execute(select(appointments.c.id).where(
            appointments.c.employer_id == tenant,
            appointments.c.datetime_start == slot,
        )).scalars().all()
        assert len(rows) == 1, "SQLCIPHER_TWO_SAME_SLOT_APPOINTMENTS"
        appt_id = int(rows[0])
    with Session(engine) as session:
        locks.lock_cabinet_booking(session, tenant)
        next_slot = slot + timedelta(minutes=duration)
        assert not conflict_ids(session, next_slot), "SQLCIPHER_ADJACENT_REJECTED"
        session.execute(appointments.insert().values(
            employer_id=tenant, praticien_id=doctor, datetime_start=next_slot,
            duration_minutes=duration, status="PREVU",
            scheduling_type="EXACT_TIME"))
        session.commit()
    with Session(engine) as session:
        assert len(session.execute(select(appointments.c.id)).all()) == 2
        rev0 = int(session.execute(select(appointments.c.clinical_revision).where(
            appointments.c.id == appt_id)).scalar_one())
        assert rev0 == 0
    for state in ("TERMINE", "PREVU"):
        with Session(engine) as session:
            assert session.execute(update(appointments).where(
                appointments.c.id == appt_id).values(status=state)).rowcount == 1
            session.commit()
    with Session(engine) as session:
        snapshot = session.execute(select(
            appointments.c.status, appointments.c.clinical_revision).where(
            appointments.c.id == appt_id)).one()
        assert snapshot.status == "PREVU"
        assert int(snapshot.clinical_revision) == rev0 + 2, "SQLCIPHER_ABA_VERSION"
        current_rev = int(snapshot.clinical_revision)
        rejected = session.execute(update(appointments).where(
            appointments.c.id == appt_id,
            appointments.c.clinical_revision == rev0,
            appointments.c.status == "PREVU",
        ).values(status="TERMINE")).rowcount
        assert rejected == 0, "SQLCIPHER_STALE_ABA_ACCEPTED"
        session.rollback()
    with Session(engine) as session:
        accepted = session.execute(update(appointments).where(
            appointments.c.id == appt_id,
            appointments.c.clinical_revision == current_rev,
            appointments.c.status == "PREVU",
        ).values(status="TERMINE")).rowcount
        assert accepted == 1
        session.commit()
    with Session(engine) as session:
        rev3 = int(session.execute(select(
            appointments.c.clinical_revision).where(
            appointments.c.id == appt_id)).scalar_one())
        assert rev3 == current_rev + 1
    engine.dispose()

report = {
    "schema": "CB01_SQLCIPHER_S07_S09_PRIMITIVES_V1",
    "sourceHead": head,
    "isolation": "SQLCIPHER_ENCRYPTED_TEMP_FILE_DESTROYED",
    "plaintextReadRefused": True,
    "S07": {"status": "PASS_SQLCIPHER_PRIMITIVES_ONLY",
            "sameSlotCreated": 1, "adjacentSlotCreated": 1,
            "secondWriter": outcomes[1]},
    "S09": {"status": "PASS_SQLCIPHER_REVISION_PRIMITIVE_ONLY",
            "oldRevision": rev0, "afterABARevision": current_rev,
            "staleCASUpdatedRows": rejected,
            "freshCASUpdatedRows": accepted},
    "limitations": [
        "Minimal encrypted fixture, not a complete Alembic SQLCipher cabinet",
        "DB concurrent transactions only, no HTTP or real operator UI",
        "No production key, no existing clinical file or workstation",
    ],
    "humanE2EValidated": 0, "converged": False,
}
output = Path("artifacts/cb01-associate-sidecar/sqlcipher-s07-s09-evidence.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("CB01_SQLCIPHER_S07_S09: PASS_ENCRYPTED_DB_PRIMITIVES; NO_HUMAN_E2E")
