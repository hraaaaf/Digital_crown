"""LOT05.7-J9: test real JWT -> RSA order -> real ephemeral Windows SCM.
Fake SQLCipher principals, temporary service, no production clinical code changes.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from backend.tests import test_legacy_sql_057i_real_jwt_wal_worker_lab as i
from backend.tests import test_legacy_sql_057e_real_backupservice_sqlcipher_head as e

class J9JwtToRealFakeScm(unittest.TestCase):
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
        self.tmp = tempfile.TemporaryDirectory(prefix="lot05j9_fake_")
        self.root = Path(self.tmp.name)
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_bytes = self.key.private_bytes(Encoding.PEM,PrivateFormat.PKCS8,NoEncryption())
        (self.root/"signer-private.pem").write_bytes(private_bytes)
        p = self.key.public_key().public_numbers()
        (self.root/"trusted-rsa-public.fake").write_text(
            base64.b64encode(p.n.to_bytes(256,"big")).decode("ascii")+"\n"+
            base64.b64encode(p.e.to_bytes((p.e.bit_length()+7)//8,"big")).decode("ascii")+"\n"+
            str(self.fake_owners[0].id)+"\n",encoding="ascii")

    def tearDown(self):
        try: self.tmp.cleanup()
        finally: i.SyntheticJwtAndWalWorkerEvidence.tearDown(self)

    def jwt(self, owner=0):
        return i.SyntheticJwtAndWalWorkerEvidence._jwt(self, owner)

    def sign(self, token=None, owner=None):
        principal=self.fake_owners[0].id if owner is None else owner
        env=dict(os.environ, SECRET_KEY=self.fake_jwt_secret,
                 LOT05J9_REAL_JWT_SCM_FAKE_ONLY="1",
                 PYTHONDONTWRITEBYTECODE="1")
        run=subprocess.run([sys.executable,"-B","-m",
            "backend.tests.fixtures.lot05j9_real_jwt_rsa_signer_lab",
            str(self.root)], input=json.dumps({"jwt":self.jwt() if token is None else token,
                                               "owner":principal}),
            capture_output=True,text=True,timeout=50,env=env)
        return run

    def test_01_actual_backend_auth_signs_matching_pinned_owner(self):
        r=self.sign()
        self.assertEqual(r.returncode,0,r.stderr)
        signed=json.loads(r.stdout)
        self.assertTrue(signed["body"].startswith(
            "owner=%d|audience=LOT05J9_FAKE_WORKER|" % self.fake_owners[0].id))
        self.assertNotIn("public_key",signed)
        self.assertNotIn("private_key",signed)
        self.key.public_key().verify(base64.b64decode(signed["signature"]),
            signed["body"].encode("ascii"),padding.PKCS1v15(),hashes.SHA256())
        self.assertNotEqual(signed["signer_pid"],os.getpid())

    def test_02_invalid_jwt_never_produces_signed_job(self):
        r=self.sign(token="invalid.jwt.sig")
        self.assertNotEqual(r.returncode,0)
        self.assertIn("J9_DENIED_HTTP_401",r.stderr)
        self.assertEqual(r.stdout,"")

    def test_03_owner_mismatch_never_produces_signed_job(self):
        r=self.sign(owner=self.fake_owners[1].id)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("J9_DENIED_J8Denied",r.stderr)
        self.assertEqual(r.stdout,"")

    def test_04_real_windows_scm_consumes_same_jwt_gated_rsa_ticket_and_denies_replay(self):
        self.assertEqual(os.name,"nt","J9_SCM_PROOF_REQUIRES_REAL_WINDOWS")
        r=self.sign()
        self.assertEqual(r.returncode,0,r.stderr)
        order=json.loads(r.stdout)
        (self.root/"signed-order.fake").write_text(
            order["body"]+"\n"+order["signature"]+"\n",encoding="ascii")
        script=Path(__file__).parent/"fixtures"/"lot05j9_real_jwt_linked_scm_probe.ps1"
        env=dict(os.environ,LOT05J9_FAKE_INPUT_ROOT=str(self.root),
                 LOT05J9_REAL_SCM_SIGNED_FAKE_ONLY="1")
        scm=subprocess.run(["pwsh","-NoProfile","-File",str(script)],
            capture_output=True,text=True,timeout=200,env=env)
        proof=scm.stdout+"\n"+scm.stderr
        self.assertEqual(scm.returncode,0,proof[-6000:])
        for marker in (
          "J9_EXACT_PUBLIC_PIN_AND_LEDGER_SERVICE_SID_ACL",
          "J9_REAL_SCM_PINNED_PUBLIC_KEY_RSA_SIGNATURE_VERIFIED",
          "J9_REAL_SCM_FORGED_SIGNATURE_DENIED",
          "J9_REAL_SCM_RESTART_PERSISTENT_NONCE_REPLAY_DENIED",
          "J9_SAME_LOCALSERVICE_WITHOUT_SERVICE_SID_CANNOT_VERIFY",
          "J9_DETACHED_JWT_SIGNED_TICKET_LINKED_TO_ACTUAL_SCM_FAKE",
          "J9_NO_CLINICAL_RESTORE_ENABLED"):
            self.assertIn(marker,proof)

if __name__=="__main__":
    unittest.main(verbosity=2)
