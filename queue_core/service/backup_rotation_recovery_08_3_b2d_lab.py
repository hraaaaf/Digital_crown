"""LOT08.3-B2-D: explicit signed recovery of interrupted Queue rotation, LAB only.

A journal does not certify physical power-loss durability or independent key
custody. The caller MUST provide its last separately trusted HMAC anchor.
Every archived file removed here is named by a verified HMAC journal, and
only after the previous or successor catalog is proven authentic.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import hmac
import json
import re

from queue_core.service.backup_restore_clone_08_3_b2_lab import (
    RestoreCloneLabError, _now_epoch,
)
from queue_core.service.backup_rotation_08_3_b2c_lab import (
    _DAILY_KEEP, _DIGEST_RE, _ENTRY_KEYS, _JOURNAL_NAME,
    _MAX_JOURNAL_BYTES, _WEEKLY_KEEP, _ARCHIVE_RE,
    _bucket, _calendar_windows, _canonical, _keys, _mac, _read_catalog,
    _safe_archive, _vault_folder,
)

_PLAN_KEYS = frozenset({
    "version", "prior_anchor", "next_anchor", "prior_generation",
    "prior_latest_epoch", "next_generation", "epoch", "created", "retired",
})


@dataclass(frozen=True, slots=True)
class RotationRecoveryLabResult:
    phase: str
    trusted_anchor: str | None
    generation: int
    removed: int


def _entries_valid(items: object, *, epoch: int) -> list[dict]:
    if type(items) is not list or len(items) > 11:
        raise RestoreCloneLabError("ROTATION_JOURNAL_INVALID")
    seen, slots = set(), set()
    result = []
    for e in items:
        if type(e) is not dict or set(e) != _ENTRY_KEYS:
            raise RestoreCloneLabError("ROTATION_JOURNAL_INVALID")
        try:
            slot, bucket, name, digest, created = (
                e["slot"], e["bucket"], e["name"], e["sha256"], e["epoch"]
            )
            if (type(slot) is not str or slot not in ("daily", "weekly")
                or type(bucket) is not str or type(name) is not str
                or type(digest) is not str or type(created) is not int
                or not 0 <= created <= epoch
                or bucket != _bucket(created, slot)
                or _DIGEST_RE.fullmatch(digest) is None
                or _ARCHIVE_RE.fullmatch(name) is None
                or not name.startswith(
                    "lot08_3_b_lab_backup_" + slot + "_" + bucket.replace("-", "") + "_"
                ) or name in seen or (slot, bucket) in slots):
                raise ValueError("invalid entry")
        except (ValueError, TypeError, KeyError, OverflowError, OSError):
            raise RestoreCloneLabError("ROTATION_JOURNAL_INVALID") from None
        seen.add(name)
        slots.add((slot, bucket))
        result.append(e)
    return result


def _signed_intent(vault: Path, signing_key: bytes, now_epoch: int) -> dict:
    journal = vault / _JOURNAL_NAME
    if (journal.is_symlink() or not journal.is_file()
        or journal.stat().st_size > _MAX_JOURNAL_BYTES):
        raise RestoreCloneLabError("ROTATION_RECOVERY_JOURNAL_REQUIRED")
    try:
        data = json.loads(journal.read_text(encoding="utf-8"))
        if type(data) is not dict or set(data) != {"plan", "mac"}:
            raise ValueError("outer")
        plan, tag = data["plan"], data["mac"]
        if type(plan) is not dict or set(plan) != _PLAN_KEYS:
            raise ValueError("plan")
        if (type(tag) is not str or _DIGEST_RE.fullmatch(tag) is None
            or not hmac.compare_digest(tag, _mac(signing_key, plan))):
            raise RestoreCloneLabError("ROTATION_RECOVERY_SIGNATURE_DENIED")
        old, new = plan["prior_anchor"], plan["next_anchor"]
        if (plan["version"] != 1 or type(plan["epoch"]) is not int
            or not 0 <= plan["epoch"] <= now_epoch
            or type(plan["prior_generation"]) is not int
            or not 0 <= plan["prior_generation"]
            or type(plan["next_generation"]) is not int
            or plan["next_generation"] != plan["prior_generation"] + 1
            or type(plan["prior_latest_epoch"]) is not int
            or not -1 <= plan["prior_latest_epoch"] <= plan["epoch"]
            or (old is not None and
                (type(old) is not str or _DIGEST_RE.fullmatch(old) is None))
            or type(new) is not str or _DIGEST_RE.fullmatch(new) is None
            or new == old
            or (plan["prior_generation"] == 0) != (old is None)
            or (plan["prior_generation"] == 0) != (plan["prior_latest_epoch"] == -1)):
            raise ValueError("header")
        created = _entries_valid(plan["created"], epoch=plan["epoch"])
        retired = _entries_valid(plan["retired"], epoch=plan["epoch"])
        if not 1 <= len(created) <= 2:
            raise ValueError("created")
        if {e["name"] for e in created} & {e["name"] for e in retired}:
            raise ValueError("overlap")
        return plan
    except RestoreCloneLabError:
        raise
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        raise RestoreCloneLabError("ROTATION_JOURNAL_INVALID") from None


def _current_manifest_tag(vault: Path) -> str | None:
    path = vault / "manifest.json"
    if path.is_symlink():
        raise RestoreCloneLabError("ROTATION_RECOVERY_MANIFEST_INVALID")
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > 64 * 1024:
        raise RestoreCloneLabError("ROTATION_RECOVERY_MANIFEST_INVALID")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if type(document) is not dict or set(document) != {"payload", "mac"}:
            raise ValueError("manifest")
        tag = document["mac"]
        if type(tag) is not str or _DIGEST_RE.fullmatch(tag) is None:
            raise ValueError("tag")
        return tag
    except (OSError, ValueError, UnicodeError, TypeError):
        raise RestoreCloneLabError("ROTATION_RECOVERY_MANIFEST_INVALID") from None


def _validate_plan_against_catalog(
    plan: dict, stage: str, catalog: dict, signing_key: bytes,
) -> None:
    """Reconstruct BOTH catalog generations before any file removal."""
    created, retired = plan["created"], plan["retired"]
    made = {e["name"]: e for e in created}
    dropped = {e["name"]: e for e in retired}
    if stage == "before":
        old_entries = catalog["entries"]
        if (catalog["generation"] != plan["prior_generation"]
            or catalog["latest_epoch"] != plan["prior_latest_epoch"]):
            raise RestoreCloneLabError("ROTATION_RECOVERY_GENERATION_DENIED")
    else:
        kept = {e["name"]: e for e in catalog["entries"]}
        if (catalog["generation"] != plan["next_generation"]
            or catalog["latest_epoch"] != plan["epoch"]
            or any(kept.get(name) != e for name, e in made.items())
            or any(name in kept for name in dropped)):
            raise RestoreCloneLabError("ROTATION_RECOVERY_GENERATION_DENIED")
        old_entries = [e for name,e in kept.items() if name not in made] + retired

    old_entries = sorted(old_entries, key=lambda e: (e["slot"],e["bucket"],e["name"]))
    previous = {
        "version": 1, "generation": plan["prior_generation"],
        "latest_epoch": plan["prior_latest_epoch"], "entries": old_entries,
    }
    if plan["prior_generation"] == 0:
        if old_entries or plan["prior_anchor"] is not None:
            raise RestoreCloneLabError("ROTATION_RECOVERY_CHAIN_DENIED")
    elif not hmac.compare_digest(_mac(signing_key, previous), plan["prior_anchor"]):
        raise RestoreCloneLabError("ROTATION_RECOVERY_CHAIN_DENIED")

    current_names = {e["name"]:e for e in old_entries}
    if (any(name in current_names for name in made)
        or any(current_names.get(name) != e for name,e in dropped.items())):
        raise RestoreCloneLabError("ROTATION_RECOVERY_CHAIN_DENIED")
    todays_daily = _bucket(plan["epoch"], "daily")
    todays_weekly = _bucket(plan["epoch"], "weekly")
    planned_slots = [("daily", todays_daily)]
    if not any(e["slot"] == "weekly" and e["bucket"] == todays_weekly
               for e in old_entries):
        planned_slots.append(("weekly", todays_weekly))
    if (any(e["slot"]=="daily" and e["bucket"]==todays_daily for e in old_entries)
        or {(e["slot"],e["bucket"]) for e in created} != set(planned_slots)
        or any(e["epoch"] != plan["epoch"] for e in created)):
        raise RestoreCloneLabError("ROTATION_RECOVERY_PLAN_DENIED")
    daily, weekly = _calendar_windows(plan["epoch"])
    all_entries = old_entries + created
    expected_kept = sorted([
        e for e in all_entries
        if (e["slot"] == "daily" and e["bucket"] in daily)
        or (e["slot"] == "weekly" and e["bucket"] in weekly)
    ], key=lambda e: (e["slot"],e["bucket"],e["name"]))
    expected_retired = sorted([
        e for e in all_entries if e not in expected_kept
    ], key=lambda e: (e["slot"],e["bucket"],e["name"]))
    if expected_retired != sorted(retired,key=lambda e: (e["slot"],e["bucket"],e["name"])):
        raise RestoreCloneLabError("ROTATION_RECOVERY_PLAN_DENIED")
    successor = {
        "version": 1, "generation": plan["next_generation"],
        "latest_epoch": plan["epoch"], "entries": expected_kept,
    }
    if not hmac.compare_digest(_mac(signing_key, successor), plan["next_anchor"]):
        raise RestoreCloneLabError("ROTATION_RECOVERY_CHAIN_DENIED")
    if stage == "after" and successor != catalog:
        raise RestoreCloneLabError("ROTATION_RECOVERY_GENERATION_DENIED")


def recover_queue_vault_rotation_lab(
    vault: str | Path, *, backup_key: bytes, manifest_key: bytes,
    trusted_anchor: str | None, now,
) -> RotationRecoveryLabResult:
    """Explicit recovery, with a caller-held independently trusted anchor.

    Before catalog commit: remove only signed *new* files, keep all old files.
    After commit: remove only signed *retired* files; return successor anchor
    for caller to persist independently. Missing already-removed files make
    recovery idempotent while the signed journal still exists. No orphan is
    silently adopted or removed without a matching signed entry and digest.
    """
    _keys(backup_key, manifest_key)
    stamp = _now_epoch(now)
    location = _vault_folder(vault)
    plan = _signed_intent(location, manifest_key, stamp)
    current_tag = _current_manifest_tag(location)
    if current_tag == plan["prior_anchor"]:
        phase = "before"
        if trusted_anchor != plan["prior_anchor"]:
            raise RestoreCloneLabError("ROTATION_RECOVERY_ANCHOR_DENIED")
        current_anchor = plan["prior_anchor"]
        allowed = frozenset(e["name"] for e in plan["created"])
    elif current_tag == plan["next_anchor"]:
        phase = "after"
        if trusted_anchor not in (plan["prior_anchor"], plan["next_anchor"]):
            raise RestoreCloneLabError("ROTATION_RECOVERY_ANCHOR_DENIED")
        current_anchor = plan["next_anchor"]
        allowed = frozenset(e["name"] for e in plan["retired"])
    else:
        raise RestoreCloneLabError("ROTATION_RECOVERY_MANIFEST_MISMATCH")

    verified_catalog = _read_catalog(
        location, manifest_key, current_anchor, stamp, backup_key=backup_key,
        recovery_mode=True, allowed_orphans=allowed,
    )
    _validate_plan_against_catalog(plan, phase, verified_catalog, manifest_key)
    candidates = plan["created"] if phase=="before" else plan["retired"]
    # Validate ALL present signed files, including sizes and digests,
    # before deleting the first one. Unknown or changed files fail closed.
    existing = []
    for e in candidates:
        candidate = location / e["name"]
        if candidate.exists() or candidate.is_symlink():
            archive = _safe_archive(location, e["name"], exists=True)
            if (archive.stat().st_size > 8 * 1024 * 1024
                or sha256(archive.read_bytes()).hexdigest() != e["sha256"]):
                raise RestoreCloneLabError("ROTATION_RECOVERY_ARCHIVE_TAMPERED")
            existing.append(archive)
    for archive in existing:
        archive.unlink()
    (location / _JOURNAL_NAME).unlink()
    return RotationRecoveryLabResult(
        phase="rolled_back" if phase=="before" else "committed",
        trusted_anchor=current_anchor,
        generation=plan["prior_generation"] if phase=="before"
                   else plan["next_generation"],
        removed=len(existing),
    )
