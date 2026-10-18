"""LOT05.7-H -- DORMANT, FAKE-ONLY authority-bound recovery rehearsal.

Neither the API nor GuidedRestoreWorker imports this module.  It issues an
ephemeral test capability across a SYNTHETIC request/job/worker boundary; this
is not a trusted identity origin, not an SCM proof and not a clinical token.
It never writes to a cabinet, applies restore, or publishes any files.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
from pathlib import Path

from backend.services.legacy_migration_gateway_v15 import (
    MigrationPreflightRefused,
    require_cabinet_owner,
)
from backend.services.legacy_migration_restore_policy_v15 import (
    RestoreContractDenied,
    evaluate_tenant_snapshot_read_only,
)


class AuthorityHandoffDenied(PermissionError):
    """Safe diagnostic code only, never patient data or raw job contents."""


FAKE_FLAG = "LOT05H_SYNTHETIC_ONLY"
NAMES = ("database.db", "license_fake.bin", "media-fake/image.fake",
         "media-fake/receipt.fake")
_JOB = re.compile(r"fakejob_[a-f0-9]{16}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_TTL = 300


def _require_fake():
    if os.environ.get(FAKE_FLAG) != "1":
        raise AuthorityHandoffDenied("FAKE_ONLY_DISABLED")


def _digest(path: Path) -> tuple[int, str]:
    h = hashlib.sha256()
    count = 0
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            count += len(block)
            if count > 128 * 1024 * 1024:
                raise AuthorityHandoffDenied("FAKE_COMPONENT_OVERSIZE")
            h.update(block)
    if not count:
        raise AuthorityHandoffDenied("FAKE_COMPONENT_EMPTY")
    return count, h.hexdigest()


def _location(root: Path):
    _require_fake()
    if (not isinstance(root, Path) or not root.is_absolute()
            or not root.name.startswith("lot05e_fake_sqlcipher_")
            or root.is_symlink() or not root.is_dir()):
        raise AuthorityHandoffDenied("FAKE_ROOT_REQUIRED")
    # This is not a Windows directory-handle ACL/reparse proof.
    return root.resolve(strict=True)


def _files(root: Path):
    base = _location(root)
    media = root / "media-fake"
    if (not media.is_dir() or media.is_symlink()
            or media.resolve(strict=True).parent != base):
        raise AuthorityHandoffDenied("FAKE_MEDIA_DIRECTORY_REQUIRED")
    all_files = set()
    for p in root.rglob("*"):
        if p.is_symlink() or (p.is_dir() and p != root / "media-fake"):
            raise AuthorityHandoffDenied("UNEXPECTED_OR_LINKED_COMPONENT")
        if p.is_file():
            if p.resolve(strict=True).parent not in (base, (root / "media-fake").resolve(strict=True)):
                raise AuthorityHandoffDenied("COMPONENT_PARENT_REDIRECTED")
            all_files.add(p.relative_to(root).as_posix())
    if all_files != set(NAMES):
        raise AuthorityHandoffDenied("FAKE_COMPONENT_SET_MISMATCH")
    return [(name, root / name) for name in NAMES]


def fake_manifest(root: Path) -> dict:
    """Hash EXACTLY the four allowed fake components; no patient files."""
    components = []
    for name, path in _files(root):
        size, sha = _digest(path)
        components.append({"name": name, "size": size, "sha256": sha})
    return {"v": 1, "type": "LOT05H_FAKE_COMPONENT_MANIFEST", "components": components}


def fake_manifest_sha(manifest: dict) -> str:
    if not isinstance(manifest, dict):
        raise AuthorityHandoffDenied("MANIFEST_MALFORMED")
    return hashlib.sha256(json.dumps(
        manifest, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def verify_fake_manifest(root: Path, expected: dict) -> str:
    _require_fake()
    if not isinstance(expected, dict) or set(expected) != {"v", "type", "components"}:
        raise AuthorityHandoffDenied("MANIFEST_MALFORMED")
    observed = fake_manifest(root)
    if not hmac.compare_digest(fake_manifest_sha(observed), fake_manifest_sha(expected)):
        raise AuthorityHandoffDenied("MULTICOMPONENT_INTEGRITY_DENIED")
    return fake_manifest_sha(observed)


def _key(key: bytes):
    if type(key) is not bytes or len(key) != 32:
        raise AuthorityHandoffDenied("EPHEMERAL_TEST_SIGNING_KEY_REQUIRED")


def _encode(data: dict):
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fake_issue_request_ticket(connection, principal, *, expected_owners: tuple[int, ...],
                              job_id: str, manifest_sha: str, now: int,
                              signing_key: bytes) -> dict:
    """Request-side rehearsal; real owner helper and DB scan, NO auth origin.

    A real integration must obtain principal from require_permission/settings
    + workstation gate; providing a Python user object is not authentication.
    """
    _require_fake()
    _key(signing_key)
    if not isinstance(job_id, str) or not _JOB.fullmatch(job_id):
        raise AuthorityHandoffDenied("FAKE_JOB_ID_REQUIRED")
    if not isinstance(manifest_sha, str) or not _SHA.fullmatch(manifest_sha):
        raise AuthorityHandoffDenied("MANIFEST_SHA_REQUIRED")
    if type(now) is not int or now <= 0:
        raise AuthorityHandoffDenied("FAKE_CLOCK_REQUIRED")
    try:
        owner = require_cabinet_owner(principal)  # actual Digital Crown helper
        observation = evaluate_tenant_snapshot_read_only(
            connection, principal, expected_owners=expected_owners)
    except (MigrationPreflightRefused, RestoreContractDenied) as exc:
        raise AuthorityHandoffDenied("REQUEST_OWNER_OR_TENANT_DENIED") from exc
    if observation.get("clinical_restore_permitted") is not False:
        raise AuthorityHandoffDenied("CLINICAL_PERMISSION_FALSE_REQUIRED")
    claims = {
        "v": 1, "purpose": "LOT05H_SYNTHETIC_HANDOFF_ONLY", "owner": owner,
        "job": job_id, "manifest": manifest_sha, "issued": now,
        "expires": now + _TTL, "nonce": secrets.token_hex(16),
    }
    return {"claims": claims,
            "mac": hmac.new(signing_key, _encode(claims), hashlib.sha256).hexdigest()}


def fake_worker_verify_ticket(ticket: dict, job: dict, *,
                              expected_owner: int, manifest_sha: str,
                              now: int, signing_key: bytes, used_nonces: set) -> dict:
    """Separate fake worker boundary: validate ALL claims before consuming.

    Does not call GuidedRestoreWorker.run(), spawn SCM, touch target or import.
    """
    _require_fake()
    _key(signing_key)
    if (type(expected_owner) is not int or expected_owner <= 0
            or type(now) is not int or now <= 0
            or not isinstance(manifest_sha, str)
            or not _SHA.fullmatch(manifest_sha)
            or not isinstance(used_nonces, set)):
        raise AuthorityHandoffDenied("WORKER_BOUNDARY_INVALID")
    if not isinstance(ticket, dict) or set(ticket) != {"claims", "mac"}:
        raise AuthorityHandoffDenied("TICKET_MALFORMED")
    claims, mac = ticket["claims"], ticket["mac"]
    if not isinstance(claims, dict) or set(claims) != {
        "v", "purpose", "owner", "job", "manifest", "issued", "expires", "nonce"
    } or not isinstance(mac, str) or not _SHA.fullmatch(mac):
        raise AuthorityHandoffDenied("TICKET_MALFORMED")
    expected_mac = hmac.new(signing_key, _encode(claims), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_mac, mac):
        raise AuthorityHandoffDenied("TICKET_SIGNATURE_DENIED")
    if (claims["v"] != 1 or claims["purpose"] != "LOT05H_SYNTHETIC_HANDOFF_ONLY"
            or type(claims["owner"]) is not int
            or claims["owner"] != expected_owner
            or not isinstance(claims["job"], str) or not _JOB.fullmatch(claims["job"])
            or claims["manifest"] != manifest_sha
            or type(claims["issued"]) is not int or type(claims["expires"]) is not int
            or claims["expires"] - claims["issued"] != _TTL
            or now < claims["issued"] or now >= claims["expires"]
            or not isinstance(claims["nonce"], str)
            or not re.fullmatch(r"[0-9a-f]{32}", claims["nonce"])):
        raise AuthorityHandoffDenied("SIGNED_CLAIMS_OUT_OF_SCOPE")
    if not isinstance(job, dict) or set(job) != {
        "job_id", "owner_employer_id", "manifest_sha256", "state"
    }:
        raise AuthorityHandoffDenied("JOB_ATTESTATION_MISSING")
    if (type(job["owner_employer_id"]) is not int
            or job["owner_employer_id"] != expected_owner
            or job["job_id"] != claims["job"]
            or job["manifest_sha256"] != manifest_sha
            or job["state"] != "prepared_fake"):
        raise AuthorityHandoffDenied("JOB_OWNER_OR_CONTENT_MISMATCH")
    if claims["nonce"] in used_nonces:
        raise AuthorityHandoffDenied("REPLAY_DENIED")
    used_nonces.add(claims["nonce"])
    return {"fake_handoff_verified": True, "clinical_restore_permitted": False,
            "clinical_import_permitted": False}
