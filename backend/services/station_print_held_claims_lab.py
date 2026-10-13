"""04.8-C parallel LAB: durable destination-independent HELD print claims.

This module never enqueues printer hardware, retrieves a PDF, claims a physical
output is complete, or exposes a Station endpoint. Storage is not permission.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import (
    CheckConstraint, Column, DateTime, Integer, MetaData, String, Table,
    insert, select, update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from backend.services.station_document_print_policy import delivery_identity

SCHEMA = MetaData()
claims = Table(
    "station_print_held_claims_lab", SCHEMA,
    Column("tenant_id", Integer, primary_key=True),
    Column("delivery_key", String(64), primary_key=True),
    Column("first_printer_id", String(80), nullable=False),
    Column("state", String(16), nullable=False),
    Column("revision", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("state IN ('held','uncertain')", name="ck_print_claim_state"),
    CheckConstraint("revision > 0", name="ck_print_claim_revision"),
)


class PrintClaimRejected(ValueError):
    pass


class PrintClaimDuplicate(ValueError):
    pass


@dataclass(frozen=True)
class HeldClaim:
    tenant_id: int
    delivery_key: str
    first_printer_id: str
    state: str
    revision: int


def reserve_held_claim(
    engine: Engine, *,
    tenant_id: int,
    session_id: str,
    document_kind: str,
    document_id: str,
    document_sha256: str,
    printer_id: str,
) -> HeldClaim:
    """Reserve unique identity independent of printer; ALWAYS held, never release.

    Caller must still validate patient/document/session/tenant on the Cabinet
    before any future dispatch. Never pass unauthenticated Station inputs to a
    print worker. Atomic DB PK blocks concurrent different destination claims.
    """
    if type(tenant_id) is not int or tenant_id <= 0:
        raise PrintClaimRejected("INVALID_TENANT")
    if type(printer_id) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,79}", printer_id) is None:
        raise PrintClaimRejected("INVALID_PRINTER")
    if any(type(x) is not str for x in (session_id, document_kind, document_id, document_sha256)):
        raise PrintClaimRejected("INVALID_IDENTITY")
    try:
        key = delivery_identity(tenant_id, session_id, document_kind, document_id, document_sha256)
    except ValueError as exc:
        raise PrintClaimRejected("INVALID_IDENTITY") from exc
    now = datetime.now(timezone.utc)
    try:
        with engine.begin() as conn:
            conn.execute(insert(claims).values(
                tenant_id=tenant_id, delivery_key=key,
                first_printer_id=printer_id, state="held",
                revision=1, created_at=now, updated_at=now,
            ))
    except IntegrityError as exc:
        raise PrintClaimDuplicate("ALREADY_CLAIMED_CROSS_DESTINATION") from exc
    return HeldClaim(tenant_id, key, printer_id, "held", 1)


def mark_uncertain(
    engine: Engine, *,
    tenant_id: int,
    delivery_key: str,
    expected_revision: int,
) -> HeldClaim:
    """On ambiguous spool/crash observation, lock permanently for human review.

    No transition out of uncertain, no automatic retry or destination change.
    """
    if (
        type(tenant_id) is not int or tenant_id <= 0
        or type(delivery_key) is not str
        or re.fullmatch(r"[a-f0-9]{64}", delivery_key) is None
        or type(expected_revision) is not int or expected_revision <= 0
    ):
        raise PrintClaimRejected("INVALID_TRANSITION")
    with engine.begin() as conn:
        changed = conn.execute(
            update(claims)
            .where(
                claims.c.tenant_id == tenant_id,
                claims.c.delivery_key == delivery_key,
                claims.c.revision == expected_revision,
                claims.c.state == "held",
            )
            .values(state="uncertain", revision=expected_revision + 1,
                    updated_at=datetime.now(timezone.utc))
        )
        if changed.rowcount != 1:
            raise PrintClaimRejected("INVALID_TRANSITION")
        row = conn.execute(select(claims).where(
            claims.c.tenant_id == tenant_id, claims.c.delivery_key == delivery_key
        )).mappings().one()
    return HeldClaim(tenant_id, delivery_key, row["first_printer_id"], "uncertain", row["revision"])


def get_claim(engine: Engine, *, tenant_id: int, delivery_key: str) -> HeldClaim | None:
    if type(tenant_id) is not int or tenant_id <= 0:
        raise PrintClaimRejected("INVALID_TENANT")
    if type(delivery_key) is not str or re.fullmatch(r"[a-f0-9]{64}", delivery_key) is None:
        raise PrintClaimRejected("INVALID_IDENTITY")
    with engine.connect() as conn:
        row = conn.execute(select(claims).where(
            claims.c.tenant_id == tenant_id, claims.c.delivery_key == delivery_key
        )).mappings().one_or_none()
    if row is None:
        return None
    return HeldClaim(tenant_id, delivery_key, row["first_printer_id"], row["state"], row["revision"])
