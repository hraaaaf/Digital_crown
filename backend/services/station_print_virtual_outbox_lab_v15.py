"""LOT04.8-C: never-clinical, transactionally fenced virtual-print outbox LAB.

This deliberately cannot ingest any caller-selected patient/document/printer
identity, PDF bytes, filepath or spool commands. It is a SYNTHETIC lab-only
bridge whose schema is NOT registered in Alembic, therefore it is never added
to the Cabinet's production tables. It cannot authorize patient printing.

Safety over liveness: claim is changed to UNCERTAIN and a one-shot outbox
attempt is durably fenced in ONE transaction *before* CUPS is invoked. Crash
before/during/after spool => no automatic retry, no second destination, never
a false "printed" or "delivered". Out-of-band human audit is needed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os

from sqlalchemy import (
    CheckConstraint, Column, DateTime, ForeignKeyConstraint, Integer,
    String, Table, insert, select, update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from backend.services.station_document_print_policy import delivery_identity
from backend.services.station_print_held_claims_lab import (
    SCHEMA, claims, claim_events, HeldClaim,
)

SYNTHETIC_TENANT = 10
SYNTHETIC_SESSION = "SYNTHETIC_NOT_A_PATIENT_SESSION"
SYNTHETIC_KIND = "care_sheet"
SYNTHETIC_DOCUMENT = "SYNTHETIC_PRINT_BRIDGE"
SYNTHETIC_DIGEST = "1" * 64
SYNTHETIC_PRINTER = "DC_VIRTUAL_PDF"
SYNTHETIC_DELIVERY_KEY = delivery_identity(
    SYNTHETIC_TENANT, SYNTHETIC_SESSION,
    SYNTHETIC_KIND, SYNTHETIC_DOCUMENT, SYNTHETIC_DIGEST,
)

virtual_outbox = Table(
    "station_print_virtual_outbox_lab", SCHEMA,
    Column("tenant_id", Integer, primary_key=True),
    Column("delivery_key", String(64), primary_key=True),
    Column("printer_id", String(80), nullable=False),
    Column("state", String(16), nullable=False),
    Column("attempts", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    ForeignKeyConstraint(
        ["tenant_id", "delivery_key"],
        ["station_print_held_claims.tenant_id", "station_print_held_claims.delivery_key"],
        ondelete="RESTRICT", name="fk_virtual_lab_outbox_claim",
    ),
    CheckConstraint("state IN ('reserved','attempted')", name="ck_virtual_lab_outbox_state"),
    CheckConstraint("attempts IN (0,1)", name="ck_virtual_lab_outbox_attempts"),
    CheckConstraint(
        "(state = 'reserved' AND attempts = 0) OR "
        "(state = 'attempted' AND attempts = 1)",
        name="ck_virtual_lab_outbox_one_shot",
    ),
)


class VirtualLabRejected(ValueError):
    pass


class VirtualLabDuplicate(ValueError):
    pass


@dataclass(frozen=True)
class VirtualLabTicket:
    tenant_id: int
    delivery_key: str
    printer_id: str
    state: str
    attempts: int


def _lab_guard() -> None:
    # This is a defense in depth flag, NOT an authorization token; the
    # important invariant is the hardcoded fake identity and absent route.
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("DC_SYNTHETIC_VIRTUAL_SPOOL_LAB") != "1"
    ):
        raise VirtualLabRejected("SYNTHETIC_GITHUB_ACTIONS_LAB_ONLY")


def reserve_synthetic_outbox(engine: Engine) -> VirtualLabTicket:
    """Insert held claim + event + one outbox row in ONE SQL transaction."""
    _lab_guard()
    now = datetime.now(timezone.utc)
    try:
        with engine.begin() as conn:
            conn.execute(insert(claims).values(
                tenant_id=SYNTHETIC_TENANT,
                delivery_key=SYNTHETIC_DELIVERY_KEY,
                first_printer_id=SYNTHETIC_PRINTER,
                state="held", revision=1,
                created_at=now, updated_at=now,
            ))
            conn.execute(insert(claim_events).values(
                tenant_id=SYNTHETIC_TENANT,
                delivery_key=SYNTHETIC_DELIVERY_KEY,
                revision=1, transition="held_reserved", created_at=now,
            ))
            conn.execute(insert(virtual_outbox).values(
                tenant_id=SYNTHETIC_TENANT,
                delivery_key=SYNTHETIC_DELIVERY_KEY,
                printer_id=SYNTHETIC_PRINTER,
                state="reserved", attempts=0,
                created_at=now, updated_at=now,
            ))
    except IntegrityError as exc:
        raise VirtualLabDuplicate("LAB_DELIVERY_ALREADY_RESERVED") from exc
    return VirtualLabTicket(
        SYNTHETIC_TENANT, SYNTHETIC_DELIVERY_KEY,
        SYNTHETIC_PRINTER, "reserved", 0,
    )


def fence_virtual_attempt(engine: Engine) -> VirtualLabTicket:
    """Atomically fence attempt BEFORE any external spool/driver side effect.

    A second worker cannot acquire a second ticket. Any failed event/outbox
    write rolls back claim state, and no ticket is returned => never spool.
    """
    _lab_guard()
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        changed = conn.execute(
            update(claims).where(
                claims.c.tenant_id == SYNTHETIC_TENANT,
                claims.c.delivery_key == SYNTHETIC_DELIVERY_KEY,
                claims.c.first_printer_id == SYNTHETIC_PRINTER,
                claims.c.state == "held",
                claims.c.revision == 1,
            ).values(state="uncertain", revision=2, updated_at=now)
        )
        if changed.rowcount != 1:
            raise VirtualLabRejected("ALREADY_ATTEMPTED_OR_NOT_RESERVED")
        changed = conn.execute(
            update(virtual_outbox).where(
                virtual_outbox.c.tenant_id == SYNTHETIC_TENANT,
                virtual_outbox.c.delivery_key == SYNTHETIC_DELIVERY_KEY,
                virtual_outbox.c.printer_id == SYNTHETIC_PRINTER,
                virtual_outbox.c.state == "reserved",
                virtual_outbox.c.attempts == 0,
            ).values(state="attempted", attempts=1, updated_at=now)
        )
        if changed.rowcount != 1:
            raise VirtualLabRejected("VIRTUAL_OUTBOX_NOT_RESERVED")
        conn.execute(insert(claim_events).values(
            tenant_id=SYNTHETIC_TENANT,
            delivery_key=SYNTHETIC_DELIVERY_KEY,
            revision=2, transition="marked_uncertain", created_at=now,
        ))
    return VirtualLabTicket(
        SYNTHETIC_TENANT, SYNTHETIC_DELIVERY_KEY,
        SYNTHETIC_PRINTER, "attempted", 1,
    )


def read_synthetic_outbox(engine: Engine) -> VirtualLabTicket | None:
    _lab_guard()
    with engine.connect() as conn:
        row = conn.execute(select(virtual_outbox).where(
            virtual_outbox.c.tenant_id == SYNTHETIC_TENANT,
            virtual_outbox.c.delivery_key == SYNTHETIC_DELIVERY_KEY,
        )).mappings().one_or_none()
    if row is None:
        return None
    return VirtualLabTicket(
        row["tenant_id"], row["delivery_key"], row["printer_id"],
        row["state"], row["attempts"],
    )
