"""CB-03 G4 SQLCipher persistence + production claim/lock/revision primitives.

Disposable encrypted file only. Never a real cabinet database or key. This
does NOT invoke the full FastAPI app or prove clinical SQLCipher E2E.
"""
from __future__ import annotations

import importlib.util
import json
import os
import secrets
import sqlite3
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier

if (os.getenv("GITHUB_ACTIONS") != "true" or
        os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1"):
    raise RuntimeError("REFUSED: only disposable CI runtime")
HEAD = os.getenv("CB03_G4_SOURCE_HEAD", "")
if (len(HEAD) != 40 or any(c not in "0123456789abcdef" for c in HEAD)
        or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != HEAD):
    raise RuntimeError("REFUSED: exact HEAD required")

from sqlalchemy import (
    Column, DateTime, Integer, MetaData, String, Table, Text, create_engine, select, update,
)
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError
from sqlcipher3 import dbapi2 as cipher

ROOT = Path(__file__).resolve().parents[2]
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

claims = load("backend/services/bot/atomic_action_claim.py", "g4_cipher_claims")
locks = load("backend/services/agenda_transaction_lock.py", "g4_cipher_locks")
ddl = load("backend/core/appointment_revision_ddl.py", "g4_cipher_ddl")

# Mapped class for the exact G2 prepared-only claim helper.
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase):
    pass
class Action(Base):
    __tablename__ = "synthetic_g4_bot_actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    employer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    receipt: Mapped[str | None] = mapped_column(Text, nullable=True)

metadata = Base.metadata
appts = Table(
    "appointments", metadata,
    Column("id", Integer, primary_key=True),
    Column("employer_id", Integer, nullable=False),
    Column("patient_id", Integer, nullable=False),
    Column("praticien_id", Integer, nullable=False),
    Column("resource_id", Integer, nullable=True),
    Column("datetime_start", DateTime, nullable=False),
    Column("duration_minutes", Integer, nullable=False),
    Column("status", String(30), nullable=False),
    Column("scheduling_type", String(35), nullable=False),
    Column("deleted_at", DateTime, nullable=True),
    Column("clinical_revision", Integer, nullable=False, server_default="0"),
)
audit = Table("synthetic_g4_audit", metadata,
    Column("id", Integer, primary_key=True),
    Column("action_id", String(36), nullable=False),
    Column("kind", String(40), nullable=False))

events = []
tenant, user, patient = 912901, 912902, 912903
future = datetime(2027, 9, 6, 10, 0)
with tempfile.TemporaryDirectory(prefix="cb03-g4-sqlcipher-") as tmp:
    dbfile = Path(tmp) / "ephemeral-encrypted-only.db"
    key = secrets.token_hex(32)

    def connect_with(password):
        conn = cipher.connect(str(dbfile), timeout=7, check_same_thread=False)
        conn.execute("PRAGMA key = \"x'%s'\"" % password)
        if not conn.execute("PRAGMA cipher_version").fetchone():
            raise RuntimeError("SQLCipher not available")
        conn.execute("PRAGMA busy_timeout=7000")
        return conn

    engine = create_engine("sqlite://", creator=lambda: connect_with(key),
                           poolclass=NullPool)
    with engine.begin() as conn:
        metadata.create_all(conn)
        ddl.install_appointment_revision_guard(conn)
        ddl.install_appointment_overlap_index(conn)
        conn.execute(appts.insert().values(
            id=1, employer_id=tenant, patient_id=patient, praticien_id=user,
            datetime_start=future, duration_minutes=30, status="PREVU",
            scheduling_type="EXACT_TIME"))
        conn.execute(appts.insert().values(
            id=2, employer_id=tenant, patient_id=patient, praticien_id=user,
            datetime_start=future + timedelta(hours=1), duration_minutes=30,
            status="PREVU", scheduling_type="EXACT_TIME"))
    assert dbfile.read_bytes()[:16] != b"SQLite format 3\x00"
    try:
        with sqlite3.connect(dbfile) as plain:
            plain.execute("SELECT name FROM sqlite_master").fetchall()
    except sqlite3.DatabaseError:
        pass
    else:
        raise AssertionError("PLAINTEXT_DRIVER_READ_ENCRYPTED_DB")
    try:
        wrong = connect_with(secrets.token_hex(32))
        try:
            wrong.execute("SELECT COUNT(*) FROM appointments").fetchone()
        finally:
            wrong.close()
    except sqlite3.DatabaseError:
        pass
    else:
        raise AssertionError("WRONG_KEY_DECRYPTED_DB")
    events.append({"case": "SQLCIPHER_WRONG_KEY_AND_PLAINTEXT", "pass": True})

    def insert_action(id, ttl=30):
        with Session(engine) as db:
            db.add(Action(id=id, user_id=user, employer_id=tenant,
                          status="prepared", expires_at=datetime.utcnow() +
                          timedelta(minutes=ttl)))
            db.commit()
    id1, id2, id3 = (secrets.token_hex(16) for _ in range(3))
    insert_action(id1)
    insert_action(id2)
    insert_action(id3, -1)

    # Race G2 *actual production* claim helper on independent encrypted
    # connections. Only one claimant can commit; a lock error fails closed.
    barrier = Barrier(2, timeout=10)
    def compete():
        with Session(engine) as db:
            barrier.wait()
            try:
                ok = claims.claim_prepared_action(
                    db, Action, id1, user, tenant, datetime.utcnow())
                if ok:
                    db.query(Action).filter_by(id=id1, status="executing").update(
                        {"status": "executed", "receipt": '{"appointment_id":1}'})
                    db.execute(audit.insert().values(action_id=id1, kind="confirmed"))
                db.commit()
                return "won" if ok else "rejected"
            except OperationalError as exc:
                db.rollback()
                if "locked" not in str(exc).lower() and "busy" not in str(exc).lower():
                    raise
                return "locked-refused"
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(compete) for _ in range(2)]
        result = [f.result(timeout=23) for f in futures]
    assert result.count("won") == 1, result
    assert len(result) == 2 and all(v in {"won", "rejected", "locked-refused"} for v in result)
    with Session(engine) as db:
        assert db.get(Action, id1).status == "executed"
        assert db.execute(select(audit.c.id).where(audit.c.action_id == id1)).rowcount != -1 or True
        assert len(db.execute(select(audit.c.id).where(audit.c.action_id == id1)).all()) == 1
        assert not claims.claim_prepared_action(db, Action, id1, user, tenant, datetime.utcnow())
        assert not claims.claim_prepared_action(db, Action, id2, user + 1, tenant, datetime.utcnow())
        assert not claims.claim_prepared_action(db, Action, id2, user, tenant + 1, datetime.utcnow())
        assert not claims.claim_prepared_action(db, Action, id3, user, tenant, datetime.utcnow())
        db.rollback()
    events.append({"case": "PREPARED_ONLY_CONCURRENT_CLAIM", "results": sorted(result),
                   "receiptAudits": 1})

    # Crash before commit rolls back the same protected action & appointment.
    with Session(engine) as db:
        assert claims.claim_prepared_action(db, Action, id2, user, tenant, datetime.utcnow())
        assert locks.lock_cabinet_booking(db, tenant)
        before = db.execute(select(appts.c.clinical_revision).where(appts.c.id == 1)).scalar_one()
        rowcount = db.execute(update(appts).where(
            appts.c.id == 1, appts.c.employer_id == tenant,
            appts.c.patient_id == patient, appts.c.status == "PREVU",
            appts.c.clinical_revision == before,
        ).values(status="EN_SALLE_ATTENTE")).rowcount
        assert rowcount == 1
        db.query(Action).filter_by(id=id2, status="executing").update(
            {"status": "executed", "receipt": '{"appointment_id":1}'})
        db.execute(audit.insert().values(action_id=id2, kind="confirmed"))
        db.flush()
        db.rollback()  # simulate killed worker before commit
    engine.dispose()  # force fresh SQLCipher connection to re-open file
    with Session(engine) as db:
        assert db.get(Action, id2).status == "prepared"
        status, revision = db.execute(select(
            appts.c.status, appts.c.clinical_revision).where(appts.c.id == 1)).one()
        assert status == "PREVU" and revision == before
        assert not db.execute(select(audit.c.id).where(audit.c.action_id == id2)).all()
    events.append({"case": "CRASH_PRE_COMMIT_REOPEN", "claim": "prepared",
                   "appointment": "PREVU", "audit": 0})

    # Successful single transaction remains durable after engine restart,
    # including stored receipt and exactly one audit.
    with Session(engine) as db:
        assert claims.claim_prepared_action(db, Action, id2, user, tenant, datetime.utcnow())
        assert locks.lock_cabinet_booking(db, tenant)
        updated = db.execute(update(appts).where(
            appts.c.id == 1, appts.c.employer_id == tenant,
            appts.c.patient_id == patient, appts.c.status == "PREVU",
            appts.c.clinical_revision == before,
        ).values(status="EN_SALLE_ATTENTE")).rowcount
        assert updated == 1
        db.query(Action).filter_by(id=id2, status="executing").update(
            {"status": "executed", "receipt": '{"appointment_id":1,"status":"EN_SALLE_ATTENTE"}'})
        db.execute(audit.insert().values(action_id=id2, kind="confirmed"))
        db.commit()
    engine.dispose()
    with Session(engine) as db:
        a = db.get(Action, id2)
        status, revision = db.execute(select(
            appts.c.status, appts.c.clinical_revision).where(appts.c.id == 1)).one()
        assert a.status == "executed"
        assert json.loads(a.receipt) == {
            "appointment_id": 1, "status": "EN_SALLE_ATTENTE"}
        assert status == "EN_SALLE_ATTENTE" and revision == before + 1
        assert len(db.execute(select(audit.c.id).where(audit.c.action_id == id2)).all()) == 1
        assert not claims.claim_prepared_action(db, Action, id2, user, tenant, datetime.utcnow())
        db.rollback()
    events.append({"case": "POST_COMMIT_REOPEN_LOST_ACK", "action": "executed",
                   "receiptReopened": True, "replayRejected": True})

    # ABA even though status returns to the same visible state.
    with Session(engine) as db:
        rev0 = db.execute(select(appts.c.clinical_revision).where(appts.c.id == 2)).scalar_one()
    for status in ("ANNULE", "PREVU"):
        with Session(engine) as db:
            db.execute(update(appts).where(appts.c.id == 2).values(status=status))
            db.commit()
    with Session(engine) as db:
        status, rev = db.execute(select(
            appts.c.status, appts.c.clinical_revision).where(appts.c.id == 2)).one()
        assert status == "PREVU" and rev == rev0 + 2
        rejected = db.execute(update(appts).where(
            appts.c.id == 2, appts.c.status == "PREVU",
            appts.c.clinical_revision == rev0,
        ).values(status="EN_SALLE_ATTENTE")).rowcount
        assert rejected == 0
        db.rollback()
    events.append({"case": "SQLCIPHER_DB_TRIGGER_ABA", "revisionDelta": 2,
                   "oldCasAccepted": False})
    engine.dispose()
    assert dbfile.exists()

report = {
    "schema": "CB03_G4_SQLCIPHER_PERSISTENT_PRIMITIVES_V1",
    "head": HEAD, "isolatedFileEncrypted": True, "plainDriverReadable": False,
    "wrongKeyReadable": False, "freshConnectionAfterCommit": True,
    "cases": events,
    "limitations": [
        "Minimal SQLCipher tables, not full app FastAPI/SQLCipher schema",
        "Rollback on worker before commit is simulated; no actual OS kill",
        "No Windows cabinet file or master key",
        "No browser or real clinical data",
    ],
}
target = Path("artifacts/cb03-g4/sqlcipher-persistent-primitives.json")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("CB03_G4_SQLCIPHER_PRIMITIVES_PASS", json.dumps(report))
