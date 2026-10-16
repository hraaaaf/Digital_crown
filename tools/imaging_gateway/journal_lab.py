"""LOT06-K: synthetic, in-memory HMAC-linked migration checkpoint journal.

Anti-rollback ONLY relative to an independently supplied, trusted monotonic
anchor. No durable I/O, clinical authorization, service, external trust anchor
implementation, filesystem or production collector integration.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import re

from . import migration_lab as migration

_ZERO_MAC = "0" * 64
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_RECORDS = 256
_DOMAIN = b"DC06K|journal-record|v1\0"


class JournalLabError(RuntimeError):
    """Never include keys, image content, scope or user identifiers in errors."""


@dataclass(frozen=True)
class Record:
    sequence: int
    previous_mac: str
    snapshot: migration.Snapshot
    mac: str


@dataclass(frozen=True)
class Journal:
    records: tuple[Record, ...]


@dataclass(frozen=True)
class TrustedAnchor:
    """Caller-owned external high-water mark (here: only a Python object)."""

    sequence: int
    mac: str


def _fail(code: str) -> None:
    raise JournalLabError(code)


def _keys(journal_key: bytes, legacy_key: bytes, keys: dict) -> None:
    if type(journal_key) is not bytes or len(journal_key) != 32:
        _fail("JOURNAL_KEY_INVALID")
    if type(legacy_key) is not bytes or len(legacy_key) != 32:
        _fail("LEGACY_KEY_INVALID")
    if type(keys) is not dict:
        _fail("TARGET_KEYRING_INVALID")
    if journal_key == legacy_key or journal_key in keys.values():
        _fail("JOURNAL_KEY_REUSED")


def _manifest(state: migration.Snapshot) -> bytes:
    # All byte strings are represented by hashes. Record MAC covers these
    # hashes; storage remains wholly synthetic in this demonstration.
    if type(state) is not migration.Snapshot:
        _fail("SNAPSHOT_INVALID")
    values = (
        state.cabinet, state.workstation, state.identity, state.digest,
        state.phase, state.target_key_id,
    )
    if any(v is not None and type(v) is not str for v in values):
        _fail("SNAPSHOT_INVALID")
    if type(state.source) is not bytes:
        _fail("SNAPSHOT_INVALID")
    if state.candidate is not None and type(state.candidate) is not bytes:
        _fail("SNAPSHOT_INVALID")
    if type(state.revision) is not int or state.revision < 0:
        _fail("SNAPSHOT_INVALID")
    obj = {
        "cabinet": state.cabinet,
        "workstation": state.workstation,
        "identity": state.identity,
        "digest": state.digest,
        "phase": state.phase,
        "revision": state.revision,
        "target_key_id": state.target_key_id,
        "source_sha256": state.source_sha256,
        "source_bytes_hash": hashlib.sha256(state.source).hexdigest(),
        "candidate_sha256": state.candidate_sha256,
        "candidate_bytes_hash": (
            hashlib.sha256(state.candidate).hexdigest()
            if state.candidate is not None else None
        ),
    }
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")


def _mac(sequence: int, previous_mac: str, state: migration.Snapshot,
         journal_key: bytes) -> str:
    content = json.dumps(
        {"sequence": sequence, "previous_mac": previous_mac},
        sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hmac.new(
        journal_key, _DOMAIN + content + b"\0" + _manifest(state),
        hashlib.sha256
    ).hexdigest()


def _transition(before: migration.Snapshot, after: migration.Snapshot) -> None:
    if (after.revision != before.revision + 1
            or (before.cabinet, before.workstation, before.identity, before.digest)
            != (after.cabinet, after.workstation, after.identity, after.digest)
            or after.source != before.source
            or after.source_sha256 != before.source_sha256):
        _fail("MIGRATION_HISTORY_INVALID")
    permitted = {
        "SOURCE": {"PREPARED"},
        "PREPARED": {"VERIFIED", "ROLLED_BACK"},
        "VERIFIED": {"COMMITTED", "ROLLED_BACK"},
        "COMMITTED": {"ROLLED_BACK"},
        "ROLLED_BACK": {"PREPARED"},
    }
    if after.phase not in permitted.get(before.phase, ()):
        _fail("MIGRATION_HISTORY_INVALID")
    if after.phase in {"VERIFIED", "COMMITTED"}:
        if (after.candidate != before.candidate
                or after.candidate_sha256 != before.candidate_sha256
                or after.target_key_id != before.target_key_id):
            _fail("MIGRATION_HISTORY_INVALID")
    if after.phase == "ROLLED_BACK":
        if (after.candidate is not None or after.candidate_sha256 is not None
                or after.target_key_id is not None):
            _fail("MIGRATION_HISTORY_INVALID")


def _validate_snapshot(state: migration.Snapshot, *, legacy_key: bytes,
                       keys: dict) -> None:
    try:
        migration.restart(state, legacy_key=legacy_key, keys=keys)
    except (migration.MigrationLabError, TypeError, ValueError):
        _fail("CHECKPOINT_UNAVAILABLE")


def _anchor(anchor: TrustedAnchor) -> None:
    if (type(anchor) is not TrustedAnchor or type(anchor.sequence) is not int
            or not 1 <= anchor.sequence <= _MAX_RECORDS
            or type(anchor.mac) is not str or not _SHA.fullmatch(anchor.mac)):
        _fail("ANCHOR_INVALID")


def initialize(state: migration.Snapshot, *, journal_key: bytes,
               legacy_key: bytes, keys: dict) -> tuple[Journal, TrustedAnchor]:
    """Create genesis and caller-owned trusted head from synthetic SOURCE."""
    _keys(journal_key, legacy_key, keys)
    _validate_snapshot(state, legacy_key=legacy_key, keys=keys)
    if state.phase != "SOURCE" or state.revision != 0:
        _fail("GENESIS_SOURCE_REQUIRED")
    tag = _mac(1, _ZERO_MAC, state, journal_key)
    return Journal((Record(1, _ZERO_MAC, state, tag),)), TrustedAnchor(1, tag)


def verify_chain(journal: Journal, anchor: TrustedAnchor, *,
                 journal_key: bytes, legacy_key: bytes,
                 keys: dict) -> migration.Snapshot:
    """Fail-closed if chain diverges from the independently trusted anchor."""
    _keys(journal_key, legacy_key, keys)
    _anchor(anchor)
    if (type(journal) is not Journal or type(journal.records) is not tuple
            or not 1 <= len(journal.records) <= _MAX_RECORDS):
        _fail("JOURNAL_INVALID")
    previous_mac = _ZERO_MAC
    prior = None
    for index, record in enumerate(journal.records, 1):
        if (type(record) is not Record or type(record.sequence) is not int
                or record.sequence != index
                or type(record.previous_mac) is not str
                or not _SHA.fullmatch(record.previous_mac)
                or type(record.mac) is not str or not _SHA.fullmatch(record.mac)):
            _fail("RECORD_INVALID")
        if not hmac.compare_digest(record.previous_mac, previous_mac):
            _fail("CHAIN_LINK_INVALID")
        # Authenticate record metadata and byte digests BEFORE decrypting media.
        # Authentication prevents unauthenticated state from reaching recovery.
        expected = _mac(index, previous_mac, record.snapshot, journal_key)
        if not hmac.compare_digest(record.mac, expected):
            _fail("RECORD_AUTHENTICATION_FAILED")
        _validate_snapshot(record.snapshot, legacy_key=legacy_key, keys=keys)
        if prior is None:
            if record.snapshot.phase != "SOURCE" or record.snapshot.revision != 0:
                _fail("GENESIS_SOURCE_REQUIRED")
        else:
            _transition(prior, record.snapshot)
        previous_mac = record.mac
        prior = record.snapshot
    # TrustedAnchor is supplied independently by the caller; if the attacker
    # can roll it back too, anti-rollback is NOT obtained.
    if anchor.sequence != len(journal.records) or not hmac.compare_digest(
            anchor.mac, previous_mac):
        _fail("ANCHOR_DIVERGENCE")
    return prior


def append(journal: Journal, anchor: TrustedAnchor,
           state: migration.Snapshot, *, journal_key: bytes,
           legacy_key: bytes, keys: dict) -> tuple[Journal, TrustedAnchor]:
    """Model one append, not atomic journaling or an external CAS update."""
    prior = verify_chain(
        journal, anchor, journal_key=journal_key,
        legacy_key=legacy_key, keys=keys
    )
    if len(journal.records) >= _MAX_RECORDS:
        _fail("JOURNAL_LIMIT")
    _validate_snapshot(state, legacy_key=legacy_key, keys=keys)
    _transition(prior, state)
    sequence = len(journal.records) + 1
    tag = _mac(sequence, anchor.mac, state, journal_key)
    return (
        Journal(journal.records + (Record(sequence, anchor.mac, state, tag),)),
        TrustedAnchor(sequence, tag),
    )
