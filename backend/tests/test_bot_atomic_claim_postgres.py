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


class Base(DeclarativeBase):
    pass


class ClaimRow(Base):
    __tablename__ = "synthetic_bot_claim_ci"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    employer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


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
