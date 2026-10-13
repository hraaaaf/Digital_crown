"""LAB-only print claim tests: atomic unique claim across printer destinations."""
import concurrent.futures

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import QueuePool

from backend.services.station_print_held_claims_lab import (
    SCHEMA, claims, HeldClaim, PrintClaimDuplicate, PrintClaimRejected,
    reserve_held_claim, mark_uncertain, get_claim,
)


@pytest.fixture
def engine():
    db = create_engine("sqlite+pysqlite:///:memory:")
    SCHEMA.create_all(db)
    yield db
    db.dispose()


def reserve(engine, *, tenant=10, session="station_session", kind="care_sheet",
            document="doc1", sha="a" * 64, printer="desk1"):
    return reserve_held_claim(
        engine, tenant_id=tenant, session_id=session,
        document_kind=kind, document_id=document,
        document_sha256=sha, printer_id=printer,
    )


def test_first_claim_is_held_and_not_dispatched(engine):
    result = reserve(engine)
    assert len(result.delivery_key) == 64
    assert (result.tenant_id, result.state, result.revision) == (10, "held", 1)
    assert get_claim(engine, tenant_id=10, delivery_key=result.delivery_key) == result
    assert set(claims.c.keys()) == {
        "tenant_id", "delivery_key", "first_printer_id", "state",
        "revision", "created_at", "updated_at",
    }


def test_duplicate_destination_and_cross_destination_both_denied(engine):
    original = reserve(engine)
    for printer in ("desk1", "near1"):
        with pytest.raises(PrintClaimDuplicate, match="ALREADY_CLAIMED"):
            reserve(engine, printer=printer)
    with engine.connect() as conn:
        rows = conn.execute(select(claims.c.first_printer_id)).scalars().all()
    assert rows == ["desk1"]


def test_same_document_two_sessions_separate_claims(engine):
    a = reserve(engine, session="s1")
    b = reserve(engine, session="s2")
    assert a.delivery_key != b.delivery_key


def test_tenant_isolation(engine):
    a = reserve(engine, tenant=10)
    b = reserve(engine, tenant=11)
    assert a.delivery_key != b.delivery_key
    assert get_claim(engine, tenant_id=11, delivery_key=a.delivery_key) is None


def test_uncertain_transition_is_one_way_and_still_blocks_reprint(engine):
    original = reserve(engine)
    uncertain = mark_uncertain(engine, tenant_id=10,
                               delivery_key=original.delivery_key, expected_revision=1)
    assert uncertain.state == "uncertain"
    assert uncertain.revision == 2
    with pytest.raises(PrintClaimRejected, match="INVALID_TRANSITION"):
        mark_uncertain(engine, tenant_id=10,
                       delivery_key=original.delivery_key, expected_revision=2)
    with pytest.raises(PrintClaimDuplicate):
        reserve(engine, printer="near1")


@pytest.mark.parametrize("kwargs", [
    {"tenant": True}, {"tenant": -1}, {"tenant": "10"},
    {"session": ""}, {"session": "station|foo"}, {"kind": "unknown"},
    {"document": ""}, {"sha": "b" * 63}, {"sha": "A" * 64},
    {"printer": ""}, {"printer": "../foo"}, {"printer": "x" * 81},
])
def test_malformed_or_spoofed_identity_cannot_write(engine, kwargs):
    with pytest.raises(PrintClaimRejected):
        reserve(engine, **kwargs)
    with engine.connect() as conn:
        assert conn.execute(select(claims)).all() == []


def test_invalid_uncertain_never_mutates(engine):
    original = reserve(engine)
    for tenant, key, rev in [
        (11, original.delivery_key, 1),
        (10, original.delivery_key, 0),
        (10, original.delivery_key, 2),
        (10, "bad", 1),
    ]:
        with pytest.raises(PrintClaimRejected):
            mark_uncertain(engine, tenant_id=tenant, delivery_key=key, expected_revision=rev)
    assert get_claim(engine, tenant_id=10, delivery_key=original.delivery_key) == original


def test_separate_sql_connections_race_winner_is_unique(tmp_path):
    db = create_engine(
        "sqlite+pysqlite:///" + str(tmp_path / "claims.sqlite"),
        poolclass=QueuePool,
        connect_args={"check_same_thread": False, "timeout": 15},
    )
    SCHEMA.create_all(db)
    def contender(printer):
        try:
            return reserve(db, printer=printer)
        except PrintClaimDuplicate:
            return "duplicate"
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(contender, ("desk1", "near1")))
    assert sum(isinstance(v, HeldClaim) for v in values) == 1, values
    assert values.count("duplicate") == 1
    with db.connect() as conn:
        all_rows = conn.execute(select(claims)).all()
    assert len(all_rows) == 1
    db.dispose()
