"""LOT06-M: compact ciphertext cold-archive *experiment* (pure memory).

No I/O, no durable witness, no authority signature or clinical ACK.
The only proofs are relative to separately supplied trusted anchor and keys.
All media must be reauthenticated by J/K + AES-GCM on cold reassembly.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import re

from . import journal_lab as journal
from . import migration_lab as migration
from . import spool_version_lab as codec

_DOMAIN = b"DC06M|compact-cold-bundle|v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_SCAN_BYTES = 512 * 1024 * 1024  # per-invocation cold verification work


class CompactColdLabError(RuntimeError):
    """Fixed diagnostics without paths, keys, image content or patient data."""


def _refuse(reason: str) -> None:
    raise CompactColdLabError(reason)


@dataclass(frozen=True)
class BlobRef:
    sha256: str
    length: int


@dataclass(frozen=True)
class SnapshotRef:
    cabinet: str
    workstation: str
    identity: str
    digest: str
    phase: str
    revision: int
    source: BlobRef
    source_sha256: str
    candidate: BlobRef | None
    candidate_sha256: str | None
    target_key_id: str | None


@dataclass(frozen=True)
class CompactRecord:
    sequence: int
    previous_mac: str
    mac: str
    snapshot: SnapshotRef


@dataclass(frozen=True)
class CompactBundle:
    """Metadata only; no ciphertext or plaintext inside the bundle."""
    anchor: journal.TrustedAnchor
    records: tuple[CompactRecord, ...]
    seal: str


class VolatileBlobStore:
    """Deduplicate ciphertexts by digest; ordinary mutable in-memory storage."""

    def __init__(self):
        self._blobs: dict[str, bytes] = {}

    def put(self, blob: bytes) -> BlobRef:
        if (type(blob) is not bytes or not 0 < len(blob)
                <= codec.MAX_CLEAR_BYTES + codec.V2_OVERHEAD):
            _refuse("BLOB_SIZE_REFUSE")
        digest = hashlib.sha256(blob).hexdigest()
        current = self._blobs.get(digest)
        if current is not None and not hmac.compare_digest(
                hashlib.sha256(current).hexdigest(), digest):
            _refuse("BLOB_STORE_CORRUPT")
        self._blobs[digest] = blob
        return BlobRef(digest, len(blob))

    def get(self, ref: BlobRef) -> bytes:
        if not _valid_ref(ref):
            _refuse("BLOB_REFERENCE_REFUSE")
        data = self._blobs.get(ref.sha256)
        if data is None:
            _refuse("BLOB_MISSING_REFUSE")
        if (type(data) is not bytes or len(data) != ref.length
                or not hmac.compare_digest(
                    hashlib.sha256(data).hexdigest(), ref.sha256)):
            _refuse("BLOB_INTEGRITY_REFUSE")
        return data

    def distinct_bytes(self) -> int:
        return sum(len(data) for data in self._blobs.values())


def _valid_ref(ref: object) -> bool:
    return (type(ref) is BlobRef and type(ref.sha256) is str
            and _SHA.fullmatch(ref.sha256) is not None
            and type(ref.length) is int
            and 0 < ref.length <= codec.MAX_CLEAR_BYTES + codec.V2_OVERHEAD)


def _archive_key(archive_key: bytes, journal_key: bytes,
                 legacy_key: bytes, keys: dict) -> None:
    if (type(archive_key) is not bytes or len(archive_key) != 32
            or archive_key == journal_key or archive_key == legacy_key
            or type(keys) is not dict or archive_key in keys.values()):
        _refuse("ARCHIVE_KEY_DOMAIN_REFUSE")


def _work_budget(lengths) -> None:
    total = 0
    for length in lengths:
        if type(length) is not int or length < 0:
            _refuse("ARCHIVE_SHAPE_REFUSE")
        total += length
        if total > _MAX_SCAN_BYTES:
            _refuse("COLD_VERIFICATION_BUDGET_REFUSE")


def _canonical(bundle: CompactBundle) -> bytes:
    """Reject malformed metadata before JSON and MAC checks."""
    if (type(bundle) is not CompactBundle or
            type(bundle.records) is not tuple or
            not 1 <= len(bundle.records) <= 256 or
            type(bundle.anchor) is not journal.TrustedAnchor or
            type(bundle.anchor.sequence) is not int or
            bundle.anchor.sequence != len(bundle.records) or
            type(bundle.anchor.mac) is not str or
            _SHA.fullmatch(bundle.anchor.mac) is None or
            type(bundle.seal) is not str):
        _refuse("ARCHIVE_SHAPE_REFUSE")
    obj = ["DC06M-COLD-v1", bundle.anchor.sequence, bundle.anchor.mac]
    records = []
    for index, record in enumerate(bundle.records, 1):
        if (type(record) is not CompactRecord
                or type(record.sequence) is not int
                or record.sequence != index
                or type(record.previous_mac) is not str
                or _SHA.fullmatch(record.previous_mac) is None
                or type(record.mac) is not str
                or _SHA.fullmatch(record.mac) is None):
            _refuse("ARCHIVE_SHAPE_REFUSE")
        s = record.snapshot
        if type(s) is not SnapshotRef or not _valid_ref(s.source):
            _refuse("ARCHIVE_SHAPE_REFUSE")
        if (s.candidate is not None and not _valid_ref(s.candidate)
                or any(type(v) is not str for v in
                    (s.cabinet, s.workstation, s.identity, s.digest, s.phase,
                     s.source_sha256))
                or type(s.revision) is not int or s.revision < 0
                or (s.target_key_id is not None and type(s.target_key_id) is not str)
                or (s.candidate_sha256 is not None
                    and type(s.candidate_sha256) is not str)
                or s.source.sha256 != s.source_sha256
                or (s.candidate is None) != (s.candidate_sha256 is None)
                or (s.candidate is not None
                    and s.candidate.sha256 != s.candidate_sha256)):
            _refuse("ARCHIVE_SHAPE_REFUSE")
        records.append([
            record.sequence, record.previous_mac, record.mac,
            [s.cabinet, s.workstation, s.identity, s.digest,
             s.phase, s.revision, s.source.sha256, s.source.length,
             s.source_sha256, s.candidate.sha256 if s.candidate else None,
             s.candidate.length if s.candidate else None,
             s.candidate_sha256, s.target_key_id]])
    obj.append(records)
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _seal(bundle: CompactBundle, key: bytes) -> str:
    return hmac.new(key, _DOMAIN + _canonical(bundle), hashlib.sha256).hexdigest()


def pack_verified(history: journal.Journal, anchor: journal.TrustedAnchor,
                  *, store: VolatileBlobStore, archive_key: bytes,
                  journal_key: bytes, legacy_key: bytes,
                  keys: dict) -> CompactBundle:
    """Full incoming J/K+AEAD verify BEFORE packing; ciphertext only.

    A cold store is NOT a monotonic authority or independent custodian.
    """
    _archive_key(archive_key, journal_key, legacy_key, keys)
    if (type(store) is not VolatileBlobStore or
            type(history) is not journal.Journal or
            type(history.records) is not tuple or
            not 1 <= len(history.records) <= 256):
        _refuse("ARCHIVE_SHAPE_REFUSE")
    sizes = []
    for record in history.records:
        if type(record) is not journal.Record or type(record.snapshot) is not migration.Snapshot:
            _refuse("ARCHIVE_SHAPE_REFUSE")
        snapshot = record.snapshot
        if (type(snapshot.source) is not bytes or
                (snapshot.candidate is not None
                 and type(snapshot.candidate) is not bytes)):
            _refuse("ARCHIVE_SHAPE_REFUSE")
        sizes.append(len(snapshot.source))
        if snapshot.candidate is not None:
            sizes.append(len(snapshot.candidate))
    _work_budget(sizes)
    try:
        journal.verify_chain(history, anchor, journal_key=journal_key,
                             legacy_key=legacy_key, keys=keys)
    except (journal.JournalLabError, ValueError, TypeError, AttributeError):
        _refuse("UNAUTHENTICATED_HISTORY_REFUSE")
    compact = []
    for record in history.records:
        snap = record.snapshot
        src = store.put(snap.source)
        target = store.put(snap.candidate) if snap.candidate is not None else None
        compact.append(CompactRecord(
            record.sequence, record.previous_mac, record.mac,
            SnapshotRef(snap.cabinet, snap.workstation, snap.identity,
                        snap.digest, snap.phase, snap.revision,
                        src, snap.source_sha256, target,
                        snap.candidate_sha256, snap.target_key_id)))
    draft = CompactBundle(anchor, tuple(compact), "0" * 64)
    return CompactBundle(anchor, draft.records, _seal(draft, archive_key))


def reassemble_verified(bundle: CompactBundle, trusted_anchor: journal.TrustedAnchor,
                        *, store: VolatileBlobStore, archive_key: bytes,
                        journal_key: bytes, legacy_key: bytes,
                        keys: dict) -> journal.Journal:
    """Read-only reassemble; independently provided CURRENT anchor is required.

    Always verify HMAC metadata, SHA of EVERY retrieved blob, J/K chain and
    source/candidate AEAD again. No clinical ACK or durable restore operation.
    """
    _archive_key(archive_key, journal_key, legacy_key, keys)
    if type(store) is not VolatileBlobStore:
        _refuse("ARCHIVE_SHAPE_REFUSE")
    manifest = _canonical(bundle)
    if type(trusted_anchor) is not journal.TrustedAnchor:
        _refuse("TRUSTED_HEAD_REQUIRED")
    if (type(trusted_anchor.sequence) is not int
            or type(trusted_anchor.mac) is not str
            or (trusted_anchor.sequence, trusted_anchor.mac)
               != (bundle.anchor.sequence, bundle.anchor.mac)):
        _refuse("INDEPENDENT_HEAD_MISMATCH")
    if not _SHA.fullmatch(bundle.seal):
        _refuse("ARCHIVE_SEAL_REFUSE")
    expected = hmac.new(
        archive_key, _DOMAIN + manifest, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(bundle.seal, expected):
        _refuse("ARCHIVE_SEAL_REFUSE")
    _work_budget(
        len_value for record in bundle.records
        for len_value in (
            (record.snapshot.source.length,)
            + ((record.snapshot.candidate.length,)
               if record.snapshot.candidate is not None else ())))
    records = []
    for item in bundle.records:
        s = item.snapshot
        source = store.get(s.source)
        candidate = store.get(s.candidate) if s.candidate is not None else None
        snap = migration.Snapshot(
            s.cabinet, s.workstation, s.identity, s.digest,
            source, s.source_sha256, s.phase, s.revision,
            candidate, s.candidate_sha256, s.target_key_id)
        records.append(journal.Record(
            item.sequence, item.previous_mac, snap, item.mac))
    result = journal.Journal(tuple(records))
    try:
        journal.verify_chain(result, trusted_anchor, journal_key=journal_key,
                             legacy_key=legacy_key, keys=keys)
    except (journal.JournalLabError, ValueError, TypeError, AttributeError):
        _refuse("COLD_CHAIN_REFUSE")
    return result
