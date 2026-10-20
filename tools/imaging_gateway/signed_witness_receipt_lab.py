"""LOT06-M: read-only verification of SYNTHETIC external-signed CAS receipts.

THIS IS NOT AN AUTHORITY SERVICE. The PIN and the CURRENT HEAD are supplied
by the caller, not discovered or authenticated out-of-band. Signature validity
alone does NOT establish monotonic freshness, physical durability, enrollment,
key custody, remote CAS, patient consent or a clinical ACK. No filesystem I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from . import journal_lab as journal

_DOMAIN = b"DC06M|independent-witness-receipt|v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[0-9a-f]{32}\Z")
_ACTOR = re.compile(r"[a-zA-Z0-9._-]{1,64}\Z")


class SignedReceiptLabError(RuntimeError):
    """Opaque, fixed, non-clinical refusal codes."""


def _refuse(code: str) -> None:
    raise SignedReceiptLabError(code)


@dataclass(frozen=True)
class AuthorityPin:
    """Hypothetical OUT-OF-BAND pinned witness identity; caller-held in LAB."""
    authority_id: str
    epoch: str
    opaque_scope: str
    public_key_id: str
    public_key: bytes


@dataclass(frozen=True)
class DecisionEnvelope:
    authority_id: str
    epoch: str
    opaque_scope: str
    public_key_id: str
    operation_id: str
    before: journal.TrustedAnchor
    after: journal.TrustedAnchor
    transition_digest: str
    decision: str = "ACCEPTED"


@dataclass(frozen=True)
class SignedDecision:
    envelope: DecisionEnvelope
    signature: bytes


@dataclass(frozen=True)
class ReadOnlyReceiptAssessment:
    code: str
    """Never an authority ACK, an archive repair or a clinical receipt."""


def _valid_anchor(anchor: object) -> bool:
    return (type(anchor) is journal.TrustedAnchor
            and type(anchor.sequence) is int
            and 1 <= anchor.sequence <= 256
            and type(anchor.mac) is str
            and _SHA.fullmatch(anchor.mac) is not None)


def _validate_pin(pin: AuthorityPin) -> None:
    if (type(pin) is not AuthorityPin
            or type(pin.authority_id) is not str
            or _ACTOR.fullmatch(pin.authority_id) is None
            or type(pin.epoch) is not str
            or _ACTOR.fullmatch(pin.epoch) is None
            or type(pin.opaque_scope) is not str
            or _ID.fullmatch(pin.opaque_scope) is None
            or type(pin.public_key_id) is not str
            or _ID.fullmatch(pin.public_key_id) is None
            or type(pin.public_key) is not bytes
            or len(pin.public_key) != 32
            or not hmac.compare_digest(
                pin.public_key_id,
                hashlib.sha256(pin.public_key).hexdigest()[:32])):
        _refuse("PIN_INVALID")


def canonical_envelope(envelope: DecisionEnvelope) -> bytes:
    """Strict, versioned, domain-separated data signed by a FUTURE authority.

    No private key is exposed or used by this production-isolated LAB module.
    """
    if (type(envelope) is not DecisionEnvelope
            or type(envelope.authority_id) is not str
            or _ACTOR.fullmatch(envelope.authority_id) is None
            or type(envelope.epoch) is not str
            or _ACTOR.fullmatch(envelope.epoch) is None
            or type(envelope.opaque_scope) is not str
            or _ID.fullmatch(envelope.opaque_scope) is None
            or type(envelope.public_key_id) is not str
            or _ID.fullmatch(envelope.public_key_id) is None
            or type(envelope.operation_id) is not str
            or _ID.fullmatch(envelope.operation_id) is None
            or envelope.operation_id == "0" * 32
            or not _valid_anchor(envelope.before)
            or not _valid_anchor(envelope.after)
            or envelope.after.sequence != envelope.before.sequence + 1
            or not isinstance(envelope.transition_digest, str)
            or _SHA.fullmatch(envelope.transition_digest) is None
            or type(envelope.decision) is not str
            or envelope.decision != "ACCEPTED"):
        _refuse("RECEIPT_SHAPE_REFUSE")
    values = [
        "DC06M-WITNESS-RECEIPT-v1", envelope.authority_id, envelope.epoch,
        envelope.opaque_scope, envelope.public_key_id, envelope.operation_id,
        [envelope.before.sequence, envelope.before.mac],
        [envelope.after.sequence, envelope.after.mac],
        envelope.transition_digest, envelope.decision,
    ]
    return _DOMAIN + json.dumps(
        values, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def verify_read_only(
    receipt: SignedDecision, pin: AuthorityPin, *,
    expected_operation_id: str, expected_previous: journal.TrustedAnchor,
    expected_transition_digest: str, supplied_current_head: journal.TrustedAnchor,
) -> ReadOnlyReceiptAssessment:
    """Attest binding of ONE receipt, not the durability of signer/head.

    The caller must obtain the PIN and LATEST head from a separate, previously
    approved trust channel before any future authorization. NOT DONE HERE.
    """
    _validate_pin(pin)
    if type(receipt) is not SignedDecision or type(receipt.signature) is not bytes or len(receipt.signature) != 64:
        _refuse("RECEIPT_SHAPE_REFUSE")
    envelope = receipt.envelope
    payload = canonical_envelope(envelope)
    if (envelope.authority_id != pin.authority_id
            or envelope.epoch != pin.epoch
            or envelope.opaque_scope != pin.opaque_scope
            or envelope.public_key_id != pin.public_key_id):
        _refuse("AUTHORITY_BINDING_REFUSE")
    if (type(expected_operation_id) is not str
            or not hmac.compare_digest(envelope.operation_id, expected_operation_id)
            or not _valid_anchor(expected_previous)
            or envelope.before != expected_previous
            or type(expected_transition_digest) is not str
            or not hmac.compare_digest(
                envelope.transition_digest, expected_transition_digest)):
        _refuse("REQUEST_BINDING_REFUSE")
    if not _valid_anchor(supplied_current_head):
        _refuse("CURRENT_HEAD_UNKNOWN_REFUSE")
    try:
        Ed25519PublicKey.from_public_bytes(pin.public_key).verify(
            receipt.signature, payload)
    except (InvalidSignature, TypeError, ValueError):
        _refuse("SIGNATURE_REFUSE")
    if supplied_current_head.sequence < envelope.after.sequence:
        _refuse("CURRENT_HEAD_ROLLBACK_REFUSE")
    if supplied_current_head.sequence == envelope.after.sequence:
        if not hmac.compare_digest(supplied_current_head.mac, envelope.after.mac):
            _refuse("CURRENT_HEAD_FORK_REFUSE")
        return ReadOnlyReceiptAssessment("SIGNED_MATCH_NO_AUTHORIZATION")
    return ReadOnlyReceiptAssessment("SIGNED_HISTORICAL_ONLY_NO_AUTHORIZATION")
