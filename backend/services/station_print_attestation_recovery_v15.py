"""LOT04.8: evidence intake and UNCERTAIN investigation without any print permit.

This is NOT a physical printer certification service. Device evidence remains
PENDING_FIELD_VERIFICATION regardless of who submits it. No operator, owner,
settings payload or stored digest can promote it to TrustedPrinter(enabled).
That approval requires independent, observable human/device proof in V1.5-10.

Reviews of ambiguous print jobs are append-only, tenant-scoped observations.
They NEVER clear an UNCERTAIN claim, change destinations, enqueue a worker,
mark anything printed/collected or allow a second attempt. No PHI or free text.
Only trusted Cabinet owner identities may invoke these INTERNAL functions;
no HTTP endpoints are exported.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import (
    CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint,
    Integer, String, Table, UniqueConstraint, insert, select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from backend.services.station_print_held_claims_lab import SCHEMA, claims


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_REVIEWS = frozenset({"investigating", "evidence_checked", "escalated"})
_PENDING_STATUS = "pending_field_verification"

device_evidence = Table(
    "station_print_device_evidence", SCHEMA,
    Column("tenant_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("printer_id", String(80), primary_key=True),
    Column("evidence_sha256", String(64), primary_key=True),
    Column("recorded_by", Integer, nullable=False),
    Column("status", String(32), nullable=False, server_default=_PENDING_STATUS),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    CheckConstraint(
        "status = 'pending_field_verification'",
        name="ck_device_evidence_never_certified",
    ),
)

uncertain_reviews = Table(
    "station_print_uncertain_reviews", SCHEMA,
    Column("review_id", Integer, primary_key=True, autoincrement=True),
    Column("tenant_id", Integer, nullable=False),
    Column("delivery_key", String(64), nullable=False),
    Column("reviewed_by", Integer, nullable=False),
    Column("finding", String(24), nullable=False),
    Column("evidence_sha256", String(64), nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    ForeignKeyConstraint(
        ["tenant_id", "delivery_key"],
        ["station_print_held_claims.tenant_id", "station_print_held_claims.delivery_key"],
        ondelete="RESTRICT", name="fk_uncertain_review_claim",
    ),
    UniqueConstraint("tenant_id", "delivery_key", "finding", name="uq_uncertain_review_one_finding"),
    CheckConstraint(
        "finding IN ('investigating','evidence_checked','escalated')",
        name="ck_uncertain_review_finding",
    ),
)


class PrintReviewRejected(ValueError):
    pass


class PrintReviewConflict(ValueError):
    pass


@dataclass(frozen=True)
class DeviceEvidenceReceipt:
    tenant_id: int
    printer_id: str
    evidence_sha256: str
    status: str = _PENDING_STATUS
    printing_enabled: bool = False


@dataclass(frozen=True)
class UncertainReviewReceipt:
    tenant_id: int
    delivery_key: str
    finding: str
    status: str = "uncertain"
    printing_enabled: bool = False


def _owner(tenant_id: object, actor_id: object, actor_employer_id: object) -> int:
    # The caller MUST derive actor from authenticated Cabinet context, not a
    # browser-supplied string. No routes use this internal service today.
    if (
        type(tenant_id) is not int or tenant_id <= 0
        or type(actor_id) is not int or actor_id != tenant_id
        or actor_employer_id is not None
    ):
        raise PrintReviewRejected("CABINET_ROOT_OWNER_REQUIRED")
    return tenant_id


def record_pending_device_evidence(
    engine: Engine, *,
    tenant_id: int, actor_user_id: int, actor_employer_id: int | None,
    printer_id: str, evidence_sha256: str,
) -> DeviceEvidenceReceipt:
    """Store a digest/reference, NEVER an approval or physical attestation."""
    _owner(tenant_id, actor_user_id, actor_employer_id)
    if (
        type(printer_id) is not str or _IDENTIFIER.fullmatch(printer_id) is None
        or type(evidence_sha256) is not str or _DIGEST.fullmatch(evidence_sha256) is None
    ):
        raise PrintReviewRejected("INVALID_EVIDENCE_REFERENCE")
    try:
        with engine.begin() as conn:
            conn.execute(insert(device_evidence).values(
                tenant_id=tenant_id, printer_id=printer_id,
                evidence_sha256=evidence_sha256,
                recorded_by=actor_user_id,
                status=_PENDING_STATUS,
                recorded_at=datetime.now(timezone.utc),
            ))
    except IntegrityError as exc:
        raise PrintReviewConflict("EVIDENCE_ALREADY_RECORDED") from exc
    return DeviceEvidenceReceipt(tenant_id, printer_id, evidence_sha256)


def record_uncertain_investigation(
    engine: Engine, *,
    tenant_id: int, actor_user_id: int, actor_employer_id: int | None,
    delivery_key: str, finding: str, evidence_sha256: str,
) -> UncertainReviewReceipt:
    """Add immutable-by-API investigation; NEVER reset/release a claim.

    One shared transaction verifies the claim is still UNCERTAIN before the
    append. A missing claim, HELD state, wrong tenant or duplicate finding
    fails closed. Permissions and DB-level append-only grants are required
    for any future operational user-facing route.
    """
    _owner(tenant_id, actor_user_id, actor_employer_id)
    if (
        type(delivery_key) is not str or _DIGEST.fullmatch(delivery_key) is None
        or type(evidence_sha256) is not str or _DIGEST.fullmatch(evidence_sha256) is None
        or type(finding) is not str or finding not in _ALLOWED_REVIEWS
    ):
        raise PrintReviewRejected("INVALID_REVIEW")
    try:
        with engine.begin() as conn:
            existing = conn.execute(
                select(claims.c.state)
                .where(
                    claims.c.tenant_id == tenant_id,
                    claims.c.delivery_key == delivery_key,
                ).with_for_update()
            ).scalar_one_or_none()
            if existing != "uncertain":
                raise PrintReviewRejected("ONLY_UNCERTAIN_CLAIMS_REVIEWABLE")
            conn.execute(insert(uncertain_reviews).values(
                tenant_id=tenant_id, delivery_key=delivery_key,
                reviewed_by=actor_user_id, finding=finding,
                evidence_sha256=evidence_sha256,
                recorded_at=datetime.now(timezone.utc),
            ))
    except IntegrityError as exc:
        raise PrintReviewConflict("REVIEW_ALREADY_RECORDED") from exc
    return UncertainReviewReceipt(tenant_id, delivery_key, finding)


def inspect_uncertain_reviews(engine: Engine, *, tenant_id: int, actor_user_id: int,
                              actor_employer_id: int | None,
                              delivery_key: str) -> tuple[UncertainReviewReceipt, ...]:
    _owner(tenant_id, actor_user_id, actor_employer_id)
    if type(delivery_key) is not str or _DIGEST.fullmatch(delivery_key) is None:
        raise PrintReviewRejected("INVALID_DELIVERY_KEY")
    with engine.connect() as conn:
        rows = conn.execute(
            select(uncertain_reviews.c.finding)
            .where(
                uncertain_reviews.c.tenant_id == tenant_id,
                uncertain_reviews.c.delivery_key == delivery_key,
            ).order_by(uncertain_reviews.c.review_id)
        ).scalars().all()
    return tuple(UncertainReviewReceipt(tenant_id, delivery_key, finding) for finding in rows)
