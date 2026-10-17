"""SEC-P1.4 reference-only Ed25519 licence verifier (NOT wired into product).

This executable-lab module demonstrates a possible offline-verifiable
publisher-to-cabinet trust boundary. It is NOT an issuer and cannot issue
licences. No private key or network client belongs in this module.

Important limitation: trusted_now and minimum_revocation_epoch MUST be provided
by a trustworthy production authority; this lab DOES NOT supply a secure
hardware clock, trusted monotonic state or remote revocation.
"""
from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

MAX_ENVELOPE_BYTES = 8192
MAX_OFFLINE_SECONDS = 72 * 3600
DOMAINTAG = b"DigitalCrown/licence/v1\x00"
KID_RE = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
B64URL_RE = re.compile(r"[A-Za-z0-9_-]{86}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}\Z")
PACKS = {"BASIC", "GOLD", "ELITE"}
CHANNELS = {"stable", "pilot"}
FEATURES = {"agenda", "patients", "imaging", "reports", "finance", "mobile"}
ENVELOPE_FIELDS = {"v", "kid", "payload", "signature"}
PAYLOAD_FIELDS = {
    "license_id", "cabinet_id", "device_binding_hash", "pack",
    "features", "channel", "issued_at", "not_before", "expires_at",
    "last_online_at", "offline_until", "revocation_epoch",
}


class LicenseRejected(ValueError):
    """Refusal without logging payloads, tokens, cabinet identifiers or keys."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class LicenseClaims:
    license_id: str
    cabinet_id: str
    pack: str
    features: frozenset[str]
    expires_at: int
    offline_until: int
    revocation_epoch: int


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for name, value in pairs:
        if name in data:
            raise LicenseRejected("duplicate-field")
        data[name] = value
    return data


def canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("ascii")


def signing_message(kid: str, payload: dict[str, Any]) -> bytes:
    """Domain-separate licence signatures from other Ed25519 uses."""
    return DOMAINTAG + kid.encode("ascii") + b"\x00" + canonical_payload(payload)


def _u64(value: object) -> bool:
    return type(value) is int and 0 <= value <= 2**63 - 1


def verify_license(
    envelope_json: str,
    *,
    public_keys: Mapping[str, Ed25519PublicKey],
    trusted_now: int,
    cabinet_id: str,
    device_binding_hash: str,
    required_pack: str,
    required_feature: str,
    release_channel: str,
    minimum_revocation_epoch: int,
    revoked_key_ids: frozenset[str] = frozenset(),
) -> LicenseClaims:
    """Verify authenticity AND signed policy. Reject ambiguity, never fail open.

    The caller must supply *trusted* time, device identity and revocation state.
    Passing wall-clock time and mutable client local state here does NOT make
    offline enforcement tamper-proof. No error should remove clinical data.
    """
    if (
        type(envelope_json) is not str
        or len(envelope_json.encode("utf-8")) > MAX_ENVELOPE_BYTES
        or not envelope_json
    ):
        raise LicenseRejected("invalid-envelope")
    if not all(
        isinstance(v, str)
        for v in (cabinet_id, device_binding_hash, required_pack,
                  required_feature, release_channel)
    ) or not _u64(trusted_now) or not _u64(minimum_revocation_epoch):
        raise LicenseRejected("invalid-verifier-context")
    if required_pack not in PACKS or required_feature not in FEATURES or release_channel not in CHANNELS:
        raise LicenseRejected("invalid-verifier-context")
    if not SHA256_RE.fullmatch(device_binding_hash):
        raise LicenseRejected("invalid-device-identity")

    try:
        data = json.loads(envelope_json, object_pairs_hook=_no_duplicates,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              LicenseRejected("invalid-number")))
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise LicenseRejected("invalid-envelope") from exc

    if not isinstance(data, dict) or set(data) != ENVELOPE_FIELDS or data.get("v") != 1 or type(data["v"]) is not int:
        raise LicenseRejected("invalid-envelope")
    kid = data["kid"]
    if not isinstance(kid, str) or not KID_RE.fullmatch(kid):
        raise LicenseRejected("invalid-key-id")
    if kid in revoked_key_ids or kid not in public_keys:
        raise LicenseRejected("untrusted-key-id")
    key = public_keys[kid]
    if not isinstance(key, Ed25519PublicKey):
        raise LicenseRejected("invalid-public-key")

    signed = data["payload"]
    if not isinstance(signed, dict) or set(signed) != PAYLOAD_FIELDS:
        raise LicenseRejected("invalid-payload")
    if not all(isinstance(signed[k], str) and ID_RE.fullmatch(signed[k])
               for k in ("cabinet_id", "license_id")):
        raise LicenseRejected("invalid-payload")
    if not isinstance(signed["device_binding_hash"], str) or not SHA256_RE.fullmatch(signed["device_binding_hash"]):
        raise LicenseRejected("invalid-payload")
    if type(signed["pack"]) is not str or signed["pack"] not in PACKS:
        raise LicenseRejected("invalid-pack")
    if type(signed["channel"]) is not str or signed["channel"] not in CHANNELS:
        raise LicenseRejected("invalid-channel")
    features = signed["features"]
    if not (isinstance(features, list) and features
            and all(isinstance(f, str) and f in FEATURES for f in features)
            and len(set(features)) == len(features)):
        raise LicenseRejected("invalid-features")
    time_fields = ("issued_at", "not_before", "expires_at", "last_online_at",
                   "offline_until", "revocation_epoch")
    if not all(_u64(signed[f]) for f in time_fields):
        raise LicenseRejected("invalid-time")
    if not (
        signed["issued_at"] <= signed["last_online_at"] <= signed["offline_until"]
        and signed["issued_at"] <= signed["not_before"] < signed["expires_at"]
        and signed["offline_until"] <= signed["last_online_at"] + MAX_OFFLINE_SECONDS
        and signed["offline_until"] <= signed["expires_at"]
    ):
        raise LicenseRejected("invalid-time-window")

    signature = data["signature"]
    if not isinstance(signature, str) or not B64URL_RE.fullmatch(signature):
        raise LicenseRejected("invalid-signature-encoding")
    try:
        raw = base64.b64decode(signature + "==", altchars=b"-_", validate=True)
        if len(raw) != 64 or base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != signature:
            raise LicenseRejected("invalid-signature-encoding")
        key.verify(raw, signing_message(kid, signed))
    except (InvalidSignature, ValueError, binascii.Error) as exc:
        raise LicenseRejected("bad-signature") from exc

    if signed["cabinet_id"] != cabinet_id or signed["device_binding_hash"] != device_binding_hash:
        raise LicenseRejected("identity-mismatch")
    if signed["pack"] != required_pack or required_feature not in features or signed["channel"] != release_channel:
        raise LicenseRejected("entitlement-denied")
    if signed["revocation_epoch"] < minimum_revocation_epoch:
        raise LicenseRejected("revoked-epoch")
    if trusted_now < signed["not_before"]:
        raise LicenseRejected("not-yet-valid")
    if trusted_now > signed["expires_at"]:
        raise LicenseRejected("expired")
    if trusted_now > signed["offline_until"]:
        raise LicenseRejected("offline-window-exhausted")

    return LicenseClaims(
        license_id=signed["license_id"], cabinet_id=signed["cabinet_id"],
        pack=signed["pack"], features=frozenset(features),
        expires_at=signed["expires_at"], offline_until=signed["offline_until"],
        revocation_epoch=signed["revocation_epoch"],
    )
