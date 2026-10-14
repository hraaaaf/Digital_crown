"""LOT06-M volatile decision/receipt and archive-evidence model (LAB ONLY).

An in-process dictionary is NOT an independent authority, durable transaction,
persistent idempotency ledger, cryptographic receipt, or recovery approval.
Never use this module to approve a patient upload or to repair a physical spool.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import re

from . import fork_lab as fork
from . import journal_lab as journal


class WitnessLabError(RuntimeError):
    """Fixed diagnostic codes: no media, keys, patient or scope in errors."""


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


def _fail(code: str) -> None:
    raise WitnessLabError(code)


def _request_digest(draft: fork.Draft) -> str:
    """Digest the *entire* synthetic proposal, not only a caller's claim."""
    if (type(draft) is not fork.Draft
            or type(draft.candidate) is not journal.Journal
            or type(draft.candidate.records) is not tuple
            or not 2 <= len(draft.candidate.records) <= 256
            or type(draft.expected) is not journal.TrustedAnchor
            or type(draft.next_anchor) is not journal.TrustedAnchor):
        _fail("PROPOSAL_INVALID")
    h = hashlib.sha256(b"DC06M|synthetic-proposal|v1\0")
    try:
        anchors = (
            draft.expected.sequence, draft.expected.mac,
            draft.next_anchor.sequence, draft.next_anchor.mac,
        )
        data = json.dumps(anchors, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        h.update(len(data).to_bytes(4, "big") + data)
        for record in draft.candidate.records:
            if type(record) is not journal.Record:
                _fail("PROPOSAL_INVALID")
            # 06-K's deterministic manifest includes both image byte digests.
            fields = [record.sequence, record.previous_mac, record.mac]
            data = json.dumps(fields, separators=(",", ":"), ensure_ascii=True).encode("ascii")
            manifest = journal._manifest(record.snapshot)
            for part in (data, manifest):
                h.update(len(part).to_bytes(4, "big") + part)
    except (journal.JournalLabError, ValueError, TypeError,
            AttributeError, OverflowError, UnicodeError):
        _fail("PROPOSAL_INVALID")
    return h.hexdigest()


def _same(a: journal.TrustedAnchor, b: journal.TrustedAnchor) -> bool:
    return (type(a) is journal.TrustedAnchor and type(b) is journal.TrustedAnchor
            and type(a.sequence) is int and type(b.sequence) is int
            and type(a.mac) is str and type(b.mac) is str
            and a.sequence == b.sequence and hmac.compare_digest(a.mac, b.mac))


class VolatileDecisionWitness:
    """Serial model only: CAS and receipt ledger updated as one Python call.

    The state can be cloned, reset or forged by Python code. This is NOT an
    OS-atomic transaction or a physically trustworthy witness.
    """

    def __init__(self, genesis: journal.Journal,
                 anchor: journal.TrustedAnchor, *, authority_id: str,
                 epoch: str, opaque_scope: str, journal_key: bytes,
                 legacy_key: bytes, keys: dict):
        if (type(authority_id) is not str
                or not re.fullmatch(r"[a-zA-Z0-9._-]{1,64}", authority_id)
                or type(epoch) is not str
                or not re.fullmatch(r"[a-zA-Z0-9._-]{1,64}", epoch)
                or type(opaque_scope) is not str
                or not re.fullmatch(r"[0-9a-f]{32}", opaque_scope)):
            _fail("IDENTITY_INVALID")
        self._authority = fork.VolatileAuthority(
            genesis, anchor, journal_key=journal_key, legacy_key=legacy_key,
            keys=keys
        )
        self._authority_id = authority_id
        self._epoch = epoch
        self._opaque_scope = opaque_scope
        self._decisions: dict[str, Receipt] = {}

    def _identity(self, epoch: str) -> None:
        if type(epoch) is not str or not hmac.compare_digest(epoch, self._epoch):
            _fail("EPOCH_REFUSED")

    @staticmethod
    def _operation(operation_id: str) -> None:
        if (type(operation_id) is not str
                or not re.fullmatch(r"[0-9a-f]{32}", operation_id)
                or operation_id == "0" * 32):
            _fail("OPERATION_ID_INVALID")

    def observe(self, *, epoch: str) -> journal.TrustedAnchor:
        self._identity(epoch)
        return self._authority.observe()

    def decide(self, draft: fork.Draft, *, operation_id: str,
               epoch: str) -> Receipt:
        """Accept one synthetic CAS; retry of *identical* op returns receipt.

        Physical design MUST persist CAS + operation_id->payload->receipt in
        ONE atomic authority transaction before acknowledging anything.
        """
        self._identity(epoch)
        self._operation(operation_id)
        digest = _request_digest(draft)
        previous = self._decisions.get(operation_id)
        if previous is not None:
            if not hmac.compare_digest(previous.request_digest, digest):
                _fail("IDEMPOTENCY_CONFLICT")
            return previous  # Old receipt does NOT assert current head.
        try:
            head = self._authority.compare_and_swap(draft)
        except fork.ForkLabError as exc:
            if str(exc) in {"STALE_FORK", "FORK_PARENT_MISMATCH"}:
                _fail("STALE_FORK")
            _fail("PROPOSAL_REFUSED")
        receipt = Receipt(operation_id, digest, self._authority_id,
                          self._opaque_scope, self._epoch,
                          draft.expected, head)
        self._decisions[operation_id] = receipt
        return receipt

    def lookup(self, draft: fork.Draft, *, operation_id: str,
               epoch: str) -> Receipt | None:
        """Read simulated decision by (epoch, op_id, request body).

        An absent result is NOT proof an in-flight request cannot arrive.
        Retry, if permitted, with exactly the same id and body.
        """
        self._identity(epoch)
        self._operation(operation_id)
        digest = _request_digest(draft)
        previous = self._decisions.get(operation_id)
        if previous is not None and not hmac.compare_digest(
                previous.request_digest, digest):
            _fail("IDEMPOTENCY_CONFLICT")
        return previous

    def lost_reply(self, local: journal.Journal | None,
                   draft: fork.Draft, *, operation_id: str,
                   epoch: str) -> Assessment:
        """Observe after a lost reply. NEVER finalize or commit local data."""
        previous = self.lookup(draft, operation_id=operation_id, epoch=epoch)
        head = self.observe(epoch=epoch)
        if previous is None:
            if _same(draft.expected, head):
                return Assessment("UNKNOWN_RETRY_SAME_OP_ONLY")
            return Assessment("UNDECIDED_STALE_HEAD_REFUSE")
        if not _same(previous.after, head):
            return Assessment("OLD_DECISION_RECHECK_CURRENT_HEAD")
        if type(local) is journal.Journal and local == draft.candidate:
            try:
                self._authority.recover(local)
            except fork.ForkLabError:
                return Assessment("LOCAL_INVALID_REFUSE")
            return Assessment("DECIDED_LOCAL_REVIEW_REQUIRED")
        return Assessment("DECIDED_NOT_FINALIZED")

    def assess_archive(self, local: journal.Journal | None,
                       archive: journal.Journal | None, *,
                       epoch: str) -> Assessment:
        """Evidence classifier: even complete evidence REQUIRES human gate.

        No archive is written or restored. Missing local journal cannot prove
        which prior genesis/state was authoritative; fail closed.
        """
        self._identity(epoch)
        head = self._authority.observe()
        if (type(local) is not journal.Journal or
                type(local.records) is not tuple or
                not 1 <= len(local.records) <= 256):
            return Assessment("LOCAL_EVIDENCE_MISSING")
        if len(local.records) > head.sequence:
            return Assessment("LOCAL_AHEAD_REFUSE")
        if len(local.records) == head.sequence:
            try:
                self._authority.recover(local)
            except fork.ForkLabError:
                return Assessment("LOCAL_DIVERGENCE_REFUSE")
            return Assessment("ALIGNED_NO_CLINICAL_ACK")
        if type(archive) is not journal.Journal:
            return Assessment("INDEPENDENT_ARCHIVE_REQUIRED")
        try:
            self._authority.recover(archive)  # 06-K HMAC + 06-J AEAD + head
        except (fork.ForkLabError, TypeError, AttributeError):
            return Assessment("ARCHIVE_UNTRUSTED_REFUSE")
        if local.records != archive.records[:len(local.records)]:
            return Assessment("LOCAL_PREFIX_FORK_REFUSE")
        # Every missing suffix event must correspond to one decision in this
        # volatile ledger. A count or a single final MAC alone is insufficient.
        for sequence in range(len(local.records) + 1, head.sequence + 1):
            before = archive.records[sequence - 2]
            after = archive.records[sequence - 1]
            matching = [
                receipt for receipt in self._decisions.values()
                if receipt.after.sequence == sequence
                and receipt.epoch == self._epoch
                and _same(receipt.before,
                          journal.TrustedAnchor(before.sequence, before.mac))
                and _same(receipt.after,
                          journal.TrustedAnchor(after.sequence, after.mac))
            ]
            if len(matching) != 1:
                return Assessment("DECISION_LEDGER_INCOMPLETE_REFUSE")
        # The caller-provided archive has NO independent provenance proof.
        return Assessment("CHAIN_VALID_PROVENANCE_UNVERIFIED_HUMAN_GATE")
