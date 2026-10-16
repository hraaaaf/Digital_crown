"""LOT06-L isolated in-memory CAS fork-arbitration demonstrator.

NOT a durable, independent monotonic authority or an actual interprocess CAS.
No filesystem/SQL/collector/clinical integration.
"""
from __future__ import annotations

from dataclasses import dataclass
import hmac

from . import journal_lab as journal
from . import migration_lab as migration


class ForkLabError(RuntimeError):
    """Only fixed public error codes."""


@dataclass(frozen=True)
class Draft:
    expected: journal.TrustedAnchor
    candidate: journal.Journal
    next_anchor: journal.TrustedAnchor


def _fail(code: str) -> None:
    raise ForkLabError(code)


def _same_anchor(a: journal.TrustedAnchor,
                 b: journal.TrustedAnchor) -> bool:
    return (type(a) is journal.TrustedAnchor
            and type(b) is journal.TrustedAnchor
            and type(a.sequence) is int and type(b.sequence) is int
            and type(a.mac) is str and type(b.mac) is str
            and a.sequence == b.sequence and hmac.compare_digest(a.mac, b.mac))


def propose(base: journal.Journal, expected: journal.TrustedAnchor,
            state: migration.Snapshot, *, journal_key: bytes,
            legacy_key: bytes, keys: dict) -> Draft:
    """Prepare one fork, without writing or changing any authority."""
    try:
        candidate, head = journal.append(
            base, expected, state, journal_key=journal_key,
            legacy_key=legacy_key, keys=keys
        )
    except (journal.JournalLabError, TypeError, ValueError):
        _fail("DRAFT_REJECTED")
    return Draft(expected, candidate, head)


class VolatileAuthority:
    """One in-process high-watermark voter; callable code CAN recreate it."""

    __slots__ = ("_head", "_scope", "_journal_key", "_legacy_key", "_keys")

    def __init__(self, genesis: journal.Journal,
                 anchor: journal.TrustedAnchor, *, journal_key: bytes,
                 legacy_key: bytes, keys: dict):
        if (type(genesis) is not journal.Journal
                or type(genesis.records) is not tuple
                or len(genesis.records) != 1
                or type(anchor) is not journal.TrustedAnchor
                or type(anchor.sequence) is not int or anchor.sequence != 1):
            _fail("GENESIS_REQUIRED")
        try:
            state = journal.verify_chain(
                genesis, anchor, journal_key=journal_key,
                legacy_key=legacy_key, keys=keys
            )
        except (journal.JournalLabError, TypeError, ValueError):
            _fail("GENESIS_INVALID")
        if state.phase != "SOURCE" or state.revision != 0:
            _fail("GENESIS_REQUIRED")
        self._head = anchor
        self._scope = (
            state.cabinet, state.workstation, state.identity,
            state.digest, state.source_sha256
        )
        self._journal_key = journal_key
        self._legacy_key = legacy_key
        self._keys = dict(keys)

    def observe(self) -> journal.TrustedAnchor:
        return self._head

    def compare_and_swap(self, draft: Draft) -> journal.TrustedAnchor:
        """A sequential simulated CAS; not an OS-atomic or durable operation."""
        if type(draft) is not Draft:
            _fail("DRAFT_INVALID")
        if not _same_anchor(draft.expected, self._head):
            _fail("STALE_FORK")
        if (type(draft.next_anchor) is not journal.TrustedAnchor
                or type(draft.next_anchor.sequence) is not int
                or draft.next_anchor.sequence != self._head.sequence + 1
                or type(draft.next_anchor.mac) is not str
                or type(draft.candidate) is not journal.Journal
                or type(draft.candidate.records) is not tuple
                or len(draft.candidate.records) != draft.next_anchor.sequence
                or len(draft.candidate.records) < 2):
            _fail("DRAFT_INVALID")
        prior = draft.candidate.records[-2]
        if (type(prior) is not journal.Record
                or type(prior.mac) is not str
                or not hmac.compare_digest(prior.mac, self._head.mac)):
            _fail("FORK_PARENT_MISMATCH")
        try:
            ending = journal.verify_chain(
                draft.candidate, draft.next_anchor,
                journal_key=self._journal_key,
                legacy_key=self._legacy_key, keys=self._keys
            )
        except (journal.JournalLabError, TypeError, ValueError):
            _fail("DRAFT_INVALID")
        if (ending.cabinet, ending.workstation, ending.identity,
                ending.digest, ending.source_sha256) != self._scope:
            _fail("CAPTURE_SCOPE_MISMATCH")
        self._head = draft.next_anchor
        return self._head

    def recover(self, local: journal.Journal) -> migration.Snapshot:
        """Refuse local history ahead of or behind the current high-watermark."""
        try:
            ending = journal.verify_chain(
                local, self._head, journal_key=self._journal_key,
                legacy_key=self._legacy_key, keys=self._keys
            )
        except (journal.JournalLabError, TypeError, ValueError):
            _fail("RECOVERY_REFUSED")
        if (ending.cabinet, ending.workstation, ending.identity,
                ending.digest, ending.source_sha256) != self._scope:
            _fail("CAPTURE_SCOPE_MISMATCH")
        return ending
