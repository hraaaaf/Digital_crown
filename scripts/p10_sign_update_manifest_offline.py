from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Kept intentionally explicit and dependency-light so this operator tool can run
# on the offline signing machine without importing the application/database stack.
# CI cross-checks this mapping against UpdateEngine.PINNED_UPDATE_KEYS.
PINNED_UPDATE_PUBLIC_KEYS: dict[str, str] = {
    "77b4db9273df41c7c0757fe72e22e72e4db5047dc9e93b4a7727057721c6327d": "b/G7b36fLA+hHzsZSZgHZW+/KciLo6TtTigKZrR2i3I=",
    "197844cf7453ce0f1d2a36f14c699deafbbc6e05d2dae22b753e50ad3c3877bc": "E1RFOhXrP58VFolAYvNFaMCgv7+8othjnID3On9cTnE=",
}


class OfflineSigningError(RuntimeError):
    pass


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _load_private_key(path: Path) -> Ed25519PrivateKey:
    data = path.expanduser().resolve().read_bytes()
    try:
        key = serialization.load_pem_private_key(data, password=None)
    except TypeError:
        password = getpass.getpass("Private key passphrase: ").encode("utf-8")
        key = serialization.load_pem_private_key(data, password=password)
    except (ValueError, OSError) as exc:
        raise OfflineSigningError("PRIVATE_KEY_LOAD_FAILED") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise OfflineSigningError("PRIVATE_KEY_NOT_ED25519")
    return key


def _validate_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise OfflineSigningError("MANIFEST_PAYLOAD_MUST_BE_OBJECT")
    if int(payload.get("schema", 0)) != 1:
        raise OfflineSigningError("MANIFEST_SCHEMA_UNSUPPORTED")
    sequence = payload.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= 0:
        raise OfflineSigningError("MANIFEST_SEQUENCE_INVALID")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", str(payload.get("version") or "")):
        raise OfflineSigningError("MANIFEST_VERSION_INVALID")
    targets = payload.get("targets")
    if not isinstance(targets, list) or not targets:
        raise OfflineSigningError("MANIFEST_TARGETS_REQUIRED")
    return payload


def sign_payload(
    payload: dict[str, Any],
    private_key: Ed25519PrivateKey,
    *,
    expected_key_id: str,
) -> dict[str, Any]:
    expected = str(expected_key_id or "").strip().lower()
    if not SHA256_PATTERN.fullmatch(expected):
        raise OfflineSigningError("EXPECTED_KEY_ID_INVALID")

    raw_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    derived_key_id = hashlib.sha256(raw_public).hexdigest()
    if derived_key_id != expected:
        raise OfflineSigningError("PRIVATE_KEY_ID_MISMATCH")

    pinned_b64 = PINNED_UPDATE_PUBLIC_KEYS.get(derived_key_id)
    if pinned_b64 is None:
        raise OfflineSigningError("PRIVATE_KEY_NOT_PINNED")
    if base64.b64decode(pinned_b64, validate=True) != raw_public:
        raise OfflineSigningError("PINNED_PUBLIC_KEY_MISMATCH")

    signed = _validate_payload(payload)
    signature = private_key.sign(_canonical_json(signed))
    return {
        "signed": signed,
        "signature": {
            "keyid": derived_key_id,
            "algorithm": "ed25519",
            "sig": base64.b64encode(signature).decode("ascii"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Sign a Digital Crown update manifest payload on an offline machine. "
            "The private key never leaves the local filesystem."
        )
    )
    parser.add_argument("--private-key", required=True, type=Path)
    parser.add_argument(
        "--expected-key-id",
        required=True,
        help="SHA-256 key id of the operational primary key from the offline custody record.",
    )
    parser.add_argument("--payload", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    payload = json.loads(args.payload.expanduser().resolve().read_text(encoding="utf-8"))
    key = _load_private_key(args.private_key)
    envelope = sign_payload(payload, key, expected_key_id=args.expected_key_id)

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(envelope, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    manifest_sha256 = hashlib.sha256(_canonical_json(envelope["signed"])).hexdigest()
    print(
        "P10_OFFLINE_MANIFEST_SIGNED "
        f"keyid={envelope['signature']['keyid']} manifest_sha256={manifest_sha256} output={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
