"""LOT05.7-G adversarial FAKE-only integration against dormant product contract.

Uses E's exact real SQLCipher/Alembic fixture and production BackupService.
It does NOT call an import API or attach the dormant module to any route.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.tests import test_legacy_sql_057e_real_backupservice_sqlcipher_head as e
from backend.services import legacy_migration_restore_policy_v15 as guard

FAKE_FLAG = "LOT05G_SYNTHETIC_ONLY"


class DormantPolicyContractLab(unittest.TestCase):
    @classmethod
    def _seed_fake_orm(cls):
        e.RealEncryptedBackupServiceLab._seed_fake_orm.__func__(cls)

    @classmethod
    def setUpClass(cls):
        if os.environ.get(FAKE_FLAG) != "1":
            raise guard.RestoreContractDenied("FAKE_LAB_DISABLED")
        e.RealEncryptedBackupServiceLab.setUpClass.__func__(cls)
        from sqlalchemy import text
        with cls.engine.connect() as connection:
            cls.owners = tuple(connection.execute(text(
                "SELECT id FROM users WHERE employer_id IS NULL ORDER BY id"
            )).scalars())
        if len(cls.owners) != 2:
            raise guard.RestoreContractDenied("FAKE_OWNER_FIXTURE_BROKEN")
        cls.principal = SimpleNamespace(
            id=cls.owners[0], role="DENTISTE",
            is_active=True, employer_id=None, approval_status="approved",
        )

    @classmethod
    def tearDownClass(cls):
        e.RealEncryptedBackupServiceLab.tearDownClass.__func__(cls)

    def setUp(self):
        e.RealEncryptedBackupServiceLab.setUp(self)

    def tearDown(self):
        e.RealEncryptedBackupServiceLab.tearDown(self)

    def backup(self):
        return e.RealEncryptedBackupServiceLab.backup(self)

    def restored_engine(self, path):
        return e.RealEncryptedBackupServiceLab.restored_engine(self, path)

    def scan(self, connection=None, *, principal=None, owners=None):
        principal = self.principal if principal is None else principal
        owners = self.owners if owners is None else owners
        if connection is not None:
            return guard.evaluate_tenant_snapshot_read_only(
                connection, principal, expected_owners=owners)
        with self.engine.connect() as c:
            return guard.evaluate_tenant_snapshot_read_only(
                c, principal, expected_owners=owners)

    def staging(self, backup=None):
        from backend.services.backup_service import BackupService
        backup = self.backup() if backup is None else backup
        path = self.home / (".lot05g_stage_" + secrets.token_hex(8) + ".db")
        BackupService.restore_backup(
            backup, path, verify_sqlcipher=True, passphrase=self.fake_key,
        )
        return path

    def verified_stage(self):
        from backend.core.schema_runtime import assert_database_at_current_head
        from backend.tests.test_legacy_sql_057e_real_backupservice_sqlcipher_head import rows_digest
        staged = self.staging()
        engine = self.restored_engine(staged)
        try:
            assert_database_at_current_head(engine)
            with engine.connect() as c:
                proof = self.scan(c)
                self.assertEqual(proof["checked_join_families"], 6)
                self.assertIs(proof["clinical_restore_permitted"], False)
            self.assertEqual(rows_digest(engine), self.before)
        finally:
            engine.dispose()
        return staged

    def publish(self, staged, *, sha=None, race_hook=None):
        return guard.fake_lab_publish_no_replace(
            self.root, staged, self.home / "restored_fake.db",
            expected_sha256=sha or hashlib.sha256(staged.read_bytes()).hexdigest(),
            race_hook=race_hook,
        )

    def test_01_clinical_apply_is_unconditionally_disabled_even_if_flagged(self):
        with patch.dict(os.environ, {
            "LOT05G_RESTORE_ENABLED": "1",
            "LOT05G_CLINICAL_APPLY": "true",
            "ENVIRONMENT": "cabinet",
        }):
            for args in ((), (self.principal, "RESTORE"), ("force", True)):
                with self.subTest(args=args):
                    with self.assertRaisesRegex(guard.RestoreContractDenied,
                                                "CLINICAL_APPLY_DISABLED"):
                        guard.require_clinical_apply(*args, owner_id=self.owners[0])

    def test_02_read_only_owner_and_real_head_match_but_never_permit_import(self):
        result = self.scan()
        self.assertEqual(result["schema_head"], "neo000000031")
        self.assertEqual(result["checked_join_families"], 6)
        self.assertIs(result["clinical_restore_permitted"], False)
        self.assertIs(result["clinical_import_permitted"], False)

    def test_03_reject_absent_and_forged_owner_claims(self):
        with self.engine.connect() as c:
            with self.assertRaisesRegex(guard.RestoreContractDenied,
                                        "TRUSTED_PRINCIPAL_REQUIRED"):
                guard.verify_owner_observation(c, None)
            for forged in (
                SimpleNamespace(id="1", role="DENTISTE", is_active=True,
                                employer_id=None, approval_status="approved"),
                SimpleNamespace(id=self.owners[0], role="SECRETAIRE", is_active=True,
                                employer_id=None, approval_status="approved"),
                SimpleNamespace(id=self.owners[0], role="DENTISTE", is_active=False,
                                employer_id=None, approval_status="approved"),
                SimpleNamespace(id=self.owners[0], role="DENTISTE", is_active=True,
                                employer_id=self.owners[1], approval_status="approved"),
                SimpleNamespace(id=self.owners[0], role="DENTISTE", is_active=True,
                                employer_id=None, approval_status="pending"),
                SimpleNamespace(id=9876543, role="DENTISTE", is_active=True,
                                employer_id=None, approval_status="approved"),
            ):
                with self.subTest(principal=forged), self.assertRaises(
                        guard.RestoreContractDenied):
                    guard.verify_owner_observation(c, forged)

    def test_04_owner_scope_and_alembic_head_must_be_exact(self):
        from sqlalchemy import text
        for scope in ((), (self.owners[0],), (self.owners[0], 99999),
                      (self.owners[0], self.owners[0]), (True, 2)):
            with self.subTest(scope=scope), self.assertRaises(guard.RestoreContractDenied):
                self.scan(owners=scope)
        with self.engine.connect() as c:
            transaction = c.begin()
            try:
                c.execute(text("UPDATE alembic_version SET version_num='neo000000030'"))
                with self.assertRaisesRegex(guard.RestoreContractDenied,
                                            "ALEMBIC_HEAD_MISMATCH"):
                    self.scan(c)
            finally:
                transaction.rollback()
        self.assertEqual(self.scan()["schema_head"], "neo000000031")

    def test_05_wrong_patient_appointment_join_is_read_only_denied(self):
        from sqlalchemy import text
        with self.engine.connect() as c:
            transaction = c.begin()
            try:
                c.execute(text("""UPDATE appointments SET employer_id=:other
                    WHERE id=(SELECT MIN(id) FROM appointments)"""),
                    {"other":self.owners[1]})
                with self.assertRaisesRegex(guard.RestoreContractDenied,
                                            "APPOINTMENT_PATIENT"):
                    self.scan(c)
            finally:
                transaction.rollback()
        self.assertEqual(self.scan()["checked_join_families"], 6)

    def test_06_wrong_acte_practitioner_join_denied(self):
        from sqlalchemy import text
        with self.engine.connect() as c:
            tx = c.begin()
            try:
                c.execute(text("""UPDATE actes SET praticien_id=:other
                    WHERE id=(SELECT MIN(id) FROM actes)"""),
                    {"other":self.owners[1]})
                with self.assertRaisesRegex(guard.RestoreContractDenied,
                                            "ACTE_PRACTITIONER"):
                    self.scan(c)
            finally:
                tx.rollback()

    def test_07_wrong_payment_patient_acte_join_denied(self):
        from sqlalchemy import text
        with self.engine.connect() as c:
            tx = c.begin()
            try:
                c.execute(text("""UPDATE payments SET patient_id=(
                    SELECT MAX(id) FROM patients)
                    WHERE id=(SELECT MIN(id) FROM payments)"""))
                with self.assertRaisesRegex(guard.RestoreContractDenied,
                                            "PAYMENT_ACTE_PATIENT"):
                    self.scan(c)
            finally:
                tx.rollback()

    def test_08_wrong_document_uploader_join_denied(self):
        from sqlalchemy import text
        with self.engine.connect() as c:
            tx = c.begin()
            try:
                c.execute(text("""UPDATE document_archives
                    SET uploaded_by_id=:other
                    WHERE id=(SELECT MIN(id) FROM document_archives)"""),
                    {"other":self.owners[1]})
                with self.assertRaisesRegex(guard.RestoreContractDenied,
                                            "DOCUMENT_UPLOADER"):
                    self.scan(c)
            finally:
                tx.rollback()

    def test_09_real_backupservice_stage_and_exclusive_publish(self):
        from backend.core.schema_runtime import assert_database_at_current_head
        from backend.tests.test_legacy_sql_057e_real_backupservice_sqlcipher_head import rows_digest
        staged = self.verified_stage()
        target = self.publish(staged)
        self.assertTrue(target.is_file())
        self.assertNotEqual(target.read_bytes()[:16], b"SQLite format 3\x00")
        engine = self.restored_engine(target)
        try:
            assert_database_at_current_head(engine)
            self.assertEqual(rows_digest(engine), self.before)
            with engine.connect() as c:
                self.assertEqual(self.scan(c)["checked_join_families"], 6)
        finally:
            engine.dispose()

    def test_10_preexisting_target_never_replaced(self):
        staged = self.verified_stage()
        target = self.home / "restored_fake.db"
        target.write_bytes(b"FAKE_SENTINEL_NEVER_OVERWRITE")
        with self.assertRaisesRegex(guard.RestoreContractDenied,
                                    "FOREIGN_OR_OCCUPIED_FAKE_TARGET"):
            self.publish(staged)
        self.assertEqual(target.read_bytes(), b"FAKE_SENTINEL_NEVER_OVERWRITE")

    def test_11_race_injected_after_digest_exclusively_denied(self):
        staged = self.verified_stage()
        def race(target):
            target.write_bytes(b"RACE_TARGET_KEEP")
        with self.assertRaisesRegex(guard.RestoreContractDenied,
                                    "ATOMIC_TARGET_ALREADY_EXISTS"):
            self.publish(staged, race_hook=race)
        self.assertEqual((self.home / "restored_fake.db").read_bytes(),
                         b"RACE_TARGET_KEEP")

    def test_12_unknown_hardlink_capability_fails_without_copy_fallback(self):
        staged = self.verified_stage()
        with patch.object(guard.os, "link", side_effect=PermissionError("no-link")):
            with self.assertRaisesRegex(guard.RestoreContractDenied,
                                        "ATOMIC_LINK_UNAVAILABLE"):
                self.publish(staged)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_13_changed_staged_bytes_and_digest_mismatch_denied(self):
        staged = self.verified_stage()
        valid = hashlib.sha256(staged.read_bytes()).hexdigest()
        with staged.open("ab") as stream:
            stream.write(b"TAMPER_FAKE")
        with self.assertRaisesRegex(guard.RestoreContractDenied,
                                    "STAGED_DIGEST_MISMATCH"):
            self.publish(staged, sha=valid)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_14_symlink_stage_and_external_target_denied(self):
        staged = self.verified_stage()
        other = self.root / "foreign.db"
        with self.assertRaisesRegex(guard.RestoreContractDenied,
                                    "FOREIGN_OR_OCCUPIED_FAKE_TARGET"):
            guard.fake_lab_publish_no_replace(
                self.root, staged, other,
                expected_sha256=hashlib.sha256(staged.read_bytes()).hexdigest())
        # Simulate an actual parent/source reparse observation on each OS,
        # without requiring Windows symlink privileges in GitHub runners.
        cls = type(staged)
        original_is_symlink = cls.is_symlink
        with patch.object(cls, "is_symlink",
                          lambda item: item == staged or original_is_symlink(item)):
            with self.assertRaisesRegex(guard.RestoreContractDenied,
                                        "FOREIGN_OR_OCCUPIED_FAKE_TARGET"):
                self.publish(staged)

    def test_15_missing_fake_flag_denies_even_valid_staging(self):
        staged = self.verified_stage()
        with patch.dict(os.environ, {FAKE_FLAG:"0"}):
            with self.assertRaisesRegex(guard.RestoreContractDenied,
                                        "FAKE_LAB_DISABLED"):
                self.publish(staged)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_16_invalid_backup_fernet_key_denied_before_staging(self):
        from backend.services.backup_service import BackupService
        from cryptography.fernet import Fernet, InvalidToken
        backup = self.backup()
        with patch.object(BackupService, "_get_or_create_key",
                          return_value=Fernet(Fernet.generate_key())):
            with self.assertRaises(InvalidToken):
                self.staging(backup)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_17_a_legal_patientless_appointment_remains_accepted(self):
        from sqlalchemy import text
        from sqlalchemy.orm import Session
        from backend import models
        with Session(self.engine) as s:
            s.add(models.Appointment(
                patient_id=None, patient_name="FAKE_PATIENTLESS_G",
                employer_id=self.owners[0],
                datetime_start=datetime(2027, 6, 1, 9),
                duration_minutes=30, motif="FAKE_ONLY",
            ))
            s.commit()
        try:
            self.assertFalse(self.scan()["clinical_restore_permitted"])
        finally:
            with self.engine.begin() as c:
                c.execute(text(
                    "DELETE FROM appointments WHERE patient_name='FAKE_PATIENTLESS_G'"
                ))
        self.assertEqual(self.scan()["checked_join_families"], 6)


if __name__ == "__main__":
    unittest.main()
