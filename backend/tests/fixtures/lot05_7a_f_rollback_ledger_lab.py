"""LOT05.7A-F — isolated monotonic-witness replay ledger FUE (LAB ONLY).

This is a disposable test harness, NOT a product replay store.
The witness is injected by the CI test; no independently provisioned publisher
key, TPM, Windows service, signed installer or authenticated issuer exists here.
In product, the witness MUST be independent of the clinic DB, installer caller
and any rollback-capable writable local snapshot. Never use this fixture to
authorize SQL import, consent, rollback or clinical operations.

Safety property modelled: a successful no-op consume requires both an atomic
durable local commit and a strictly advancing external counter. An interruption
between the external advance and local commit fails closed on the next attempt.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Protocol


class LedgerLabDenied(ValueError):
    """Non-sensitive denial; never infer authorization from an exception."""


class IndependentMonotonicWitness(Protocol):
    def current_counter(self, installation_id: str) -> int:
        """Read the authoritative non-rollback-able counter."""

    def compare_and_advance(self, installation_id: str, expected: int) -> int:
        """Atomically advance expected -> expected + 1, or fail."""


class WitnessedReplayLedgerLab:
    """Test-only replay ledger implementing AtomicReplayLedger.consume_once.

    A witness supplied by a requester is NOT independent; the caller must
    establish product trust and durable witness origin separately.
    """

    def __init__(
        self, database_path: Path, installation_id: str,
        witness: IndependentMonotonicWitness,
    ) -> None:
        if type(database_path) is not type(Path(".")) or database_path.is_symlink():
            raise LedgerLabDenied("UNTRUSTED_LEDGER_PATH")
        if not database_path.parent.is_dir() or (
            database_path.exists() and not database_path.is_file()
        ):
            raise LedgerLabDenied("UNTRUSTED_LEDGER_PATH")
        if type(installation_id) is not str or len(installation_id) != 32 or any(
            ch not in "0123456789abcdef" for ch in installation_id
        ):
            raise LedgerLabDenied("INVALID_INSTALLATION")
        if witness is None or not callable(getattr(witness, "current_counter", None)) or not callable(
            getattr(witness, "compare_and_advance", None)
        ):
            raise LedgerLabDenied("NO_INDEPENDENT_WITNESS")
        self._path = database_path
        self._installation_id = installation_id
        self._witness = witness
        try:
            with self._connect() as db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS state("
                    "id INTEGER PRIMARY KEY CHECK(id=1),"
                    "installation_id TEXT NOT NULL, seq INTEGER NOT NULL CHECK(seq>=0))"
                )
                db.execute(
                    "CREATE TABLE IF NOT EXISTS consumed("
                    "namespace TEXT NOT NULL, nonce TEXT NOT NULL,"
                    "PRIMARY KEY(namespace, nonce))"
                )
                db.execute(
                    "INSERT OR IGNORE INTO state(id, installation_id, seq) VALUES(1, ?, 0)",
                    (installation_id,),
                )
                row = db.execute("SELECT installation_id FROM state WHERE id=1").fetchone()
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
        if type(namespace) is not str or not 1 <= len(namespace) <= 384 or any(
            not 33 <= ord(ch) <= 126 for ch in namespace
        ):
            raise LedgerLabDenied("INVALID_NAMESPACE")
        if type(nonce) is not str or len(nonce) != 32 or any(
            ch not in "0123456789abcdef" for ch in nonce
        ):
            raise LedgerLabDenied("INVALID_NONCE")
        if self._path.is_symlink():
            raise LedgerLabDenied("UNTRUSTED_LEDGER_PATH")
        try:
            with self._connect() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT installation_id, seq FROM state WHERE id=1"
                ).fetchone()
                if row is None or row[0] != self._installation_id:
                    raise LedgerLabDenied("INSTALLATION_BINDING_MISMATCH")
                seq = row[1]
                if type(seq) is not int or seq < 0 or seq >= (2**63 - 1):
                    raise LedgerLabDenied("INVALID_SEQUENCE")
                observed = self._witness.current_counter(self._installation_id)
                if type(observed) is not int or observed != seq:
                    raise LedgerLabDenied("INDEPENDENT_WITNESS_MISMATCH")
                if db.execute(
                    "SELECT 1 FROM consumed WHERE namespace=? AND nonce=?",
                    (namespace, nonce),
                ).fetchone():
                    return False
                # External advancement BEFORE local commit intentionally fails
                # closed if the process crashes before the SQLite transaction.
                new_counter = self._witness.compare_and_advance(
                    self._installation_id, seq
                )
                if type(new_counter) is not int or new_counter != seq + 1:
                    raise LedgerLabDenied("INDEPENDENT_WITNESS_ADVANCE_FAILED")
                db.execute(
                    "INSERT INTO consumed(namespace, nonce) VALUES(?, ?)",
                    (namespace, nonce),
                )
                db.execute("UPDATE state SET seq=? WHERE id=1", (new_counter,))
            return True
        except LedgerLabDenied:
            raise
        except (sqlite3.Error, OSError, Exception) as exc:
            # Never convert unavailable or inconsistent authority to approval.
            raise LedgerLabDenied("LEDGER_OR_WITNESS_UNAVAILABLE") from exc
