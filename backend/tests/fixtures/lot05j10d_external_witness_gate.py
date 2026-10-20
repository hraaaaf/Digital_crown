"""LOT05 J10D -- synthetic OFFLINE external witness envelope, DENY only.

No external provider, HSM, PKI, owner consent, or monotonic service is included.
This fixture verifies a *fake* Ed25519 receipt's integrity and scope. A valid
cryptographic receipt NEVER establishes an independent publisher/rollback root.
The production outcome of this laboratory function is ALWAYS DENY.
"""
import base64
import json
import re
import sys
import time
from collections.abc import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

SCHEMA = "DC-LOT05-J10D-EXTERNAL-WITNESS-FAKE-V1"
DOMAIN = b"DC-LOT05-J10D-EXTERNAL-WITNESS-FAKE-V1\x00"
FIELDS = frozenset((
    "schema", "device", "challenge", "ledger_id", "signer_sha256",
    "consumer_sha256", "checkpoint", "issued_at", "expires_at", "decision",
))
MAX_RECEIPT_BYTES = 2048
HEX32 = re.compile(r"^[0-9a-f]{32}$")
HEX24 = re.compile(r"^[0-9a-f]{24}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def canonical_payload(payload):
    """Canonical signing bytes; never trust an unsigned annotation."""
    return DOMAIN + json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _deny(reason):
    return "DENY_J10D_WITNESS_" + reason


def evaluate_fake_witness(
    receipt, *, raw_fake_public_key, expected_device, expected_challenge,
    expected_ledger_id, expected_signer_sha256, expected_consumer_sha256,
    last_externally_confirmed_checkpoint, now,
):
    """Fail-closed specimen, not a production authorization API.

    The caller-supplied checkpoint floor is NOT authenticated by this code;
    real monotonicity requires an external witness's independently stored state.
    Even a fully valid fake receipt returns DENY, never ALLOW.
    """
    try:
        if type(receipt) is not dict or set(receipt) != {"payload", "signature"}:
            return _deny("STRUCTURE")
        payload = receipt["payload"]
        if type(payload) is not dict or set(payload) != FIELDS:
            return _deny("STRUCTURE")
        if not isinstance(raw_fake_public_key, bytes) or len(raw_fake_public_key) != 32:
            return _deny("ROOT_UNAVAILABLE")
        if not all(isinstance(x, str) for x in (
            expected_device, expected_challenge, expected_ledger_id,
            expected_signer_sha256, expected_consumer_sha256,
        )):
            return _deny("CONTEXT")
        if not HEX32.fullmatch(expected_challenge) or not HEX24.fullmatch(expected_ledger_id):
            return _deny("CONTEXT")
        if not HEX64.fullmatch(expected_signer_sha256) or not HEX64.fullmatch(expected_consumer_sha256):
            return _deny("CONTEXT")
        if type(last_externally_confirmed_checkpoint) is not int or last_externally_confirmed_checkpoint < 0:
            return _deny("CHECKPOINT_FLOOR")
        if type(now) is not int or now < 0:
            return _deny("TIME")
        if payload["schema"] != SCHEMA or payload["decision"] != "DENY_ONLY_LAB":
            return _deny("SCHEMA")
        for key, expected in (
            ("device", expected_device),
            ("challenge", expected_challenge),
            ("ledger_id", expected_ledger_id),
            ("signer_sha256", expected_signer_sha256),
            ("consumer_sha256", expected_consumer_sha256),
        ):
            if payload[key] != expected:
                return _deny("SCOPE")
        if not expected_device or len(expected_device) > 128 or not expected_device.isascii():
            return _deny("DEVICE")
        if any(type(payload[key]) is not int for key in ("checkpoint", "issued_at", "expires_at")):
            return _deny("STRUCTURE")
        issued = payload["issued_at"]
        expires = payload["expires_at"]
        if issued > now + 5 or issued < now - 60 or expires <= now or expires > issued + 60:
            return _deny("TIME")
        if payload["checkpoint"] <= last_externally_confirmed_checkpoint:
            return _deny("ROLLBACK_OR_REPLAY")
        signing_bytes = canonical_payload(payload)
        if len(signing_bytes) > MAX_RECEIPT_BYTES:
            return _deny("OVERSIZE")
        signature_text = receipt["signature"]
        if not isinstance(signature_text, str) or len(signature_text) != 88:
            return _deny("SIGNATURE")
        signature = base64.b64decode(signature_text, validate=True)
        if len(signature) != 64:
            return _deny("SIGNATURE")
        Ed25519PublicKey.from_public_bytes(raw_fake_public_key).verify(
            signature, signing_bytes,
        )
    except (InvalidSignature, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        return _deny("SIGNATURE_OR_MALFORMED")
    # It is cryptographically bound, but public key/checkpoint were provided by
    # the same disposable test runner. NEVER set a product GO flag.
    return _deny("CRYPTO_VALID_FAKE_ROOT_IS_NOT_INDEPENDENT")


def product_readiness(*_args, **_kwargs):
    """No independent vendor root, remote monotonic authority or powercut proof."""
    return _deny("EXTERNAL_AUTHORITY_NOT_ENROLLED")


def main():
    print(product_readiness())
    return 3  # explicitly nonzero, including when run on CI Windows


if __name__ == "__main__":
    sys.exit(main())
