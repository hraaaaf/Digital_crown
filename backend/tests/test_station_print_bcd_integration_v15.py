"""04.8 B/C integrated SQL LAB on one engine (nothing is printed).

This is the first shared-database proof of the independent draft catalog and
held-ledger modules. All patient/session keys are synthetic. No API, device,
real archive, printer or live Cabinet database is used.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, event, insert, inspect, select
from sqlalchemy.exc import IntegrityError

from backend.services.station_print_printer_draft_lab import (
    draft_printers, register_unverified_draft, list_unverified_drafts,
    unverified_drafts_are_never_trusted, PrinterDraftConflict,
)
from backend.services.station_print_held_claims_lab import (
    claims, claim_events, reserve_held_claim, get_claim, mark_uncertain,
    PrintClaimDuplicate, PrintClaimRejected,
)
from backend.services.station_document_print_configuration import (
    compile_owner_print_config, PrintConfigurationRejected,
    TrustedStation,
)


def make_engine(path: Path):
    engine = create_engine(
        "sqlite+pysqlite:///" + str(path), connect_args={"timeout": 15}
    )
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")
    return engine


def tables_on_engine(engine):
    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    draft_printers.to_metadata(metadata)
    claims.to_metadata(metadata)
    claim_events.to_metadata(metadata)
    metadata.create_all(engine)  # isolated SQLite, never Cabinet DDL
    with engine.begin() as connection:
        connection.execute(insert(metadata.tables["users"]), [{"id": 10}, {"id": 20}])
    return metadata


def test_shared_database_draft_and_claim_remain_separately_inert(tmp_path):
    engine = make_engine(tmp_path / "integrated.sqlite")
    tables_on_engine(engine)
    rev = register_unverified_draft(
        engine, tenant_id=10, actor_user_id=10, actor_employer_id=None,
        printer_id="desk1", location="reception", station_id=None,
        expected_revision=0,
    )
    assert rev == 1
    draft = list_unverified_drafts(engine, tenant_id=10)
    inventory = unverified_drafts_are_never_trusted(draft)
    assert inventory["desk1"].enabled is False
    with pytest.raises(PrintConfigurationRejected):
        compile_owner_print_config(
            tenant_id=10, actor_user_id=10, actor_employer_id=None,
            raw={"schemaVersion": 1, "mode": "reception",
                 "stationIds": ["station1"], "printerIds": ["desk1"]},
            trusted_stations={"station1": TrustedStation("station1", 10, "station")},
            trusted_printers=inventory,
        )
    held = reserve_held_claim(
        engine, tenant_id=10, session_id="session1", document_kind="care_sheet",
        document_id="synthetic1", document_sha256="a" * 64, printer_id="desk1",
    )
    assert held.state == "held"
    with engine.connect() as connection:
        entries = connection.execute(select(
            claim_events.c.revision, claim_events.c.transition
        ).where(claim_events.c.tenant_id == 10)).all()
    assert entries == [(1, "held_reserved")]
    with pytest.raises(PrintClaimDuplicate):
        reserve_held_claim(
            engine, tenant_id=10, session_id="session1", document_kind="care_sheet",
            document_id="synthetic1", document_sha256="a" * 64, printer_id="near1",
        )
    with engine.connect() as conn:
        assert conn.execute(select(claims.c.first_printer_id)).scalar_one() == "desk1"
        assert conn.execute(select(draft_printers.c.printer_id)).scalar_one() == "desk1"
    engine.dispose()


def test_claim_survives_engine_restart_and_uncertain_cannot_be_replayed(tmp_path):
    path = tmp_path / "recovered.sqlite"
    engine = make_engine(path)
    tables_on_engine(engine)
    held = reserve_held_claim(
        engine, tenant_id=10, session_id="session1", document_kind="care_sheet",
        document_id="doc1", document_sha256="b" * 64, printer_id="desk1",
    )
    engine.dispose()
    restart = make_engine(path)
    assert get_claim(restart, tenant_id=10, delivery_key=held.delivery_key) == held
    uncertain = mark_uncertain(
        restart, tenant_id=10, delivery_key=held.delivery_key, expected_revision=1,
    )
    assert uncertain.state == "uncertain"
    with restart.connect() as connection:
        events = connection.execute(select(
            claim_events.c.revision, claim_events.c.transition
        ).where(
            claim_events.c.tenant_id == 10,
            claim_events.c.delivery_key == held.delivery_key,
        ).order_by(claim_events.c.revision)).all()
    assert events == [(1, "held_reserved"), (2, "marked_uncertain")]
    with pytest.raises(PrintClaimDuplicate):
        reserve_held_claim(
            restart, tenant_id=10, session_id="session1", document_kind="care_sheet",
            document_id="doc1", document_sha256="b" * 64, printer_id="near1",
        )
    restart.dispose()


def test_physical_tenant_fk_and_cross_tenant_query(tmp_path):
    engine = make_engine(tmp_path / "tenants.sqlite")
    tables_on_engine(engine)
    with pytest.raises(PrinterDraftConflict):
        register_unverified_draft(
            engine, tenant_id=999, actor_user_id=999, actor_employer_id=None,
            printer_id="desk1", location="reception", station_id=None,
            expected_revision=0,
        )
    assert list_unverified_drafts(engine, tenant_id=20) == ()
    with engine.connect() as conn:
        assert conn.execute(select(draft_printers)).all() == []
        assert conn.execute(select(claims)).all() == []
        assert {row["referred_table"] for row in inspect(conn).get_foreign_keys("station_print_printer_drafts")} == {"users"}
        assert {row["referred_table"] for row in inspect(conn).get_foreign_keys("station_print_held_claims")} == {"users"}
    engine.dispose()


def test_no_valid_public_print_destination_is_possible_from_combined_lab(tmp_path):
    engine = make_engine(tmp_path / "gates.sqlite")
    tables_on_engine(engine)
    for location, printer, station in (
        ("reception", "frontdesk", None), ("near_station", "nearstation", "station1"),
    ):
        register_unverified_draft(
            engine, tenant_id=10, actor_user_id=10, actor_employer_id=None,
            printer_id=printer, location=location, station_id=station,
            expected_revision=0,
        )
    inventory = unverified_drafts_are_never_trusted(
        list_unverified_drafts(engine, tenant_id=10)
    )
    with pytest.raises(PrintConfigurationRejected):
        compile_owner_print_config(
            tenant_id=10, actor_user_id=10, actor_employer_id=None,
            raw={"schemaVersion": 1, "mode": "both",
                 "stationIds": ["station1"], "printerIds": ["frontdesk", "nearstation"]},
            trusted_stations={"station1": TrustedStation("station1", 10, "station")},
            trusted_printers=inventory,
        )
    engine.dispose()


def test_claim_write_rolls_back_if_audit_journal_is_unavailable(tmp_path):
    # Broken audit table MUST fail closed: never reserve a claim without an
    # auditable event. Ephemeral SQLite, not a Cabinet database.
    from sqlalchemy.exc import OperationalError

    engine = make_engine(tmp_path / "journal-failure.sqlite")
    tables_on_engine(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE station_print_claim_events")
    with pytest.raises(OperationalError):
        reserve_held_claim(
            engine, tenant_id=10, session_id="synthetic", document_kind="care_sheet",
            document_id="document1", document_sha256="f" * 64, printer_id="desk",
        )
    with engine.connect() as connection:
        assert connection.execute(select(claims.c.tenant_id)).all() == []
    engine.dispose()


def test_no_patient_data_in_claim_journal_or_print_ledger_schema():
    journal_cols = {column.name for column in claim_events.columns}
    assert journal_cols == {
        "event_id", "tenant_id", "delivery_key", "revision", "transition", "created_at",
    }
    assert not journal_cols.intersection({
        "patient_id", "session_id", "medical_record", "pdf", "token",
        "document_bytes", "patient_name",
    })
