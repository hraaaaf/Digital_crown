"""LOT06-M LAB: verify compact J/K event HMACs without repeat media decrypt.

Pure in-memory experiment, no I/O, NO physically independent witness/receipt,
NO durable monotonicity, NO clinical authorization and NO live spool mutation.
Original J/K events are validated against their exact v1 canonical MAC form.
Each distinct encrypted blob is SHA checked and AES-GCM decrypted once in
this invocation (per authenticated role/context); no persistent trust cache.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json

from . import compact_cold_lab as cold
from . import journal_lab as journal
from . import spool_version_lab as codec

_MAX_UNIQUE_COLD_VERIFY_BYTES = 512 * 1024 * 1024
_ALLOWED = {
    "SOURCE": frozenset(("PREPARED",)),
    "PREPARED": frozenset(("VERIFIED", "ROLLED_BACK")),
    "VERIFIED": frozenset(("COMMITTED", "ROLLED_BACK")),
    "COMMITTED": frozenset(("ROLLED_BACK",)),
    "ROLLED_BACK": frozenset(("PREPARED",)),
}


class IncrementalColdLabError(RuntimeError):
    """Fixed diagnostics with no identifiers, keys or media data."""


def _fail(reason: str) -> None:
    raise IncrementalColdLabError(reason)


@dataclass(frozen=True)
class ColdAudit:
    """Non-authorizing read-only report, NOT a signed witness receipt."""
    anchor: journal.TrustedAnchor
    event_count: int
    unique_ciphertexts: int
    unique_verified_bytes: int
    metadata_sha256: str


def _meta_manifest(s: cold.SnapshotRef) -> bytes:
    """Exact journal._manifest semantics, using VERIFIED ciphertext hashes."""
    data = {
        "cabinet": s.cabinet,
        "workstation": s.workstation,
        "identity": s.identity,
        "digest": s.digest,
        "phase": s.phase,
        "revision": s.revision,
        "target_key_id": s.target_key_id,
        "source_sha256": s.source_sha256,
        "source_bytes_hash": s.source.sha256,
        "candidate_sha256": s.candidate_sha256,
        "candidate_bytes_hash": (
            s.candidate.sha256 if s.candidate is not None else None),
    }
    return json.dumps(data, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":")).encode("ascii")


def _event_mac(sequence: int, previous_mac: str, s: cold.SnapshotRef,
               journal_key: bytes) -> str:
    head = json.dumps({"sequence": sequence, "previous_mac": previous_mac},
                      sort_keys=True, separators=(",", ":")).encode("ascii")
    return hmac.new(journal_key, journal._DOMAIN + head + b"\0" +
                    _meta_manifest(s), hashlib.sha256).hexdigest()


def _transition(prev: cold.SnapshotRef, nxt: cold.SnapshotRef) -> bool:
    if (nxt.revision != prev.revision + 1
            or (prev.cabinet, prev.workstation, prev.identity, prev.digest)
               != (nxt.cabinet, nxt.workstation, nxt.identity, nxt.digest)
            or prev.source != nxt.source
            or prev.source_sha256 != nxt.source_sha256
            or nxt.phase not in _ALLOWED.get(prev.phase, ())):
        return False
    if nxt.phase in ("VERIFIED", "COMMITTED"):
        if (nxt.candidate != prev.candidate
                or nxt.candidate_sha256 != prev.candidate_sha256
                or nxt.target_key_id != prev.target_key_id):
            return False
    if nxt.phase == "ROLLED_BACK" and (
            nxt.candidate is not None or nxt.candidate_sha256 is not None
            or nxt.target_key_id is not None):
        return False
    return True


def _blob_context(role: str, s: cold.SnapshotRef) -> tuple:
    # Same ciphertext under different AAD/key context MUST be authenticated
    # separately. Ordinary capture history uses one AAD/digest for all records.
    return (role, s.source.sha256 if role == "source" else s.candidate.sha256,
            s.cabinet, s.workstation, s.identity, s.digest,
            None if role == "source" else s.target_key_id)


def audit_unique_ciphertexts(
    bundle: cold.CompactBundle, current_anchor: journal.TrustedAnchor, *,
    store: cold.VolatileBlobStore, archive_key: bytes, journal_key: bytes,
    legacy_key: bytes, keys: dict,
) -> ColdAudit:
    """Verify metadata/HMAC chain then each unique ciphertext once.

    A caller may supply a stale anchor and archive together: this does NOT
    guarantee freshness. A physical independent monotonic witness is REQUIRED
    outside LAB. No plaintext, patient state or usable clinical ACK returned.
    """
    try:
        cold._archive_key(archive_key, journal_key, legacy_key, keys)
        journal._keys(journal_key, legacy_key, keys)
        if type(store) is not cold.VolatileBlobStore:
            _fail("COLD_STORE_INVALID")
        manifest = cold._canonical(bundle)
    except (cold.CompactColdLabError, journal.JournalLabError,
            AttributeError, ValueError, TypeError):
        _fail("COLD_INPUT_REFUSED")

    if (type(current_anchor) is not journal.TrustedAnchor
            or type(current_anchor.sequence) is not int
            or type(current_anchor.mac) is not str):
        _fail("TRUSTED_ANCHOR_REQUIRED")
    if (current_anchor.sequence != bundle.anchor.sequence
            or not hmac.compare_digest(current_anchor.mac, bundle.anchor.mac)):
        _fail("INDEPENDENT_HEAD_MISMATCH")
    if (cold._SHA.fullmatch(bundle.seal) is None
            or not hmac.compare_digest(
                bundle.seal, hmac.new(archive_key, cold._DOMAIN + manifest,
                                      hashlib.sha256).hexdigest())):
        _fail("COMPACT_SEAL_REFUSE")

    previous_mac = journal._ZERO_MAC
    previous_state = None
    blobs: dict[tuple, tuple[cold.BlobRef, cold.SnapshotRef]] = {}
    count = 0
    for record in bundle.records:
        s = record.snapshot
        if not hmac.compare_digest(record.previous_mac, previous_mac):
            _fail("METADATA_CHAIN_REFUSE")
        if not hmac.compare_digest(record.mac, _event_mac(
                record.sequence, previous_mac, s, journal_key)):
            _fail("JOURNAL_HMAC_REFUSE")
        if previous_state is None:
            if s.phase != "SOURCE" or s.revision != 0:
                _fail("GENESIS_REFUSE")
        elif not _transition(previous_state, s):
            _fail("MIGRATION_TRANSITION_REFUSE")
        previous_state, previous_mac = s, record.mac
        for role, ref in (
            ("source", s.source),
            ("candidate", s.candidate),
        ):
            if ref is not None:
                identity = _blob_context(role, s)
                existing = blobs.get(identity)
                if existing is not None and existing[0] != ref:
                    _fail("BLOB_CONTEXT_CONFLICT")
                blobs[identity] = (ref, s)
        count += 1

    if not hmac.compare_digest(previous_mac, bundle.anchor.mac):
        _fail("FINAL_ANCHOR_REFUSE")

    byte_count = 0
    for ref, _s in blobs.values():
        byte_count += ref.length
        if byte_count > _MAX_UNIQUE_COLD_VERIFY_BYTES:
            _fail("UNIQUE_VERIFICATION_BUDGET_REFUSE")

    # All metadata and budget checks precede costly ciphertext retrieval.
    # Each distinct role+AAD context decrypts once; a missing/mutated blob
    # fails closed even if every HMAC in the archive is valid.
    try:
        for identity, (ref, s) in blobs.items():
            raw = store.get(ref)  # full SHA256 of actual encrypted bytes
            if identity[0] == "source":
                codec.decode_legacy_v1(
                    raw, cabinet=s.cabinet, workstation=s.workstation,
                    identity=s.identity, digest=s.digest, legacy_key=legacy_key)
            else:
                if (s.target_key_id is None or not raw.startswith(
                        codec.MAGIC_V2 + bytes.fromhex(s.target_key_id))):
                    _fail("TARGET_KEY_ID_REFUSE")
                codec.decode_v2(
                    raw, cabinet=s.cabinet, workstation=s.workstation,
                    identity=s.identity, digest=s.digest, keys=keys)
    except (cold.CompactColdLabError, codec.SpoolCodecError,
            TypeError, ValueError, AttributeError):
        _fail("CIPHERTEXT_AUTHENTICATION_REFUSE")

    return ColdAudit(current_anchor, count, len(blobs), byte_count,
                     hashlib.sha256(manifest).hexdigest())
