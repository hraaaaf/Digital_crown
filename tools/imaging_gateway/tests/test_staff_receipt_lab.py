"""Synthetic contract exercise, never clinical confirmations or real server ACKs."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from tools.imaging_gateway.staff_receipt_lab import (
    LabReceiptRejected, SyntheticReceiptLedger,
)


FAKE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
    "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
)


class StaffReceiptContractLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dc06b-synthetic-receipt-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".digitalcrown-ack-contract-lab-only").write_bytes(
            b"DC06B_SYNTHETIC_ACK_CONTRACT_V1\n")
        env = patch.dict(os.environ, {
            "ENVIRONMENT": "test",
            "DIGITALCROWN_ISOLATED_RUNTIME": "true",
            "DC_V15_06_ACK_CONTRACT_LAB": "1",
        })
        env.start()
        self.addCleanup(env.stop)
        self.ledger = SyntheticReceiptLedger(self.root)
        self.token = self.ledger.fixture_staff("cab1", "staff1")
        self.ledger.fixture_station("cab1", "station1")
        self.ledger.fixture_patient("cab1", "patient1")
        self.ledger.fixture_appointment("cab1", "rdv1", "patient1")
        self.digest = self.ledger.fixture_capture(
            "cab1", "capture1", "station1", FAKE_PNG)

    def approve(self, **override):
        args = dict(
            tenant="cab1", staff_id="staff1", staff_token=self.token,
            station_id="station1", capture_id="capture1",
            patient_id="patient1", appointment_id="rdv1",
            digest=self.digest, explicit_staff_action=True,
        )
        args.update(override)
        return self.ledger.approve(**args)

    def test_guard_fails_closed_outside_test_or_marker(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "cabinet"}):
            with self.assertRaisesRegex(LabReceiptRejected, "LAB_DISABLED"):
                self.ledger.inspect("cab1", "capture1")
        with patch.dict(os.environ, {"DC_V15_06_ACK_CONTRACT_LAB": "0"}):
            with self.assertRaisesRegex(LabReceiptRejected, "LAB_DISABLED"):
                SyntheticReceiptLedger(self.root)
        (self.root / ".digitalcrown-ack-contract-lab-only").unlink()
        with self.assertRaisesRegex(LabReceiptRejected, "INVALID_TEMP_LAB_MARKER"):
            self.ledger.inspect("cab1", "capture1")

    def test_no_approval_or_implicit_action_cannot_create_receipt(self):
        with self.assertRaisesRegex(LabReceiptRejected, "NO_EXPLICIT_APPROVAL"):
            self.ledger.commit("a" * 32, staff_token=self.token)
        with self.assertRaisesRegex(LabReceiptRejected, "EXPLICIT_STAFF_ACTION_REQUIRED"):
            self.approve(explicit_staff_action=False)
        self.assertEqual(self.ledger.inspect("cab1", "capture1"),
                         {"receipts": [], "audit": []})

    def test_real_encrypted_ready_hotfolder_remains_unconfirmed_by_lab_receipt(self):
        from tools.imaging_gateway import Config, HotFolder

        incoming = self.root / "synthetic-watch"
        incoming.mkdir()
        image = incoming / "synthetic.png"
        image.write_bytes(FAKE_PNG)
        image.with_name(image.name + ".ready").write_text(json.dumps({
            "version": 1, "size": len(FAKE_PNG),
            "sha256": hashlib.sha256(FAKE_PNG).hexdigest(),
        }), encoding="utf-8")
        agent = HotFolder(Config(
            "cab1", "station1", incoming, self.root / "synthetic-private",
            b"k" * 32, require_ready_manifest=True,
        ))
        self.assertEqual(agent.scan_once()["unstable"], 1)
        self.assertEqual(agent.scan_once()["staged"], 1)
        [item] = agent.items()
        self.assertEqual(agent.read_verified(item["id"]), FAKE_PNG)
        self.assertEqual(item["digest"], self.digest)
        approval = self.approve()
        receipt = self.ledger.commit(approval, staff_token=self.token)
        self.assertEqual(receipt.state, "LAB_RECEIPT_COMMITTED")
        self.assertTrue(receipt.receipt_id.startswith("LAB-"))
        # Not a real transport: the source and real HotFolder ledger NEVER
        # gain patient, upload, confirmation, or another audit event.
        self.assertEqual(agent.items(), [item])
        self.assertEqual(item["state"], "PENDING_CONFIRMATION")
        self.assertEqual(agent.audit(item["id"]), ["PENDING_CONFIRMATION"])
        self.assertEqual(image.read_bytes(), FAKE_PNG)

    def test_committed_receipt_idempotent_after_reopen_and_retry(self):
        approval = self.approve()
        first = self.ledger.commit(approval, staff_token=self.token)
        for _ in range(3):
            self.assertEqual(self.ledger.commit(approval, staff_token=self.token), first)
        reopened = SyntheticReceiptLedger(self.root)
        self.assertEqual(reopened.commit(approval, staff_token=self.token), first)
        self.assertEqual(self.ledger.inspect("cab1", "capture1"), {
            "receipts": [first.receipt_id],
            "audit": ["SYNTHETIC_STAFF_APPROVED", "SYNTHETIC_RECEIPT_COMMITTED"],
        })

    def test_concurrent_same_approval_one_receipt_and_one_commit_audit(self):
        approval = self.approve()
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(
                lambda _i: self.ledger.commit(approval, staff_token=self.token),
                range(12),
            ))
        self.assertEqual(len({x.receipt_id for x in results}), 1)
        self.assertEqual(self.ledger.inspect("cab1", "capture1")["audit"],
                         ["SYNTHETIC_STAFF_APPROVED", "SYNTHETIC_RECEIPT_COMMITTED"])

    def test_failure_after_insert_and_after_audit_rolls_back_both(self):
        approval = self.approve()
        for fault in ("after_receipt", "after_audit"):
            with self.assertRaisesRegex(LabReceiptRejected, "INJECTED_TRANSACTION_ABORT"):
                self.ledger.commit(approval, staff_token=self.token, fail_at=fault)
            self.assertEqual(self.ledger.inspect("cab1", "capture1"), {
                "receipts": [], "audit": ["SYNTHETIC_STAFF_APPROVED"],
            })
        got = self.ledger.commit(approval, staff_token=self.token)
        self.assertEqual(self.ledger.inspect("cab1", "capture1")["receipts"],
                         [got.receipt_id])

    def test_tenant_mismatch_and_cross_patient_rdv_fail_closed(self):
        self.ledger.fixture_patient("cab2", "patient2")
        self.ledger.fixture_appointment("cab2", "rdv2", "patient2")
        for data, reason in [
            ({"tenant": "cab2"}, "STAFF_NOT_AUTHORIZED"),
            ({"patient_id": "patient2"}, "PATIENT_NOT_FOUND"),
            ({"appointment_id": "rdv2"}, "PATIENT_APPOINTMENT_CONFLICT"),
            ({"patient_id": "patient2", "appointment_id": "rdv2"}, "PATIENT_NOT_FOUND"),
        ]:
            with self.subTest(data=data), self.assertRaisesRegex(LabReceiptRejected, reason):
                self.approve(**data)
        self.assertEqual(self.ledger.inspect("cab1", "capture1")["audit"], [])

    def test_wrong_staff_token_and_unverified_digest_are_refused(self):
        for data, reason in [
            ({"staff_token": "fake-token"}, "STAFF_NOT_AUTHORIZED"),
            ({"digest": "f" * 64}, "UNVERIFIED_CAPTURE_BINDING"),
            ({"capture_id": "capture2"}, "UNVERIFIED_CAPTURE_BINDING"),
            ({"station_id": "otherstation"}, "STATION_NOT_AUTHORIZED"),
        ]:
            with self.subTest(data=data), self.assertRaisesRegex(LabReceiptRejected, reason):
                self.approve(**data)
        approved = self.approve()
        with self.assertRaisesRegex(LabReceiptRejected, "STAFF_NOT_AUTHORIZED"):
            self.ledger.commit(approved, staff_token="bad")
        self.assertEqual(self.ledger.inspect("cab1", "capture1")["receipts"], [])

    def test_revocation_or_rdv_reassignment_at_commit_refused(self):
        for revoke in (
            lambda: self.ledger.fixture_patient("cab1", "patient1", active=False),
            lambda: self.ledger.fixture_appointment("cab1", "rdv1", "otherpatient"),
            lambda: self.ledger.fixture_station("cab1", "station1", active=False),
            lambda: self.ledger.fixture_staff("cab1", "staff1", active=False),
        ):
            # Each case starts from an already-approved synthetic action.
            with self.subTest(revoke=revoke):
                self.ledger.fixture_patient("cab1", "patient1")
                self.ledger.fixture_appointment("cab1", "rdv1", "patient1")
                self.ledger.fixture_station("cab1", "station1")
                self.token = self.ledger.fixture_staff("cab1", "staff1")
                approval = self.approve()
                revoke()
                with self.assertRaises(LabReceiptRejected):
                    self.ledger.commit(approval, staff_token=self.token)
                self.assertEqual(self.ledger.inspect("cab1", "capture1")["receipts"], [])

    def test_conflicting_second_approval_for_same_capture_never_changes_first_receipt(self):
        first = self.approve()
        original = self.ledger.commit(first, staff_token=self.token)
        second = self.approve()
        with self.assertRaisesRegex(LabReceiptRejected, "CONFLICTING_CAPTURE_RECEIPT"):
            self.ledger.commit(second, staff_token=self.token)
        self.assertEqual(self.ledger.inspect("cab1", "capture1")["receipts"],
                         [original.receipt_id])
        self.assertEqual(self.ledger.inspect("cab1", "capture1")["audit"].count(
            "SYNTHETIC_RECEIPT_COMMITTED"), 1)

    def test_fixture_capture_cannot_be_rebound_silently(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.ledger.fixture_capture("cab1", "capture1", "station1", b"altered")
        approval = self.approve()
        self.assertEqual(self.ledger.commit(approval, staff_token=self.token).state,
                         "LAB_RECEIPT_COMMITTED")


if __name__ == "__main__":
    unittest.main()
