"""Real Windows SCM signer/JWT and manifest-bound encrypted SQLCipher FAKE chain."""
import json, os, secrets, subprocess, sys, tempfile, unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from backend.tests import test_legacy_sql_057j9_isolated_signer_lab as parent_lab
from backend.tests import test_legacy_sql_057e_real_backupservice_sqlcipher_head as evidence
from backend.tests.fixtures import lot05j10b_sqlcipher_multicomponent_lab as source
from backend.tests.fixtures import lot05j10c_bound_sqlcipher_verifier_lab as gate

class ConnectedJ10C(unittest.TestCase):
    @classmethod
    def _seed_fake_orm(cls): parent_lab.J9TrueWindowsProtectedSignerLab._seed_fake_orm.__func__(cls)
    @classmethod
    def setUpClass(cls): parent_lab.J9TrueWindowsProtectedSignerLab.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls): parent_lab.J9TrueWindowsProtectedSignerLab.tearDownClass.__func__(cls)
    def setUp(self): parent_lab.J9TrueWindowsProtectedSignerLab.setUp(self)
    def tearDown(self): parent_lab.J9TrueWindowsProtectedSignerLab.tearDown(self)
    def test_01_actual_scm_jwt_rsa_job_manifest_sqlcipher_copy(self):
        self.assertEqual(os.name,"nt","ACTUAL_WINDOWS_SCM_REQUIRED")
        tmp=tempfile.TemporaryDirectory(prefix="lot05j10b_fake_"); self.addCleanup(tmp.cleanup)
        root=Path(tmp.name); inp=root/"inputs"; inp.mkdir(); (inp/"media-fake").mkdir()
        for name,payload in (("media-fake/scan.fake",b"FAKE_SCAN"),
                             ("media-fake/invoice.fake",b"FAKE_INVOICE"),
                             ("license_fake.bin",b"FAKE_VAULT")):
            (inp/name).write_bytes(payload)
        sqlkey=secrets.token_hex(32)
        with closing(source.dbopen(inp/"clinical_fake.db",sqlkey)) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA wal_autocheckpoint=0")
            db.execute("CREATE TABLE fake_truth(v TEXT)")
            db.execute("INSERT INTO fake_truth VALUES ('J10C_WAL_ROW')")
            db.commit()
            self.assertGreater(Path(str(inp/"clinical_fake.db")+"-wal").stat().st_size,0)
            # Keep the WAL owner open until the native encrypted backup has
            # actually captured its committed WAL frames (not an auto checkpoint).
            with patch.dict(os.environ,{source.FLAG:"1"}):
                source.publish(root,sqlkey)
                directory,record=source.verify(root,sqlkey)
        manifest=gate.digest_pointer(record)
        owner=int(self.fake_owners[0].id)
        job=secrets.token_hex(16)
        with closing(evidence.sqlcipher_connection(self.source,self.fake_key)) as c:
            self.assertEqual(c.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0],0)
            self.assertIsNotNone(c.execute("SELECT id FROM users WHERE id=?",(owner,)).fetchone())
        self.engine.dispose()
        env=dict(os.environ,LOT05J9_SIGNER_SID_FAKE_ONLY="1",
                 LOT05J9_FAKE_OUTPUT_ROOT=str(self.root),
                 LOT05J9_FAKE_PYTHON=sys.executable,LOT05J9_FAKE_SOURCE_DB=str(self.source),
                 LOT05J9_FAKE_SQL_KEY=self.fake_key,LOT05J9_FAKE_JWT_SECRET=self.fake_jwt_secret,
                 LOT05J9_FAKE_JWT=self.security.create_access_token({"sub":self.fake_owners[0].email}),
                 LOT05J9_FAKE_OWNER=str(owner),LOT05J10C_EXPECT_JOB=job,
                 LOT05J10C_EXPECT_GENERATION=record["generation"],
                 LOT05J10C_EXPECT_MANIFEST=manifest,
                 PYTHONDONTWRITEBYTECODE="1")
        script=Path(__file__).resolve().parent/"fixtures"/"lot05j10c_scm_bound_signer_probe.ps1"
        proc=subprocess.run(["pwsh","-NoProfile","-File",str(script)],
                            capture_output=True,text=True,timeout=230,env=env)
        out=proc.stdout+"\n"+proc.stderr
        self.assertEqual(proc.returncode,0,out[-7000:])
        for marker in ("J9_REAL_SIGNER_PRIVATE_PINNED_TO_DISTINCT_SCM_SID",
                       "J9_UNPRIVILEGED_SAME_LOCALSERVICE_CLIENT_CANNOT_READ_RSA_PRIVATE_OR_JWT_SECRET",
                       "J9_ISSUED_RSA_TICKET_INTEGRITY_SURVIVES_SECOND_REAL_CLIENT_ATTACK",
                       "J9_TRUE_BACKEND_JWT_IN_DETACHED_WINDOWS_SCM_SIGNER",
                       "J9_SIGNER_REJECTS_MISSING_JWT_WITHOUT_RSA_SIGNATURE",
                       "J10C_SIGNER_REJECTS_AUTHENTICATED_JWT_WITH_WRONG_SQLCIPHER_MANIFEST"):
            self.assertIn(marker,out)
        ticket=json.loads((self.root/"isolated-signed.json").read_text("utf-8-sig"))
        pin=(self.root/"trusted-rsa-public.fake").read_text("ascii")
        self.assertEqual(len(gate.verify_ticket(ticket,pin,owner=owner,job=job,
            generation=record["generation"],manifest=manifest)),32)
        malformed=dict(ticket,body=ticket["body"].replace("job="+job,"job="+("f"*32)))
        with self.assertRaises(gate.Denied):
            gate.verify_ticket(malformed,pin,owner=owner,job=job,
                               generation=record["generation"],manifest=manifest)
        for owner_,job_,gen_,digest_ in (
            (owner+1,job,record["generation"],manifest),
            (owner,"f"*32,record["generation"],manifest),
            (owner,job,"g_"+"f"*32,manifest),
            (owner,job,record["generation"],"f"*64)):
            with self.assertRaises(gate.Denied):
                gate.verify_ticket(ticket,pin,owner=owner_,job=job_,generation=gen_,manifest=digest_)
        with patch.dict(os.environ,{source.FLAG:"1"}):
            result=gate.authorized_fake_copy(root,ticket=ticket,pin=pin,owner=owner,job=job,
                key=sqlkey,generation=record["generation"],manifest=manifest)
            self.assertIs(result["clinical_restore_permitted"],False)
            with closing(source.dbopen(root/"isolated-recovery"/"snapshot.db",sqlkey)) as db:
                self.assertEqual(db.execute("SELECT v FROM fake_truth").fetchone(),("J10C_WAL_ROW",))
            (root/"isolated-recovery").rename(root/"previous-fake-copy")
            with self.assertRaisesRegex(gate.Denied,"J10C_REPLAY_DENIED"):
                gate.authorized_fake_copy(root,ticket=ticket,pin=pin,owner=owner,job=job,
                    key=sqlkey,generation=record["generation"],manifest=manifest)
        self.assertFalse((root/"isolated-recovery").exists())
        print("J10C_TRUE_SCM_JWT_RSA_MANIFEST_BOUND_SQLCIPHER_FAKE_COPY")
if __name__=="__main__": unittest.main(verbosity=2)
