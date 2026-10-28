"""TEST-ONLY backup/restore and rollback detection over the DR04 synthetic ledger.

This does NOT enable guarded LAB transfer on persistent databases. A witness
outside the restored snapshot detects stale SQLCipher rollback *only when its
key and newest value remain trusted and outside attacker control*. No hardware
security, third-party custody, power-fail, production backup or retention proof.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import sys
import uuid

from tools.imaging_gateway.qa_durable_receipt_restart_lab import (
    TENANT, PATIENT, CAPTURE, DEVICE, RECEIPT, REASON,
    _open, _png, _store, _blob, _assert_integrity, _require_key,
)
from backend.services.clinical_asset_storage import _decrypt_payload

NEXT_CAPTURE = "synthetic-DR-restore-v2"
NEXT_RECEIPT = "SYNTH-DR-RECEIPT-02"
CHECKPOINT_DDL = (
    "CREATE TABLE IF NOT EXISTS synthetic_checkpoint "
    "(id INTEGER PRIMARY KEY CHECK(id=1), epoch INTEGER NOT NULL)"
)


class WitnessRejected(RuntimeError):
    pass


def _witness_path(root: Path) -> Path:
    # Crucial: OUTSIDE root and outside any file/Media snapshot.
    return root.parent / "independent-test-witness.json"


def _witness_key() -> bytes:
    return bytes.fromhex(_require_key("DC06B_TEST_WITNESS_KEY"))


def _mac(payload: dict) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(_witness_key(), data, hashlib.sha256).hexdigest()


def _ledger_fingerprint(con) -> str:
    # Deterministic snapshot of the exact receipt, audit, and outbox rows.
    all_rows = {}
    for table in ("synthetic_receipts", "synthetic_audit", "synthetic_outbox"):
        all_rows[table] = con.execute(
            "SELECT * FROM " + table + " ORDER BY 1,2"
        ).fetchall()
    raw = json.dumps(all_rows, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def _epoch(con) -> int:
    row = con.execute(
        "SELECT epoch FROM synthetic_checkpoint WHERE id=1"
    ).fetchone()
    if row is None or not isinstance(row[0], int) or row[0] < 1:
        raise WitnessRejected("EPOCH_MISSING")
    return row[0]


def _write_witness(root: Path, con) -> None:
    # Commit SQL *before* publishing witness. If witness publication fails,
    # the next read must fail-closed rather than silently lower the epoch.
    data = {"epoch": _epoch(con), "fingerprint": _ledger_fingerprint(con)}
    document = {**data, "hmac": _mac(data)}
    path = _witness_path(root)
    temporary = path.with_name("." + uuid.uuid4().hex + ".tmp")
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(document, handle, sort_keys=True, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_witness(root: Path) -> dict:
    try:
        value = json.loads(_witness_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise WitnessRejected("WITNESS_MISSING_OR_INVALID") from exc
    if not isinstance(value, dict) or set(value) != {"epoch", "fingerprint", "hmac"}:
        raise WitnessRejected("WITNESS_FORMAT_INVALID")
    material = {"epoch": value["epoch"], "fingerprint": value["fingerprint"]}
    if not isinstance(value["epoch"], int) or type(value["epoch"]) is bool:
        raise WitnessRejected("WITNESS_EPOCH_INVALID")
    if not isinstance(value["fingerprint"], str) or not isinstance(value["hmac"], str):
        raise WitnessRejected("WITNESS_FIELDS_INVALID")
    if not hmac.compare_digest(_mac(material), value["hmac"]):
        raise WitnessRejected("WITNESS_AUTHENTICATION_FAILED")
    return material


def _check(root: Path, con, expected_epoch: int) -> None:
    # Authenticate the external witness BEFORE inspecting the DB state.
    witness = _read_witness(root)
    actual = _epoch(con)
    if actual < witness["epoch"]:
        raise WitnessRejected("BACKUP_ROLLBACK_DETECTED")
    if actual > witness["epoch"]:
        raise WitnessRejected("WITNESS_BEHIND_DATABASE")
    if _ledger_fingerprint(con) != witness["fingerprint"]:
        raise WitnessRejected("RECEIPT_SET_MISMATCH")
    if actual != expected_epoch:
        raise WitnessRejected("UNEXPECTED_CHECKPOINT_EPOCH")
    receipts = con.execute(
        "SELECT receipt_id,asset_id,patient,digest,size FROM synthetic_receipts "
        "WHERE tenant=? AND device=? ORDER BY asset_id", (TENANT, DEVICE)
    ).fetchall()
    assert len(receipts) == expected_epoch
    expected = [(RECEIPT, 1, _png((15, 45, 75)))]
    if expected_epoch == 2:
        expected.append((NEXT_RECEIPT, 2, _png((95, 110, 140))))
    for (rid, aid, patient, digest, size), (expected_rid, expected_id, content) in zip(
        receipts, expected, strict=True
    ):
        assert rid == expected_rid and aid == expected_id and patient == PATIENT
        assert digest == hashlib.sha256(content).hexdigest() and size == len(content)
        raw = _blob(root, content).read_bytes()
        assert raw.startswith(b"DCM1") and content not in raw
        assert _decrypt_payload(raw, TENANT, digest) == content
        assert con.execute(
            "SELECT event,patient_only_reason FROM synthetic_audit WHERE receipt_id=?",
            (rid,)
        ).fetchone() == ("LAB_ACQUISITION_COMMITTED", REASON)
        assert con.execute(
            "SELECT event FROM synthetic_outbox WHERE receipt_id=?", (rid,)
        ).fetchone() == ("LAB_MEDIA_READY",)
    assert con.execute("SELECT COUNT(*) FROM synthetic_audit").fetchone()[0] == expected_epoch
    assert con.execute("SELECT COUNT(*) FROM synthetic_outbox").fetchone()[0] == expected_epoch
    assert (root / "isolated-ledger.db").read_bytes()[:16] != b"SQLite format 3\x00"


def run(root: Path, phase: str) -> int:
    # Reuses actual DR04 SQLCipher and C2 AES-GCM helpers, no separate fake cipher.
    os.environ["CABINET_MASTER_KEY_HEX"] = _require_key("DC06B_TEST_MEDIA_KEY")
    if phase == "tamper-witness":
        path = _witness_path(root)
        document = json.loads(path.read_text(encoding="utf-8"))
        document["hmac"] = "0" * 64 if document["hmac"] != "0" * 64 else "1" * 64
        path.write_text(json.dumps(document), encoding="utf-8")
        print("SYNTHETIC_WITNESS_TAMPERED")
        return 0

    with _open(root) as con:
        if phase == "checkpoint-one":
            _assert_integrity(root, con)  # real DR04 proof must already exist
            con.execute(CHECKPOINT_DDL)
            con.execute("INSERT INTO synthetic_checkpoint VALUES(1,1)")
            con.commit()
            _write_witness(root, con)
            _check(root, con, 1)
            print("BACKUP_V1_INDEPENDENT_WITNESS_COMMITTED")
        elif phase == "advance-two":
            _check(root, con, 1)
            content = _png((95, 110, 140))
            digest = _store(root, content)
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO synthetic_receipts VALUES(?,?,?,?,?,?,?,?)",
                (TENANT, DEVICE, NEXT_CAPTURE, NEXT_RECEIPT,
                 2, PATIENT, digest, len(content)),
            )
            con.execute(
                "INSERT INTO synthetic_audit VALUES(?,?,?)",
                (NEXT_RECEIPT, "LAB_ACQUISITION_COMMITTED", REASON),
            )
            con.execute(
                "INSERT INTO synthetic_outbox VALUES(?,?)",
                (NEXT_RECEIPT, "LAB_MEDIA_READY"),
            )
            con.execute("UPDATE synthetic_checkpoint SET epoch=2 WHERE id=1")
            con.commit()
            _write_witness(root, con)
            _check(root, con, 2)
            print("BACKUP_V2_NEW_SQL_RECEIPT_AND_WITNESS_COMMITTED")
        elif phase == "verify-one":
            _check(root, con, 1)
            print("RESTORED_BACKUP_V1_VALID_WITH_MATCHING_WITNESS")
        elif phase == "verify-two":
            _check(root, con, 2)
            print("RESTORED_BACKUP_V2_VALID_WITH_INDEPENDENT_WITNESS")
        elif phase == "expect-rollback":
            try:
                _check(root, con, 2)
            except WitnessRejected as exc:
                if str(exc) != "BACKUP_ROLLBACK_DETECTED":
                    raise
                print("STALE_ENCRYPTED_BACKUP_BLOCKED_BY_EXTERNAL_WITNESS")
                return 0
            raise AssertionError("OLD_BACKUP_NOT_DETECTED")
        elif phase == "expect-tamper":
            try:
                _check(root, con, 2)
            except WitnessRejected as exc:
                if str(exc) != "WITNESS_AUTHENTICATION_FAILED":
                    raise
                print("TAMPERED_HMAC_WITNESS_REJECTED")
                return 0
            raise AssertionError("WITNESS_TAMPER_NOT_DETECTED")
        elif phase == "expect-wrong-witness-key":
            try:
                _check(root, con, 2)
            except WitnessRejected as exc:
                if str(exc) != "WITNESS_AUTHENTICATION_FAILED":
                    raise
                print("WRONG_WITNESS_KEY_REJECTED")
                return 0
            raise AssertionError("WRONG_WITNESS_KEY_ACCEPTED")
        else:
            raise AssertionError("UNKNOWN_BACKUP_TEST_PHASE")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phase", required=True, choices=(
        "checkpoint-one", "advance-two", "verify-one", "verify-two",
        "expect-rollback", "tamper-witness", "expect-tamper",
        "expect-wrong-witness-key",
    ))
    options = parser.parse_args()
    try:
        sys.exit(run(options.root, options.phase))
    except Exception as exc:
        print("SYNTHETIC_BACKUP_RESTORE_REJECTED", type(exc).__name__, file=sys.stderr)
        sys.exit(2)
