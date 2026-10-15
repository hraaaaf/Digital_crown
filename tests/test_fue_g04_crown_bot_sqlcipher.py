"""Real file-backed encrypted SQLCipher concurrency and crash tests.

Synthetic rows only; no real clinic data. Uses the same booking lock helper as
the canonical Agenda router. Run through the existing FUE-G04 Linux/Windows CI.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier
import sys
import uuid
import subprocess

import pytest
from sqlalchemy import DateTime, Integer, String, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import QueuePool

import sqlcipher3
sys.modules["pysqlcipher3"] = sqlcipher3

from backend.services.agenda_transaction_lock import lock_cabinet_booking
from backend.services.bot.atomic_action_claim import claim_pending_action


class Base(DeclarativeBase):
    pass


class SyntheticAppointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    datetime_start: Mapped[str] = mapped_column(String(32), nullable=False)


class SyntheticAction(Base):
    __tablename__ = "bot_pending_actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    employer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


@pytest.fixture
def encrypted_sessions(tmp_path):
    dbfile = tmp_path / "synthetic-clinic-encrypted.db"
    # This URL mirrors backend.database's cabinet SQLCipher dialect, but
    # deliberately uses a disposable synthetic password and database.
    password = "e" * 64
    engine = create_engine(
        f"sqlite+pysqlcipher://:{password}@/{dbfile.as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 15},
        poolclass=QueuePool,
    )
    Base.metadata.create_all(engine)
    assert dbfile.exists()
    assert not dbfile.read_bytes().startswith(b"SQLite format 3")
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA cipher_version").scalar()
    yield sessionmaker(engine, expire_on_commit=False), dbfile
    engine.dispose()


def test_two_independent_sqlcipher_connections_same_slot_one_booking(encrypted_sessions):
    Session, filename = encrypted_sessions
    barrier = Barrier(2)
    slot = "2026-11-17T11:30:00"

    def create_one():
        with Session() as session:
            barrier.wait(timeout=12)
            try:
                assert lock_cabinet_booking(session, employer_id=7)
                if session.query(SyntheticAppointment).filter_by(
                    employer_id=7, datetime_start=slot
                ).count():
                    session.rollback()
                    return "conflict"
                session.add(SyntheticAppointment(
                    employer_id=7, datetime_start=slot
                ))
                session.commit()
                return "created"
            except OperationalError as exc:
                # Lock contention may fail closed instead of waiting on slower
                # Windows CI. A busy error is not permission to bypass checks.
                session.rollback()
                if "locked" not in str(exc).lower():
                    raise
                return "busy_fail_closed"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(create_one) for _ in range(2)]
        outcomes = [f.result(timeout=30) for f in futures]
    assert outcomes.count("created") == 1, outcomes
    assert set(outcomes) <= {"created", "conflict", "busy_fail_closed"}
    with Session() as session:
        assert session.query(SyntheticAppointment).filter_by(
            employer_id=7, datetime_start=slot
        ).count() == 1
    assert not filename.read_bytes().startswith(b"SQLite format 3")


def test_bot_claim_booking_and_status_roll_back_as_one_sqlcipher_transaction(encrypted_sessions):
    Session, _ = encrypted_sessions
    action_id = str(uuid.uuid4())
    with Session.begin() as session:
        session.add(SyntheticAction(
            id=action_id, user_id=11, employer_id=7, status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        ))

    with Session() as session:
        assert claim_pending_action(
            session, SyntheticAction, action_id, 11, 7, datetime.utcnow()
        )
        assert lock_cabinet_booking(session, 7)
        session.add(SyntheticAppointment(
            employer_id=7, datetime_start="2026-11-18T10:00:00"
        ))
        session.flush()
        session.query(SyntheticAction).filter_by(
            id=action_id, status="executing"
        ).update({"status": "executed"}, synchronize_session=False)
        session.flush()
        # A process crash before COMMIT discards all these writes.
        session.rollback()

    with Session() as session:
        assert session.get(SyntheticAction, action_id).status == "pending"
        assert session.query(SyntheticAppointment).count() == 0
        assert claim_pending_action(
            session, SyntheticAction, action_id, 11, 7, datetime.utcnow()
        )
        assert lock_cabinet_booking(session, 7)
        session.add(SyntheticAppointment(
            employer_id=7, datetime_start="2026-11-18T10:00:00"
        ))
        session.query(SyntheticAction).filter_by(
            id=action_id, status="executing"
        ).update({"status": "executed"}, synchronize_session=False)
        session.commit()

    with Session() as session:
        assert session.get(SyntheticAction, action_id).status == "executed"
        assert session.query(SyntheticAppointment).count() == 1
        assert not claim_pending_action(
            session, SyntheticAction, action_id, 11, 7, datetime.utcnow()
        )
        session.rollback()


def test_real_process_crash_before_sqlcipher_commit_reverts_business_and_action(encrypted_sessions):
    """Abrupt child-process death is stronger evidence than session.rollback()."""
    Session, dbfile = encrypted_sessions
    action_id = str(uuid.uuid4())
    with Session.begin() as session:
        session.add(SyntheticAction(
            id=action_id, user_id=11, employer_id=7, status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        ))

    # Use actual SQLCipher DBAPI on the same encrypted database in a NEW
    # interpreter. os._exit prevents Python cleanup and normal DBAPI close.
    child_script = """
import os, sys
from sqlcipher3 import dbapi2
db = dbapi2.connect(sys.argv[1], timeout=15)
db.execute("PRAGMA key = '" + ("e" * 64) + "'")
assert db.execute("PRAGMA cipher_version").fetchone()[0]
db.execute("UPDATE bot_pending_actions SET status = 'executing' WHERE id = ?", (sys.argv[2],))
db.execute("INSERT INTO appointments (employer_id, datetime_start) VALUES (?, ?)", (7, "2026-11-19T15:00:00"))
db.execute("UPDATE bot_pending_actions SET status = 'executed' WHERE id = ?", (sys.argv[2],))
os._exit(0)  # no commit, no close: simulated hard worker crash
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", child_script, str(dbfile), action_id],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr

    # A genuinely fresh SQLCipher connection must observe rollback; its
    # encrypted file remains intact and a safe retry can claim pending.
    with Session() as session:
        assert session.get(SyntheticAction, action_id).status == "pending"
        assert session.query(SyntheticAppointment).count() == 0
        assert claim_pending_action(
            session, SyntheticAction, action_id, 11, 7, datetime.utcnow()
        )
        assert lock_cabinet_booking(session, 7)
        session.add(SyntheticAppointment(
            employer_id=7, datetime_start="2026-11-19T15:00:00"
        ))
        session.query(SyntheticAction).filter_by(
            id=action_id, status="executing",
        ).update({"status": "executed"}, synchronize_session=False)
        session.commit()
    with Session() as session:
        assert session.get(SyntheticAction, action_id).status == "executed"
        assert session.query(SyntheticAppointment).count() == 1
    assert not dbfile.read_bytes().startswith(b"SQLite format 3")
