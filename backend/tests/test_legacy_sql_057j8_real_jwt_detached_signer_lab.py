"""LOT05.7-J8, 14 standalone adversarial cases: REAL JWT in detached FAKE signer.

The test owns all synthetic key material and pin installation: never an SCM
identity, clinic signer, or clinical data source. Does NOT inherit 21 I tests;
they are independently rerun by the J8 workflow.
"""
from __future__ import annotations

from datetime import timedelta
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
from jose import jwt
from sqlalchemy import text

from backend.tests import test_legacy_sql_057i_real_jwt_wal_worker_lab as i
from backend.tests import test_legacy_sql_057e_real_backupservice_sqlcipher_head as e
from backend.tests.fixtures import lot05j8_real_jwt_separate_signer_lab as j8


class TrueJwtDetachedFakeSignerLab(unittest.TestCase):
    @classmethod
    def _seed_fake_orm(cls):
        e.RealEncryptedBackupServiceLab._seed_fake_orm.__func__(cls)

    @classmethod
    def setUpClass(cls):
        i.SyntheticJwtAndWalWorkerEvidence.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        i.SyntheticJwtAndWalWorkerEvidence.tearDownClass.__func__(cls)

    def setUp(self):
        i.SyntheticJwtAndWalWorkerEvidence.setUp(self)
        self.old_flag = os.environ.get(j8.FLAG)
        os.environ[j8.FLAG] = "1"
        self.temp_j8 = tempfile.TemporaryDirectory(prefix="lot05j8_fake_")
        self.j8_root = Path(self.temp_j8.name)
        self.pin = self.j8_root / "installed-public"
        self.pin.mkdir()
        self.private = Ed25519PrivateKey.generate()
        private_bytes = self.private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        self.public = self.private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        (self.j8_root / "signer-private.fake").write_bytes(private_bytes)
        (self.pin / "trusted-ed25519.fake").write_bytes(self.public)
        (self.pin / "owner.fake").write_text(str(self.fake_owners[0].id), encoding="ascii")

    def tearDown(self):
        try:
            self.temp_j8.cleanup()
            if self.old_flag is None:
                os.environ.pop(j8.FLAG, None)
            else:
                os.environ[j8.FLAG] = self.old_flag
        finally:
            i.SyntheticJwtAndWalWorkerEvidence.tearDown(self)

    def _jwt(self, owner=0):
        return i.SyntheticJwtAndWalWorkerEvidence._jwt(self, owner)

    def subprocess(self, role, request):
        # Never inject a real app key: this key belongs to FAKE SQLCipher users.
        env=dict(os.environ, SECRET_KEY=self.fake_jwt_secret,
                 PYTHONDONTWRITEBYTECODE="1", LOT05J8_REAL_JWT_SIGNER_FAKE_ONLY="1")
        return subprocess.run(
            [sys.executable, "-B", "-m",
             "backend.tests.fixtures.lot05j8_real_jwt_separate_signer_lab",
             role, str(self.j8_root)], input=json.dumps(request),
            capture_output=True, text=True, timeout=40, env=env,
        )

    def signed(self, *, token=None, owner=None):
        principal = self.fake_owners[0].id if owner is None else owner
        result = self.subprocess("sign", {
            "jwt": self._jwt() if token is None else token,
            "owner": principal})
        self.assertEqual(result.returncode, 0, result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data["body"]["owner"], principal)
        self.assertNotIn("public_key", data)
        self.assertNotIn("private_key", data)
        return data

    def denied(self, role, request):
        response=self.subprocess(role, request)
        self.assertNotEqual(response.returncode, 0, response.stdout)
        self.assertIn("J8_DENIED_", response.stderr)
        self.assertNotIn("BEGIN PRIVATE KEY", response.stderr)

    def test_01_true_jwt_guard_and_pinned_verifier_independent_pids(self):
        order=self.signed()
        result=self.subprocess("verify", {"envelope":order})
        self.assertEqual(result.returncode,0,result.stderr)
        body=json.loads(result.stdout)
        self.assertTrue(body["fake_only"] and body["accepted"])
        self.assertEqual(body["owner"], self.fake_owners[0].id)
        self.assertNotEqual(order["signer_pid"], body["worker_pid"])
        self.assertNotEqual(body["worker_pid"], os.getpid())

    def test_02_missing_jwt_denied_before_key_signature(self):
        self.denied("sign", {"jwt":"", "owner":self.fake_owners[0].id})

    def test_03_wrong_jwt_mac_denied(self):
        wrong=jwt.encode({
            "sub":self.fake_owners[0].email,"type":"access",
            "jti":secrets.token_hex(16),"exp":int(time.time())+120},
            secrets.token_urlsafe(32), algorithm=self.auth.ALGORITHM)
        self.denied("sign",{"jwt":wrong,"owner":self.fake_owners[0].id})

    def test_04_expired_real_access_jwt_denied(self):
        expired=jwt.encode({
            "sub":self.fake_owners[0].email,"type":"access",
            "jti":secrets.token_hex(16),"exp":int(time.time())-10},
            self.fake_jwt_secret,algorithm=self.auth.ALGORITHM)
        self.denied("sign",{"jwt":expired,"owner":self.fake_owners[0].id})

    def test_05_real_refresh_jwt_denied(self):
        refresh=self.security.create_refresh_token({"sub":self.fake_owners[0].email})
        self.denied("sign",{"jwt":refresh,"owner":self.fake_owners[0].id})

    def test_06_signed_claim_owner_cannot_override_authenticated_principal(self):
        self.denied("sign",{"jwt":self._jwt(),
                            "owner":self.fake_owners[1].id})

    def test_07_inactive_true_db_user_denied(self):
        with self.engine.begin() as c:
            c.execute(text("UPDATE users SET is_active=0 WHERE id=:u"),
                      {"u":self.fake_owners[0].id})
        try:
            self.denied("sign",{"jwt":self._jwt(),"owner":self.fake_owners[0].id})
        finally:
            with self.engine.begin() as c:
                c.execute(text("UPDATE users SET is_active=1 WHERE id=:u"),
                          {"u":self.fake_owners[0].id})

    def test_08_employee_even_with_settings_permission_denied_by_owner_only(self):
        with self.engine.begin() as c:
            c.execute(text("""UPDATE users SET employer_id=:parent,
                 permissions='{"settings": true}' WHERE id=:u"""),
                 {"parent":self.fake_owners[0].id,"u":self.fake_owners[1].id})
        try:
            self.denied("sign",{"jwt":self._jwt(1),"owner":self.fake_owners[1].id})
        finally:
            with self.engine.begin() as c:
                c.execute(text("UPDATE users SET employer_id=NULL,permissions=NULL WHERE id=:u"),
                          {"u":self.fake_owners[1].id})

    def test_09_wrong_pin_public_key_rejected_not_taken_from_signer(self):
        order=self.signed()
        foreign=Ed25519PrivateKey.generate()
        (self.pin / "trusted-ed25519.fake").write_bytes(
            foreign.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw))
        self.denied("verify",{"envelope":order})

    def test_10_signed_claim_tampering_rejected(self):
        order=self.signed()
        order["body"]["audience"]="REAL_CLINICAL_RESTORE"
        self.denied("verify",{"envelope":order})

    def test_11_replay_denied_across_fresh_verifier_processes(self):
        order=self.signed()
        first=self.subprocess("verify",{"envelope":order})
        self.assertEqual(first.returncode,0,first.stderr)
        self.denied("verify",{"envelope":order})

    def test_12_wrong_worker_owner_pin_denied(self):
        order=self.signed()
        (self.pin / "owner.fake").write_text(str(self.fake_owners[1].id),encoding="ascii")
        self.denied("verify",{"envelope":order})

    def test_13_symlinked_replay_ledger_denied(self):
        order=self.signed()
        alternate=self.j8_root/"fake-other-ledger"
        alternate.write_bytes(b"DISPOSABLE")
        (self.j8_root/"worker-replay.sqlite").symlink_to(alternate)
        self.denied("verify",{"envelope":order})

    def test_14_real_clinical_restore_policy_unconditionally_denies(self):
        from backend.services.legacy_migration_restore_policy_v15 import require_clinical_apply
        order=self.signed()
        self.assertEqual(order["body"]["audience"],j8.AUDIENCE)
        with self.assertRaisesRegex(PermissionError,"CLINICAL_APPLY_DISABLED"):
            require_clinical_apply(owner_id=self.fake_owners[0].id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
