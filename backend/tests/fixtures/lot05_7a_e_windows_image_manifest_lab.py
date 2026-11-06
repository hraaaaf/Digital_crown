"""LOT05.7A-E: ephemeral publisher manifest vs Windows-observed SCM image (CI only).

The Windows probe supplies SCM-queried service/process facts. Its admin account
creates the disposable publisher signing root here, so independence of a real
publisher, product installer, loaded-image signer and revocation are NOT proven.
"""
from __future__ import annotations

import base64
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import sys
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


DOMAIN = b"DIGITAL-CROWN-LOT05-INSTALL-MANIFEST-V1\x00"
AUDIENCE = "digital-crown:lot05:synthetic-noop:v1"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def signed(key: Ed25519PrivateKey, body: dict) -> bytes:
    signature = key.sign(DOMAIN + canonical(body))
    return canonical({
        "body": body,
        "signature": base64.urlsafe_b64encode(signature).decode("ascii").rstrip("="),
    })


def denied(verifier, envelope: bytes, root, facts, now: int, label: str) -> None:
    try:
        receipt = verifier.verify_synthetic_installer_manifest(
            envelope, publisher_root=root, observed_service=facts, now_epoch=now)
    except verifier.SyntheticInstallationDenied:
        return
    raise AssertionError("05E_INVALID_CASE_ACCEPTED_" + label + "_" + receipt.authorized_operation)


def main() -> int:
    if (os.getenv("LOT05_7A_E_FAKE_ONLY") != "1"
            or os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("RUNNER_OS") != "Windows" or len(sys.argv) != 6):
        return 61
    module_file = Path(sys.argv[1])
    service_name, service_sid, os_image, ps_sha256 = sys.argv[2:]
    if not module_file.is_file() or module_file.is_symlink():
        return 62
    image = Path(os_image)
    if not image.is_absolute() or not image.is_file() or image.is_symlink():
        return 63
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    if digest != ps_sha256:
        raise AssertionError("05E_POWERSHELL_PYTHON_IMAGE_DIGEST_MISMATCH")

    spec = importlib.util.spec_from_file_location("_lot05e_installer_attestation", module_file)
    if spec is None or spec.loader is None:
        return 64
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)

    issuer = Ed25519PrivateKey.generate()
    public = issuer.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    root = m.PublisherRoot(
        "ci-disposable-publisher-not-product", public,
        hashlib.sha256(public).hexdigest(), 7)
    facts = m.ObservedService(
        service_name, service_sid, "1.5.7.1", image,
        secrets.token_hex(16), "ci-disposable-ticket-issuer",
        "b" * 64, 7)
    now = int(time.time())
    body = {
        "schema_version": 1, "publisher": "Digital Crown",
        "publisher_root_id": root.key_id,
        "service_name": facts.service_name,
        "service_sid": facts.service_sid,
        "service_version": facts.service_version,
        "executable_sha256": digest,
        "installation_id": facts.installation_id,
        "ipc_audience": AUDIENCE,
        "authorized_operation": "SYNTHETIC_NOOP",
        "ticket_issuer_key_id": facts.ticket_issuer_key_id,
        "ticket_issuer_fingerprint_sha256": facts.ticket_issuer_fingerprint_sha256,
        "policy_version": facts.policy_version,
        "manifest_serial": 7,
        "not_before": now - 30,
        "expires_at": now + 90,
    }
    good = signed(issuer, body)
    receipt = m.verify_synthetic_installer_manifest(
        good, publisher_root=root, observed_service=facts, now_epoch=now)
    assert receipt.executable_sha256 == digest
    assert receipt.service_sid == service_sid
    assert receipt.clinical_import_permitted is False
    assert receipt.authorized_operation == "SYNTHETIC_NOOP"
    print("05E_SIGNED_MANIFEST_MATCHES_SCM_PROCESS_IMAGE_SHA256_AND_SERVICE_SID", flush=True)

    # Attacker's claimed service identity cannot override SCM-observed SID.
    denied(m, good, root, replace(facts, service_sid="S-1-5-80-1-2-3-4-5"),
           now, "WRONG_SERVICE_SID")
    denied(m, good, root, replace(facts, service_name="OtherService"),
           now, "WRONG_SERVICE_NAME")

    # The disk image hash is remeasured by the verifier, not accepted by claim.
    substitute = image.parent / ("fake-replaced-" + secrets.token_hex(6) + ".exe")
    try:
        substitute.write_bytes(b"LOT05E_REPLACED_BINARY_IS_NOT_PRODUCTION")
        denied(m, good, root, replace(facts, executable_path=substitute),
               now, "REPLACED_BINARY")
    finally:
        substitute.unlink(missing_ok=True)

    denied(m, signed(issuer, dict(body, executable_sha256="0" * 64)),
           root, facts, now, "SIGNED_WRONG_IMAGE_DIGEST")
    denied(m, signed(issuer, dict(body, service_sid="S-1-5-80-1-2-3-4-5")),
           root, facts, now, "SIGNED_WRONG_SERVICE_SID")
    denied(m, signed(issuer, dict(body, authorized_operation="CLINICAL_IMPORT")),
           root, facts, now, "CLINICAL_OPERATION")
    denied(m, signed(issuer, dict(body, manifest_serial=6)),
           root, facts, now, "ROLLBACK_SERIAL")
    denied(m, signed(issuer, dict(body, expires_at=now-1)),
           root, facts, now, "EXPIRED_MANIFEST")
    denied(m, signed(Ed25519PrivateKey.generate(), body),
           root, facts, now, "FORGED_ROOT")
    denied(m, good, None, facts, now, "MISSING_PUBLISHER_ROOT")
    print("05E_REPLACED_IMAGE_SID_FORGERY_CLINICAL_AND_ROLLBACK_DENIED", flush=True)
    print("05E_CI_EPHEMERAL_SIGNER_NOT_PRODUCT_PUBLISHER_NO_CLINICAL_IMPORT", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("05E_DENY_" + type(exc).__name__, file=sys.stderr)
        sys.exit(70)
