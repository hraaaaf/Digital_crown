"""LOT06-C05A PostgreSQL receipt-authority *candidate*, test-only and not wired.

No production schema migration, API route, patient data or clinical authorization.
The server-side approval here is a synthetic fixture; staff/device validation and
the independently verified durable AES-GCM media binding are future gates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
import secrets

from sqlalchemy import (
    Boolean, CheckConstraint, Column, ForeignKey, Integer, MetaData,
    String, Table, insert, select,
)
from sqlalchemy.engine import Engine


metadata = MetaData()
approvals = Table(
    "lot06c05a_approved_captures", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("digest", String(64), nullable=False),
    Column("byte_size", Integer, nullable=False),
    Column("patient", Integer, nullable=False),
    Column("staff", Integer, nullable=False),
    Column("approval_version", Integer, nullable=False),
    Column("asset_id", Integer, nullable=False),
    Column("reason", String(32), nullable=False),
    Column("approved", Boolean, nullable=False),
    CheckConstraint("approval_version > 0", name="lot06c05a_approval_positive"),
)
receipts = Table(
    "lot06c05a_receipts", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("receipt_id", String(64), unique=True, nullable=False),
    Column("digest", String(64), nullable=False),
    Column("byte_size", Integer, nullable=False),
    Column("patient", Integer, nullable=False),
    Column("staff", Integer, nullable=False),
    Column("approval_version", Integer, nullable=False),
    Column("asset_id", Integer, unique=True, nullable=False),
    Column("reason", String(32), nullable=False),
)
audit = Table(
    "lot06c05a_audit", metadata,
    Column("receipt_id", String(64), ForeignKey("lot06c05a_receipts.receipt_id"), primary_key=True),
    Column("event", String(64), nullable=False),
)
outbox = Table(
    "lot06c05a_outbox", metadata,
    Column("receipt_id", String(64), ForeignKey("lot06c05a_receipts.receipt_id"), primary_key=True),
    Column("event", String(64), nullable=False),
)


class AuthorityRejected(ValueError):
    """Fail-closed candidate receipt result; no clinical authority granted."""


@dataclass(frozen=True)
class ApprovalClaim:
    tenant: int
    device: str
    capture: str
    digest: str
    byte_size: int
    patient: int
    staff: int
    approval_version: int
    asset_id: int
    reason: str


def guard(engine: Engine) -> None:
    """Hard gate: only an ephemeral locally hosted test database is permitted."""
    url = engine.url
    if (
        os.environ.get("ENVIRONMENT") != "test"
        or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
        or os.environ.get("DC06C05A_PG_TEST") != "1"
        or engine.dialect.name != "postgresql"
        or url.database != "dc_lot06c_test"
        or url.host not in ("127.0.0.1", "localhost")
    ):
        raise AuthorityRejected("ISOLATED_PG_AUTHORITY_DISABLED")


def _where(claim: ApprovalClaim):
    return (
        (approvals.c.tenant == claim.tenant)
        & (approvals.c.device == claim.device)
        & (approvals.c.capture == claim.capture)
    )


def _matching(record, claim: ApprovalClaim) -> bool:
    return all(record.get(field) == value for field, value in asdict(claim).items())


def _assert_claim(claim: ApprovalClaim) -> None:
    if (
        not isinstance(claim.tenant, int) or claim.tenant <= 0
        or not isinstance(claim.patient, int) or claim.patient <= 0
        or not isinstance(claim.staff, int) or claim.staff <= 0
        or not isinstance(claim.asset_id, int) or claim.asset_id <= 0
        or not isinstance(claim.approval_version, int) or claim.approval_version <= 0
        or not isinstance(claim.byte_size, int) or claim.byte_size <= 0
        or len(claim.device) > 64 or not claim.device
        or len(claim.capture) > 128 or not claim.capture
        or len(claim.digest) != 64 or any(c not in "0123456789abcdef" for c in claim.digest)
        or claim.reason not in {"LAB_WALK_IN", "LAB_UNSCHEDULED", "LAB_URGENT"}
    ):
        raise AuthorityRejected("INVALID_APPROVAL_CLAIM")


def seed_test_approval(engine: Engine, claim: ApprovalClaim) -> None:
    """Synthetic server-owned approval fixture: never exported as a clinical API."""
    guard(engine)
    _assert_claim(claim)
    with engine.begin() as conn:
        conn.execute(insert(approvals).values(**asdict(claim), approved=True))


def _verified_receipt(conn, claim: ApprovalClaim) -> dict | None:
    row = conn.execute(select(receipts).where(
        (receipts.c.tenant == claim.tenant)
        & (receipts.c.device == claim.device)
        & (receipts.c.capture == claim.capture)
    )).mappings().first()
    if row is None:
        return None
    if not _matching(row, claim):
        raise AuthorityRejected("IMMUTABLE_RECEIPT_CONFLICT")
    rid = row["receipt_id"]
    if conn.execute(select(audit.c.event).where(audit.c.receipt_id == rid)).scalar_one_or_none() != "CAPTURE_COMMITTED":
        raise AuthorityRejected("AUDIT_MISSING_FAIL_CLOSED")
    if conn.execute(select(outbox.c.event).where(outbox.c.receipt_id == rid)).scalar_one_or_none() != "MEDIA_READY":
        raise AuthorityRejected("OUTBOX_MISSING_FAIL_CLOSED")
    return {"receipt_id": rid, "tenant": claim.tenant,
            "device": claim.device, "capture": claim.capture,
            "approval_version": claim.approval_version,
            "asset_id": claim.asset_id, "server_confirmed": False,
            "scope": "TEST_CANDIDATE_NOT_CLINICAL"}


def issue_test_receipt(
    engine: Engine, claim: ApprovalClaim, *, fail_at: str | None = None
) -> dict:
    """Serialize real PostgreSQL writers on the server approval row.

    The entire receipt+audit+outbox SQL unit commits atomically. The caller
    MUST independently prove persisted AES media integrity before any future
    product integration; this candidate does not certify that prerequisite.
    """
    guard(engine)
    _assert_claim(claim)
    if fail_at not in (None, "after_receipt", "after_audit", "after_outbox"):
        raise AuthorityRejected("INVALID_TEST_FAILPOINT")
    with engine.begin() as conn:
        approved = conn.execute(
            select(approvals).where(_where(claim)).with_for_update()
        ).mappings().first()
        if approved is None or not approved["approved"] or not _matching(approved, claim):
            raise AuthorityRejected("SERVER_APPROVAL_BINDING_CONFLICT")
        old = _verified_receipt(conn, claim)
        if old is not None:
            return old
        rid = "C05A-TEST-" + secrets.token_hex(16)
        conn.execute(insert(receipts).values(
            **asdict(claim), receipt_id=rid,
        ))
        if fail_at == "after_receipt":
            raise AuthorityRejected("INJECTED_POSTGRES_ROLLBACK")
        conn.execute(insert(audit).values(receipt_id=rid, event="CAPTURE_COMMITTED"))
        if fail_at == "after_audit":
            raise AuthorityRejected("INJECTED_POSTGRES_ROLLBACK")
        conn.execute(insert(outbox).values(receipt_id=rid, event="MEDIA_READY"))
        if fail_at == "after_outbox":
            raise AuthorityRejected("INJECTED_POSTGRES_ROLLBACK")
    result = lookup_test_receipt(engine, claim)
    if result is None:
        raise AuthorityRejected("COMMITTED_RECEIPT_NOT_FOUND")
    return result


def lookup_test_receipt(engine: Engine, claim: ApprovalClaim) -> dict | None:
    """Lookup cannot claim clinical confirmation; no media bytes inspected."""
    guard(engine)
    _assert_claim(claim)
    with engine.connect() as conn:
        approved = conn.execute(select(approvals).where(_where(claim))).mappings().first()
        if approved is None or not approved["approved"] or not _matching(approved, claim):
            raise AuthorityRejected("SERVER_APPROVAL_BINDING_CONFLICT")
        return _verified_receipt(conn, claim)
