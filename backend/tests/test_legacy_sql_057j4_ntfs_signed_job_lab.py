"""LOT05.7-J4 synthetic path attacks and fake signed/replay job tests only."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from backend.tests.fixtures import lot05j4_signed_job_lab as j4


class J4SignedJobNtfsAdversarialLab(unittest.TestCase):
    def setUp(self):
        self.old = os.environ.get(j4.FLAG)
        os.environ[j4.FLAG] = "1"
        self.addCleanup(self.restore_env)
        self.temp = tempfile.TemporaryDirectory(prefix="lot05j4_fake_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        self.file = self.inputs / "payload.fake"
        self.file.write_bytes(j4.PAYLOAD)
        self.key = bytes(range(32))
        self.now = 1800000000

    def restore_env(self):
        if self.old is None:
            os.environ.pop(j4.FLAG, None)
        else:
            os.environ[j4.FLAG] = self.old

    def sign(self):
        return j4.sign_fake_job(self.root, owner=7, key=self.key, now=self.now)

    def consume(self, env, **kwargs):
        return j4.consume_fake_job(self.root, env, owner=7, key=self.key,
                                   now=self.now + 1, **kwargs)

    def assertDenied(self, fn):
        with self.assertRaises(j4.J4Denied):
            fn()

    def resign(self, value):
        body = value["body"]
        value["mac"] = hmac.new(self.key, j4._canonical(body), hashlib.sha256).hexdigest()
        return value

    def make_directory_link(self, link: Path, target: Path):
        if os.name == "nt":
            out = subprocess.run(["cmd.exe", "/c", "mklink", "/J",
                                  str(link), str(target)],
                                 capture_output=True, text=True)
            if out.returncode != 0:
                self.fail("REAL_WINDOWS_JUNCTION_CREATION_FAILED: " + out.stderr)
            self.assertTrue(link.is_junction())
        else:
            link.symlink_to(target, target_is_directory=True)
            self.assertTrue(link.is_symlink())

    def test_01_valid_fake_signature_verified_once(self):
        env = self.sign()
        self.assertEqual(self.consume(env), j4.PAYLOAD)
        self.assertTrue((self.root / "j4_replays.sqlite").is_file())

    def test_02_replay_denied_even_after_new_sqlite_connection(self):
        env = self.sign()
        self.consume(env)
        self.assertDenied(lambda: self.consume(env))
        self.assertDenied(lambda: j4.consume_fake_job(self.root, env, owner=7,
                          key=self.key, now=self.now + 2))

    def test_03_concurrent_duplicate_nonce_one_winner(self):
        env = self.sign()
        def act(_):
            try:
                self.consume(env)
                return "accepted"
            except j4.J4Denied:
                return "denied"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(act, range(2)))
        self.assertEqual(sorted(results), ["accepted", "denied"])

    def test_04_tampered_owner_or_worker_denied_by_mac(self):
        for field, value in (("owner", 8), ("worker", "REAL_CLINICAL"),
                             ("path", "../patient.db"), ("issued", 0),
                             ("expires", self.now + 100000)):
            with self.subTest(field=field):
                env = copy.deepcopy(self.sign())
                env["body"][field] = value
                self.assertDenied(lambda env=env: self.consume(env))
        self.assertFalse((self.root / "j4_replays.sqlite").exists())

    def test_05_valid_signature_but_wrong_owner_denied(self):
        env = self.sign()
        self.assertDenied(lambda: j4.consume_fake_job(self.root, env, owner=8,
                          key=self.key, now=self.now + 1))

    def test_06_mismatched_key_denied(self):
        env = self.sign()
        self.assertDenied(lambda: j4.consume_fake_job(self.root, env, owner=7,
                          key=os.urandom(32), now=self.now + 1))

    def test_07_expiry_and_not_yet_valid_denied(self):
        env = self.sign()
        for moment in (self.now - 1, self.now + 120, self.now + 9999):
            with self.subTest(moment=moment):
                self.assertDenied(lambda moment=moment: j4.consume_fake_job(
                    self.root, env, owner=7, key=self.key, now=moment))
        self.assertFalse((self.root / "j4_replays.sqlite").exists())

    def test_08_boolean_or_string_owner_denied(self):
        for owner in (None, True, False, 0, -7, "7", 7.0):
            with self.subTest(owner=owner):
                self.assertDenied(lambda owner=owner: j4.sign_fake_job(
                    self.root, owner=owner, key=self.key, now=self.now))
                env = self.sign()
                self.assertDenied(lambda owner=owner: j4.consume_fake_job(
                    self.root, env, owner=owner, key=self.key, now=self.now + 1))

    def test_09_invalid_key_flag_and_root_denied(self):
        os.environ[j4.FLAG] = "0"
        self.assertDenied(self.sign)
        os.environ[j4.FLAG] = "1"
        for key in (None, "not a key", b"x" * 31, bytearray(32)):
            self.assertDenied(lambda key=key: j4.sign_fake_job(
                self.root, owner=7, key=key, now=self.now))
        wrong_root = Path(tempfile.gettempdir()) / "not_j4_clinical"
        self.assertDenied(lambda: j4.sign_fake_job(
            wrong_root, owner=7, key=self.key, now=self.now))

    def test_10_content_swap_after_signing_denied(self):
        env = self.sign()
        self.file.write_bytes(b"NOT_AN_AUTHORIZED_FAKE_PAYLOAD")
        self.assertDenied(lambda: self.consume(env))
        self.assertFalse((self.root / "j4_replays.sqlite").exists())

    def test_11_regular_hardlink_from_sibling_denied(self):
        twin = self.root / "another-fake-link.bin"
        os.link(self.file, twin)
        self.assertGreaterEqual(self.file.stat().st_nlink, 2)
        self.assertDenied(lambda: j4.safe_fake_read(self.root))

    def test_12_link_to_external_fake_file_denied(self):
        dest = self.root / "target.fake"
        dest.write_bytes(j4.PAYLOAD)
        self.file.unlink()
        self.file.symlink_to(dest)
        self.assertDenied(lambda: j4.safe_fake_read(self.root))

    def test_13_real_windows_junction_or_posix_directory_symlink_denied(self):
        alternate = self.root / "alternate-inputs"
        alternate.mkdir()
        (alternate / "payload.fake").write_bytes(j4.PAYLOAD)
        self.file.unlink()
        self.inputs.rmdir()
        self.make_directory_link(self.inputs, alternate)
        self.assertDenied(lambda: j4.safe_fake_read(self.root))
        # On Windows rmdir deletes a junction rather than recursively
        # deleting the linked target; never follow it with shutil.rmtree.
        self.inputs.rmdir() if os.name == "nt" else self.inputs.unlink()
        self.inputs.mkdir()
        self.file.write_bytes(j4.PAYLOAD)

    def test_14_race_swapping_regular_file_after_path_validation_denied(self):
        def attack():
            parked = self.inputs / "parked.fake"
            self.file.rename(parked)
            self.file.write_bytes(j4.PAYLOAD)  # content identical, file identity changed
        self.assertDenied(lambda: j4.safe_fake_read(self.root, attack_hook=attack))

    def test_15_race_replacing_parent_with_reparse_denied(self):
        alternate = self.root / "alternate-inputs"
        alternate.mkdir()
        (alternate / "payload.fake").write_bytes(j4.PAYLOAD)
        def attack():
            self.inputs.rename(self.root / "inputs-parked")
            self.make_directory_link(self.inputs, alternate)
        self.assertDenied(lambda: j4.safe_fake_read(self.root, attack_hook=attack))
        self.inputs.rmdir() if os.name == "nt" else self.inputs.unlink()
        (self.root / "inputs-parked").rename(self.inputs)

    def test_16_missing_payload_denied(self):
        self.file.unlink()
        self.assertDenied(lambda: j4.safe_fake_read(self.root))

    def test_17_signed_claim_with_correct_mac_but_wrong_worker_denied(self):
        env = self.sign()
        env["body"]["worker"] = "OTHER_FAKE_WORKER"
        self.resign(env)
        self.assertDenied(lambda: self.consume(env))

    def test_18_signed_claim_with_correct_mac_but_invalid_ttl_denied(self):
        env = self.sign()
        env["body"]["expires"] = self.now + 5000
        self.resign(env)
        self.assertDenied(lambda: self.consume(env))

    def test_19_replay_ledger_symlink_denied(self):
        ledger = self.root / "j4_replays.sqlite"
        other = self.root / "other-fake-ledger"
        other.write_bytes(b"FAKE_LEDGER")
        ledger.symlink_to(other)
        self.assertDenied(lambda: self.consume(self.sign()))

    def test_20_corrupted_persisted_nonce_ledger_denied(self):
        (self.root / "j4_replays.sqlite").write_bytes(b"NOT_SQLITE")
        self.assertDenied(lambda: self.consume(self.sign()))

    def test_21_no_clinical_files_created(self):
        self.consume(self.sign())
        for path in ("clinical_vault.db", "license_vault.bin", "media",
                     "patients.db", "backup-active.db"):
            self.assertFalse((self.root / path).exists())

    def test_22_bad_signature_envelope_and_nonce_denied(self):
        original = self.sign()
        for env in (None, [], {}, {"body": original["body"]},
                    {"body": original["body"], "mac": "0"*64, "extra": True}):
            self.assertDenied(lambda env=env: self.consume(env))
        self.assertDenied(lambda: j4.sign_fake_job(
            self.root, owner=7, key=self.key, now=self.now, nonce="../BAD"))
        self.assertFalse((self.root / "j4_replays.sqlite").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
