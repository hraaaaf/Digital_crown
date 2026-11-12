"""LOT08.3-B2-C: authenticated 7-daily / 4-weekly backup rotation (LAB ONLY).

Not a production scheduler, key vault, restore manager or physical offsite
backup. An HMAC catalog is meaningful ONLY when the caller safeguards the
latest trusted anchor and independent manifest key OUTSIDE this backup folder.
An OS administrator with all keys and the anchor can defeat this simulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import hmac
import json
import os
import re
import tempfile
from uuid import uuid4

from queue_core.service.backup_restore_clone_08_3_b2_lab import (
    RestoreCloneLabError, _fernet, _now_epoch, restore_queue_clone_lab,
    seal_queue_snapshot_lab,
)
from queue_core.service.retention_lab_08_3_b import _verify_lab_file, RetentionLabError

_DAILY_KEEP = 7
_WEEKLY_KEEP = 4
_MAX_MANIFEST_BYTES = 64 * 1024
_MAX_ARCHIVE_BYTES = 8 * 1024 * 1024
_ENTRY_KEYS = frozenset({"slot", "bucket", "name", "sha256", "epoch"})
_PAYLOAD_KEYS = frozenset({"version", "generation", "latest_epoch", "entries"})
_ARCHIVE_RE = re.compile(
    r"lot08_3_b_lab_backup_(daily_[0-9]{8}|weekly_[0-9]{4}W[0-9]{2})_[a-f0-9]{24}\.fernet"
)
_DIGEST_RE = re.compile(r"[a-f0-9]{64}")


@dataclass(frozen=True, slots=True)
class LabVaultStatus:
    anchor: str
    generation: int
    daily: int
    weekly: int
    created: int
    removed: int


def _before_catalog_publish_lab() -> None:
    """Crash-injection oracle. No production use."""


def _vault_folder(value: str | Path) -> Path:
    try:
        source = Path(value)
        resolved = source.resolve(strict=True)
        temp = Path(tempfile.gettempdir()).resolve()
    except (OSError, ValueError, TypeError):
        raise RestoreCloneLabError("ROTATION_LAB_VAULT_REQUIRED") from None
    if (source.is_symlink() or not resolved.is_dir()
        or not resolved.is_relative_to(temp)
        or resolved.parent == temp
        or not resolved.name.startswith("lot08_3_b_lab_vault_")):
        raise RestoreCloneLabError("ROTATION_LAB_VAULT_REQUIRED")
    return resolved


def _keys(backup_key: bytes, manifest_key: bytes) -> None:
    _fernet(backup_key)
    if (not isinstance(manifest_key, bytes)
        or len(manifest_key) != 32
        or manifest_key == backup_key):
        raise RestoreCloneLabError("SEPARATE_MANIFEST_KEY_REQUIRED")


def _canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _mac(key: bytes, payload: dict) -> str:
    return hmac.digest(key, _canonical(payload), "sha256").hex()


def _bucket(epoch: int, slot: str) -> str:
    when = datetime.fromtimestamp(epoch, timezone.utc)
    if slot == "daily":
        return when.strftime("%Y-%m-%d")
    year, week, _ = when.isocalendar()
    return f"{year}-W{week:02d}"


def _new_filename(slot: str, bucket: str) -> str:
    stub = bucket.replace("-", "")
    return f"lot08_3_b_lab_backup_{slot}_{stub}_{uuid4().hex[:24]}.fernet"


def _safe_archive(vault: Path, name: str, *, exists: bool) -> Path:
    if (not isinstance(name, str) or _ARCHIVE_RE.fullmatch(name) is None):
        raise RestoreCloneLabError("ROTATION_ARCHIVE_NAME_INVALID")
    path = vault / name
    if path.is_symlink() or (path.exists() != exists) or (exists and not path.is_file()):
        raise RestoreCloneLabError("ROTATION_ARCHIVE_STATE_INVALID")
    return path


def _read_catalog(
    vault: Path, key: bytes, trusted_anchor: str | None, epoch: int,
) -> dict:
    manifest = vault / "manifest.json"
    if manifest.is_symlink():
        raise RestoreCloneLabError("ROTATION_MANIFEST_INVALID")
    if not manifest.exists():
        if trusted_anchor is not None or any(vault.glob("*.fernet")):
            raise RestoreCloneLabError("ROTATION_ANCHOR_REQUIRED")
        return {"version": 1, "generation": 0, "latest_epoch": -1, "entries": []}
    if (trusted_anchor is None or not isinstance(trusted_anchor, str)
        or _DIGEST_RE.fullmatch(trusted_anchor) is None):
        raise RestoreCloneLabError("ROTATION_ANCHOR_REQUIRED")
    if not manifest.is_file() or manifest.stat().st_size > _MAX_MANIFEST_BYTES:
        raise RestoreCloneLabError("ROTATION_MANIFEST_INVALID")
    try:
        parsed = json.loads(manifest.read_text(encoding="utf-8"))
        if type(parsed) is not dict or set(parsed) != {"payload", "mac"}:
            raise ValueError("outer")
        payload, tag = parsed["payload"], parsed["mac"]
        if type(payload) is not dict or set(payload) != _PAYLOAD_KEYS:
            raise ValueError("payload")
        expected = _mac(key, payload)
        if (type(tag) is not str or not hmac.compare_digest(tag, expected)
            or not hmac.compare_digest(trusted_anchor, tag)):
            raise RestoreCloneLabError("ROTATION_ANCHOR_MISMATCH")
        if (payload["version"] != 1
            or type(payload["generation"]) is not int or payload["generation"] < 1
            or type(payload["latest_epoch"]) is not int
            or payload["latest_epoch"] > epoch
            or type(payload["entries"]) is not list
            or not 1 <= len(payload["entries"]) <= 11):
            raise ValueError("catalog")
        seen, names = set(), set()
        counts = {"daily": 0, "weekly": 0}
        for entry in payload["entries"]:
            if type(entry) is not dict or set(entry) != _ENTRY_KEYS:
                raise ValueError("entry")
            slot, bucket, name, digest, created = (
                entry["slot"], entry["bucket"], entry["name"], entry["sha256"], entry["epoch"]
            )
            if (slot not in counts or type(created) is not int or created > epoch
                or created < 0 or type(bucket) is not str
                or bucket != _bucket(created, slot)
                or type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None
                or type(name) is not str or _ARCHIVE_RE.fullmatch(name) is None
                or not name.startswith("lot08_3_b_lab_backup_" + slot + "_" + bucket.replace("-", "") + "_")
                or (slot, bucket) in seen or name in names):
                raise ValueError("entryfields")
            seen.add((slot, bucket))
            names.add(name)
            counts[slot] += 1
            archive = _safe_archive(vault, name, exists=True)
            if archive.stat().st_size > _MAX_ARCHIVE_BYTES:
                raise ValueError("size")
            if sha256(archive.read_bytes()).hexdigest() != digest:
                raise RestoreCloneLabError("ROTATION_ARCHIVE_TAMPERED")
        if (counts["daily"] > _DAILY_KEEP or counts["weekly"] > _WEEKLY_KEEP
            or max(e["epoch"] for e in payload["entries"]) != payload["latest_epoch"]):
            raise ValueError("bounds")
        # An orphan archive is an interrupted transaction. Never conceal it.
        if {p.name for p in vault.glob("*.fernet")} != names:
            raise RestoreCloneLabError("ROTATION_ORPHAN_OR_MISSING_ARCHIVE")
        return payload
    except RestoreCloneLabError:
        raise
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        raise RestoreCloneLabError("ROTATION_MANIFEST_INVALID") from None


def _seal_verified(
    source: Path, vault: Path, name: str, backup_key: bytes, now: datetime,
) -> dict:
    archive = _safe_archive(vault, name, exists=False)
    try:
        seal_queue_snapshot_lab(source, archive, key=backup_key, now=now)
        # Verify the ACTUAL encrypted payload meets G3, not a prior stale
        # preflight snapshot. A disposable clone is outside the backup medium.
        trial = vault.parent / f"lot08_3_b_lab_restored_verify_{uuid4().hex}.sqlite"
        try:
            restore_queue_clone_lab(archive, trial, key=backup_key, now=now)
        finally:
            trial.unlink(missing_ok=True)
        return {"name": name, "sha256": sha256(archive.read_bytes()).hexdigest()}
    except BaseException:
        archive.unlink(missing_ok=True)
        raise


def rotate_queue_vault_lab(
    source: str | Path, vault: str | Path, *, backup_key: bytes,
    manifest_key: bytes, trusted_anchor: str | None, now: datetime,
) -> LabVaultStatus:
    """Add one UTC daily and optionally one ISO weekly archive; keep 7+4.

    Every write requires the current trusted anchor, independently held by the
    caller. The new anchor must be stored safely OUTSIDE the vault before
    trusting any future restore. A failure before manifest publication rolls
    back all newly created files. No archive can be restored via this API with
    a stale catalog/anchor. A manifest does not protect against full OS/key theft.
    """
    _keys(backup_key, manifest_key)
    stamp = _now_epoch(now)
    location = _vault_folder(vault)
    try:
        source_path = _verify_lab_file(source)
    except RetentionLabError as exc:
        raise RestoreCloneLabError(str(exc)) from None
    if source_path.is_relative_to(location):
        raise RestoreCloneLabError("ROTATION_SOURCE_IN_VAULT_DENIED")
    current = _read_catalog(location, manifest_key, trusted_anchor, stamp)
    if current["latest_epoch"] > stamp:
        raise RestoreCloneLabError("ROTATION_CLOCK_REGRESSION")
    daily, weekly = _bucket(stamp, "daily"), _bucket(stamp, "weekly")
    if any(e["slot"] == "daily" and e["bucket"] == daily for e in current["entries"]):
        raise RestoreCloneLabError("ROTATION_DAILY_ALREADY_PRESENT")
    slots = [("daily", daily)]
    if not any(e["slot"] == "weekly" and e["bucket"] == weekly for e in current["entries"]):
        slots.append(("weekly", weekly))
    new_files, new_entries = [], []
    published = False
    try:
        for slot, bucket in slots:
            name = _new_filename(slot, bucket)
            seal = _seal_verified(source_path, location, name, backup_key, now)
            new_files.append(name)
            new_entries.append({
                "slot": slot, "bucket": bucket, "epoch": stamp,
                "name": name, "sha256": seal["sha256"],
            })
        all_entries = current["entries"] + new_entries
        # Calendar windows, NOT the last N snapshots: a vault left idle
        # must not carry a 40-day-old daily archive into the next rotation.
        today = datetime.fromtimestamp(stamp, timezone.utc)
        permitted_daily = {
            _bucket(int((today - timedelta(days=offset)).timestamp()), "daily")
            for offset in range(_DAILY_KEEP)
        }
        permitted_weekly = {
            _bucket(int((today - timedelta(weeks=offset)).timestamp()), "weekly")
            for offset in range(_WEEKLY_KEEP)
        }
        selected = {
            e["name"] for e in all_entries
            if (e["slot"] == "daily" and e["bucket"] in permitted_daily)
            or (e["slot"] == "weekly" and e["bucket"] in permitted_weekly)
        }
        removed = [e for e in all_entries if e["name"] not in selected]
        kept = sorted((e for e in all_entries if e["name"] in selected),
                      key=lambda e: (e["slot"], e["bucket"], e["name"]))
        payload = {
            "version": 1, "generation": current["generation"] + 1,
            "latest_epoch": stamp, "entries": kept,
        }
        anchor = _mac(manifest_key, payload)
        encoded = _canonical({"payload": payload, "mac": anchor})
        if len(encoded) > _MAX_MANIFEST_BYTES:
            raise RestoreCloneLabError("ROTATION_MANIFEST_INVALID")
        stage = location / f".lot08_3_b_lab_manifest_{uuid4().hex}.tmp"
        try:
            with stage.open("xb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            _before_catalog_publish_lab()
            os.replace(stage, location / "manifest.json")
            published = True
        finally:
            stage.unlink(missing_ok=True)
        # Never discard previous backups before a verified new archive and
        # committed authenticated catalog. Old files are untrusted after prune.
        for e in removed:
            _safe_archive(location, e["name"], exists=True).unlink()
        return LabVaultStatus(
            anchor=anchor, generation=payload["generation"],
            daily=sum(e["slot"] == "daily" for e in kept),
            weekly=sum(e["slot"] == "weekly" for e in kept),
            created=len(new_entries), removed=len(removed),
        )
    except BaseException:
        if not published:
            for name in new_files:
                _safe_archive(location, name, exists=True).unlink()
        raise


def restore_queue_vault_clone_lab(
    vault: str | Path, destination: str | Path, *, backup_key: bytes,
    manifest_key: bytes, trusted_anchor: str, slot: str, bucket: str,
    now: datetime,
) -> str:
    """Restore only an archive in the latest externally-anchored catalog."""
    _keys(backup_key, manifest_key)
    stamp = _now_epoch(now)
    location = _vault_folder(vault)
    payload = _read_catalog(location, manifest_key, trusted_anchor, stamp)
    matching = [e for e in payload["entries"]
                if e["slot"] == slot and e["bucket"] == bucket]
    if len(matching) != 1:
        raise RestoreCloneLabError("ROTATION_ARCHIVE_NOT_AUTHORIZED")
    archive = _safe_archive(location, matching[0]["name"], exists=True)
    return restore_queue_clone_lab(archive, destination, key=backup_key, now=now)
