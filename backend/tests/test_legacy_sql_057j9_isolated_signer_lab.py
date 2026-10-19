"""LOT05/05.7-J9: actual SCM Service SID signer -> same RSA ticket verified by SCM worker.
Disposable native SQLCipher users/JWT only; no patient data, product, import or restore.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from backend.tests import test_legacy_sql_057j9_real_jwt_scm_bridge_lab as inherited

class J9TrueWindowsProtectedSignerLab(unittest.TestCase):
    @classmethod
    def _seed_fake_orm(cls):
        inherited.J9JwtToRealFakeScm._seed_fake_orm.__func__(cls)

    @classmethod
    def setUpClass(cls):
        inherited.J9JwtToRealFakeScm.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        inherited.J9JwtToRealFakeScm.tearDownClass.__func__(cls)

    def setUp(self):
        inherited.J9JwtToRealFakeScm.setUp(self)

    def tearDown(self):
        inherited.J9JwtToRealFakeScm.tearDown(self)

    def test_01_distinct_windows_scm_signer_sid_denies_client_key_and_missing_jwt(self):
        self.assertEqual(os.name, "nt", "Native Windows SCM CI is required")
        base = Path(__file__).resolve().parent / "fixtures"
        env = dict(os.environ,
                   LOT05J9_SIGNER_SID_FAKE_ONLY="1",
                   LOT05J9_FAKE_OUTPUT_ROOT=str(self.root),
                   LOT05J9_FAKE_PYTHON=sys.executable,
                   LOT05J9_FAKE_SOURCE_DB=str(self.source),
                   LOT05J9_FAKE_SQL_KEY=self.fake_key,
                   LOT05J9_FAKE_JWT_SECRET=self.fake_jwt_secret,
                   LOT05J9_FAKE_JWT=self.security.create_access_token({
                       "sub": self.fake_owners[0].email
                   }),
                   LOT05J9_FAKE_OWNER=str(self.fake_owners[0].id),
                   LOT05J9_REAL_SCM_SIGNED_FAKE_ONLY="1",
                   PYTHONDONTWRITEBYTECODE="1")
        # This FAKE native SQLCipher DB uses WAL. A raw Copy-Item of only the
        # main database would discard uncheckpointed synthetic users; the
        # detached signer could then reject a genuinely valid JWT as HTTP 401.
        # Checkpoint synchronously and assert the fake principals are present
        # in the MAIN file before the Windows fixture copies it.
        from contextlib import closing
        from backend.tests import test_legacy_sql_057e_real_backupservice_sqlcipher_head as fake_db
        with closing(fake_db.sqlcipher_connection(self.source, self.fake_key)) as db:
            state = db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            self.assertEqual(state[0], 0, "J9_FAKE_WAL_CHECKPOINT_BUSY")
            rows = db.execute("SELECT id,email FROM users WHERE employer_id IS NULL ORDER BY id").fetchall()
            self.assertEqual(tuple(int(row[0]) for row in rows),
                             tuple(int(owner.id) for owner in self.fake_owners),
                             "J9_FAKE_PRINCIPALS_NOT_IN_COHERENT_MAIN_DB")
        # No active writer is permitted for the disposable raw-copy fixture.
        self.engine.dispose()
        probe=subprocess.run(
            ["pwsh", "-NoProfile", "-File",
             str(base / "lot05j9_isolated_signer_probe.ps1")],
            capture_output=True, text=True, timeout=230, env=env
        )
        report=probe.stdout+"\n"+probe.stderr
        self.assertEqual(probe.returncode, 0, report[-6500:])
        for marker in (
            "J9_REAL_SIGNER_PRIVATE_PINNED_TO_DISTINCT_SCM_SID",
            "J9_UNPRIVILEGED_SAME_LOCALSERVICE_CLIENT_CANNOT_READ_RSA_PRIVATE_OR_JWT_SECRET",
            "J9_SIDLESS_CLIENT_CANNOT_TAMPER_RSA_CONFIG_JWT_REQUEST_OR_SIGNER_OUTBOX",
            "J9_ISSUED_RSA_TICKET_INTEGRITY_SURVIVES_SECOND_REAL_CLIENT_ATTACK",
            "J9_SIGNER_EXECUTABLE_ROOT_AND_RSA_PUBLIC_PIN_READ_ONLY_FOR_LOCALSERVICE",
            "J9_SIDLESS_CLIENT_CANNOT_WRITE_SIGNER_ROOT_OR_RSA_PIN",
            "J9_TRUE_BACKEND_JWT_IN_DETACHED_WINDOWS_SCM_SIGNER",
            "J9_SIGNER_REJECTS_MISSING_JWT_WITHOUT_RSA_SIGNATURE",
            "J9_CLINICAL_WORKER_REMAINS_DENIED",
        ):
            self.assertIn(marker, report)
        # The signer under SCM produced JSON, never handed client the PRIVATE key.
        signed=json.loads((self.root/"isolated-signed.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(set(signed), {"body","signature","signer_pid"})
        self.assertIn("audience=LOT05J9_FAKE_WORKER", signed["body"])
        self.assertNotIn("private_key",signed)
        self.assertNotIn("public_key",signed)
        # The old client-side RSA key from legacy J9 must NOT be the signer-service key.
        ownpin=(self.root/"trusted-rsa-public.fake").read_text(encoding="ascii")
        self.assertNotEqual(self.key.public_key().public_numbers().n,
                            int.from_bytes(__import__("base64").b64decode(ownpin.splitlines()[0]),"big"))
        (self.root/"signed-order.fake").write_text(
            signed["body"]+"\n"+signed["signature"]+"\n", encoding="ascii"
        )
        worker=subprocess.run(
            ["pwsh","-NoProfile","-File",
             str(base/"lot05j9_real_jwt_linked_scm_probe.ps1")],
            capture_output=True, text=True, timeout=210,
            env=dict(env, LOT05J9_FAKE_INPUT_ROOT=str(self.root))
        )
        proof=worker.stdout+"\n"+worker.stderr
        self.assertEqual(worker.returncode,0,proof[-6000:])
        for marker in (
           "J9_REAL_SCM_PINNED_PUBLIC_KEY_RSA_SIGNATURE_VERIFIED",
           "J9_REAL_SCM_FORGED_SIGNATURE_DENIED",
           "J9_REAL_SCM_RESTART_PERSISTENT_NONCE_REPLAY_DENIED",
           "J9_SAME_LOCALSERVICE_WITHOUT_SERVICE_SID_CANNOT_VERIFY",
           "J9_NO_CLINICAL_RESTORE_ENABLED",
        ):
            self.assertIn(marker,proof)

        # The SAME ticket was genuinely signed by SCM A and verified by the
        # separate SCM worker above. It has a FAKE audience and no clinical
        # command; its existence must never authorize product restore.
        # Exercise unmodified REAL product entry points against disposable
        # fake paths, not a mocked GuidedRestoreService or fake worker.
        from hashlib import sha256
        from unittest.mock import patch
        from backend.core.paths import AppPaths
        from backend.services.guided_restore import GuidedRestoreService
        from backend.services.guided_restore_worker import GuidedRestoreWorker
        from backend.services import legacy_migration_restore_policy_v15 as policy
        owner = int(self.fake_owners[0].id)
        job_id = "a" * 32
        clinical_fake = self.root / "clinical_vault_fake_no_write.db"
        clinical_fake.write_bytes(b"J9_FAKE_ACTIVE_DB_UNCHANGED")
        expected_db = sha256(clinical_fake.read_bytes()).hexdigest()
        fake_source = b"J9_ONLY_FAKE_SOURCE"
        fake_backup = b"J9_ONLY_FAKE_BACKUP"
        with patch.object(AppPaths, "get_user_data_dir", return_value=self.root):
            job_dir = GuidedRestoreService.job_dir(job_id)
            job_dir.mkdir(parents=True, exist_ok=True)
            (job_dir / "source.upload").write_bytes(fake_source)
            (job_dir / "database.enc").write_bytes(fake_backup)
            job = {
                "restore_id": job_id,
                "owner_employer_id": owner,
                "status": "prepared",
                "compatible": True,
                "restore_media": False,
                "source_sha256": sha256(fake_source).hexdigest(),
                "database_sha256": sha256(fake_backup).hexdigest(),
            }
            GuidedRestoreService._write_job(job)
            original_job = (job_dir / "job.json").read_bytes()
            fake_order = (self.root / "signed-order.fake").read_bytes()
            fake_pin = (self.root / "trusted-rsa-public.fake").read_bytes()
            # Simulate a frozen cabinet and a permissive dormant policy.
            # Neither may turn a lab JWT+RSA fake order into a clinical GO.
            with patch.object(GuidedRestoreService, "runtime_apply_supported",
                              return_value=True), \\
                 patch.object(GuidedRestoreService, "_launch_detached_worker",
                              side_effect=AssertionError("PRODUCT_PROCESS_MUST_NOT_START")) as launcher, \\
                 patch.object(GuidedRestoreService, "_terminate_parent_after_response",
                              side_effect=AssertionError("PRODUCT_MUST_NOT_EXIT")) as terminator, \\
                 patch.object(policy, "require_clinical_apply", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "autorité worker non attestée"):
                    GuidedRestoreService.request_apply(
                        job_id, "RESTAURER", owner_employer_id=owner)
                launcher.assert_not_called()
                terminator.assert_not_called()
            # Calling actual worker must deny BEFORE job lookup or file write.
            with patch.object(GuidedRestoreService, "get_job",
                              side_effect=AssertionError("PRODUCT_JOB_MUST_NOT_BE_READ")) as lookup:
                with self.assertRaisesRegex(RuntimeError, "worker non attesté"):
                    GuidedRestoreWorker.run(job_id, parent_pid=999)
                lookup.assert_not_called()
            self.assertEqual((job_dir / "job.json").read_bytes(), original_job)
            self.assertEqual(GuidedRestoreService.get_job(job_id)["status"], "prepared")
            self.assertFalse((job_dir / "rescue").exists())
            self.assertFalse((job_dir / "scheduled").exists())
            self.assertEqual(sha256(clinical_fake.read_bytes()).hexdigest(), expected_db)
            self.assertEqual((self.root / "signed-order.fake").read_bytes(), fake_order)
            self.assertEqual((self.root / "trusted-rsa-public.fake").read_bytes(), fake_pin)
        print("J9_REAL_PRODUCT_REQUEST_AND_WORKER_DENY_AFTER_GENUINE_SCM_RSA_FAKE")

if __name__=="__main__":
    unittest.main(verbosity=2)
