"""LOT05/J10D FAKE off-ledger witness transactional laboratory, always product DENY.

SQLite is on the SAME CI runner, not an independent provider. Keys and
checkpoint state are controlled by the test Administrator. Never clinical.
"""
import base64
import json
import os
from pathlib import Path
import sqlite3
import sys
from urllib.parse import quote

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import lot05j10d_external_witness_gate as gate

MAX_CHECKPOINT = 2**63 - 2


def _deny(reason):
    return "DENY_J10D_FAKE_REMOTE_" + reason


def _open_existing(path):
    # mode=rw prevents accidental recreation of deleted/corrupt witness state.
    absolute = str(Path(path).absolute()).replace("\\", "/")
    uri = "file:" + quote(absolute, safe="/:") + "?mode=rw"
    conn = sqlite3.connect(uri, uri=True, timeout=3, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=3000")
    return conn


def provision_fake_state(path, device):
    """Explicit CI-only creation; product client must never self-enrol."""
    if not isinstance(device, str) or not device or len(device) > 128 or not device.isascii():
        raise ValueError("invalid fake device")
    path = Path(path)
    # Exclusive create: never silently reset a witness that may be missing.
    with path.open("xb"):
        pass
    try:
        with _open_existing(path) as conn:
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("CREATE TABLE witness (device TEXT PRIMARY KEY, checkpoint INTEGER NOT NULL)")
            conn.execute("CREATE TABLE seen (device TEXT NOT NULL, challenge TEXT NOT NULL, "
                         "PRIMARY KEY(device,challenge))")
            conn.execute("INSERT INTO witness VALUES (?, ?)", (device, 0))
    except Exception:
        path.unlink(missing_ok=True)
        raise


class FakeWitness:
    def __init__(self, db_path, fake_private_key):
        self.db_path = str(db_path)
        self.signer = fake_private_key

    def issue(self, *, device, challenge, ledger_id, signer_sha256,
              consumer_sha256, presented_checkpoint, now,
              inject_lost_response=False):
        """Commit one fake monotonic receipt or return DENY; never ALLOW.

        A transport timeout *after* COMMIT still advances the fake counter.
        Replay after timeout and client-ledger rollback must DENY.
        """
        fields = (device, challenge, ledger_id, signer_sha256, consumer_sha256)
        if (not all(isinstance(x, str) for x in fields) or
            not isinstance(device, str) or not device or not device.isascii() or
            len(device) > 128 or not gate.HEX32.fullmatch(challenge) or
            not gate.HEX24.fullmatch(ledger_id) or
            not gate.HEX64.fullmatch(signer_sha256) or
            not gate.HEX64.fullmatch(consumer_sha256) or
            type(presented_checkpoint) is not int or presented_checkpoint < 0 or
            presented_checkpoint > MAX_CHECKPOINT or
            type(now) is not int or now <= 0):
            return _deny("INVALID_REQUEST"), None
        if not isinstance(self.signer, Ed25519PrivateKey):
            return _deny("SIGNER_UNAVAILABLE"), None
        conn = None
        committed = False
        try:
            conn = _open_existing(self.db_path)
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT checkpoint FROM witness WHERE device=?",
                               (device,)).fetchone()
            if row is None:
                return _deny("NOT_ENROLLED"), None
            remote_checkpoint = row[0]
            if type(remote_checkpoint) is not int or remote_checkpoint < 0 or remote_checkpoint > MAX_CHECKPOINT:
                return _deny("DAMAGED_STATE"), None
            if presented_checkpoint != remote_checkpoint:
                return _deny("CHECKPOINT_MISMATCH"), None
            if conn.execute("SELECT 1 FROM seen WHERE device=? AND challenge=?",
                            (device, challenge)).fetchone() is not None:
                return _deny("CHALLENGE_REPLAY"), None
            value = remote_checkpoint + 1
            payload = dict(
                schema=gate.SCHEMA, device=device, challenge=challenge,
                ledger_id=ledger_id, signer_sha256=signer_sha256,
                consumer_sha256=consumer_sha256, checkpoint=value,
                issued_at=now - 1, expires_at=now + 30,
                decision="DENY_ONLY_LAB",
            )
            raw = gate.canonical_payload(payload)
            signature = self.signer.sign(raw)
            receipt = dict(payload=payload,
                           signature=base64.b64encode(signature).decode("ascii"))
            conn.execute("UPDATE witness SET checkpoint=? WHERE device=? AND checkpoint=?",
                         (value, device, remote_checkpoint))
            if conn.execute("SELECT changes()").fetchone()[0] != 1:
                return _deny("CONCURRENT_MODIFICATION"), None
            conn.execute("INSERT INTO seen(device,challenge) VALUES(?,?)",
                         (device, challenge))
            conn.execute("COMMIT")
            committed = True
            if inject_lost_response:
                return _deny("RESPONSE_LOST_AFTER_COMMIT"), None
            return _deny("FAKE_RECEIPT_ISSUED_NO_PRODUCT_AUTHORITY"), receipt
        except (sqlite3.Error, OSError, ValueError, TypeError):
            return _deny("STATE_UNAVAILABLE"), None
        finally:
            if conn is not None:
                if not committed:
                    try:
                        conn.execute("ROLLBACK")
                    except sqlite3.Error:
                        pass
                conn.close()

    def checkpoint(self, device):
        try:
            with _open_existing(self.db_path) as conn:
                row = conn.execute("SELECT checkpoint FROM witness WHERE device=?",
                                   (device,)).fetchone()
                return None if row is None else row[0]
        except (sqlite3.Error, OSError):
            return None


def worker_cli(argv):
    """CI-only isolated process, no network or product authority."""
    if len(argv) != 10 or argv[0] != "--j10d-fake-worker":
        print(_deny("INVALID_REQUEST"))
        return 3
    _, db_path, key_path, device, challenge, ledger_id, signer_hash, consumer_hash, floor, now = argv
    try:
        # Fake private key resides in disposable CI-controlled temp dir.
        raw = Path(key_path).read_bytes()
        if len(raw) != 32:
            raise ValueError("fake private key length")
        signer = Ed25519PrivateKey.from_private_bytes(raw)
        code, receipt = FakeWitness(db_path, signer).issue(
            device=device, challenge=challenge, ledger_id=ledger_id,
            signer_sha256=signer_hash, consumer_sha256=consumer_hash,
            presented_checkpoint=int(floor), now=int(now))
        print(json.dumps({"status": code, "receipt": receipt},
                         separators=(",", ":"), sort_keys=True))
        return 0 if receipt is not None else 3
    except (OSError, ValueError, TypeError, UnicodeError):
        print(json.dumps({"status": _deny("STATE_UNAVAILABLE"), "receipt": None}))
        return 3


if __name__ == "__main__":
    sys.exit(worker_cli(sys.argv[1:]))
