"""LOT05.7-J5: true JWT principal -> signed fake job -> fake worker.

Inherits and reruns the 21 REAL JWT + native SQLCipher WAL I regression
methods as-is. This does not authenticate a detached SCM Windows service.
"""
from __future__ import annotations
from contextlib import closing
import os
from pathlib import Path
import secrets
import tempfile
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.tests import test_legacy_sql_057i_real_jwt_wal_worker_lab as i
from backend.tests.fixtures import lot05j4_signed_job_lab as j4


class RealJwtToFakeSignedWorkerLab(i.SyntheticJwtAndWalWorkerEvidence):
    def setUp(self):
        super().setUp()
        self.j4_before = os.environ.get(j4.FLAG)
        os.environ[j4.FLAG] = "1"
        self.j4_temp = tempfile.TemporaryDirectory(prefix="lot05j4_fake_")
        self.j4_root = Path(self.j4_temp.name)
        (self.j4_root / "inputs").mkdir()
        (self.j4_root / "inputs" / "payload.fake").write_bytes(j4.PAYLOAD)
        self.j4_key = secrets.token_bytes(32)
        self.j4_now = 1800000000

    def tearDown(self):
        try:
            self.j4_temp.cleanup()
            if self.j4_before is None:
                os.environ.pop(j4.FLAG, None)
            else:
                os.environ[j4.FLAG] = self.j4_before
        finally:
            super().tearDown()

    def _validated_fake_ticket(self, *, token=None):
        from backend.routers.legacy_migration_v15 import _owner_only
        with Session(self.engine) as db:
            principal = self._get_principal(token=token, session=db)
            self.auth.require_permission("settings")(current_user=principal)
            _owner_only(principal=principal)
            owner_id = principal.id
            return j4.sign_fake_job(self.j4_root, owner=owner_id,
                                    key=self.j4_key, now=self.j4_now)

    def test_22_authenticated_real_jwt_yields_fake_signed_job_for_matching_owner(self):
        envelope = self._validated_fake_ticket()
        self.assertEqual(envelope["body"]["owner"], self.fake_owners[0].id)
        result = j4.consume_fake_job(self.j4_root, envelope,
                                     owner=self.fake_owners[0].id,
                                     key=self.j4_key, now=self.j4_now + 1)
        self.assertEqual(result, j4.PAYLOAD)

    def test_23_real_jwt_different_root_user_cannot_consume_others_signed_job(self):
        envelope = self._validated_fake_ticket()
        with self.assertRaisesRegex(j4.J4Denied, "CLAIMS_INVALID"):
            j4.consume_fake_job(self.j4_root, envelope, owner=self.fake_owners[1].id,
                                key=self.j4_key, now=self.j4_now + 1)

    def test_24_invalid_real_jwt_cannot_get_a_fake_signed_job(self):
        from jose import jwt
        bad = jwt.encode({"sub": self.fake_owners[0].email,
                          "type": "access", "exp": 1950000000,
                          "jti": secrets.token_hex(16)},
                         secrets.token_urlsafe(48), algorithm=self.auth.ALGORITHM)
        with self.assertRaises(HTTPException):
            self._validated_fake_ticket(token=bad)
        self.assertFalse((self.j4_root / "j4_replays.sqlite").exists())

    def test_25_fake_ticket_not_a_permission_to_clinical_restore(self):
        from backend.services.legacy_migration_restore_policy_v15 import require_clinical_apply
        envelope = self._validated_fake_ticket()
        self.assertTrue(envelope["mac"])
        with self.assertRaisesRegex(PermissionError, "CLINICAL_APPLY_DISABLED"):
            require_clinical_apply(owner_id=self.fake_owners[0].id)


if __name__ == "__main__":
    import unittest
    unittest.main(verbosity=2)
