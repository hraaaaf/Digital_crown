#!/usr/bin/env python3
"""04.8 C: subprocess PostgreSQL concurrency against a disposable SQL-only lab schema.

Uses REAL SQLAlchemy reserve_held_claim and mark_uncertain, not mocked SQL.
No actual Cabinet user, PDF, patient, printer, network agent or production data.
"""
from __future__ import annotations

import os
import subprocess
import sys
import types

from sqlalchemy import create_engine, insert, select, text
from sqlalchemy.exc import SQLAlchemyError

for module_name, directory in (("backend", "backend"), ("backend.services", "backend/services")):
    package = types.ModuleType(module_name)
    package.__path__ = [os.path.abspath(directory)]
    sys.modules[module_name] = package

from backend.services.station_print_held_claims_lab import (
    SCHEMA, claims, claim_events, PrintClaimDuplicate, reserve_held_claim,
    mark_uncertain, get_claim,
)

SCHEMA_NAME = "dc_station_print_claim_pg_lab"


def engine_for_lab():
    uri = os.environ.get("DATABASE_URL", "")
    if not uri.startswith(("postgresql://", "postgresql+")):
        raise RuntimeError("LAB REQUIRES POSTGRES; refuse SQLite or missing URI")
    return create_engine(
        uri,
        connect_args={"options": "-csearch_path=" + SCHEMA_NAME},
        pool_pre_ping=True,
    )


def reserve(engine, printer):
    return reserve_held_claim(
        engine,
        tenant_id=10, session_id="SYNTHETIC_RACE_SESSION",
        document_kind="care_sheet", document_id="SYNTHETIC_DOCUMENT",
        document_sha256="e" * 64, printer_id=printer,
    )


def worker(printer: str):
    engine = engine_for_lab()
    try:
        result = reserve(engine, printer)
        assert result.state == "held"
        print("RESERVED " + printer)
        return 0
    except PrintClaimDuplicate:
        print("DUPLICATE_DENIED " + printer)
        return 7
    finally:
        engine.dispose()


def main():
    base_uri = os.environ["DATABASE_URL"]
    root = create_engine(base_uri)
    with root.begin() as connection:
        connection.execute(text("CREATE SCHEMA " + SCHEMA_NAME))
    root.dispose()

    engine = engine_for_lab()
    SCHEMA.create_all(engine)
    with engine.begin() as connection:
        connection.execute(insert(SCHEMA.tables["users"]).values(id=10))
    engine.dispose()

    # TWO genuinely independent OS processes/PG sessions contend for the
    # SAME document identity but DIFFERENT printer IDs.
    cmds = []
    for printer in ("reception", "near_station"):
        cmds.append(subprocess.Popen(
            [sys.executable, __file__, "reserve", printer],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=dict(os.environ),
        ))
    results = []
    for proc in cmds:
        stdout, stderr = proc.communicate(timeout=45)
        print(stdout.strip())
        if stderr.strip():
            print(stderr.strip(), file=sys.stderr)
        results.append(proc.returncode)
    assert sorted(results) == [0, 7], f"expected one win, one duplicate: {results}"

    engine = engine_for_lab()  # fresh connection pool emulates a worker restart
    with engine.connect() as connection:
        all_claims = connection.execute(select(claims)).mappings().all()
        journal = connection.execute(
            select(claim_events.c.revision, claim_events.c.transition)
            .order_by(claim_events.c.revision)
        ).all()
    assert len(all_claims) == 1
    assert journal == [(1, "held_reserved")], journal
    entry = all_claims[0]
    assert entry["state"] == "held" and entry["revision"] == 1
    assert entry["first_printer_id"] in {"reception", "near_station"}
    delivery_key = entry["delivery_key"]

    # No recovery auto-retry: a crash/ambiguous spool report transitions the
    # same reservation to UNCERTAIN with an atomic journal entry.
    uncertain = mark_uncertain(
        engine, tenant_id=10, delivery_key=delivery_key, expected_revision=1
    )
    assert uncertain.state == "uncertain" and uncertain.revision == 2
    with engine.connect() as connection:
        journal = connection.execute(
            select(claim_events.c.revision, claim_events.c.transition)
            .order_by(claim_events.c.revision)
        ).all()
    assert journal == [(1, "held_reserved"), (2, "marked_uncertain")]

    restarted = engine_for_lab()
    assert get_claim(restarted, tenant_id=10, delivery_key=delivery_key).state == "uncertain"
    try:
        reserve(restarted, "third_destination")
    except PrintClaimDuplicate:
        pass
    else:
        raise AssertionError("post-restart replay/destination switch was accepted")

    # The journal is a required part of the SAME transaction. If it
    # disappears, new reservations must fail and roll back completely.
    # This intentionally drops a table only in the disposable TEST schema.
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE station_print_claim_events"))
    try:
        reserve_held_claim(
            restarted,
            tenant_id=10, session_id="SYNTHETIC_SECOND_SESSION",
            document_kind="care_sheet", document_id="SYNTHETIC_DOCUMENT",
            document_sha256="a" * 64, printer_id="reception",
        )
    except SQLAlchemyError:
        pass
    else:
        raise AssertionError("claim committed without audit journal")
    with restarted.connect() as connection:
        assert connection.execute(select(claims.c.delivery_key)).all() == [(delivery_key,)]
    restarted.dispose()
    engine.dispose()
    print(
        "PG_MULTIPROCESS_CLAIM_PASS two_independent_connections=2 "
        "unique_winners=1 duplicate_denied=1 events=2 "
        "uncertain_replay_denied=1 rollback_on_audit_failure=1 "
        "no_patient_data=1 physical_print=0"
    )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "reserve":
        raise SystemExit(worker(sys.argv[2]))
    if len(sys.argv) != 1:
        raise SystemExit("invalid runner args")
    main()
