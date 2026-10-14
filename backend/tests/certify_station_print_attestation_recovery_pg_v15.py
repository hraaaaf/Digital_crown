#!/usr/bin/env python3
"""PostgreSQL 18 proof: device evidence & uncertain review, two OS workers.

Dedicated disposable schema, test identities and document only. No real
printer/clinical file, no certification or release; tables mirror neo30.
"""
from __future__ import annotations
import os
import subprocess
import sys
import types
from datetime import datetime, timezone
from sqlalchemy import create_engine, insert, select, text

for name,path in (("backend","backend"),("backend.services","backend/services")):
    p=types.ModuleType(name);p.__path__=[os.path.abspath(path)];sys.modules[name]=p

from backend.services.station_print_held_claims_lab import SCHEMA, claims, claim_events, reserve_held_claim, mark_uncertain
from backend.services.station_print_attestation_recovery_v15 import (
    device_evidence, uncertain_reviews,
    record_pending_device_evidence, record_uncertain_investigation,
    PrintReviewConflict, PrintReviewRejected,
)
SCHEMA_NAME="dc_print_evidence_recovery_pg_lab"
SHA="e"*64

def engine():
    url=os.environ.get("DATABASE_URL","")
    if not url.startswith("postgresql"):
        raise RuntimeError("POSTGRES_ONLY")
    return create_engine(url,connect_args={"options":"-csearch_path="+SCHEMA_NAME},pool_pre_ping=True)

def act(kind: str, key: str):
    db=engine()
    try:
        if kind=="evidence":
            result=record_pending_device_evidence(
                db,tenant_id=10,actor_user_id=10,actor_employer_id=None,
                printer_id="frontdesk",evidence_sha256=SHA,
            )
            assert result.printing_enabled is False
        elif kind=="review":
            result=record_uncertain_investigation(
                db,tenant_id=10,actor_user_id=10,actor_employer_id=None,
                delivery_key=key,finding="investigating",evidence_sha256=SHA,
            )
            assert result.status=="uncertain" and result.printing_enabled is False
        else:
            raise RuntimeError("INVALID_OPERATION")
        print("WIN",kind)
        return 0
    except PrintReviewConflict:
        print("DUPLICATE_DENIED",kind)
        return 7
    finally:
        db.dispose()

def race(kind: str,key: str):
    children=[subprocess.Popen(
        [sys.executable,__file__,kind,key],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=dict(os.environ),
    ) for _ in range(2)]
    results=[]
    for p in children:
        out,err=p.communicate(timeout=45)
        print(out.strip())
        if err.strip(): print(err.strip(),file=sys.stderr)
        results.append(p.returncode)
    assert sorted(results)==[0,7],(kind,results)

def main():
    admin=create_engine(os.environ["DATABASE_URL"])
    with admin.begin() as conn:conn.execute(text("CREATE SCHEMA "+SCHEMA_NAME))
    admin.dispose()
    db=engine()
    SCHEMA.create_all(db)
    with db.begin() as conn:
        conn.execute(insert(SCHEMA.tables["users"]).values(id=10))
        conn.execute(insert(SCHEMA.tables["station_print_printer_drafts"]).values(
            tenant_id=10,printer_id="frontdesk",location="reception",
            station_id=None,revision=1,updated_by=10,updated_at=datetime.now(timezone.utc),
        ))
    claim=reserve_held_claim(
        db,tenant_id=10,session_id="synthetic_session",document_kind="care_sheet",
        document_id="synthetic_document",document_sha256="f"*64,printer_id="frontdesk",
    )
    mark_uncertain(db,tenant_id=10,delivery_key=claim.delivery_key,expected_revision=1)
    db.dispose()
    race("evidence",claim.delivery_key)
    race("review",claim.delivery_key)
    restarted=engine()
    with restarted.connect() as conn:
        assert conn.execute(select(device_evidence.c.status)).scalar_one()=="pending_field_verification"
        assert conn.execute(select(uncertain_reviews.c.finding)).scalar_one()=="investigating"
        assert conn.execute(select(claims.c.state)).scalar_one()=="uncertain"
        assert conn.execute(select(claim_events.c.transition).order_by(claim_events.c.revision)).scalars().all()==[
            "held_reserved","marked_uncertain",
        ]
    assert record_uncertain_investigation(
        restarted,tenant_id=10,actor_user_id=10,actor_employer_id=None,
        delivery_key=claim.delivery_key,finding="escalated",evidence_sha256=SHA,
    ).status=="uncertain"
    with restarted.connect() as conn:
        assert conn.execute(select(claims.c.revision)).scalar_one()==2
        assert conn.execute(select(uncertain_reviews.c.finding).order_by(uncertain_reviews.c.review_id)).scalars().all()==["investigating","escalated"]
    restarted.dispose()
    print(
        "PG_PRINT_REVIEW_PASS two_evidence_workers=2 evidence_winners=1 "
        "two_review_workers=2 review_winners=1 status=pending_field_verification "
        "claim_still_uncertain=1 no_reprint=1 certified_printers=0"
    )

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1] in ("evidence","review"):
        raise SystemExit(act(sys.argv[1],sys.argv[2]))
    if len(sys.argv)!=1:raise SystemExit("INVALID_RUNNER_ARGS")
    main()
