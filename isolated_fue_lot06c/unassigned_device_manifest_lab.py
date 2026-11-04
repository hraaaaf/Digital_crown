"""LOT06 B06: patient-UNASSIGNED Ed25519 capture manifest, SQLCipher LAB only.

A device signs the media before any staff or patient selection. This does
NOT enroll a real scanner or authorize product ingestion. Clinical binding
is a separate explicit staff review after verification of this manifest.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re
import secrets
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from sqlalchemy import (
    Column, Integer, MetaData, String, Table, UniqueConstraint,
    insert, select, update,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from isolated_fue_lot06c.c05b03m_security_gate_lab import (
    BridgeRejected, _guard, identity,
)

metadata = MetaData()
unassigned = Table(
    "c05b03n_lab_unassigned_signed_capture", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("station", String(36), nullable=False),
    Column("generation", Integer, nullable=False),
    Column("digest", String(64), nullable=False),
    Column("byte_size", Integer, nullable=False),
    Column("mime", String(32), nullable=False),
    Column("nonce", String(48), nullable=False),
    Column("issued_at", Integer, nullable=False),
    Column("expires_at", Integer, nullable=False),
    Column("signature", String(128), nullable=False),
    Column("consumed", Integer, nullable=False, default=0),
    UniqueConstraint("tenant", "device", "nonce", name="uq_c05b03n_nonce"),
)


@dataclass(frozen=True)
class UnassignedManifest:
    tenant: int
    device: str
    station: str
    generation: int
    capture: str
    digest: str
    byte_size: int
    mime: str
    nonce: str
    issued_at: int
    expires_at: int


def _wire(manifest: UnassignedManifest) -> bytes:
    """Stable signed bytes: intentionally no patient, staff, dossier or RDV."""
    if (not isinstance(manifest, UnassignedManifest)
            or type(manifest.tenant) is not int or manifest.tenant <= 0
            or type(manifest.generation) is not int or manifest.generation <= 0
            or not isinstance(manifest.device, str)
            or re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", manifest.device) is None
            or not isinstance(manifest.station, str)
            or not 1 <= len(manifest.station) <= 36
            or not isinstance(manifest.capture, str)
            or re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", manifest.capture) is None
            or not isinstance(manifest.digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", manifest.digest) is None
            or type(manifest.byte_size) is not int
            or not 1 <= manifest.byte_size <= 50 * 1024 * 1024
            or manifest.mime != "image/png"
            or not isinstance(manifest.nonce, str)
            or re.fullmatch(r"[a-f0-9]{48}", manifest.nonce) is None
            or type(manifest.issued_at) is not int
            or type(manifest.expires_at) is not int
            or not 0 < manifest.issued_at < manifest.expires_at
            or manifest.expires_at - manifest.issued_at > 180):
        raise BridgeRejected("UNASSIGNED_MANIFEST_CANONICAL_DENIED")
    data = {
        "purpose": "DC06_B06_UNASSIGNED_DEVICE_CAPTURE_LAB_V1",
        **vars(manifest),
    }
    return json.dumps(
        data, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")


def new_unassigned_manifest(
    *, tenant: int, device: str, station: str, generation: int,
    capture: str, digest: str, byte_size: int, mime: str = "image/png",
    nonce: str | None = None, now: int | None = None,
) -> UnassignedManifest:
    """Device-side contract: accepts ONLY unassigned capture metadata.

    Cannot receive a Patient/User/Appointment model or a patient-bound claim.
    The future physical scanner must produce this BEFORE any staff selection.
    """
    issued = int(time.time()) if now is None else now
    result = UnassignedManifest(
        tenant=tenant, device=device, station=station,
        generation=generation, capture=capture,
        digest=digest, byte_size=byte_size, mime=mime,
        nonce=nonce if nonce is not None else secrets.token_hex(24),
        issued_at=issued, expires_at=issued + 170,
    )
    _wire(result)
    return result


def sign_unassigned(manifest: UnassignedManifest,
                    key: Ed25519PrivateKey) -> str:
    if not isinstance(key, Ed25519PrivateKey):
        raise BridgeRejected("UNASSIGNED_DEVICE_PRIVATE_KEY_REQUIRED")
    return key.sign(_wire(manifest)).hex()


def _registry(db: Session, manifest: UnassignedManifest, signature: str) -> None:
    _guard(db)
    _wire(manifest)
    if (not isinstance(signature, str)
            or re.fullmatch(r"[a-f0-9]{128}", signature) is None):
        raise BridgeRejected("UNASSIGNED_MANIFEST_SIGNATURE_REQUIRED")
    dev = db.execute(select(identity).where(
        identity.c.tenant == manifest.tenant,
        identity.c.device == manifest.device,
    )).mappings().one_or_none()
    if (dev is None or dev["active"] != 1
            or dev["station"] != manifest.station
            or dev["generation"] != manifest.generation):
        raise BridgeRejected("UNASSIGNED_DEVICE_NOT_ENROLLED_OR_REVOKED")
    try:
        Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(dev["public_key_hex"])
        ).verify(bytes.fromhex(signature), _wire(manifest))
    except (InvalidSignature, ValueError, TypeError):
        raise BridgeRejected("UNASSIGNED_SIGNATURE_INVALID") from None


def _fresh(manifest: UnassignedManifest) -> None:
    now = int(time.time())
    if (manifest.issued_at > now + 5
            or now - manifest.issued_at > 120
            or manifest.expires_at <= now):
        raise BridgeRejected("UNASSIGNED_MANIFEST_EXPIRED_OR_FUTURE")


def register_unassigned(db: Session, manifest: UnassignedManifest,
                        signature: str) -> None:
    """Synthetic device arrival: durable immutable capture, still NO patient."""
    _registry(db, manifest, signature)
    _fresh(manifest)
    metadata.create_all(bind=db.get_bind(), checkfirst=True)
    # SQLCipher's native driver can raise a raw DB-API IntegrityError,
    # bypassing SQLAlchemy's wrapped exception type. Keep uniqueness atomic:
    # a duplicate capture or nonce never inserts and never escapes as a raw
    # SQL exception. Other SQL/storage errors still fail closed.
    result = db.execute(
        sqlite_insert(unassigned).values(
            **vars(manifest), signature=signature, consumed=0,
        ).on_conflict_do_nothing()
    )
    if result.rowcount != 1:
        db.rollback()
        raise BridgeRejected("UNASSIGNED_MANIFEST_DUPLICATE_OR_NONCE_REPLAY")
    db.commit()


def _from_row(row) -> UnassignedManifest:
    return UnassignedManifest(**{
        name: row[name] for name in UnassignedManifest.__dataclass_fields__
    })


def check_pending(db: Session, claim) -> None:
    """Server's independent capture proof; no patient/clinician in signature."""
    _guard(db)
    row = db.execute(select(unassigned).where(
        unassigned.c.tenant == claim.tenant,
        unassigned.c.device == claim.device,
        unassigned.c.capture == claim.capture,
    )).mappings().one_or_none()
    if row is None or row["consumed"] != 0:
        raise BridgeRejected("UNASSIGNED_CAPTURE_ABSENT_OR_CONSUMED")
    manifest = _from_row(row)
    if (manifest.station != claim.station
            or manifest.generation != claim.generation
            or manifest.digest != claim.digest
            or manifest.byte_size != claim.byte_size):
        raise BridgeRejected("UNASSIGNED_CAPTURE_BYTES_OR_DEVICE_CHANGED")
    _fresh(manifest)
    _registry(db, manifest, row["signature"])


def consume_for_review(db: Session, claim) -> None:
    """Must run INSIDE the same SQLCipher transaction as staff confirmation."""
    check_pending(db, claim)
    changed = db.execute(update(unassigned).where(
        unassigned.c.tenant == claim.tenant,
        unassigned.c.device == claim.device,
        unassigned.c.capture == claim.capture,
        unassigned.c.consumed == 0,
    ).values(consumed=1))
    if changed.rowcount != 1:
        raise BridgeRejected("UNASSIGNED_CAPTURE_CONSUMPTION_RACE")
