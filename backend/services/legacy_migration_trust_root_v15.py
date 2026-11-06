"""LOT05.7A: verify-only SYNTHETIC_NOOP signed tickets (FUE isolation).

This module CANNOT issue tickets or activate a clinical import. The anchor and
expected context MUST eventually come from an independently attested product
service, not from a request. No such product provisioning/IPC exists yet.
A test replay store is NOT evidence of crash/rollback-resistant persistence.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import re
from typing import Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


_AUDIENCE = "digital-crown:lot05:synthetic-noop:v1"
_DOMAIN = b"DIGITAL-CROWN-LOT05-SYNTHETIC-NOOP-V1\x00"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_NONCE = re.compile(r"[0-9a-f]{32}\Z")
_MAX_TTL_SECONDS = 120
_MAX_ENVELOPE_BYTES = 8192
_FIELDS = frozenset({
    "version", "audience", "operation", "tenant_id", "source_sha256",
    "target_sha256", "mapping_sha256", "dry_run_sha256", "backup_sha256",
    "consent_sha256", "manifest_sha256", "issuer_key_id", "service_identity",
    "policy_version", "nonce", "issued_at", "expires_at",
})


class SyntheticAuthorityDenied(ValueError):
    """Non-PHI refusal code. Never interpret a denial as approval."""


@dataclass(frozen=True)
class ProvisionedVerifier:
    """Test input: NOT trustworthy until an installer/service attests its source."""

    public_key_raw: bytes
    key_fingerprint_sha256: str
    issuer_key_id: str
    service_identity: str
    manifest_sha256: str
    policy_version: int


@dataclass(frozen=True)
class ExpectedSyntheticContext:
    tenant_id: str
    source_sha256: str
    target_sha256: str
    mapping_sha256: str
    dry_run_sha256: str
    backup_sha256: str
    consent_sha256: str


@dataclass(frozen=True)
class SyntheticNoopReceipt:
    tenant_id: str
    nonce: str
    verified_noop: bool = True
    clinical_import_permitted: bool = False


class AtomicReplayLedger(Protocol):
    def consume_once(self, namespace: str, nonce: str) -> bool:
        """Atomically return True only on the first use, with durable persistence."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SyntheticAuthorityDenied("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _hash_ok(value: object) -> bool:
    return type(value) is str and bool(_HEX64.fullmatch(value))


def _deny_unless(condition: bool, code: str) -> None:
    if not condition:
        raise SyntheticAuthorityDenied(code)


def verify_synthetic_noop_ticket(
    envelope_bytes: bytes,
    *,
    provisioned: ProvisionedVerifier,
    expected: ExpectedSyntheticContext,
    now_epoch: int,
    replay_ledger: AtomicReplayLedger,
) -> SyntheticNoopReceipt:
    """Offline FUE verifier only. Never call this to execute an import.

    Ticket private-key signing is deliberately absent from product runtime.
    The verifier pin/context/ledger must not be caller controlled in a product.
    """
    _deny_unless(type(provisioned) is ProvisionedVerifier, "UNPROVISIONED_ROOT")
    _deny_unless(type(expected) is ExpectedSyntheticContext, "UNBOUND_REQUEST")
    _deny_unless(type(now_epoch) is int and now_epoch >= 0, "INVALID_CLOCK")
    _deny_unless(replay_ledger is not None, "REPLAY_STORE_MISSING")
    _deny_unless(type(envelope_bytes) is bytes and 0 < len(envelope_bytes) <= _MAX_ENVELOPE_BYTES, "INVALID_ENVELOPE_SIZE")
    _deny_unless(type(provisioned.public_key_raw) is bytes and len(provisioned.public_key_raw) == 32, "INVALID_PROVISIONED_KEY")
    _deny_unless(_hash_ok(provisioned.key_fingerprint_sha256), "INVALID_KEY_FINGERPRINT")
    _deny_unless(hmac.compare_digest(hashlib.sha256(provisioned.public_key_raw).hexdigest(), provisioned.key_fingerprint_sha256), "PIN_MISMATCH")
    _deny_unless(_hash_ok(provisioned.manifest_sha256), "INVALID_MANIFEST_DIGEST")
    _deny_unless(type(provisioned.policy_version) is int and provisioned.policy_version >= 1, "INVALID_POLICY")
    _deny_unless(type(provisioned.issuer_key_id) is str and 0 < len(provisioned.issuer_key_id) <= 128, "INVALID_ISSUER")
    _deny_unless(type(provisioned.service_identity) is str and 0 < len(provisioned.service_identity) <= 128, "INVALID_SERVICE_IDENTITY")
    _deny_unless(type(expected.tenant_id) is str and 0 < len(expected.tenant_id) <= 128, "INVALID_TENANT")
    for field in ("source_sha256", "target_sha256", "mapping_sha256", "dry_run_sha256", "backup_sha256", "consent_sha256"):
        _deny_unless(_hash_ok(getattr(expected, field)), "UNBOUND_DIGEST")

    try:
        envelope = json.loads(envelope_bytes.decode("utf-8", errors="strict"), object_pairs_hook=_reject_duplicate_pairs,
                              parse_constant=lambda _value: (_ for _ in ()).throw(SyntheticAuthorityDenied("INVALID_JSON_CONSTANT")))
    except (ValueError, UnicodeError, TypeError, RecursionError) as exc:
        raise SyntheticAuthorityDenied("INVALID_ENVELOPE_JSON") from exc
    _deny_unless(type(envelope) is dict and set(envelope) == {"body", "signature"}, "INVALID_ENVELOPE_SHAPE")
    _deny_unless(hmac.compare_digest(envelope_bytes, _canonical(envelope)), "NONCANONICAL_ENVELOPE")
    body, encoded_signature = envelope["body"], envelope["signature"]
    _deny_unless(type(body) is dict and set(body) == _FIELDS, "INVALID_BODY_SHAPE")
    _deny_unless(type(encoded_signature) is str and len(encoded_signature) == 86 and
                 bool(re.fullmatch(r"[A-Za-z0-9_-]{86}", encoded_signature)), "INVALID_SIGNATURE_ENCODING")
    try:
        signature = base64.urlsafe_b64decode(encoded_signature + "==")
    except ValueError as exc:
        raise SyntheticAuthorityDenied("INVALID_SIGNATURE_ENCODING") from exc
    _deny_unless(len(signature) == 64 and base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=") == encoded_signature, "INVALID_SIGNATURE_ENCODING")
    try:
        Ed25519PublicKey.from_public_bytes(provisioned.public_key_raw).verify(signature, _DOMAIN + _canonical(body))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise SyntheticAuthorityDenied("INVALID_SIGNATURE") from exc

    expected_claims = {
        "version": 1, "audience": _AUDIENCE, "operation": "SYNTHETIC_NOOP",
        "tenant_id": expected.tenant_id, "source_sha256": expected.source_sha256,
        "target_sha256": expected.target_sha256, "mapping_sha256": expected.mapping_sha256,
        "dry_run_sha256": expected.dry_run_sha256, "backup_sha256": expected.backup_sha256,
        "consent_sha256": expected.consent_sha256, "manifest_sha256": provisioned.manifest_sha256,
        "issuer_key_id": provisioned.issuer_key_id, "service_identity": provisioned.service_identity,
        "policy_version": provisioned.policy_version,
    }
    for key, value in expected_claims.items():
        _deny_unless(type(body[key]) is type(value) and body[key] == value, "CLAIM_MISMATCH_" + key.upper())
    _deny_unless(type(body["nonce"]) is str and bool(_NONCE.fullmatch(body["nonce"])), "INVALID_NONCE")
    _deny_unless(type(body["issued_at"]) is int and type(body["expires_at"]) is int, "INVALID_TIME_CLAIMS")
    _deny_unless(body["issued_at"] <= now_epoch < body["expires_at"] <= body["issued_at"] + _MAX_TTL_SECONDS, "EXPIRED_OR_LONG_TTL")
    namespace = f"{provisioned.issuer_key_id}:{provisioned.key_fingerprint_sha256}:{body['tenant_id']}"
    try:
        consumed = replay_ledger.consume_once(namespace, body["nonce"])
    except Exception as exc:
        raise SyntheticAuthorityDenied("REPLAY_LEDGER_UNAVAILABLE") from exc
    _deny_unless(consumed is True, "REPLAY_OR_LEDGER_INVALID")
    return SyntheticNoopReceipt(tenant_id=expected.tenant_id, nonce=body["nonce"])
