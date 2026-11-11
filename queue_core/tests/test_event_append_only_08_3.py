"""LOT08.3-A — real SQLite append-only event ledger FUE-0.

Synthetic, independent database: no clinical tables, installable or patient data.
Only existing event facts are protected; future authenticated retention/purge
needs its own explicit lifecycle contract and must not bypass this protection.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from queue_core.persistence import QueueBase
from queue_core.persistence.models import QueueEventRecord, QueueTenant


def _event(event_id: str, version: int) -> QueueEventRecord:
    return QueueEventRecord(
        id=event_id, tenant_id="TENANT_SYNTH", visit_ref="VISIT_SYNTH",
        aggregate_version=version,
        event_type="CALLED" if version == 1 else "RECALLED",
        state_before="WAITING" if version == 1 else "CALLED",
        state_after="CALLED",
        occurred_at_utc=datetime(2030, 2, 1, 10, tzinfo=timezone.utc),
        actor_kind="HUMAN", actor_ref="STAFF_SYNTH",
    )


def test_event_ledger_sql_direct_update_delete_denied_after_restart(tmp_path):
    db_path = tmp_path / "isolated-queue-events.sqlite"
    uri = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(uri)
    try:
        QueueBase.metadata.create_all(engine)
        with Session(engine) as db:
            db.add(QueueTenant(
                id="TENANT_SYNTH", timezone_name="Africa/Casablanca",
                created_at_utc=datetime(2030, 2, 1, tzinfo=timezone.utc),
            ))
            db.commit()
            db.add(_event("EVENT1", 1))
            db.commit()
    finally:
        engine.dispose()

    # Reconnect as a new engine. SQL direct must be denied at the database
    # boundary, not merely through a Python ORM or service validation.
    reopened = create_engine(uri)
    try:
        with reopened.connect() as db:
            triggers = set(db.execute(text(
                "SELECT name FROM sqlite_master WHERE type='trigger' "
                "AND tbl_name='queue_event_log'"
            )).scalars())
        assert {"queue_event_log_no_update", "queue_event_log_no_delete"} <= triggers

        with pytest.raises(IntegrityError, match="QUEUE_EVENT_IMMUTABLE"):
            with reopened.begin() as db:
                db.execute(text(
                    "UPDATE queue_event_log SET actor_ref='FORGED' WHERE id='EVENT1'"
                ))
        with pytest.raises(IntegrityError, match="QUEUE_EVENT_IMMUTABLE"):
            with reopened.begin() as db:
                db.execute(text("DELETE FROM queue_event_log WHERE id='EVENT1'"))
        with reopened.connect() as db:
            row = db.execute(text(
                "SELECT actor_ref, aggregate_version, event_type "
                "FROM queue_event_log WHERE id='EVENT1'"
            )).one()
            assert tuple(row) == ("STAFF_SYNTH", 1, "CALLED")
            assert db.scalar(text("SELECT count(*) FROM queue_event_log")) == 1

        # Append still works after both attempted tamper operations.
        with Session(reopened) as db:
            db.add(_event("EVENT2", 2))
            db.commit()
        with reopened.connect() as db:
            assert db.scalar(text("SELECT count(*) FROM queue_event_log")) == 2
    finally:
        reopened.dispose()
