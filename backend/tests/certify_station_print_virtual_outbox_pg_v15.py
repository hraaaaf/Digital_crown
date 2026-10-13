#!/usr/bin/env python3
"""04.8-C PostgreSQL real two-process virtual outbox concurrency certification.

Disposable schema and fixed nonclinical identity only. The script NEVER
calls CUPS itself; the paired separate CUPS job tests the synthetic side
effect after this one-shot fence. No clinical permit or production DDL.
"""
from __future__ import annotations

import os
import subprocess
import sys
import types

from sqlalchemy import create_engine, insert, select, text

for name, root in (("backend", "backend"), ("backend.services", "backend/services")):
    pkg = types.ModuleType(name)
    pkg.__path__ = [os.path.abspath(root)]
    sys.modules[name] = pkg

from backend.services.station_print_held_claims_lab import (
    SCHEMA, claims, claim_events,
)
from backend.services.station_print_virtual_outbox_lab_v15 import (
    SYNTHETIC_TENANT, SYNTHETIC_DELIVERY_KEY,
    virtual_outbox, VirtualLabDuplicate, VirtualLabRejected,
    reserve_synthetic_outbox, fence_virtual_attempt, read_synthetic_outbox,
)

SCHEMA_NAME = "dc_virtual_outbox_pg_lab"


def db():
    uri = os.environ.get("DATABASE_URL", "")
    if not uri.startswith(("postgresql://", "postgresql+")):
        raise RuntimeError("POSTGRES_ONLY")
    return create_engine(
        uri,
        connect_args={"options": "-csearch_path=" + SCHEMA_NAME},
        pool_pre_ping=True,
    )


def run_worker(operation: str):
    engine = db()
    try:
        if operation == "reserve":
            result = reserve_synthetic_outbox(engine)
            assert (result.state, result.attempts) == ("reserved", 0)
            print("RESERVATION_WIN")
        elif operation == "fence":
            result = fence_virtual_attempt(engine)
            assert (result.state, result.attempts) == ("attempted", 1)
            print("FENCE_WIN")
        else:
            raise RuntimeError("BAD_OPERATION")
        return 0
    except (VirtualLabDuplicate, VirtualLabRejected):
        print("DUPLICATE_OR_REPLAY_DENIED")
        return 7
    finally:
        engine.dispose()


def race(operation: str):
    # Independent OS processes, independent SQLAlchemy engine pools and PG
    # connections. Only one worker can reserve/fence an identity.
    children = [
        subprocess.Popen(
            [sys.executable, __file__, operation],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=dict(os.environ),
        )
        for _ in range(2)
    ]
    exits = []
    for child in children:
        stdout, stderr = child.communicate(timeout=40)
        print(stdout.strip())
        if stderr.strip():
            print(stderr.strip(), file=sys.stderr)
        exits.append(child.returncode)
    assert sorted(exits) == [0, 7], (operation, exits)


def main():
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    assert os.environ.get("DC_SYNTHETIC_VIRTUAL_SPOOL_LAB") == "1"
    root = create_engine(os.environ["DATABASE_URL"])
    with root.begin() as conn:
        conn.execute(text("CREATE SCHEMA " + SCHEMA_NAME))
    root.dispose()
    engine = db()
    SCHEMA.create_all(engine)
    with engine.begin() as conn:
        conn.execute(insert(SCHEMA.tables["users"]).values(id=SYNTHETIC_TENANT))
    engine.dispose()

    race("reserve")
    engine = db()
    with engine.connect() as conn:
        assert conn.execute(select(claims.c.state)).scalars().all() == ["held"]
        assert conn.execute(
            select(claim_events.c.revision, claim_events.c.transition)
            .order_by(claim_events.c.revision)
        ).all() == [(1, "held_reserved")]
        assert conn.execute(select(virtual_outbox.c.state)).scalars().all() == ["reserved"]
    engine.dispose()

    race("fence")
    restarted = db()
    with restarted.connect() as conn:
        assert conn.execute(select(claims.c.state)).scalars().all() == ["uncertain"]
        assert conn.execute(
            select(claim_events.c.revision, claim_events.c.transition)
            .order_by(claim_events.c.revision)
        ).all() == [(1, "held_reserved"), (2, "marked_uncertain")]
        assert conn.execute(select(virtual_outbox.c.attempts)).scalars().all() == [1]
    assert read_synthetic_outbox(restarted).state == "attempted"
    try:
        fence_virtual_attempt(restarted)
    except VirtualLabRejected:
        pass
    else:
        raise AssertionError("second attempt granted after engine restart")
    restarted.dispose()

    print(
        "PG_VIRTUAL_OUTBOX_PASS reserve_os_workers=2 reserve_winners=1 "
        "fence_os_workers=2 fence_winners=1 journal_revisions=2 "
        "post_crash_replay_blocked=1 physical_print=0 clinical_permit=0"
    )


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] in {"reserve", "fence"}:
        raise SystemExit(run_worker(sys.argv[1]))
    if len(sys.argv) != 1:
        raise SystemExit("INVALID_LAB_INVOCATION")
    main()
