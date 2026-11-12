"""LOT08.3-B2-F: immutable synthetic custody handoff; NOT physical certification.

Only copies authenticated encrypted Queue backups and a password-sealed B2-E
kit into a fresh, independently named LAB directory. The descriptor digest is
RETURNED, NEVER trusted from the bundle alone. An external trusted latest
digest is a mandatory restore input. Filesystem directories on a single host
do NOT establish independent media, escrow, rollback resistance if all stores
are rolled back, human custody, durable fsync of directories, or RPO/RTO.
No patient source, clinical restore, installer or production entry point.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import hmac
import json
import os
import re
import shutil
import tempfile
from uuid import uuid4

from queue_core.service.backup_restore_clone_08_3_b2_lab import (
    RestoreCloneLabError, _now_epoch,
)
from queue_core.service.backup_rotation_08_3_b2c_lab import (
    _ARCHIVE_RE, _DIGEST_RE, _MAX_ARCHIVE_BYTES, _canonical,
    _vault_folder,
)
from queue_core.service.recovery_kit_08_3_b2e_lab import (
    _KIT_FILE, _MAX_KIT_SIZE, _current_catalog, _kit_folder, _kit_path,
    _read_sealed, restore_queue_clone_from_kit_lab,
)

_ROOT_PREFIX = "lot08_3_b_lab_custody_"
_BUNDLE_RE = re.compile(r"lot08_3_b_lab_export_([1-9][0-9]*)_([a-f0-9]{32})")
_VAULT_NAME = "lot08_3_b_lab_vault_handoff"
_KIT_NAME = "lot08_3_b_lab_kit_handoff"
_DESCRIPTOR = "custody-descriptor.json"
_MAX_DESCRIPTOR = 8192
_ZERO = "0" * 64


@dataclass(frozen=True, slots=True)
class LabCustodyReceipt:
    bundle: Path
    external_fingerprint: str
    kit_witness: str
    generation: int


def _before_bundle_publish_lab() -> None:
    """Fault injection between fully verified copy and final rename."""


def _root_folder(path: str | Path, vault: Path | None = None,
                 kit: Path | None = None) -> Path:
    try:
        original = Path(path)
        root = original.resolve(strict=True)
        temp = Path(tempfile.gettempdir()).resolve()
    except (OSError, TypeError, ValueError):
        raise RestoreCloneLabError("CUSTODY_SYNTHETIC_ROOT_REQUIRED") from None
    if (original.is_symlink() or not root.is_dir()
        or not root.is_relative_to(temp) or root.parent == temp
        or not root.name.startswith(_ROOT_PREFIX)
        or (vault is not None and (
            root == vault or root.is_relative_to(vault)
            or vault.is_relative_to(root)))
        or (kit is not None and (
            root == kit or root.is_relative_to(kit)
            or kit.is_relative_to(root)))):
        raise RestoreCloneLabError("CUSTODY_SYNTHETIC_ROOT_REQUIRED")
    return root


def _bundle_folder(path: str | Path) -> Path:
    try:
        original = Path(path)
        bundle = original.resolve(strict=True)
        root = _root_folder(original.parent)
    except (OSError, TypeError, ValueError):
        raise RestoreCloneLabError("CUSTODY_BUNDLE_INVALID") from None
    if (original.is_symlink() or bundle.parent != root or not bundle.is_dir()
        or _BUNDLE_RE.fullmatch(bundle.name) is None):
        raise RestoreCloneLabError("CUSTODY_BUNDLE_INVALID")
    return bundle


def _digest(value: str, *, error: str) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise RestoreCloneLabError(error)
    return value


def _names(folder: Path) -> set[str]:
    try:
        paths = list(folder.iterdir())
        if any(p.is_symlink() for p in paths):
            raise RestoreCloneLabError("CUSTODY_UNSAFE_SOURCE")
        return {p.name for p in paths}
    except OSError:
        raise RestoreCloneLabError("CUSTODY_UNSAFE_SOURCE") from None


def _copy_verified(source: Path, target: Path, *, max_bytes: int,
                   expected_sha: str | None = None) -> str:
    try:
        if (source.is_symlink() or not source.is_file()
            or not 0 < source.stat().st_size <= max_bytes
            or target.exists() or target.is_symlink()):
            raise RestoreCloneLabError("CUSTODY_FILE_INVALID")
        blob = source.read_bytes()
        if not 0 < len(blob) <= max_bytes:
            raise RestoreCloneLabError("CUSTODY_FILE_INVALID")
        digest = sha256(blob).hexdigest()
        if expected_sha is not None and not hmac.compare_digest(digest, expected_sha):
            raise RestoreCloneLabError("CUSTODY_SOURCE_CHANGED")
        with target.open("xb") as stream:
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        if sha256(target.read_bytes()).hexdigest() != digest:
            raise RestoreCloneLabError("CUSTODY_COPY_INVALID")
        return digest
    except RestoreCloneLabError:
        raise
    except (OSError, ValueError, TypeError):
        raise RestoreCloneLabError("CUSTODY_COPY_INVALID") from None


def prepare_custody_bundle_lab(
    vault: str | Path, kit_directory: str | Path, custody_root: str | Path,
    *, passphrase: bytes, kit_witness: str, now: datetime,
    previous_external_fingerprint: str | None = None,
) -> LabCustodyReceipt:
    """Stage and verify an immutable encrypted copy; return digest OUT OF BAND.

    The caller MUST have an independent custodian persist the returned latest
    external_fingerprint before trusting or restoring the new bundle. Preparing
    the package is NOT an acknowledgement of physical custody. No fallback to
    older generations is decided by this function.
    """
    epoch = _now_epoch(now)
    src_vault = _vault_folder(vault)
    src_kit = _kit_folder(kit_directory, src_vault)
    root = _root_folder(custody_root, src_vault, src_kit)
    kit_witness = _digest(kit_witness, error="CUSTODY_KIT_WITNESS_REQUIRED")
    predecessor = (_ZERO if previous_external_fingerprint is None
                   else _digest(previous_external_fingerprint,
                                error="CUSTODY_PREDECESSOR_INVALID"))
    sealed = _read_sealed(_kit_path(src_kit, exists=True),
                          passphrase=passphrase, expected_fingerprint=kit_witness)
    catalog = _current_catalog(
        src_vault, sealed["backup_key"], sealed["manifest_key"],
        sealed["anchor"], epoch,
    )
    generation = catalog["generation"]
    if generation != sealed["generation"] or catalog["latest_epoch"] != sealed["latest_epoch"]:
        raise RestoreCloneLabError("CUSTODY_GENERATION_MISMATCH")
    entries = sorted(catalog["entries"], key=lambda item: item["name"])
    expected_vault = {"manifest.json"} | {item["name"] for item in entries}
    if (_names(src_vault) != expected_vault
        or _names(src_kit) != {_KIT_FILE}):
        raise RestoreCloneLabError("CUSTODY_UNSAFE_SOURCE")
    token = uuid4().hex
    staging = root / (".lot08_3_b_lab_pending_" + token)
    final = root / f"lot08_3_b_lab_export_{generation}_{token}"
    if final.exists() or final.is_symlink():
        raise RestoreCloneLabError("CUSTODY_BUNDLE_COLLISION")
    staging.mkdir(mode=0o700)
    try:
        out_vault = staging / _VAULT_NAME
        out_kit = staging / _KIT_NAME
        out_vault.mkdir(mode=0o700)
        out_kit.mkdir(mode=0o700)
        kit_hash = _copy_verified(src_kit / _KIT_FILE, out_kit / _KIT_FILE,
                                  max_bytes=_MAX_KIT_SIZE,
                                  expected_sha=kit_witness)
        manifest_hash = _copy_verified(src_vault / "manifest.json",
                                       out_vault / "manifest.json",
                                       max_bytes=64 * 1024)
        archive_hashes = []
        for entry in entries:
            name = entry["name"]
            if _ARCHIVE_RE.fullmatch(name) is None:
                raise RestoreCloneLabError("CUSTODY_ARCHIVE_INVALID")
            digest = _copy_verified(src_vault / name, out_vault / name,
                                    max_bytes=_MAX_ARCHIVE_BYTES,
                                    expected_sha=entry["sha256"])
            archive_hashes.append({"name": name, "sha256": digest})
        copied_sealed = _read_sealed(_kit_path(out_kit, exists=True),
                                     passphrase=passphrase,
                                     expected_fingerprint=kit_hash)
        copied_catalog = _current_catalog(
            out_vault, copied_sealed["backup_key"], copied_sealed["manifest_key"],
            copied_sealed["anchor"], epoch,
        )
        same_source_catalog = _current_catalog(
            src_vault, sealed["backup_key"], sealed["manifest_key"],
            sealed["anchor"], epoch,
        )
        if (copied_sealed != sealed or copied_catalog != catalog
            or same_source_catalog != catalog):
            raise RestoreCloneLabError("CUSTODY_SOURCE_CHANGED")
        descriptor = {
            "version": 1, "generation": generation,
            "latest_epoch": catalog["latest_epoch"],
            "predecessor": predecessor,
            "kit_sha256": kit_hash,
            "manifest_sha256": manifest_hash,
            "archives": archive_hashes,
        }
        content = _canonical(descriptor)
        if len(content) > _MAX_DESCRIPTOR:
            raise RestoreCloneLabError("CUSTODY_DESCRIPTOR_INVALID")
        _copy_contents(content, staging / _DESCRIPTOR)
        _before_bundle_publish_lab()
        os.rename(staging, final)
        return LabCustodyReceipt(
            bundle=final, external_fingerprint=sha256(content).hexdigest(),
            kit_witness=kit_hash, generation=generation,
        )
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _copy_contents(blob: bytes, target: Path) -> None:
    try:
        with target.open("xb") as stream:
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
    except (OSError, ValueError):
        raise RestoreCloneLabError("CUSTODY_COPY_INVALID") from None


def restore_custody_bundle_lab(
    bundle: str | Path, destination: str | Path, *,
    external_fingerprint: str, passphrase: bytes,
    slot: str, bucket: str, now: datetime,
) -> str:
    """Restore only a NEW synthetic clone against externally trusted latest SHA."""
    external_fingerprint = _digest(
        external_fingerprint, error="CUSTODY_EXTERNAL_WITNESS_REQUIRED",
    )
    location = _bundle_folder(bundle)
    out_vault, out_kit = location / _VAULT_NAME, location / _KIT_NAME
    if (_names(location) != {_VAULT_NAME, _KIT_NAME, _DESCRIPTOR}
        or out_vault.is_symlink() or not out_vault.is_dir()
        or out_kit.is_symlink() or not out_kit.is_dir()):
        raise RestoreCloneLabError("CUSTODY_BUNDLE_INVALID")
    descriptor_file = location / _DESCRIPTOR
    if (descriptor_file.is_symlink() or not descriptor_file.is_file()
        or not 0 < descriptor_file.stat().st_size <= _MAX_DESCRIPTOR):
        raise RestoreCloneLabError("CUSTODY_DESCRIPTOR_INVALID")
    raw = descriptor_file.read_bytes()
    if not hmac.compare_digest(sha256(raw).hexdigest(), external_fingerprint):
        raise RestoreCloneLabError("CUSTODY_EXTERNAL_WITNESS_MISMATCH")
    try:
        meta = json.loads(raw)
        if (type(meta) is not dict or set(meta) != {
            "version", "generation", "latest_epoch", "predecessor",
            "kit_sha256", "manifest_sha256", "archives",
        } or meta["version"] != 1 or _canonical(meta) != raw
            or type(meta["generation"]) is not int or meta["generation"] < 1
            or type(meta["latest_epoch"]) is not int or meta["latest_epoch"] < 0
            or type(meta["archives"]) is not list
            or not 1 <= len(meta["archives"]) <= 11):
            raise ValueError("descriptor")
        for field in ("predecessor", "kit_sha256", "manifest_sha256"):
            _digest(meta[field], error="CUSTODY_DESCRIPTOR_INVALID")
        match = _BUNDLE_RE.fullmatch(location.name)
        if match is None or int(match[1]) != meta["generation"]:
            raise ValueError("generation")
        names = []
        for item in meta["archives"]:
            if (type(item) is not dict or set(item) != {"name", "sha256"}
                or type(item["name"]) is not str
                or _ARCHIVE_RE.fullmatch(item["name"]) is None):
                raise ValueError("archive")
            _digest(item["sha256"], error="CUSTODY_DESCRIPTOR_INVALID")
            names.append(item["name"])
        if names != sorted(set(names)):
            raise ValueError("archive order")
    except (TypeError, ValueError, KeyError, UnicodeError):
        raise RestoreCloneLabError("CUSTODY_DESCRIPTOR_INVALID") from None
    if (_names(out_vault) != {"manifest.json"} | set(names)
        or _names(out_kit) != {_KIT_FILE}):
        raise RestoreCloneLabError("CUSTODY_BUNDLE_INVALID")
    _verify_copy(out_kit / _KIT_FILE, meta["kit_sha256"], _MAX_KIT_SIZE)
    _verify_copy(out_vault / "manifest.json",
                 meta["manifest_sha256"], 64 * 1024)
    for item in meta["archives"]:
        _verify_copy(out_vault / item["name"], item["sha256"],
                     _MAX_ARCHIVE_BYTES)
    payload = _read_sealed(_kit_path(out_kit, exists=True),
                           passphrase=passphrase,
                           expected_fingerprint=meta["kit_sha256"])
    catalog = _current_catalog(
        out_vault, payload["backup_key"], payload["manifest_key"],
        payload["anchor"], _now_epoch(now),
    )
    if (catalog["generation"] != meta["generation"]
        or catalog["latest_epoch"] != meta["latest_epoch"]):
        raise RestoreCloneLabError("CUSTODY_GENERATION_MISMATCH")
    if Path(destination).resolve(strict=False).is_relative_to(location):
        raise RestoreCloneLabError("CUSTODY_CLONE_INSIDE_BUNDLE_DENIED")
    return restore_queue_clone_from_kit_lab(
        out_vault, out_kit, destination, passphrase=passphrase,
        expected_witness=meta["kit_sha256"],
        slot=slot, bucket=bucket, now=now,
    )


def _verify_copy(path: Path, expected: str, bound: int) -> None:
    if (path.is_symlink() or not path.is_file()
        or not 0 < path.stat().st_size <= bound):
        raise RestoreCloneLabError("CUSTODY_BUNDLE_INVALID")
    if not hmac.compare_digest(sha256(path.read_bytes()).hexdigest(), expected):
        raise RestoreCloneLabError("CUSTODY_BUNDLE_TAMPERED")
