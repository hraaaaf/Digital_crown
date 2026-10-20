"""J10D CI-only transactional fake witness: no independence or clinical GO."""
from concurrent.futures import ThreadPoolExecutor
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

FIXTURES=Path(__file__).resolve().parent/"fixtures"
sys.path.insert(0,str(FIXTURES))
import lot05j10d_fake_offhost_witness_store as mock
import lot05j10d_external_witness_gate as gate


class FakeRemoteWitnessLab(unittest.TestCase):
    def setUp(self):
        self.sandbox=tempfile.TemporaryDirectory(prefix="j10d_offhost_fake_")
        self.addCleanup(self.sandbox.cleanup)
        self.root=Path(self.sandbox.name)
        self.db=self.root/"witness-off-ledger.fake.sqlite"
        self.device="DC-J10D-FAKE-DEVICE"
        self.signer=Ed25519PrivateKey.generate()
        self.public=self.signer.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        mock.provision_fake_state(self.db,self.device)
        self.witness=mock.FakeWitness(self.db,self.signer)
        self.context=dict(
            device=self.device,challenge="a"*32,ledger_id="b"*24,
            signer_sha256="c"*64,consumer_sha256="d"*64,
            presented_checkpoint=0,now=1800000100,
        )

    def issue(self, **updates):
        return self.witness.issue(**dict(self.context,**updates))

    def test_01_unique_receipt_signed_but_product_must_deny(self):
        status,receipt=self.issue()
        self.assertEqual(status,"DENY_J10D_FAKE_REMOTE_FAKE_RECEIPT_ISSUED_NO_PRODUCT_AUTHORITY")
        self.assertEqual(self.witness.checkpoint(self.device),1)
        self.assertEqual(gate.evaluate_fake_witness(
            receipt,raw_fake_public_key=self.public,
            expected_device=self.device,expected_challenge="a"*32,
            expected_ledger_id="b"*24,expected_signer_sha256="c"*64,
            expected_consumer_sha256="d"*64,
            last_externally_confirmed_checkpoint=0,now=self.context["now"]),
            "DENY_J10D_WITNESS_CRYPTO_VALID_FAKE_ROOT_IS_NOT_INDEPENDENT")
        self.assertEqual(gate.product_readiness(receipt),"DENY_J10D_WITNESS_EXTERNAL_AUTHORITY_NOT_ENROLLED")
        print("J10D_FAKE_REMOTE_SIGNED_RECEIPT_STILL_PRODUCT_DENY_PASS")

    def test_02_rolled_back_client_checkpoint_denied(self):
        self.issue()
        result,receipt=self.issue(challenge="e"*32,presented_checkpoint=0)
        self.assertEqual(result,"DENY_J10D_FAKE_REMOTE_CHECKPOINT_MISMATCH")
        self.assertIsNone(receipt)
        self.assertEqual(self.witness.checkpoint(self.device),1)
        print("J10D_FAKE_OFF_LEDGER_CLIENT_ROLLBACK_DENIED_PASS")

    def test_03_identical_request_nonce_denied_even_with_current_counter(self):
        self.issue()
        result,receipt=self.issue(presented_checkpoint=1)
        self.assertEqual(result,"DENY_J10D_FAKE_REMOTE_CHALLENGE_REPLAY")
        self.assertIsNone(receipt)

    def test_04_distinct_fresh_request_advances_one(self):
        self.issue()
        status,receipt=self.issue(challenge="e"*32,presented_checkpoint=1)
        self.assertEqual(receipt["payload"]["checkpoint"],2)
        self.assertEqual(self.witness.checkpoint(self.device),2)
        self.assertTrue(status.endswith("NO_PRODUCT_AUTHORITY"))

    def test_05_concurrent_same_checkpoint_only_one_commit(self):
        challenges=[format(n,"032x") for n in range(10,18)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda ch:self.issue(challenge=ch),challenges))
        self.assertEqual(sum(receipt is not None for _,receipt in results),1)
        self.assertEqual(self.witness.checkpoint(self.device),1)
        self.assertEqual(sum(status.endswith("CHECKPOINT_MISMATCH") for status,_ in results),7)
        print("J10D_FAKE_REMOTE_SQLITE_SINGLE_ADVANCE_CONCURRENCY_PASS")

    def test_06_response_lost_after_commit_does_not_roll_back(self):
        status,receipt=self.issue(inject_lost_response=True)
        self.assertEqual(status,"DENY_J10D_FAKE_REMOTE_RESPONSE_LOST_AFTER_COMMIT")
        self.assertIsNone(receipt)
        self.assertEqual(self.witness.checkpoint(self.device),1)
        result,again=self.issue()
        self.assertEqual(result,"DENY_J10D_FAKE_REMOTE_CHECKPOINT_MISMATCH")
        self.assertIsNone(again)
        print("J10D_FAKE_REMOTE_LOST_ACK_DOES_NOT_REUSE_CHECKPOINT_PASS")

    def test_07_restart_simulated_witness_from_same_store(self):
        self.issue()
        restarted=mock.FakeWitness(self.db,self.signer)
        self.assertEqual(restarted.checkpoint(self.device),1)
        code,receipt=restarted.issue(**dict(self.context,challenge="e"*32,
                                             presented_checkpoint=0))
        self.assertEqual(code,"DENY_J10D_FAKE_REMOTE_CHECKPOINT_MISMATCH")
        self.assertIsNone(receipt)

    def test_08_absent_witness_store_not_silently_recreated(self):
        self.db.unlink()
        self.assertIsNone(self.witness.checkpoint(self.device))
        code,receipt=self.issue()
        self.assertEqual(code,"DENY_J10D_FAKE_REMOTE_STATE_UNAVAILABLE")
        self.assertIsNone(receipt)
        self.assertFalse(self.db.exists())

    def test_09_double_enrolment_rejected_no_reset(self):
        self.issue()
        with self.assertRaises(FileExistsError):
            mock.provision_fake_state(self.db,self.device)
        self.assertEqual(self.witness.checkpoint(self.device),1)

    def test_10_unenrolled_device_denied(self):
        code,receipt=self.issue(device="DIFFERENT-FAKE-DEVICE")
        self.assertEqual(code,"DENY_J10D_FAKE_REMOTE_NOT_ENROLLED")
        self.assertIsNone(receipt)

    def test_11_malformed_request_and_boolean_checkpoint_fail(self):
        for kwargs in [dict(challenge="bad"),dict(ledger_id="../"),
                       dict(presented_checkpoint=True),
                       dict(presented_checkpoint=-1),dict(now=True),
                       dict(signer_sha256="not-a-digest")]:
            with self.subTest(kwargs=kwargs):
                code,receipt=self.issue(**kwargs)
                self.assertEqual(code,"DENY_J10D_FAKE_REMOTE_INVALID_REQUEST")
                self.assertIsNone(receipt)
        self.assertEqual(self.witness.checkpoint(self.device),0)

    def test_13_full_fake_authority_database_restore_is_not_antirollback(self):
        # NEGATIVE COUNTEREXAMPLE: an Administrator snapshots the SAME-HOST
        # fake witness state before commitment, then restores the snapshot.
        # A newly issued checkpoint can repeat despite valid signatures.
        # It MUST NOT imply independent rollback protection or a product GO.
        snapshot=self.root/"fake-authority-before-commit.snapshot"
        shutil.copyfile(self.db,snapshot)
        first_status,first_receipt=self.issue()
        self.assertIsNotNone(first_receipt)
        self.assertEqual(first_receipt["payload"]["checkpoint"],1)
        shutil.copyfile(snapshot,self.db)
        self.assertEqual(self.witness.checkpoint(self.device),0)
        second_status,second_receipt=self.issue(challenge="f"*32)
        self.assertIsNotNone(second_receipt)
        self.assertEqual(second_receipt["payload"]["checkpoint"],1)
        self.assertEqual(self.witness.checkpoint(self.device),1)
        self.assertTrue(first_status.endswith("NO_PRODUCT_AUTHORITY"))
        self.assertTrue(second_status.endswith("NO_PRODUCT_AUTHORITY"))
        self.assertEqual(gate.product_readiness(second_receipt),
                         "DENY_J10D_WITNESS_EXTERNAL_AUTHORITY_NOT_ENROLLED")
        print("J10D_FAKE_REMOTE_COMPLETE_STATE_ROLLBACK_UNPROTECTED_PRODUCT_NO_GO_PASS")

    def test_12_separate_worker_process_checkpoint_kept_and_no_go(self):
        key=self.root/"ci-generated-only.fake.key"
        key.write_bytes(self.signer.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()))
        command=[sys.executable,str(FIXTURES/"lot05j10d_fake_offhost_witness_store.py"),
                 "--j10d-fake-worker",str(self.db),str(key),self.device,
                 "a"*32,"b"*24,"c"*64,"d"*64,"0",str(self.context["now"])]
        first=subprocess.run(command,capture_output=True,text=True,timeout=10)
        self.assertEqual(first.returncode,0,first.stderr)
        data=json.loads(first.stdout)
        self.assertEqual(data["receipt"]["payload"]["checkpoint"],1)
        self.assertIn("NO_PRODUCT_AUTHORITY",data["status"])
        second=subprocess.run(command,capture_output=True,text=True,timeout=10)
        self.assertEqual(second.returncode,3,second.stderr)
        denial=json.loads(second.stdout)
        self.assertIsNone(denial["receipt"])
        self.assertEqual(denial["status"],"DENY_J10D_FAKE_REMOTE_CHECKPOINT_MISMATCH")
        self.assertEqual(self.witness.checkpoint(self.device),1)
        self.assertEqual(gate.product_readiness(),"DENY_J10D_WITNESS_EXTERNAL_AUTHORITY_NOT_ENROLLED")
        print("J10D_FAKE_REMOTE_WORKER_PROCESS_RESTART_ROLLBACK_DENIED_PASS")


if __name__=="__main__":
    unittest.main(verbosity=2)
