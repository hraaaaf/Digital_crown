"""Create in-memory ephemeral signing key + signed FUE tickets for Windows CI.

NO private signer key file is created. This is NOT an independent product issuer.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

_DOMAIN = b"DIGITAL-CROWN-LOT05-SYNTHETIC-NOOP-V1\x00"
_AUDIENCE = "digital-crown:lot05:synthetic-noop:v1"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def sign(key: Ed25519PrivateKey, body: dict) -> bytes:
    signature = key.sign(_DOMAIN + canonical(body))
    return canonical({
        "body": body,
        "signature": base64.urlsafe_b64encode(signature).decode("ascii").rstrip("="),
    })


def main() -> int:
    if os.getenv("LOT05_7A_C_FAKE_ONLY") != "1" or len(sys.argv) != 3:
        return 61
    root = Path(sys.argv[1])
    service_sid = sys.argv[2]
    if not root.is_absolute() or not root.is_dir() or root.is_symlink() or not root.name.startswith("dc05c_fake_"):
        return 62
    if not service_sid.startswith("S-1-5-80-"):
        return 63
    tickets_dir = root / "tickets"
    tickets_dir.mkdir()

    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    expected = {
        "tenant_id": "synthetic-tenant-lab",
        "source_sha256": "1" * 64,
        "target_sha256": "2" * 64,
        "mapping_sha256": "3" * 64,
        "dry_run_sha256": "4" * 64,
        "backup_sha256": "5" * 64,
        "consent_sha256": "6" * 64,
    }
    provisioned = {
        "public_key_raw_b64": base64.b64encode(public).decode("ascii"),
        "key_fingerprint_sha256": hashlib.sha256(public).hexdigest(),
        "issuer_key_id": "CI-SYNTHETIC-NOT-INDEPENDENT",
        "service_identity": service_sid,
        "manifest_sha256": "a" * 64,
        "policy_version": 1,
    }
    (root / "provision.json").write_bytes(canonical({
        "provisioned": provisioned, "expected": expected
    }))
    now = int(time.time())
    body = dict(
        version=1, audience=_AUDIENCE, operation="SYNTHETIC_NOOP",
        **expected,
        manifest_sha256=provisioned["manifest_sha256"],
        issuer_key_id=provisioned["issuer_key_id"],
        service_identity=service_sid,
        policy_version=1,
        nonce=secrets.token_hex(16), issued_at=now, expires_at=now + 100,
    )
    variants = {}
    variants["valid"] = sign(key, body)
    variants["wrong_tenant"] = sign(key, dict(body, tenant_id="other-tenant"))
    variants["wrong_source"] = sign(key, dict(body, source_sha256="b" * 64))
    variants["wrong_service"] = sign(key, dict(body, service_identity="S-1-5-80-123"))
    variants["expired"] = sign(key, dict(body, issued_at=now - 300, expires_at=now - 200))
    variants["clinical"] = sign(key, dict(body, operation="CLINICAL_IMPORT"))
    variants["forged"] = sign(Ed25519PrivateKey.generate(), body)
    tampered = json.loads(variants["valid"].decode("ascii"))
    tampered["body"]["mapping_sha256"] = "c" * 64
    variants["tampered"] = canonical(tampered)
    variants["malformed"] = b'{"operation":"CLINICAL_IMPORT"}'
    for name, data in variants.items():
        (tickets_dir / (name + ".json")).write_bytes(data)
    # In-memory private key disappears when the process exits. The CI admin
    # controls the public config, so this CANNOT attest issuer independence.
    print("05C_SYNTHETIC_TICKETS_GENERATED_NO_PRIVATE_KEY_PERSISTED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
