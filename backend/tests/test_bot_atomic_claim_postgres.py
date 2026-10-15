"""Real PostgreSQL two-connection CAS tests for production claim helper.

No backend package, clinical data or migrations are involved. The same function
is invoked by /api/bot/execute on the production mapped BotPendingAction table.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import importlib.util
import os
from pathlib import Path
import sys
from threading import Barrier
import unittest
import uuid

from sqlalchemy import DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


SOURCE = Path(__file__).resolve().parents[1] / "services" / "bot" / "atomic_action_claim.py"
SPEC = importlib.util.spec_from_file_location("isolated_atomic_action_claim", SOURCE)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
claim_pending_action = MODULE.claim_pending_action
transition_pending_action = MODULE.transition_pending_action

LOCK_SOURCE = Path(__file__).resolve().parents[1] / "services" / "agenda_transaction_lock.py"
LOCK_SPEC = importlib.util.spec_from_file_location("isolated_agenda_transaction_lock", LOCK_SOURCE)
assert LOCK_SPEC is not None and LOCK_SPEC.loader is not None
LOCK_MODULE = importlib.util.module_from_spec(LOCK_SPEC)
sys.modules[LOCK_SPEC.name] = LOCK_MODULE
LOCK_SPEC.loader.exec_module(LOCK_MODULE)
lock_cabinet_booking = LOCK_MODULE.lock_cabinet_booking



class Base(DeclarativeBase):
    pass


class ClaimRow(Base):
    __tablename__ = "synthetic_bot_claim_ci"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    employer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)



class BookingRow(Base):
    __tablename__ = "synthetic_booking_txn_ci"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    slot: Mapped[str] = mapped_column(String(32), nullable=False)

@unittest.skipUnless(
    os.getenv("CROWN_BOT_CAS_TEST_DB_URL"),
    "requires explicit PostgreSQL URL; not an in-memory SQLite simulation",
)
class TestPostgresAtomicBotClaim(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            os.environ["CROWN_BOT_CAS_TEST_DB_URL"],
            pool_pre_ping=True, connect_args={"connect_timeout": 10},
        )
        if cls.engine.dialect.name != "postgresql":
            raise AssertionError("The concurrency gate must use actual PostgreSQL")
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def _row(self, *, status="pending", minutes=30):
        key = str(uuid.uuid4())
        with self.Session.begin() as session:
            session.add(ClaimRow(
                id=key, user_id=11, employer_id=22, status=status,
                expires_at=datetime.utcnow() + timedelta(minutes=minutes),
            ))
        return key

    def _claim(self, key, *, user=11, tenant=22):
        with self.Session() as session:
            outcome = claim_pending_action(
                session, ClaimRow, key, user, tenant, datetime.utcnow()
            )
            session.commit()
            return outcome

    def test_concurrent_two_postgres_connections_only_one_wins(self):
        key = self._row()
        both_started = Barrier(2)

        def worker():
            with self.Session() as session:
                both_started.wait(timeout=10)
                claimed = claim_pending_action(
                    session, ClaimRow, key, 11, 22, datetime.utcnow()
                )
                session.commit()
                return claimed

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(worker) for _ in range(2)]
            results = [future.result(timeout=15) for future in futures]

        self.assertEqual(sorted(results), [False, True])
        with self.Session() as session:
            self.assertEqual(session.get(ClaimRow, key).status, "executing")
        self.assertFalse(self._claim(key))

    def test_wrong_owner_and_wrong_tenant_never_claim(self):
        key = self._row()
        self.assertFalse(self._claim(key, user=12))
        self.assertFalse(self._claim(key, tenant=23))
        self.assertTrue(self._claim(key))

    def test_expiry_and_stale_executing_fail_closed(self):
        expired = self._row(minutes=-1)
        inflight = self._row(status="executing")
        self.assertFalse(self._claim(expired))
        self.assertFalse(self._claim(inflight))


    def test_cancel_and_execute_race_only_one_state_transition_wins(self):
        # Real two-connection PostgreSQL test for R2-01.
        key = self._row()
        together = Barrier(2)

        def worker(transition):
            with self.Session() as db:
                together.wait(timeout=10)
                if transition == "execute":
                    result = claim_pending_action(
                        db, ClaimRow, key, 11, 22, datetime.utcnow()
                    )
                else:
                    result = transition_pending_action(
                        db, ClaimRow, key, 11, 22,
                        new_status="cancelled", now=datetime.utcnow(),
                    )
                db.commit()
                return result

        with ThreadPoolExecutor(max_workers=2) as pool:
            one = pool.submit(worker, "execute")
            two = pool.submit(worker, "cancel")
            outcomes = [one.result(timeout=15), two.result(timeout=15)]
        self.assertEqual(sorted(outcomes), [False, True])
        with self.Session() as session:
            self.assertIn(session.get(ClaimRow, key).status, {"executing", "cancelled"})

    def test_expire_and_execute_at_ttl_boundary_never_overwrite(self):
        # Simulated opposing clocks at expiry boundary with real row locking:
        # whichever pending-only update commits first owns the row.
        key = self._row(minutes=1)
        together = Barrier(2)

        def worker(expiring):
            with self.Session() as session:
                together.wait(timeout=10)
                if expiring:
                    result = transition_pending_action(
                        session, ClaimRow, key, 11, 22,
                        new_status="expired",
                        now=datetime.utcnow() + timedelta(minutes=2),
                        expired=True,
                    )
                else:
                    result = claim_pending_action(
                        session, ClaimRow, key, 11, 22, datetime.utcnow()
                    )
                session.commit()
                return result

        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(worker, True)
            b = pool.submit(worker, False)
            self.assertEqual(sorted([a.result(timeout=15), b.result(timeout=15)]),
                             [False, True])
        with self.Session() as session:
            self.assertIn(session.get(ClaimRow, key).status, {"expired", "executing"})

    def test_stale_cancel_and_expiry_cannot_change_executing(self):
        key = self._row()
        self.assertTrue(self._claim(key))
        with self.Session() as db:
            self.assertFalse(transition_pending_action(
                db, ClaimRow, key, 11, 22,
                new_status="cancelled", now=datetime.utcnow(),
            ))
            self.assertFalse(transition_pending_action(
                db, ClaimRow, key, 11, 22,
                new_status="expired",
                now=datetime.utcnow() + timedelta(days=1),
                expired=True,
            ))
            db.commit()
        with self.Session() as db:
            self.assertEqual(db.get(ClaimRow, key).status, "executing")

    def test_transactional_booking_and_status_commit_or_rollback_together(self):
        """Crash BEFORE the only commit leaves neither action nor appointment."""
        key = self._row()
        with self.Session() as session:
            self.assertTrue(claim_pending_action(
                session, ClaimRow, key, 11, 22, datetime.utcnow()
            ))
            session.add(BookingRow(employer_id=22, slot="2026-10-16T10:00"))
            session.flush()
            session.query(ClaimRow).filter(
                ClaimRow.id == key, ClaimRow.status == "executing",
            ).update({"status": "executed"}, synchronize_session=False)
            session.flush()
            # Simulates PostgreSQL automatically aborting an uncommitted
            # transaction after the worker dies between flush and COMMIT.
            session.rollback()

        with self.Session() as session:
            self.assertEqual(session.get(ClaimRow, key).status, "pending")
            self.assertEqual(session.query(BookingRow).filter_by(
                employer_id=22, slot="2026-10-16T10:00"
            ).count(), 0)

        with self.Session() as session:
            self.assertTrue(claim_pending_action(
                session, ClaimRow, key, 11, 22, datetime.utcnow()
            ))
            session.add(BookingRow(employer_id=22, slot="2026-10-16T10:00"))
            session.query(ClaimRow).filter(
                ClaimRow.id == key, ClaimRow.status == "executing",
            ).update({"status": "executed"}, synchronize_session=False)
            session.commit()

        with self.Session() as session:
            self.assertEqual(session.get(ClaimRow, key).status, "executed")
            self.assertEqual(session.query(BookingRow).filter_by(
                employer_id=22, slot="2026-10-16T10:00"
            ).count(), 1)
            self.assertFalse(claim_pending_action(
                session, ClaimRow, key, 11, 22, datetime.utcnow()
            ))
            session.rollback()

    def test_distinct_action_ids_cannot_double_book_same_slot_under_tenant_lock(self):
        """PostgreSQL xact advisory lock serializes actual check then INSERT."""
        action_a, action_b = self._row(), self._row()
        slot = "2026-10-20T11:00"
        barrier = Barrier(2)

        def book(action_id):
            with self.Session() as session:
                barrier.wait(timeout=15)
                self.assertTrue(claim_pending_action(
                    session, ClaimRow, action_id, 11, 22, datetime.utcnow()
                ))
                self.assertTrue(lock_cabinet_booking(session, 22))
                has_conflict = session.query(BookingRow).filter_by(
                    employer_id=22, slot=slot,
                ).first()
                if has_conflict is not None:
                    session.rollback()
                    return "conflict"
                session.add(BookingRow(employer_id=22, slot=slot))
                session.query(ClaimRow).filter(
                    ClaimRow.id == action_id, ClaimRow.status == "executing",
                ).update({"status": "executed"}, synchronize_session=False)
                session.commit()
                return "committed"

        with ThreadPoolExecutor(max_workers=2) as pool:
            x = pool.submit(book, action_a)
            y = pool.submit(book, action_b)
            results = [x.result(timeout=25), y.result(timeout=25)]
        self.assertEqual(sorted(results), ["committed", "conflict"])
        with self.Session() as session:
            self.assertEqual(session.query(BookingRow).filter_by(
                employer_id=22, slot=slot,
            ).count(), 1)
            statuses = [
                session.get(ClaimRow, action_a).status,
                session.get(ClaimRow, action_b).status,
            ]
            self.assertEqual(sorted(statuses), ["executed", "pending"])
