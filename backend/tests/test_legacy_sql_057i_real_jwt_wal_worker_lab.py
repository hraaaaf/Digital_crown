"""LOT05.7-I -- *actual JWT and worker helper methods* on FAKE SQLCipher.

This is an adversarial TEST FILE only; not an API route, SCM service,
runtime migration, or permission to restore clinical databases.
JWTs and signing secrets are generated only in memory for disposable users.
"""
from __future__ import annotations

from datetime import timedelta
from contextlib import closing
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from unittest.mock import patch
import hashlib
import asyncio
import os
import secrets
import shutil
import subprocess
import time
import unittest

from backend.tests import test_legacy_sql_057e_real_backupservice_sqlcipher_head as e

FLAG = "LOT05I_REAL_JWT_WAL_FAKE_ONLY"


class SyntheticJwtAndWalWorkerEvidence(unittest.TestCase):
    @classmethod
    def _seed_fake_orm(cls):
        e.RealEncryptedBackupServiceLab._seed_fake_orm.__func__(cls)

    @classmethod
    def setUpClass(cls):
        if os.getenv(FLAG) != "1":
            raise e.LabRefused("LOT05I_FAKE_ONLY_DISABLED")
        e.RealEncryptedBackupServiceLab.setUpClass.__func__(cls)
        # Real auth.py imports from a monolithic routers/__init__.py that
        # eagerly imports clinical imaging (cv2) and unrelated clinical APIs.
        # Restrict package namespace in this TEST process only: Python still
        # loads the unmodified real auth.py, workstation_mode.py and migration
        # router source files with normal importlib machinery.
        import backend
        import sys
        import types
        if "backend.routers" not in sys.modules:
            isolated = types.ModuleType("backend.routers")
            isolated.__path__ = [str(Path(__file__).resolve().parents[1] / "routers")]
            isolated.__package__ = "backend.routers"
            sys.modules["backend.routers"] = isolated
            backend.routers = isolated
        with cls.engine.connect() as c:
            owners = tuple(c.execute(text(
                "SELECT id,email FROM users WHERE employer_id IS NULL ORDER BY id"
            )).all())
        if len(owners) != 2:
            raise e.LabRefused("TWO_FAKE_OWNERS_REQUIRED")
        cls.fake_owners = owners

    @classmethod
    def tearDownClass(cls):
        e.RealEncryptedBackupServiceLab.tearDownClass.__func__(cls)

    def setUp(self):
        e.RealEncryptedBackupServiceLab.setUp(self)
        from backend import security
        from backend.routers import auth
        self.auth = auth
        self.security = security
        self.fake_jwt_secret = secrets.token_urlsafe(48)
        self._jwt_security = patch.object(security, "SECRET_KEY", self.fake_jwt_secret)
        self._jwt_auth = patch.object(auth, "SECRET_KEY", self.fake_jwt_secret)
        self._jwt_security.start()
        self._jwt_auth.start()

    def tearDown(self):
        self._jwt_auth.stop()
        self._jwt_security.stop()
        e.RealEncryptedBackupServiceLab.tearDown(self)

    def _real_request(self, path="/api/legacy-migration/preflight"):
        from starlette.requests import Request
        return Request({
            "type":"http", "http_version":"1.1", "method":"GET",
            "scheme":"http", "path":path, "raw_path":path.encode(),
            "query_string":b"", "headers":[],
            "client":("127.0.0.1",10400), "server":("localhost",8005),
        })

    def _jwt(self, owner=0):
        return self.security.create_access_token({
            "sub":self.fake_owners[owner].email
        }, expires_delta=timedelta(minutes=5))

    def _get_principal(self, *, token=None, path=None, session=None):
        own = session is None
        if own:
            session = Session(self.engine)
        try:
            return asyncio.run(self.auth.get_current_user(
                request=self._real_request(path or "/api/legacy-migration/preflight"),
                token_header=self._jwt() if token is None else token,
                db=session,
            ))
        finally:
            if own:
                session.close()

    def _fake_job(self, owner=None):
        from backend.services.guided_restore import GuidedRestoreService
        jobid = secrets.token_hex(16)
        job = {
            "restore_id":jobid,
            "owner_employer_id":self.fake_owners[0].id if owner is None else owner,
            "status":"prepared", "compatible":True,
            "source_sha256":"f"*64,
            "database_sha256":"e"*64,
            "restore_media":False,
        }
        # The true serializer writes ONLY to AppPaths patched TemporaryDirectory.
        GuidedRestoreService._write_job(job)
        return job

    def _fake_wal(self):
        from backend.services.backup_service import BackupService
        from backend.services.guided_restore_worker import GuidedRestoreWorker
        backup = e.RealEncryptedBackupServiceLab.backup(self)
        target = self.home / "fake_clinical_vault.db"
        BackupService.restore_backup(
            backup, target, verify_sqlcipher=True, passphrase=self.fake_key)
        conn = e.sqlcipher_connection(target, self.fake_key)
        row = conn.execute("PRAGMA journal_mode=WAL").fetchone()
        self.assertEqual(str(row[0]).lower(), "wal")
        conn.execute("PRAGMA wal_autocheckpoint=0")
        conn.execute("""UPDATE patients SET nom='FAKE_WAL_UNCHECKPOINTED'
                        WHERE id=(SELECT MIN(id) FROM patients)""")
        conn.commit()
        wal = Path(str(target)+"-wal")
        self.assertTrue(wal.is_file() and wal.stat().st_size > 0)
        return target, conn

    def _rescue(self, target):
        from backend.services.guided_restore_worker import GuidedRestoreWorker
        directory = self.home / "fake_rescue"
        files = GuidedRestoreWorker._rescue_database(target, directory)
        return directory, files

    def _expected_snapshot(self, target):
        result = {}
        for suffix in ("", "-wal"):
            p = Path(str(target)+suffix)
            if p.is_file():
                result[suffix] = (p.stat().st_size,
                                  hashlib.sha256(p.read_bytes()).hexdigest())
        return result

    def _verify_copy_strict(self, rescue, expected):
        if set(expected) != {"", "-wal"}:
            raise e.LabRefused("MISSING_FAKE_ACTIVE_WAL")
        for suffix, (size, checksum) in expected.items():
            candidate = rescue / ("clinical_vault.db"+suffix)
            if (not candidate.is_file() or candidate.is_symlink()
                    or candidate.stat().st_size != size
                    or hashlib.sha256(candidate.read_bytes()).hexdigest() != checksum):
                raise e.LabRefused("FAKE_SQLCIPHER_SIDECAR_PARITY_DENIED")
        return True

    def test_01_actual_access_jwt_auth_and_owner_permission_chain(self):
        from backend.routers.legacy_migration_v15 import _owner_only
        with Session(self.engine) as db:
            user = self._get_principal(session=db)
            self.assertEqual(user.id, self.fake_owners[0].id)
            self.assertIs(self.auth.require_permission("settings")(current_user=user), user)
            self.assertIs(_owner_only(principal=user), user)
        # This does NOT create any permission to call real GuidedRestoreWorker.
        from backend.services.legacy_migration_restore_policy_v15 import require_clinical_apply
        with self.assertRaisesRegex(PermissionError, "CLINICAL_APPLY_DISABLED"):
            require_clinical_apply(owner_id=self.fake_owners[0].id)

    def test_02_missing_real_bearer_is_denied(self):
        from fastapi import HTTPException
        with Session(self.engine) as db:
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(self.auth.get_current_user(
                    request=self._real_request(), token_header=None, db=db))
            self.assertEqual(raised.exception.status_code,401)

    def test_03_jwt_bad_signature_is_denied(self):
        from jose import jwt
        from fastapi import HTTPException
        payload={"sub":self.fake_owners[0].email,"type":"access",
                 "jti":secrets.token_hex(16),"exp":int(time.time())+300}
        wrong=jwt.encode(payload, secrets.token_urlsafe(32), algorithm=self.auth.ALGORITHM)
        with Session(self.engine) as db:
            with self.assertRaises(HTTPException) as raised:
                self._get_principal(token=wrong,session=db)
            self.assertEqual(raised.exception.status_code,401)

    def test_04_expired_access_jwt_is_denied(self):
        from jose import jwt
        from fastapi import HTTPException
        payload={"sub":self.fake_owners[0].email,"type":"access",
                 "jti":secrets.token_hex(16),"exp":int(time.time())-30}
        token=jwt.encode(payload,self.fake_jwt_secret,algorithm=self.auth.ALGORITHM)
        with Session(self.engine) as db:
            with self.assertRaises(HTTPException) as raised:
                self._get_principal(token=token,session=db)
            self.assertEqual(raised.exception.status_code,401)

    def test_05_real_refresh_token_cannot_authenticate_api(self):
        from fastapi import HTTPException
        refresh=self.security.create_refresh_token(
            {"sub":self.fake_owners[0].email})
        with Session(self.engine) as db:
            with self.assertRaises(HTTPException) as raised:
                self._get_principal(token=refresh,session=db)
            self.assertEqual(raised.exception.status_code,401)

    def test_06_owner_flag_is_not_equivalent_to_auth_or_settings(self):
        from backend.routers.legacy_migration_v15 import _owner_only
        from fastapi import HTTPException
        with self.engine.connect() as c:
            tx=c.begin()
            try:
                c.execute(text("""UPDATE users SET employer_id=:parent,
                  permissions='{"settings": true}'
                  WHERE id=:employee"""),{
                    "parent":self.fake_owners[0].id,
                    "employee":self.fake_owners[1].id,
                })
                with Session(bind=c) as db:
                    u=self._get_principal(token=self._jwt(1), session=db)
                    # Real permission helper grants delegated settings, but
                    # migration's separate root owner guard must refuse.
                    self.assertIs(self.auth.require_permission("settings")(
                        current_user=u),u)
                    with self.assertRaises(HTTPException) as raised:
                        _owner_only(principal=u)
                    self.assertEqual(raised.exception.status_code,403)
            finally:
                tx.rollback()

    def test_07_inactive_user_rejected_by_real_get_current_user(self):
        from fastapi import HTTPException
        with self.engine.connect() as c:
            tx=c.begin()
            try:
                c.execute(text("UPDATE users SET is_active=0 WHERE id=:id"),
                          {"id":self.fake_owners[0].id})
                with Session(bind=c) as db:
                    with self.assertRaises(HTTPException) as raised:
                        self._get_principal(session=db)
                    self.assertEqual(raised.exception.status_code,401)
            finally:
                tx.rollback()

    def test_08_station_guard_blocks_real_jwt_if_workstation_required(self):
        from backend.routers import workstation_mode
        from fastapi import HTTPException
        # Test controls ONLY a fake DB predicate; the REAL workstation guard
        # and REAL auth dependency must produce HTTP 423 for missing cookie.
        with patch.object(workstation_mode, "_tenant_has_workstations",
                          return_value=True):
            with Session(self.engine) as db:
                with self.assertRaises(HTTPException) as raised:
                    self._get_principal(session=db)
                self.assertEqual(raised.exception.status_code,423)
                self.assertEqual(raised.exception.detail,"WORKSTATION_IDENTITY_REQUIRED")

    def test_09_nonexempt_migration_path_uses_real_station_guard(self):
        with Session(self.engine) as db:
            u=self._get_principal(session=db)
            self.assertEqual(u.id,self.fake_owners[0].id)
            from backend.routers import workstation_mode
            with patch.object(workstation_mode,
                              "enforce_authenticated_workstation_access",
                              side_effect=PermissionError("FAKE_STATION_VETO")) as gate:
                with self.assertRaisesRegex(PermissionError,"FAKE_STATION_VETO"):
                    self._get_principal(session=db)
                self.assertEqual(gate.call_count,1)

    def test_10_real_guided_restore_job_persisted_in_fake_root(self):
        from backend.services.guided_restore import GuidedRestoreService
        job=self._fake_job()
        loaded=GuidedRestoreService.get_owned_job(
            job["restore_id"],self.fake_owners[0].id)
        self.assertEqual(loaded["owner_employer_id"],self.fake_owners[0].id)
        self.assertEqual(loaded["restore_id"],job["restore_id"])
        self.assertTrue((self.home/"guided-restore"/job["restore_id"]/"job.json").is_file())

    def test_11_real_get_owned_job_explicit_wrong_owner_is_denied(self):
        from backend.services.guided_restore import GuidedRestoreService
        job=self._fake_job()
        with self.assertRaises(PermissionError):
            GuidedRestoreService.get_owned_job(
                job["restore_id"],self.fake_owners[1].id)

    def test_12_real_guided_restore_missing_owner_bypass_is_observed(self):
        from backend.services.guided_restore import GuidedRestoreService
        job=self._fake_job()
        # Major discovered defect: production helper currently treats None
        # as trusted internal worker; NEVER invoke actual request_apply.
        self.assertIsNone(GuidedRestoreService._assert_owner(job,None))
        self.assertEqual(
            GuidedRestoreService.get_owned_job(job["restore_id"],None)["restore_id"],
            job["restore_id"],
        )
        # G's dormant authorization remains an unconditional veto.
        from backend.services.legacy_migration_restore_policy_v15 import require_clinical_apply
        with self.assertRaisesRegex(PermissionError,"CLINICAL_APPLY_DISABLED"):
            require_clinical_apply(job, principal=None)

    def test_13_real_worker_copies_uncheckpointed_wal_to_fake_rescue(self):
        target,cn=self._fake_wal()
        try:
            original=self._expected_snapshot(target)
            self.assertEqual(set(original),{"", "-wal"})
            rescue,files=self._rescue(target)
            self.assertEqual(set(files),
                             {"clinical_vault.db","clinical_vault.db-wal"})
            self.assertTrue(self._verify_copy_strict(rescue,original))
        finally:
            cn.close()

    def test_14_real_worker_can_restore_fake_db_and_committed_wal(self):
        from backend.services.guided_restore_worker import GuidedRestoreWorker
        target,cn=self._fake_wal()
        try:
            rescue,_=self._rescue(target)
        finally:
            cn.close()
        # Source DB now closed. Only the fake destination may be damaged.
        target.write_bytes(b"FAKE_CORRUPT_DB")
        GuidedRestoreWorker._restore_database_from_rescue(target,rescue)
        with closing(e.sqlcipher_connection(target,self.fake_key)) as read:
            row=read.execute(
                "SELECT nom FROM patients ORDER BY id LIMIT 1").fetchone()
            self.assertEqual(row,("FAKE_WAL_UNCHECKPOINTED",))

    def test_15_strict_fake_manifest_refuses_missing_or_changed_wal(self):
        target,cn=self._fake_wal()
        try:
            expected=self._expected_snapshot(target)
            rescue,_=self._rescue(target)
            wal=rescue/"clinical_vault.db-wal"
            wal.write_bytes(wal.read_bytes()+b"FAKE_TAMPER")
            with self.assertRaisesRegex(e.LabRefused,
                                        "FAKE_SQLCIPHER_SIDECAR_PARITY_DENIED"):
                self._verify_copy_strict(rescue,expected)
            wal.unlink()
            with self.assertRaisesRegex(e.LabRefused,
                                        "FAKE_SQLCIPHER_SIDECAR_PARITY_DENIED"):
                self._verify_copy_strict(rescue,expected)
        finally:
            cn.close()

    def test_16_worker_copy_fails_mid_wal_and_leaves_partial_fake_rescue(self):
        from backend.services.guided_restore_worker import GuidedRestoreWorker
        target,cn=self._fake_wal()
        try:
            rescue=self.home/"fake_rescue"
            actual=shutil.copy2
            def fail_copy(source,dest,*args,**kwargs):
                if str(source).endswith("-wal"):
                    raise OSError("FAKE_DISK_WRITE_FAILURE")
                return actual(source,dest,*args,**kwargs)
            with patch("backend.services.guided_restore_worker.shutil.copy2",
                       side_effect=fail_copy):
                with self.assertRaisesRegex(OSError,"FAKE_DISK_WRITE_FAILURE"):
                    GuidedRestoreWorker._rescue_database(target,rescue)
            self.assertTrue((rescue/"clinical_vault.db").is_file())
            self.assertFalse((rescue/"clinical_vault.db-wal").exists())
            with self.assertRaises(e.LabRefused):
                self._verify_copy_strict(rescue,self._expected_snapshot(target))
            # Worker helper is NON-ATOMIC; product must never mark rescue safe
            # until an external fail-closed manifest and fsync is certified.
        finally:
            cn.close()

    def test_17_missing_fake_db_makes_real_rescue_refuse(self):
        from backend.services.guided_restore_worker import GuidedRestoreWorker
        with self.assertRaisesRegex(RuntimeError,"secours impossible"):
            GuidedRestoreWorker._rescue_database(
                self.home/"fake_clinical_vault_missing.db",self.home/"fake_rescue")

    def test_18_real_worker_rescue_validator_accepts_valid_fake_sqlcipher(self):
        from backend.services.guided_restore_worker import GuidedRestoreWorker
        target,cn=self._fake_wal()
        try:
            rescue,_=self._rescue(target)
            GuidedRestoreWorker._verify_database_rescue(rescue,"pysqlcipher")
        finally:
            cn.close()

    def test_19_target_corrupt_sqlcipher_rescue_validation_refuses(self):
        from backend.services.guided_restore_worker import GuidedRestoreWorker
        rescue=self.home/"fake_rescue"
        rescue.mkdir()
        (rescue/"clinical_vault.db").write_bytes(b"FAKE_BROKEN_SQLCIPHER")
        from sqlcipher3.dbapi2 import DatabaseError
        with self.assertRaises((DatabaseError, ValueError)):
            GuidedRestoreWorker._verify_database_rescue(rescue,"pysqlcipher")

    def test_20_actual_windows_acl_query_is_diagnostic_not_service_sid(self):
        if os.name == "nt":
            result=subprocess.run(["icacls",str(self.home)],capture_output=True,
                                  text=True,timeout=15,check=False)
            self.assertEqual(result.returncode,0)
            self.assertTrue(result.stdout.strip())
            # NOT an installed Service SID/SCM or malicious NTFS reparse test.
        else:
            self.assertNotEqual(os.name,"nt")
            self.assertTrue(self.home.is_dir())

    def test_21_unfrozen_fake_runner_cannot_request_real_guided_apply(self):
        from backend.services.guided_restore import GuidedRestoreService
        with patch.object(__import__("sys"),"frozen",False,create=True):
            self.assertIs(GuidedRestoreService.runtime_apply_supported(),False)
        from backend.services.legacy_migration_restore_policy_v15 import require_clinical_apply
        with self.assertRaises(PermissionError):
            require_clinical_apply(restore_id="fake")


if __name__ == "__main__":
    unittest.main()
