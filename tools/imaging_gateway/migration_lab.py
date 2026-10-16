"""LOT06-J in-memory crash/recovery migration protocol demonstrator.

Synthetic immutable checkpoints only. No filesystem, SQL, live collector, real
journal durability, clinical activation, or authorization service.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import re

from . import spool_version_lab as codec

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_PHASES = frozenset({"SOURCE", "PREPARED", "VERIFIED", "COMMITTED", "ROLLED_BACK"})


class MigrationLabError(RuntimeError):
    """Fixed diagnostic codes: no plaintext, keys, identity or scopes in errors."""


@dataclass(frozen=True)
class Snapshot:
    cabinet: str
    workstation: str
    identity: str
    digest: str
    source: bytes
    source_sha256: str
    phase: str = "SOURCE"
    revision: int = 0
    candidate: bytes | None = None
    candidate_sha256: str | None = None
    target_key_id: str | None = None


class SimulatedCrash(RuntimeError):
    """Snapshot surviving a hypothetical crash; not persisted by this module."""

    def __init__(self, checkpoint: Snapshot):
        super().__init__("SIMULATED_CRASH")
        self.checkpoint = checkpoint


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject(error: str) -> None:
    raise MigrationLabError(error)


def _source_clear(state: Snapshot, legacy_key: bytes, *,
                  tolerate_candidate_corruption: bool = False) -> bytes:
    if type(state) is not Snapshot:
        _reject("SNAPSHOT_INVALID")
    if (type(state.phase) is not str or state.phase not in _PHASES
            or type(state.revision) is not int or state.revision < 0):
        _reject("CHECKPOINT_INVALID")
    if type(state.source) is not bytes or type(state.source_sha256) is not str:
        _reject("SOURCE_CHECKPOINT_INVALID")
    if not _SHA.fullmatch(state.source_sha256) or _hash(state.source) != state.source_sha256:
        _reject("SOURCE_CHECKPOINT_INVALID")
    try:
        clear = codec.decode_legacy_v1(
            state.source, cabinet=state.cabinet, workstation=state.workstation,
            identity=state.identity, digest=state.digest, legacy_key=legacy_key
        )
    except codec.SpoolCodecError:
        _reject("LEGACY_SOURCE_UNAVAILABLE")
    if state.phase in {"SOURCE", "ROLLED_BACK"}:
        if (state.candidate is not None or state.candidate_sha256 is not None
                or state.target_key_id is not None):
            _reject("CHECKPOINT_INVALID")
    elif not tolerate_candidate_corruption:
        if (type(state.candidate) is not bytes
                or type(state.candidate_sha256) is not str
                or not _SHA.fullmatch(state.candidate_sha256)
                or type(state.target_key_id) is not str
                or not re.fullmatch(r"[0-9a-f]{32}", state.target_key_id)
                or not state.candidate.startswith(
                    codec.MAGIC_V2 + bytes.fromhex(state.target_key_id)
                )):
            _reject("CHECKPOINT_INVALID")
    return clear


def _candidate_clear(state: Snapshot, keys: dict) -> bytes:
    if _hash(state.candidate) != state.candidate_sha256:
        _reject("CANDIDATE_CHECKPOINT_INVALID")
    try:
        return codec.decode_v2(
            state.candidate, cabinet=state.cabinet, workstation=state.workstation,
            identity=state.identity, digest=state.digest, keys=keys
        )
    except codec.SpoolCodecError:
        _reject("CANDIDATE_UNAVAILABLE")


def _validated(state: Snapshot, legacy_key: bytes, keys: dict,
               require_candidate: bool = True) -> bytes:
    old = _source_clear(state, legacy_key)
    if state.phase not in {"SOURCE", "ROLLED_BACK"} and require_candidate:
        new = _candidate_clear(state, keys)
        if old != new:
            _reject("CANDIDATE_CONTENT_MISMATCH")
    return old


def _lease(state: Snapshot, expected_revision: int) -> None:
    if type(expected_revision) is not int or expected_revision != state.revision:
        _reject("STALE_CHECKPOINT")


def begin(source: bytes, *, cabinet: str, workstation: str, identity: str,
          digest: str, legacy_key: bytes) -> Snapshot:
    """Register a verified synthetic legacy image, with a retained source."""
    if type(source) is not bytes:
        _reject("SOURCE_CHECKPOINT_INVALID")
    state = Snapshot(cabinet, workstation, identity, digest, source, _hash(source))
    _source_clear(state, legacy_key)
    return state


def prepare(state: Snapshot, *, expected_revision: int, legacy_key: bytes,
            target_key_id: str, keys: dict) -> Snapshot:
    """Copy-on-write candidate; does not advance the active reader pointer."""
    _validated(state, legacy_key, keys)
    _lease(state, expected_revision)
    if state.phase not in {"SOURCE", "ROLLED_BACK"}:
        _reject("INVALID_TRANSITION")
    try:
        candidate = codec.rewrap_legacy_v1(
            state.source, cabinet=state.cabinet, workstation=state.workstation,
            identity=state.identity, digest=state.digest, legacy_key=legacy_key,
            target_key_id=target_key_id, keys=keys
        )
    except codec.SpoolCodecError:
        _reject("PREPARE_REFUSED")
    return replace(
        state, phase="PREPARED", revision=state.revision + 1,
        candidate=candidate, candidate_sha256=_hash(candidate),
        target_key_id=target_key_id
    )


def verify(state: Snapshot, *, expected_revision: int, legacy_key: bytes,
           keys: dict) -> Snapshot:
    """Independently re-authenticate source and candidate before a commit."""
    _validated(state, legacy_key, keys)
    _lease(state, expected_revision)
    if state.phase != "PREPARED":
        _reject("INVALID_TRANSITION")
    return replace(state, phase="VERIFIED", revision=state.revision + 1)


def commit(state: Snapshot, *, expected_revision: int, legacy_key: bytes,
           keys: dict) -> Snapshot:
    """Simulated atomic marker: no physical atomicity or fsync is claimed."""
    _validated(state, legacy_key, keys)
    _lease(state, expected_revision)
    if state.phase != "VERIFIED":
        _reject("VERIFY_REQUIRED")
    return replace(state, phase="COMMITTED", revision=state.revision + 1)


def read_active(state: Snapshot, *, legacy_key: bytes, keys: dict) -> bytes:
    """Never auto-promote a PREPARED/VERIFIED candidate after crash."""
    old = _validated(state, legacy_key, keys)
    if state.phase == "COMMITTED":
        return _candidate_clear(state, keys)
    return old


def restart(state: Snapshot, *, legacy_key: bytes, keys: dict) -> Snapshot:
    """Check snapshot integrity, refusing unavailable keys and tampered data.

    This is a simulated recovery inspection of an immutable checkpoint, not
    actual disk replay or a monotonic persisted journal.
    """
    read_active(state, legacy_key=legacy_key, keys=keys)
    return state


def rollback(state: Snapshot, *, expected_revision: int, legacy_key: bytes,
             operator_confirmed: bool) -> Snapshot:
    """Explicit simulated rollback. Intentionally needs only retained old key.

    Allows rollback of a *corrupt* candidate; still authenticates old source.
    The boolean is a test gate, NOT real operator authentication.
    """
    # Recovery does not depend on a structurally valid candidate envelope.
    # Source hash and legacy AEAD remain mandatory.
    _source_clear(state, legacy_key, tolerate_candidate_corruption=True)
    _lease(state, expected_revision)
    if operator_confirmed is not True:
        _reject("OPERATOR_GATE_REQUIRED")
    if state.phase not in {"PREPARED", "VERIFIED", "COMMITTED"}:
        _reject("INVALID_TRANSITION")
    return replace(
        state, phase="ROLLED_BACK", revision=state.revision + 1,
        candidate=None, candidate_sha256=None, target_key_id=None
    )


def exercise(state: Snapshot, *, legacy_key: bytes, target_key_id: str,
             keys: dict, crash_after: str | None = None) -> Snapshot:
    """Crash injection AFTER each immutable checkpoint; no writes or sleeps."""
    if crash_after not in {None, "source", "prepare", "verify", "commit"}:
        _reject("INVALID_FAILPOINT")
    if crash_after == "source":
        raise SimulatedCrash(state)
    state = prepare(state, expected_revision=state.revision,
                    legacy_key=legacy_key, target_key_id=target_key_id, keys=keys)
    if crash_after == "prepare":
        raise SimulatedCrash(state)
    state = verify(state, expected_revision=state.revision,
                   legacy_key=legacy_key, keys=keys)
    if crash_after == "verify":
        raise SimulatedCrash(state)
    state = commit(state, expected_revision=state.revision,
                   legacy_key=legacy_key, keys=keys)
    if crash_after == "commit":
        raise SimulatedCrash(state)
    return state
