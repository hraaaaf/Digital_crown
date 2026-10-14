"""LOT06-M isolated synthetic decision and archive consistency model.

One immutable Python state installation models a *logical* atomic decision.
It is not physically durable, cross-process linearizable, authenticated,
an independent witness, or permission for any patient/clinical action.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import re
import threading

from . import fork_lab as fork
from . import journal_lab as journal


class WitnessLabError(RuntimeError):
    """Fixed codes only; no image/key/scope leaks."""


class SimulatedLabCrash(RuntimeError):
    """Fault injection at a logical state installation boundary, no I/O."""


@dataclass(frozen=True)
class Receipt:
    operation_id: str
    request_digest: str
    authority_id: str
    opaque_scope: str
    epoch: str
    before: journal.TrustedAnchor
    after: journal.TrustedAnchor


@dataclass(frozen=True)
class Assessment:
    code: str


@dataclass(frozen=True)
class _State:
    history: journal.Journal
    head: journal.TrustedAnchor
    decisions: tuple[Receipt, ...]


class VolatileEnrollmentRegistry:
    """LAB-only shared capture registry. Creating another defeats uniqueness."""

    def __init__(self):
        self._lock = threading.Lock()
        self._claims: dict[tuple, tuple[str, str, str]] = {}

    def claim(self, capture: tuple, authority_id: str,
              epoch: str, scope: str) -> None:
        entry = (authority_id, epoch, scope)
        with self._lock:
            previous = self._claims.get(capture)
            if previous is not None:
                _fail("ACTIVE_WITNESS_EXISTS" if previous == entry
                      else "ENROLLMENT_CONFLICT")
            self._claims[capture] = entry


def _fail(code: str) -> None:
    raise WitnessLabError(code)


def _same(a: journal.TrustedAnchor, b: journal.TrustedAnchor) -> bool:
    return (type(a) is journal.TrustedAnchor and type(b) is journal.TrustedAnchor
            and type(a.sequence) is int and type(b.sequence) is int
            and type(a.mac) is str and type(b.mac) is str
            and a.sequence == b.sequence and hmac.compare_digest(a.mac, b.mac))


def _operation(operation_id: str) -> None:
    if (type(operation_id) is not str
            or not re.fullmatch(r"[0-9a-f]{32}", operation_id)
            or operation_id == "0" * 32):
        _fail("OPERATION_ID_INVALID")


def _request_digest(draft: fork.Draft, *, authority_id: str, epoch: str,
                    opaque_scope: str, operation_id: str) -> str:
    """Single-transition v3 digest; parent authenticated MAC binds past.

    Full proposal verification remains mandatory for new decisions; returning
    an existing receipt requires exact historical prefix equality. A digest
    is NOT a cryptographic authority signature.
    """
    if (type(draft) is not fork.Draft
            or type(draft.candidate) is not journal.Journal
            or type(draft.candidate.records) is not tuple
            or not 2 <= len(draft.candidate.records) <= 256
            or type(draft.expected) is not journal.TrustedAnchor
            or type(draft.next_anchor) is not journal.TrustedAnchor):
        _fail("PROPOSAL_INVALID")
    _operation(operation_id)
    try:
        last = draft.candidate.records[-1]
        if type(last) is not journal.Record:
            _fail("PROPOSAL_INVALID")
        identity = [authority_id, epoch, opaque_scope, operation_id,
                    draft.expected.sequence, draft.expected.mac,
                    draft.next_anchor.sequence, draft.next_anchor.mac,
                    last.sequence, last.previous_mac, last.mac]
        h = hashlib.sha256(b"DC06M|synthetic-decision-envelope|v3\0")
        data = json.dumps(identity, separators=(",", ":"),
                          ensure_ascii=True).encode("ascii")
        manifest = journal._manifest(last.snapshot)
        for part in (data, manifest):
            h.update(len(part).to_bytes(4, "big") + part)
    except (journal.JournalLabError, ValueError, TypeError,
            AttributeError, OverflowError, UnicodeError):
        _fail("PROPOSAL_INVALID")
    return h.hexdigest()

class VolatileDecisionWitness:
    """Serialized LAB CAS with one immutable state snapshot; still volatile."""

    def __init__(self, genesis: journal.Journal,
                 anchor: journal.TrustedAnchor, *, authority_id: str,
                 epoch: str, opaque_scope: str,
                 registry: VolatileEnrollmentRegistry, journal_key: bytes,
                 legacy_key: bytes, keys: dict):
        if (type(authority_id) is not str
                or not re.fullmatch(r"[a-zA-Z0-9._-]{1,64}", authority_id)
                or type(epoch) is not str
                or not re.fullmatch(r"[a-zA-Z0-9._-]{1,64}", epoch)
                or type(opaque_scope) is not str
                or not re.fullmatch(r"[0-9a-f]{32}", opaque_scope)):
            _fail("IDENTITY_INVALID")
        if type(registry) is not VolatileEnrollmentRegistry:
            _fail("ENROLLMENT_REQUIRED")
        validated = fork.VolatileAuthority(
            genesis, anchor, journal_key=journal_key,
            legacy_key=legacy_key, keys=keys)
        capture_scope = self._scope_for(genesis.records[0].snapshot)
        registry.claim(capture_scope, authority_id, epoch, opaque_scope)
        self._registry = registry
        self._authority_id = authority_id
        self._epoch = epoch
        self._opaque_scope = opaque_scope
        self._journal_key = journal_key
        self._legacy_key = legacy_key
        self._keys = dict(keys)
        self._scope = capture_scope
        self._state = _State(genesis, validated.observe(), ())
        self._lock = threading.Lock()

    @staticmethod
    def _scope_for(snapshot: object) -> tuple:
        return (snapshot.cabinet, snapshot.workstation, snapshot.identity,
                snapshot.digest, snapshot.source_sha256)

    def _identity(self, epoch: str) -> None:
        if type(epoch) is not str or not hmac.compare_digest(epoch, self._epoch):
            _fail("EPOCH_REFUSED")

    def _digest(self, draft: fork.Draft, operation_id: str) -> str:
        return _request_digest(draft, authority_id=self._authority_id,
                               epoch=self._epoch, opaque_scope=self._opaque_scope,
                               operation_id=operation_id)

    def _valid_history(self, history: journal.Journal,
                       head: journal.TrustedAnchor) -> bool:
        try:
            state = journal.verify_chain(
                history, head, journal_key=self._journal_key,
                legacy_key=self._legacy_key, keys=self._keys)
            return self._scope_for(state) == self._scope
        except (journal.JournalLabError, TypeError, ValueError, AttributeError):
            return False

    def _valid_prefix(self, local: journal.Journal) -> bool:
        if (type(local) is not journal.Journal or
                type(local.records) is not tuple or
                not 1 <= len(local.records) <= 256):
            return False
        last = local.records[-1]
        if type(last) is not journal.Record:
            return False
        return self._valid_history(
            local, journal.TrustedAnchor(last.sequence, last.mac))

    def _ledger_complete(self, state: _State) -> bool:
        """Entire history, every receipt field, ID, digest and order must match.

        This is an integrity check *relative to memory-owned keys and ledger*,
        NOT independent archive custody, witness authenticity or freshness.
        """
        if (type(state) is not _State
                or not self._valid_history(state.history, state.head)
                or type(state.decisions) is not tuple
                or len(state.decisions) != state.head.sequence - 1):
            return False
        seen: set[str] = set()
        records = state.history.records
        for index, receipt in enumerate(state.decisions, start=2):
            if type(receipt) is not Receipt:
                return False
            try:
                _operation(receipt.operation_id)
                if (receipt.operation_id in seen
                        or type(receipt.request_digest) is not str
                        or len(receipt.request_digest) != 64
                        or any(c not in "0123456789abcdef"
                               for c in receipt.request_digest)
                        or receipt.authority_id != self._authority_id
                        or receipt.opaque_scope != self._opaque_scope
                        or receipt.epoch != self._epoch):
                    return False
                before = journal.TrustedAnchor(records[index-2].sequence,
                                               records[index-2].mac)
                after = journal.TrustedAnchor(records[index-1].sequence,
                                              records[index-1].mac)
                if not (_same(receipt.before, before)
                        and _same(receipt.after, after)):
                    return False
                draft = fork.Draft(before,
                                   journal.Journal((records[0], records[index-1])), after)
                if not hmac.compare_digest(
                        receipt.request_digest,
                        self._digest(draft, receipt.operation_id)):
                    return False
                seen.add(receipt.operation_id)
            except (WitnessLabError, TypeError, ValueError, AttributeError):
                return False
        return True

    def observe(self, *, epoch: str) -> journal.TrustedAnchor:
        self._identity(epoch)
        state = self._state
        if not self._ledger_complete(state):
            _fail("WITNESS_LEDGER_INCONSISTENT")
        return state.head

    def decide(self, draft: fork.Draft, *, operation_id: str,
               epoch: str, failpoint: str | None = None) -> Receipt:
        """Logical CAS, ledger and history installed with one state assignment.

        Failpoint BEFORE_INSTALL => no change; AFTER_INSTALL => decision fully
        visible even without the response. No real power-loss or fsync tested.
        """
        self._identity(epoch)
        _operation(operation_id)
        if failpoint not in (None, "BEFORE_INSTALL", "AFTER_INSTALL"):
            _fail("FAILPOINT_INVALID")
        digest = self._digest(draft, operation_id)
        with self._lock:
            old = self._state
            if not self._ledger_complete(old):
                _fail("WITNESS_LEDGER_INCONSISTENT")
            previous = next((r for r in old.decisions
                             if r.operation_id == operation_id), None)
            if previous is not None:
                if not hmac.compare_digest(previous.request_digest, digest):
                    _fail("IDEMPOTENCY_CONFLICT")
                if draft.candidate.records != old.history.records[:previous.after.sequence]:
                    _fail("PROPOSAL_REFUSED")
                return previous
            if not _same(draft.expected, old.head):
                _fail("STALE_FORK")
            if (type(draft.next_anchor.sequence) is not int
                    or draft.next_anchor.sequence != old.head.sequence + 1
                    or draft.candidate.records[:-1] != old.history.records):
                _fail("FORK_PARENT_MISMATCH")
            if not self._valid_history(draft.candidate, draft.next_anchor):
                _fail("PROPOSAL_REFUSED")
            receipt = Receipt(operation_id, digest, self._authority_id,
                              self._opaque_scope, self._epoch,
                              draft.expected, draft.next_anchor)
            staged = _State(draft.candidate, draft.next_anchor,
                            old.decisions + (receipt,))
            if failpoint == "BEFORE_INSTALL":
                raise SimulatedLabCrash("BEFORE_INSTALL")
            self._state = staged  # single linearization point in LAB
            if failpoint == "AFTER_INSTALL":
                raise SimulatedLabCrash("AFTER_INSTALL")
            return receipt

    def lookup(self, draft: fork.Draft, *, operation_id: str,
               epoch: str) -> Receipt | None:
        """Absence is UNKNOWN: an in-flight identical request can still arrive."""
        self._identity(epoch)
        _operation(operation_id)
        digest = self._digest(draft, operation_id)
        state = self._state
        if not self._ledger_complete(state):
            _fail("WITNESS_LEDGER_INCONSISTENT")
        previous = next((r for r in state.decisions
                         if r.operation_id == operation_id), None)
        if previous is not None:
            if not hmac.compare_digest(previous.request_digest, digest):
                _fail("IDEMPOTENCY_CONFLICT")
            if draft.candidate.records != state.history.records[:previous.after.sequence]:
                _fail("PROPOSAL_REFUSED")
        return previous

    def lost_reply(self, local: journal.Journal | None,
                   draft: fork.Draft, *, operation_id: str,
                   epoch: str) -> Assessment:
        """Classify only, never locally finalize or produce an ACK."""
        self._identity(epoch)
        _operation(operation_id)
        current = self._state  # one coherent snapshot; no mixed-head race
        if not self._ledger_complete(current):
            return Assessment("WITNESS_LEDGER_INCONSISTENT_REFUSE")
        digest = self._digest(draft, operation_id)
        previous = next((r for r in current.decisions
                         if r.operation_id == operation_id), None)
        if previous is not None:
            if not hmac.compare_digest(previous.request_digest, digest):
                _fail("IDEMPOTENCY_CONFLICT")
            if draft.candidate.records != current.history.records[:previous.after.sequence]:
                _fail("PROPOSAL_REFUSED")
        if previous is None:
            if _same(draft.expected, current.head):
                return Assessment("UNKNOWN_RETRY_SAME_OP_ONLY")
            return Assessment("UNDECIDED_STALE_HEAD_REFUSE")
        if not _same(previous.after, current.head):
            return Assessment("OLD_DECISION_RECHECK_CURRENT_HEAD")
        if not self._valid_prefix(local):
            return Assessment("LOCAL_EVIDENCE_MISSING" if local is None
                              else "LOCAL_INVALID_REFUSE")
        if local == current.history:
            return Assessment("DECIDED_LOCAL_REVIEW_REQUIRED")
        if (len(local.records) < len(current.history.records)
                and local.records == current.history.records[:len(local.records)]):
            return Assessment("DECIDED_NOT_FINALIZED_LOCAL_STALE")
        return Assessment("LOCAL_DIVERGENCE_REFUSE")

    def assess_archive(self, local: journal.Journal | None,
                       archive: journal.Journal | None, *,
                       epoch: str) -> Assessment:
        """Read-only consistency classification, NEVER authorization to restore."""
        self._identity(epoch)
        state = self._state
        if local is None:
            return Assessment("LOCAL_EVIDENCE_MISSING")
        if not self._valid_prefix(local):
            return Assessment("LOCAL_INVALID_REFUSE")
        if len(local.records) > state.head.sequence:
            return Assessment("LOCAL_AHEAD_REFUSE")
        if len(local.records) == state.head.sequence:
            if local != state.history:
                return Assessment("LOCAL_DIVERGENCE_REFUSE")
            if not self._ledger_complete(state):
                return Assessment("WITNESS_LEDGER_INCOMPLETE_REFUSE")
            return Assessment("ALIGNED_NO_CLINICAL_ACK")
        if local.records != state.history.records[:len(local.records)]:
            return Assessment("LOCAL_PREFIX_FORK_REFUSE")
        if type(archive) is not journal.Journal:
            return Assessment("INDEPENDENT_ARCHIVE_REQUIRED")
        if archive != state.history or not self._valid_history(archive, state.head):
            return Assessment("ARCHIVE_UNTRUSTED_REFUSE")
        if not self._ledger_complete(state):
            return Assessment("DECISION_LEDGER_INCOMPLETE_REFUSE")
        return Assessment("CHAIN_VALID_PROVENANCE_UNVERIFIED_HUMAN_GATE")
