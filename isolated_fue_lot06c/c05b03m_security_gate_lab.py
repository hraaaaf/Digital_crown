"""C05B-03M disposable SQLCipher proof: independent device key + staff review.

NOT a product enrollment API, real scanner attestation or human UI proof.
Approval is registered only by the synthetic TEST authority (never by upload).
Consumption is completed inside _issue() receipt/audit/outbox SQLCipher commit.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy import (
    Column, Integer, MetaData, String, Table, insert, select, update,
)
from sqlalchemy.orm import Session

from backend import models
from backend.routers.auth import has_permission
from isolated_fue_lot06c.test_sqlcipher_real_staff_station_bridge_v15 import (
    BridgeRejected, receipts,
)

metadata = MetaData()
identity = Table(
    "c05b03m_lab_device_identity", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("station", String(36), nullable=False),
    Column("generation", Integer, nullable=False),
    Column("public_key_hex", String(64), nullable=False),
    Column("active", Integer, nullable=False),
)
review = Table(
    "c05b03m_lab_review", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("patient", Integer, nullable=False),
    Column("staff", Integer, nullable=False),
    Column("station", String(36), nullable=False),
    Column("digest", String(64), nullable=False),
    Column("byte_size", Integer, nullable=False),
    Column("version", Integer, nullable=False),
    Column("generation", Integer, nullable=False),
    Column("challenge", String(64), nullable=False),
    Column("approved_at", Integer),
    Column("expires_at", Integer, nullable=False),
    Column("consumed", Integer, nullable=False, default=0),
)
review_audit = Table(
    "c05b03m_lab_review_audit", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("event", String(64), nullable=False),
    Column("staff", Integer, nullable=False),
)


def _guard(db: Session) -> None:
    if (os.getenv("ENVIRONMENT") != "test"
            or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
            or os.getenv("DC06C05B03M_TEST_ONLY") != "1"
            or db.bind is None or db.get_bind().dialect.name != "sqlite"
            or not db.connection().exec_driver_sql("PRAGMA cipher_version").scalar_one_or_none()):
        raise BridgeRejected("C05B03M_SQLCIPHER_TEST_ISOLATION_REQUIRED")


def _claim_values(claim):
    return {
        "tenant": claim.tenant, "device": claim.device, "capture": claim.capture,
        "patient": claim.patient, "staff": claim.staff, "station": claim.station,
        "digest": claim.digest, "byte_size": claim.byte_size,
        "version": claim.version, "generation": claim.generation,
    }


def _signed_payload(claim, challenge: str) -> bytes:
    return json.dumps(
        {**_claim_values(claim), "challenge": challenge, "purpose": "C05B03M_TEST_CAPTURE"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")



def verify_pending_device_capture_proof(
    db: Session, claim, signature: str,
) -> None:
    """Independent LAB device proof BEFORE preview/staff confirmation.

    Validate the registered pinned Ed25519 public key against the immutable
    capture claim and private device challenge already stored in SQLCipher.
    Browser JWT or review challenge alone cannot stand in for this proof.
    This deliberately does NOT authorize a real scanner or clinical upload.
    """
    _guard(db)
    if not isinstance(signature, str) or re.fullmatch(r"[a-f0-9]{128}", signature) is None:
        raise BridgeRejected("C05B03M_PENDING_DEVICE_PROOF_REQUIRED")
    dev = db.execute(select(identity).where(
        identity.c.tenant == claim.tenant,
        identity.c.device == claim.device,
    )).mappings().one_or_none()
    pending = db.execute(select(review).where(
        review.c.tenant == claim.tenant,
        review.c.device == claim.device,
        review.c.capture == claim.capture,
    )).mappings().one_or_none()
    if (dev is None or dev["active"] != 1
            or dev["station"] != claim.station
            or dev["generation"] != claim.generation
            or pending is None or pending["consumed"] != 0
            or pending["approved_at"] is not None
            or pending["expires_at"] <= int(time.time())
            or any(pending[k] != value for k, value in _claim_values(claim).items())):
        raise BridgeRejected("C05B03M_PENDING_DEVICE_OR_CAPTURE_REVOKED")
    try:
        Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(dev["public_key_hex"])
        ).verify(
            bytes.fromhex(signature),
            _signed_payload(claim, pending["challenge"]),
        )
    except (InvalidSignature, ValueError, TypeError):
        raise BridgeRejected("C05B03M_PENDING_DEVICE_SIGNATURE_DENIED") from None


def provision_test_device(db: Session, claim, *, public_key: Ed25519PublicKey) -> str:
    """ADMIN-ONLY fixture, never exposed on an HTTP route or called by client."""
    _guard(db)
    if not isinstance(public_key, Ed25519PublicKey):
        raise BridgeRejected("C05B03M_BAD_DEVICE_KEY")
    metadata.create_all(bind=db.get_bind(), checkfirst=True)
    challenge = secrets.token_hex(24)
    db.execute(insert(identity).values(
        tenant=claim.tenant, device=claim.device, station=claim.station,
        generation=claim.generation,
        public_key_hex=public_key.public_bytes(Encoding.Raw, PublicFormat.Raw).hex(),
        active=1,
    ))
    db.execute(insert(review).values(
        **_claim_values(claim), challenge=challenge,
        approved_at=None, expires_at=int(time.time()) + 180, consumed=0,
    ))
    db.commit()
    return challenge


def record_staff_review_fixture(db: Session, claim, *, staff_id: int,
                                workstation_id: str, explicit_confirm: bool) -> None:
    """Simulated separate UI action; NOT an actual clinician click."""
    _guard(db)
    if explicit_confirm is not True or staff_id != claim.staff or workstation_id != claim.station:
        raise BridgeRejected("C05B03M_EXPLICIT_STAFF_CONFIRMATION_REQUIRED")
    db.connection().exec_driver_sql("BEGIN IMMEDIATE")
    staff = db.get(models.User, staff_id)
    station = db.get(models.WorkstationMode, workstation_id)
    if (staff is None or not staff.is_active or staff.get_employer_id() != claim.tenant
            or staff.approval_status != "approved" or staff.is_archived
            or staff.is_suspended or not has_permission(staff, "patients")
            or station is None or station.employer_id != claim.tenant
            or station.revoked_at is not None or station.mode_revision != claim.station_revision):
        raise BridgeRejected("C05B03M_STAFF_OR_STATION_REVOKED")
    row = db.execute(select(review).where(
        review.c.tenant == claim.tenant, review.c.device == claim.device,
        review.c.capture == claim.capture,
    )).mappings().one_or_none()
    if (row is None or any(row[k] != val for k, val in _claim_values(claim).items())
            or row["approved_at"] is not None or row["consumed"] != 0
            or row["expires_at"] <= int(time.time())):
        raise BridgeRejected("C05B03M_REVIEW_NOT_PENDING")
    updated = db.execute(update(review).where(
        review.c.tenant == claim.tenant,
        review.c.device == claim.device,
        review.c.capture == claim.capture,
        review.c.approved_at.is_(None),
    ).values(approved_at=int(time.time())))
    if updated.rowcount != 1:
        raise BridgeRejected("C05B03M_REVIEW_RACE_DENIED")
    db.execute(insert(review_audit).values(
        tenant=claim.tenant, device=claim.device, capture=claim.capture,
        event="SYNTHETIC_STAFF_CONFIRMED", staff=staff_id,
    ))
    db.commit()


class TestOnlyMediaAuthority:
    """Uses only persistent SQLCipher state, checked under a writer lock."""

    def _state(self, db: Session, claim, signature: str):
        _guard(db)
        if not isinstance(signature, str) or re.fullmatch(r"[0-9a-f]{128}", signature) is None:
            raise BridgeRejected("C05B03M_DEVICE_SIGNATURE_REQUIRED")
        dev = db.execute(select(identity).where(
            identity.c.tenant == claim.tenant, identity.c.device == claim.device,
        )).mappings().one_or_none()
        row = db.execute(select(review).where(
            review.c.tenant == claim.tenant, review.c.device == claim.device,
            review.c.capture == claim.capture,
        )).mappings().one_or_none()
        if (dev is None or dev["active"] != 1
                or dev["station"] != claim.station or dev["generation"] != claim.generation
                or row is None or row["approved_at"] is None
                or row["expires_at"] <= int(time.time())
                or row["approved_at"] >= row["expires_at"]
                or any(row[k] != val for k, val in _claim_values(claim).items())):
            raise BridgeRejected("C05B03M_INDEPENDENT_AUTHORITY_DENIED")
        try:
            Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(dev["public_key_hex"])
            ).verify(bytes.fromhex(signature), _signed_payload(claim, row["challenge"]))
        except (InvalidSignature, ValueError, TypeError):
            raise BridgeRejected("C05B03M_DEVICE_PROOF_REJECTED") from None
        return row

    def check(self, db: Session, claim, signature: str) -> None:
        """Before writing any ClinicalAsset bytes; no local approval assumptions."""
        self._state(db, claim, signature)

    def consume(self, db: Session, claim, signature: str) -> None:
        """Inside receipt/audit/outbox's BEGIN IMMEDIATE, never a separate commit."""
        row = self._state(db, claim, signature)
        if row["consumed"] == 1:
            # A lost reply may repeat the same signed proof *only* if a receipt
            # with the same immutable capture+asset+digest+version already exists.
            previous = db.execute(select(receipts).where(
                receipts.c.tenant == claim.tenant,
                receipts.c.device == claim.device,
                receipts.c.capture == claim.capture,
            )).mappings().one_or_none()
            if (previous is None or previous["asset_id"] != claim.asset_id
                    or previous["digest"] != claim.digest
                    or previous["version"] != claim.version):
                raise BridgeRejected("C05B03M_CONSUMED_WITHOUT_RECEIPT")
            return
        changed = db.execute(update(review).where(
            review.c.tenant == claim.tenant,
            review.c.device == claim.device,
            review.c.capture == claim.capture,
            review.c.consumed == 0,
        ).values(consumed=1))
        if changed.rowcount != 1:
            raise BridgeRejected("C05B03M_REVIEW_CONSUMPTION_RACE")


def sign_test_device_claim(claim, challenge: str, device_private_key: Ed25519PrivateKey) -> str:
    """Device TEST code only: private key never exported to server registry."""
    if not isinstance(device_private_key, Ed25519PrivateKey):
        raise BridgeRejected("C05B03M_DEVICE_PRIVATE_KEY_REQUIRED")
    return device_private_key.sign(_signed_payload(claim, challenge)).hex()
