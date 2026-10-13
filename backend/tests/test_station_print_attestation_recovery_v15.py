"""04.8 field-evidence intake and UNCERTAIN investigation — no print enable.

A real SQL transaction and real composite tenant FKs are exercised against
SYNTHETIC records only. Physical witness/certification is exclusively LOT10.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, insert, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.pool import QueuePool

from backend.services.station_print_held_claims_lab import (
    SCHEMA, claims, claim_events, reserve_held_claim, mark_uncertain,
    get_claim, PrintClaimRejected, PrintClaimDuplicate,
)
from backend.services.station_print_attestation_recovery_v15 import (
    device_evidence, uncertain_reviews,
    record_pending_device_evidence, record_uncertain_investigation,
    inspect_uncertain_reviews, PrintReviewRejected, PrintReviewConflict,
)


@pytest.fixture
def engine(tmp_path):
    eng=create_engine(
        "sqlite+pysqlite:///"+str(tmp_path/"reviews.sqlite"),
        connect_args={"check_same_thread": False, "timeout": 20},
        poolclass=QueuePool,
    )
    @event.listens_for(eng, "connect")
    def fk(raw, _):
        raw.execute("PRAGMA foreign_keys=ON")
    SCHEMA.create_all(eng)
    with eng.begin() as c:
        c.execute(insert(SCHEMA.tables["users"]), [{"id":10}, {"id":20}])
        c.execute(insert(SCHEMA.tables["station_print_printer_drafts"]), [
            {"tenant_id":10,"printer_id":"frontdesk","location":"reception",
             "station_id":None,"revision":1,"updated_by":10,"updated_at":datetime(2026,10,13,tzinfo=timezone.utc)},
            {"tenant_id":20,"printer_id":"frontdesk","location":"reception",
             "station_id":None,"revision":1,"updated_by":20,"updated_at":datetime(2026,10,13,tzinfo=timezone.utc)},
        ])
    yield eng
    eng.dispose()


def owner(tenant=10):
    return {"tenant_id":tenant,"actor_user_id":tenant,"actor_employer_id":None}


def pending(engine, **extra):
    kwargs={**owner(), "printer_id":"frontdesk", "evidence_sha256":"a"*64}
    kwargs.update(extra)
    return record_pending_device_evidence(engine,**kwargs)


def uncertain(engine, tenant=10):
    claim=reserve_held_claim(
        engine, tenant_id=tenant, session_id="fake-session",
        document_kind="care_sheet", document_id="fake-doc",
        document_sha256="b"*64, printer_id="frontdesk",
    )
    mark_uncertain(engine, tenant_id=tenant, delivery_key=claim.delivery_key, expected_revision=1)
    return claim


def review(engine, delivery_key, **extra):
    kwargs={**owner(), "delivery_key":delivery_key, "finding":"investigating",
            "evidence_sha256":"c"*64}
    kwargs.update(extra)
    return record_uncertain_investigation(engine,**kwargs)


def test_evidence_is_pending_only_and_does_not_certify_a_destination(engine):
    receipt=pending(engine)
    assert (receipt.status,receipt.printing_enabled)==("pending_field_verification",False)
    with engine.connect() as c:
        evidence=c.execute(select(device_evidence)).mappings().one()
    assert evidence["status"]=="pending_field_verification"
    assert evidence["recorded_by"]==10
    from backend.services.station_document_print_inventory import independently_certified_printers_for_tenant
    assert independently_certified_printers_for_tenant(None,tenant_id=10)=={}


def test_evidence_fk_rejects_unknown_printer_or_cross_tenant_provenance(engine):
    with pytest.raises(PrintReviewConflict):
        pending(engine,printer_id="unregistered")
    with pytest.raises(PrintReviewConflict):
        pending(engine,tenant_id=21,actor_user_id=21)
    assert pending(engine,tenant_id=20,actor_user_id=20).status=="pending_field_verification"
    with engine.connect() as c:
        assert c.execute(select(device_evidence.c.tenant_id)).scalars().all()==[20]


def test_concurrent_duplicate_evidence_cannot_replace_existing_digest(engine):
    with ThreadPoolExecutor(max_workers=2) as pool:
        def submit(_):
            try:
                return pending(engine)
            except PrintReviewConflict:
                return "duplicate"
        results=list(pool.map(submit,[1,2]))
    assert sum(x!="duplicate" for x in results)==1
    assert results.count("duplicate")==1
    with engine.connect() as c:
        assert len(c.execute(select(device_evidence)).all())==1


@pytest.mark.parametrize("change",[
    {"actor_user_id":11}, {"actor_employer_id":10},
    {"tenant_id":True,"actor_user_id":True},
    {"evidence_sha256":"x"*64},
    {"evidence_sha256":"a"*63}, {"printer_id":"../device"},
])
def test_no_browser_flag_or_untrusted_actor_can_attest(engine,change):
    with pytest.raises(PrintReviewRejected):
        pending(engine,**change)
    with engine.connect() as c:
        assert c.execute(select(device_evidence)).all()==[]


def test_database_check_constraint_cannot_mark_evidence_certified(engine):
    pending(engine)
    with pytest.raises(IntegrityError):
        with engine.begin() as c:
            c.execute(text("UPDATE station_print_device_evidence SET status='certified'"))
    with engine.connect() as c:
        assert c.execute(select(device_evidence.c.status)).scalar_one()=="pending_field_verification"


def test_review_only_after_uncertain_and_ledger_never_cleared(engine):
    claim=uncertain(engine)
    finding=review(engine,claim.delivery_key)
    assert (finding.status,finding.printing_enabled)==("uncertain",False)
    review(engine,claim.delivery_key,finding="escalated",evidence_sha256="d"*64)
    assert tuple(x.finding for x in inspect_uncertain_reviews(
        engine,tenant_id=10,actor_user_id=10,actor_employer_id=None,
        delivery_key=claim.delivery_key
    ))==("investigating","escalated")
    assert get_claim(engine,tenant_id=10,delivery_key=claim.delivery_key).state=="uncertain"
    with pytest.raises(PrintReviewConflict):
        review(engine,claim.delivery_key)
    with pytest.raises(PrintClaimDuplicate):
        reserve_held_claim(
            engine,tenant_id=10,session_id="fake-session",
            document_kind="care_sheet",document_id="fake-doc",
            document_sha256="b"*64,printer_id="near_station",
        )
    with engine.connect() as c:
        assert c.execute(select(claim_events.c.transition).order_by(claim_events.c.revision)).scalars().all()==[
            "held_reserved","marked_uncertain"
        ]


def test_review_denied_on_held_or_missing_claim(engine):
    claim=reserve_held_claim(
        engine, tenant_id=10, session_id="held", document_kind="care_sheet",
        document_id="fake-doc", document_sha256="f"*64, printer_id="frontdesk",
    )
    with pytest.raises(PrintReviewRejected,match="ONLY_UNCERTAIN"):
        review(engine,claim.delivery_key)
    with pytest.raises(PrintReviewRejected,match="ONLY_UNCERTAIN"):
        review(engine,"e"*64)
    with engine.connect() as c:
        assert c.execute(select(uncertain_reviews)).all()==[]


@pytest.mark.parametrize("change", [
    {"actor_user_id":11},
    {"actor_employer_id":10},
    {"finding":"released"},
    {"finding":"printed"},
    {"finding":"auto_retry"},
    {"evidence_sha256":"D"*64},
    {"delivery_key":"not-a-sha"},
])
def test_uncertain_review_rejects_untrusted_actor_and_completion(engine,change):
    claim=uncertain(engine)
    with pytest.raises(PrintReviewRejected):
        review(engine,claim.delivery_key if "delivery_key" not in change else None,**change)
    with engine.connect() as c:
        assert c.execute(select(uncertain_reviews)).all()==[]


def test_review_failure_is_transactional_and_keeps_uncertain(engine):
    claim=uncertain(engine)
    with engine.begin() as c:
        c.exec_driver_sql("DROP TABLE station_print_uncertain_reviews")
    with pytest.raises(OperationalError):
        review(engine,claim.delivery_key)
    assert get_claim(engine,tenant_id=10,delivery_key=claim.delivery_key).state=="uncertain"


def test_cross_tenant_review_cannot_reveal_or_modify_other_claim(engine):
    claim=uncertain(engine)
    with pytest.raises(PrintReviewRejected):
        review(engine,claim.delivery_key,tenant_id=20,actor_user_id=20)
    assert inspect_uncertain_reviews(
        engine,tenant_id=20,actor_user_id=20,actor_employer_id=None,
        delivery_key=claim.delivery_key,
    )==()


def test_recovery_and_evidence_tables_have_no_patient_data_or_print_success_columns():
    assert not ({c.name for c in device_evidence.columns}|{c.name for c in uncertain_reviews.columns}) & {
        "patient_id","patient_name","pdf","file_path","session_token","document_bytes",
        "printed","collected","allow_print","enable_print","release"
    }
    assert {c.name for c in uncertain_reviews.columns} >= {"tenant_id","delivery_key","finding","recorded_at"}
