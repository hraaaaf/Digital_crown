"""LOT05.7A-F: externally witnessed replay journal, isolated LAB ONLY.

This fixture cannot authorize SQL imports or prove product/physical security.
The test witness is injected and runs in CI memory; production MUST use a
separately controlled, authenticated, non-rollback-able installation authority.
The SQLite file and its witness are NOT trusted if both can be replaced by the
same operator. CI does not prove power-loss fsync or real hardware guarantees.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
from typing import Protocol


class LedgerLabDenied(ValueError):
    """Non-sensitive fail-closed denial."""


def genesis_digest(installation_id: str) -> str:
    return hashlib.sha256(
        b"DIGITAL-CROWN-LOT05-WITNESSED-JOURNAL-V1\x00"
        + bytes.fromhex(installation_id)
    ).hexdigest()


def event_digest(previous: str, sequence: int, namespace: str, nonce: str) -> str:
    """Deterministically commit to the complete ordered journal history."""
    payload = (
        bytes.fromhex(previous)
        + sequence.to_bytes(8, "big")
        + len(namespace).to_bytes(2, "big")
        + namespace.encode("ascii")
        + bytes.fromhex(nonce)
    )
    return hashlib.sha256(payload).hexdigest()


class IndependentMonotonicWitness(Protocol):
    def current_checkpoint(self, installation_id: str) -> tuple[int, str]:
        """Return authoritative (counter, journal tip hash)."""

    def compare_and_advance(
        self, installation_id: str, expected_counter: int,
        expected_digest: str, new_digest: str,
    ) -> tuple[int, str]:
        """Atomically bind counter+1 to a new journal digest or fail."""


def _valid_namespace(value: object) -> bool:
    return type(value) is str and 1 <= len(value) <= 384 and all(
        33 <= ord(ch) <= 126 for ch in value
    )


def _valid_nonce(value: object) -> bool:
    return type(value) is str and len(value) == 32 and all(
        ch in "0123456789abcdef" for ch in value
    )


class WitnessedReplayLedgerLab:
    """Disposable SQLite journal; interfaces with AtomicReplayLedger only.

    A test-supplied witness is NOT proof of its genuine independence.
    No launcher, API, clinical importer or product service imports this class.
    """

    def __init__(
        self, database_path: Path, installation_id: str,
        witness: IndependentMonotonicWitness,
    ) -> None:
        if not isinstance(database_path, Path) or database_path.is_symlink():
            raise LedgerLabDenied("UNTRUSTED_LEDGER_PATH")
        if not database_path.parent.is_dir() or (
            database_path.exists() and not database_path.is_file()
        ):
            raise LedgerLabDenied("UNTRUSTED_LEDGER_PATH")
        if type(installation_id) is not str or len(installation_id) != 32 or any(
            ch not in "0123456789abcdef" for ch in installation_id
        ):
            raise LedgerLabDenied("INVALID_INSTALLATION")
        if witness is None or not callable(getattr(witness, "current_checkpoint", None)) or not callable(
            getattr(witness, "compare_and_advance", None)
        ):
            raise LedgerLabDenied("NO_INDEPENDENT_WITNESS")
        self._path = database_path
        self._installation_id = installation_id
        self._witness = witness
        try:
            with closing(self._connect()) as db:
                with db:
                    db.execute(
                        "CREATE TABLE IF NOT EXISTS state("
                        "id INTEGER PRIMARY KEY CHECK(id=1),"
                        "installation_id TEXT NOT NULL, seq INTEGER NOT NULL,"
                        "tip TEXT NOT NULL)"
                    )
                    db.execute(
                        "CREATE TABLE IF NOT EXISTS events("
                        "seq INTEGER PRIMARY KEY, namespace TEXT NOT NULL,"
                        "nonce TEXT NOT NULL, UNIQUE(namespace,nonce))"
                    )
                    db.execute(
                        "INSERT OR IGNORE INTO state(id,installation_id,seq,tip)"
                        " VALUES(1,?,0,?)",
                        (installation_id, genesis_digest(installation_id)),
                    )
                    row = db.execute(
                        "SELECT installation_id FROM state WHERE id=1"
                    ).fetchone()
                    if row != (installation_id,):
                        raise LedgerLabDenied("INSTALLATION_BINDING_MISMATCH")
        except (sqlite3.Error, OSError) as exc:
            raise LedgerLabDenied("LEDGER_UNAVAILABLE") from exc

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self._path), timeout=2)
        try:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA busy_timeout=2000")
        except Exception:
            db.close()
            raise
        return db

    def consume_once(self, namespace: str, nonce: str) -> bool:
        if not _valid_namespace(namespace):
            raise LedgerLabDenied("INVALID_NAMESPACE")
        if not _valid_nonce(nonce):
            raise LedgerLabDenied("INVALID_NONCE")
        if self._path.is_symlink():
            raise LedgerLabDenied("UNTRUSTED_LEDGER_PATH")
        try:
            with closing(self._connect()) as db:
                with db:
                    db.execute("BEGIN IMMEDIATE")
                    row = db.execute(
                        "SELECT installation_id,seq,tip FROM state WHERE id=1"
                    ).fetchone()
                    if row is None or row[0] != self._installation_id:
                        raise LedgerLabDenied("INSTALLATION_BINDING_MISMATCH")
                    sequence, tip = row[1:]
                    if type(sequence) is not int or not 0 <= sequence < 2**63 - 1:
                        raise LedgerLabDenied("INVALID_SEQUENCE")
                    # Recompute the whole lab journal before trusting the local
                    # tip. A modified/deleted nonce cannot be hidden by editing
                    # the SQLite counter to the externally known floor.
                    derived = genesis_digest(self._installation_id)
                    events = db.execute(
                        "SELECT seq,namespace,nonce FROM events ORDER BY seq"
                    ).fetchall()
                    if len(events) != sequence:
                        raise LedgerLabDenied("LEDGER_INTEGRITY_FAILURE")
                    for index, (event_seq, ns, previous_nonce) in enumerate(events, 1):
                        if event_seq != index or not _valid_namespace(ns) or not _valid_nonce(previous_nonce):
                            raise LedgerLabDenied("LEDGER_INTEGRITY_FAILURE")
                        derived = event_digest(derived, index, ns, previous_nonce)
                    if type(tip) is not str or tip != derived:
                        raise LedgerLabDenied("LEDGER_INTEGRITY_FAILURE")
                    observed = self._witness.current_checkpoint(self._installation_id)
                    if type(observed) is not tuple or observed != (sequence, tip):
                        raise LedgerLabDenied("INDEPENDENT_WITNESS_MISMATCH")
                    if db.execute(
                        "SELECT 1 FROM events WHERE namespace=? AND nonce=?",
                        (namespace, nonce),
                    ).fetchone():
                        return False
                    next_tip = event_digest(tip, sequence + 1, namespace, nonce)
                    # Witness advances first. If a crash occurs before durable
                    # local COMMIT, later operations fail closed on mismatch.
                    advanced = self._witness.compare_and_advance(
                        self._installation_id, sequence, tip, next_tip
                    )
                    if type(advanced) is not tuple or advanced != (sequence + 1, next_tip):
                        raise LedgerLabDenied("INDEPENDENT_WITNESS_ADVANCE_FAILED")
                    db.execute(
                        "INSERT INTO events(seq,namespace,nonce) VALUES(?,?,?)",
                        (sequence + 1, namespace, nonce),
                    )
                    db.execute(
                        "UPDATE state SET seq=?,tip=? WHERE id=1",
                        (sequence + 1, next_tip),
                    )
            return True
        except LedgerLabDenied:
            raise
        except Exception as exc:
            # A service/Witness crash, corruption or disk error NEVER grants
            # authorization: no success or silent rollback of witness counter.
            raise LedgerLabDenied("LEDGER_OR_WITNESS_UNAVAILABLE") from exc
