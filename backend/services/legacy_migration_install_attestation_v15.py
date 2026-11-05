"""LOT05.7A-D: verify-only signed installer manifest for SYNTHETIC_NOOP lab.

The trusted publisher root and observed running-service facts MUST come from
independently attested product installation / Windows OS, NEVER a caller or the
manifest itself. This function cannot provision keys, register a service, sign
a manifest, approve any clinical import or attest a running image by itself.

Lab FUE uses disposable root keys and fixture binary files. It demonstrates
verification semantics, NOT an independent production authority.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

_DOMAIN = b"DIGITAL-CROWN-LOT05-INSTALL-MANIFEST-V1\x00"
_ALLOWED_AUDIENCE = "digital-crown:lot05:synthetic-noop:v1"
_FIELDS = frozenset({
    "schema_version", "publisher", "publisher_root_id", "service_name",
    "service_sid", "service_version", "executable_sha256",
    "installation_id", "ipc_audience", "authorized_operation",
    "ticket_issuer_key_id", "ticket_issuer_fingerprint_sha256",
    "policy_version", "manifest_serial", "not_before", "expires_at",
})
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_INSTALL_ID = re.compile(r"[0-9a-f]{32}\Z")
_SID = re.compile(r"S-1-5-80-(?:[0-9]+-){4}[0-9]+\Z")
_SERVICE = re.compile(r"[A-Za-z0-9_-]{4,96}\Z")
_VERSION = re.compile(r"[0-9]+(?:\.[0-9]+){1,3}\Z")
_MAX_MANIFEST_BYTES = 8192
_MAX_BINARY_BYTES = 128 * 1024 * 1024
_MAX_MANIFEST_AGE = 366 * 24 * 3600


class SyntheticInstallationDenied(ValueError):
    """Denial is non-sensitive. Fail closed if provenance cannot be proven."""


@dataclass(frozen=True)
class PublisherRoot:
    # MUST be trusted out-of-band, e.g. vendor-controlled installer root.
    # A caller providing both public key and fingerprint is NOT a trust root.
    key_id: str
    public_key_raw: bytes
    pinned_fingerprint_sha256: str
    minimum_manifest_serial: int


@dataclass(frozen=True)
class ObservedService:
    # A product MUST obtain these from Windows SCM token / loaded executable,
    # not from UI, HTTP, JWT, target DB, temp files or request data.
    service_name: str
    service_sid: str
    service_version: str
    executable_path: Path
    installation_id: str
    ticket_issuer_key_id: str
    ticket_issuer_fingerprint_sha256: str
    policy_version: int


@dataclass(frozen=True)
class SyntheticInstallationReceipt:
    manifest_sha256: str
    service_sid: str
    executable_sha256: str
    authorized_operation: str = "SYNTHETIC_NOOP"
    clinical_import_permitted: bool = False


def _deny_unless(ok: bool, code: str) -> None:
    if not ok:
        raise SyntheticInstallationDenied(code)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SyntheticInstallationDenied("DUPLICATE_KEY")
        result[key] = value
    return result


def _hash_ok(value: object) -> bool:
    return type(value) is str and bool(_HEX64.fullmatch(value))


def _measured_binary_digest(file_path: Path) -> str:
    """Hash a single regular binary without following symlinks.

    OS-loaded-image attestation and privileged path provenance are OUT OF SCOPE
    for this primitive; its caller must establish them separately.
    """
    _deny_unless(isinstance(file_path, Path), "UNVERIFIED_EXECUTABLE_PATH")
    try:
        before = file_path.lstat()
        _deny_unless(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                     and 0 < before.st_size <= _MAX_BINARY_BYTES, "UNTRUSTED_EXECUTABLE")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
        handle = os.open(str(file_path), flags)
        try:
            opened = os.fstat(handle)
            _deny_unless(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1
                         and opened.st_dev == before.st_dev and opened.st_ino == before.st_ino
                         and opened.st_size == before.st_size
                         and opened.st_mtime_ns == before.st_mtime_ns, "EXECUTABLE_CHANGED")
            hasher = hashlib.sha256()
            with os.fdopen(handle, "rb", closefd=False) as file:
                total = 0
                while True:
                    part = file.read(1024 * 1024)
                    if not part:
                        break
                    total += len(part)
                    _deny_unless(total <= _MAX_BINARY_BYTES, "EXECUTABLE_TOO_LARGE")
                    hasher.update(part)
            after = os.fstat(handle)
            _deny_unless(after.st_size == opened.st_size
                         and after.st_mtime_ns == opened.st_mtime_ns
                         and after.st_ino == opened.st_ino, "EXECUTABLE_CHANGED")
            return hasher.hexdigest()
        finally:
            os.close(handle)
    except (OSError, ValueError) as exc:
        raise SyntheticInstallationDenied("EXECUTABLE_UNAVAILABLE") from exc


def verify_synthetic_installer_manifest(
    envelope_bytes: bytes,
    *,
    publisher_root: PublisherRoot,
    observed_service: ObservedService,
    now_epoch: int,
) -> SyntheticInstallationReceipt:
    """Verify a strictly scoped signed provisioning manifest; NOOP only.

    This validates trusted facts supplied by the *installer*, but does not
    authenticate the installer that supplied them. Product gate stays OPEN.
    """
    _deny_unless(type(publisher_root) is PublisherRoot, "MISSING_PUBLISHER_ROOT")
    _deny_unless(type(observed_service) is ObservedService, "MISSING_OS_SERVICE_FACTS")
    _deny_unless(type(now_epoch) is int and now_epoch >= 0, "INVALID_CLOCK")
    _deny_unless(type(envelope_bytes) is bytes and
                 0 < len(envelope_bytes) <= _MAX_MANIFEST_BYTES, "INVALID_MANIFEST_SIZE")
    _deny_unless(type(publisher_root.public_key_raw) is bytes
                 and len(publisher_root.public_key_raw) == 32, "INVALID_ROOT_KEY")
    _deny_unless(_hash_ok(publisher_root.pinned_fingerprint_sha256), "INVALID_ROOT_PIN")
    _deny_unless(hmac.compare_digest(
        hashlib.sha256(publisher_root.public_key_raw).hexdigest(),
        publisher_root.pinned_fingerprint_sha256), "PUBLISHER_PIN_MISMATCH")
    _deny_unless(type(publisher_root.key_id) is str
                 and 0 < len(publisher_root.key_id) <= 128, "INVALID_ROOT_ID")
    _deny_unless(type(publisher_root.minimum_manifest_serial) is int
                 and publisher_root.minimum_manifest_serial >= 1, "MISSING_ROLLBACK_FLOOR")
    _deny_unless(bool(_SERVICE.fullmatch(observed_service.service_name)), "INVALID_SERVICE_NAME")
    _deny_unless(bool(_SID.fullmatch(observed_service.service_sid)), "INVALID_SERVICE_SID")
    _deny_unless(bool(_VERSION.fullmatch(observed_service.service_version)), "INVALID_SERVICE_VERSION")
    _deny_unless(type(observed_service.installation_id) is str
                 and bool(_INSTALL_ID.fullmatch(observed_service.installation_id)), "INVALID_INSTALLATION_ID")
    _deny_unless(type(observed_service.ticket_issuer_key_id) is str
                 and 0 < len(observed_service.ticket_issuer_key_id) <= 128, "INVALID_TICKET_ISSUER")
    _deny_unless(_hash_ok(observed_service.ticket_issuer_fingerprint_sha256), "INVALID_TICKET_ISSUER_PIN")
    _deny_unless(type(observed_service.policy_version) is int
                 and observed_service.policy_version >= 1, "INVALID_POLICY")
    try:
        envelope = json.loads(envelope_bytes.decode("utf-8", errors="strict"),
                              object_pairs_hook=_unique_pairs,
                              parse_constant=lambda _: (_ for _ in ()).throw(
                                  SyntheticInstallationDenied("INVALID_JSON_CONSTANT")))
    except (UnicodeError, ValueError, RecursionError, TypeError) as exc:
        raise SyntheticInstallationDenied("INVALID_MANIFEST_JSON") from exc
    _deny_unless(type(envelope) is dict
                 and set(envelope) == {"body", "signature"}, "INVALID_ENVELOPE_SHAPE")
    _deny_unless(hmac.compare_digest(envelope_bytes, _canonical(envelope)),
                 "NONCANONICAL_MANIFEST")
    body = envelope["body"]
    signature_text = envelope["signature"]
    _deny_unless(type(body) is dict and set(body) == _FIELDS, "INVALID_MANIFEST_FIELDS")
    _deny_unless(type(signature_text) is str and
                 bool(re.fullmatch(r"[A-Za-z0-9_-]{86}", signature_text)),
                 "INVALID_MANIFEST_SIGNATURE")
    try:
        signature = base64.urlsafe_b64decode(signature_text + "==")
        _deny_unless(len(signature) == 64 and
                     base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
                     == signature_text, "INVALID_MANIFEST_SIGNATURE")
        Ed25519PublicKey.from_public_bytes(publisher_root.public_key_raw).verify(
            signature, _DOMAIN + _canonical(body))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise SyntheticInstallationDenied("INVALID_PUBLISHER_SIGNATURE") from exc

    digest = _measured_binary_digest(observed_service.executable_path)
    expected = {
        "schema_version": 1, "publisher": "Digital Crown",
        "publisher_root_id": publisher_root.key_id,
        "service_name": observed_service.service_name,
        "service_sid": observed_service.service_sid,
        "service_version": observed_service.service_version,
        "executable_sha256": digest,
        "installation_id": observed_service.installation_id,
        "ipc_audience": _ALLOWED_AUDIENCE,
        "authorized_operation": "SYNTHETIC_NOOP",
        "ticket_issuer_key_id": observed_service.ticket_issuer_key_id,
        "ticket_issuer_fingerprint_sha256": observed_service.ticket_issuer_fingerprint_sha256,
        "policy_version": observed_service.policy_version,
    }
    for key, value in expected.items():
        _deny_unless(type(body[key]) is type(value) and body[key] == value,
                     "MANIFEST_BINDING_" + key.upper())
    _deny_unless(type(body["manifest_serial"]) is int and
                 body["manifest_serial"] >= publisher_root.minimum_manifest_serial,
                 "MANIFEST_SERIAL_ROLLBACK")
    _deny_unless(type(body["not_before"]) is int and
                 type(body["expires_at"]) is int and
                 body["not_before"] <= now_epoch < body["expires_at"] <=
                 body["not_before"] + _MAX_MANIFEST_AGE, "INVALID_MANIFEST_TIME")
    return SyntheticInstallationReceipt(
        manifest_sha256=hashlib.sha256(envelope_bytes).hexdigest(),
        service_sid=observed_service.service_sid,
        executable_sha256=digest,
    )
