"""LOT05.7-F — synthetic-only tenant veto and atomic no-overwrite publication.

This module is a TEST HARNESS, NOT a runtime migration/restore API.
Reuses the independently proven E real SQLCipher/Alembic fake setup.
Nothing in this file may grant import permission, write patient source rows,
accept arbitrary paths, or authorize a clinical restore.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import errno
import hashlib
import os
import re
import secrets
import unittest

from backend.tests.test_legacy_sql_057e_real_backupservice_sqlcipher_head import (
    RealEncryptedBackupServiceLab as EFixture,
    LabRefused,
    rows_digest,
    verified_lab,
    sqlcipher_connection,
)

FLAG = "LOT05F_FAILCLOSED_FAKE_ONLY"

# All queries are static, bound to the exact current real ORM column names.
# NULL patient_id on an appointment is a legitimate quick/standalone booking.
# This does NOT pretend to cover every reference in the full medical schema.
TENANT_QUERIES = (
    ("PATIENT_OWNER_NOT_ROOT", """
     SELECT COUNT(*) FROM patients p LEFT JOIN users u ON u.id=p.employer_id
     WHERE u.id IS NULL OR u.employer_id IS NOT NULL
     """),
    ("APPOINTMENT_PATIENT_TENANT", """
     SELECT COUNT(*) FROM appointments a LEFT JOIN patients p ON p.id=a.patient_id
     WHERE a.patient_id IS NOT NULL
       AND (p.id IS NULL OR p.employer_id IS NULL OR a.employer_id <> p.employer_id)
     """),
    ("APPOINTMENT_RESOURCE_TENANT", """
     SELECT COUNT(*) FROM appointments a LEFT JOIN agenda_resources r ON r.id=a.resource_id
     WHERE a.resource_id IS NOT NULL
       AND (r.id IS NULL OR r.employer_id IS NULL OR a.employer_id <> r.employer_id)
     """),
    ("ACTE_PRACTITIONER_TENANT", """
     SELECT COUNT(*) FROM actes a
     LEFT JOIN patients p ON p.id=a.patient_id
     LEFT JOIN users u ON u.id=a.praticien_id
     WHERE p.id IS NULL OR u.id IS NULL
        OR COALESCE(u.employer_id,u.id) <> p.employer_id
     """),
    ("PAYMENT_ACTE_PATIENT", """
     SELECT COUNT(*) FROM payments m LEFT JOIN actes a ON a.id=m.acte_id
     WHERE m.acte_id IS NOT NULL AND
       (a.id IS NULL OR m.patient_id <> a.patient_id)
     """),
    ("DOCUMENT_UPLOADER_TENANT", """
     SELECT COUNT(*) FROM document_archives d
     JOIN patients p ON p.id=d.patient_id
     LEFT JOIN users u ON u.id=d.uploaded_by_id
     WHERE d.uploaded_by_id IS NOT NULL AND
       (u.id IS NULL OR COALESCE(u.employer_id,u.id) <> p.employer_id)
     """),
)


def synthetic_tenant_preflight(connection, owner_ids):
    """Strict read-only LAB preflight on the REAL Digital Crown schema.

    owner_ids is a fake *test fixture claim*, NOT an authenticated human or a
    clinical identity. This cannot be connected to runtime authorization.
    """
    from sqlalchemy import text
    if os.environ.get(FLAG) != "1":
        raise LabRefused("FAKE_GUARD_DISABLED")
    if connection.dialect.name != "sqlite":
        raise LabRefused("ONLY_FAKE_SQLCIPHER_SQLITE")
    if not isinstance(owner_ids, (tuple, frozenset)):
        raise LabRefused("EXPLICIT_SYNTHETIC_OWNERS_REQUIRED")
    if len(owner_ids) != 2 or any(type(v) is not int or v <= 0 for v in owner_ids):
        raise LabRefused("EXPLICIT_SYNTHETIC_OWNERS_REQUIRED")
    required = set(owner_ids)
    if len(required) != 2:
        raise LabRefused("DUPLICATE_SYNTHETIC_OWNER")
    owners = set(connection.execute(
        text("SELECT id FROM users WHERE employer_id IS NULL AND id IN (:a,:b)"),
        {"a":owner_ids[0], "b":owner_ids[1]}
    ).scalars())
    if owners != required:
        raise LabRefused("SYNTHETIC_OWNER_IDENTITY_MISMATCH")
    in_data = set(connection.execute(text(
        "SELECT DISTINCT employer_id FROM patients"
    )).scalars())
    if in_data != required:
        raise LabRefused("UNEXPECTED_OWNER_SCOPE")
    violations = []
    for reason, query in TENANT_QUERIES:
        if connection.execute(text(query)).scalar_one() != 0:
            violations.append(reason)
    if violations:
        # No patient names/IDs or row payload ever enter errors or CI logs.
        raise LabRefused("CROSS_TENANT_DENIED:" + ",".join(violations))
    return True


def _lab_paths(root: Path, home: Path, backup: Path, target: Path):
    """Only fully known and independent paths under temporary FAKE root."""
    if os.environ.get(FLAG) != "1":
        raise LabRefused("FAKE_GUARD_DISABLED")
    if (not isinstance(root, Path) or not isinstance(home, Path)
            or not isinstance(backup, Path) or not isinstance(target, Path)):
        raise LabRefused("FAKE_PATH_TYPE_REQUIRED")
    if (not root.is_absolute() or not root.is_dir() or root.is_symlink()
            or not root.name.startswith("lot05e_fake_sqlcipher_")
            or home.parent != root or not home.is_dir() or home.is_symlink()
            or not home.name.startswith("test_")
            or target != home / "restored_fake.db"):
        raise LabRefused("FOREIGN_RESTORE_DESTINATION")
    if (backup.parent != home / "backups" or backup.is_symlink()
            or not backup.is_file()
            or not re.fullmatch(r"db_backup_[0-9]{8}_[0-9]{6}\.db\.enc", backup.name)):
        raise LabRefused("FOREIGN_ENCRYPTED_BACKUP")
    if (not backup.parent.is_dir() or backup.parent.is_symlink()
            or backup.resolve(strict=True).parent != backup.parent.resolve(strict=True)):
        raise LabRefused("BACKUP_PATH_TRAVERSAL")
    # A preflight exists() check does not prevent races; os.link() below does.
    # Still reject symlinks and already occupied targets before doing work.
    if target.exists() or target.is_symlink():
        raise LabRefused("DESTINATION_ALREADY_EXISTS")


def verified_no_replace_lab_publish(test, backup, owners, *, race_hook=None):
    """Calls *real* BackupService.restore_backup into ephemeral staging.

    Check Alembic head, all six fake family row digests and selected tenant
    relationships BEFORE publishing with an exclusive hard link. os.link()
    atomically rejects existing name (EEXIST), unlike os.replace().
    If the platform lacks safe same-filesystem hard-link capability, FAIL CLOSED.
    """
    from backend.services.backup_service import BackupService
    from backend.core.schema_runtime import assert_database_at_current_head
    from sqlalchemy import text

    root, home = test.root, test.home
    target = home / "restored_fake.db"
    verified_lab(root, test.source, test.fake_key)
    _lab_paths(root, home, backup, target)
    staged = home / (".stage_fake_" + secrets.token_hex(12) + ".db")
    if staged.exists() or staged.is_symlink():
        raise LabRefused("STAGING_ALREADY_EXISTS")
    try:
        # This is the real shipping method, but NEVER pointed at the target.
        BackupService.restore_backup(
            backup, staged, verify_sqlcipher=True, passphrase=test.fake_key,
        )
        if not staged.is_file() or staged.is_symlink():
            raise LabRefused("STAGING_FILE_NOT_REGULAR")
        engine = test.restored_engine(staged)
        try:
            assert_database_at_current_head(engine)
            with engine.connect() as c:
                # The preflight is entirely SELECT-only and never publishes
                # a failed clinical association in the fake test.
                synthetic_tenant_preflight(c, owners)
                if c.exec_driver_sql("PRAGMA integrity_check").scalar_one() != "ok":
                    raise LabRefused("SQLCIPHER_INTEGRITY_FAILURE")
                if c.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
                    raise LabRefused("FOREIGN_KEY_FAILURE")
            if rows_digest(engine) != test.expected_for_publication:
                raise LabRefused("FAKE_DATA_PARITY_MISMATCH")
        finally:
            engine.dispose()
        if race_hook is not None:
            # Adversarial test-only injection point; NEVER provided by runtime.
            race_hook(target)
        try:
            os.link(staged, target, follow_symlinks=False)
        except FileExistsError as exc:
            raise LabRefused("ATOMIC_DESTINATION_OCCUPIED") from exc
        except (OSError, NotImplementedError) as exc:
            # No shutil.copy fallback: either exclusive link or no publish.
            raise LabRefused("ATOMIC_LINK_UNSUPPORTED") from exc
        return target
    finally:
        # If linking succeeded, the target remains independently linked and
        # staged path removal cannot delete the published file.
        if staged.exists():
            staged.unlink()


class FailClosedTenantAndPublication(unittest.TestCase):
    @classmethod
    def _seed_fake_orm(cls):
        # E's initializer dispatches this method on cls, so explicitly reuse
        # the genuine ORM fixture without inheriting and re-running E's 12 tests.
        EFixture._seed_fake_orm.__func__(cls)

    @classmethod
    def setUpClass(cls):
        if os.environ.get(FLAG) != "1":
            raise LabRefused("FAKE_GUARD_DISABLED")
        # Reuse actual operator/init/seed from 05.7-E; no duplicate mocked
        # metadata and no fabricated alembic_version marker.
        EFixture.setUpClass.__func__(cls)
        from sqlalchemy import text
        with cls.engine.connect() as c:
            cls.fake_owners = tuple(c.execute(text(
                "SELECT id FROM users WHERE employer_id IS NULL ORDER BY id"
            )).scalars())
        if len(cls.fake_owners) != 2:
            raise LabRefused("EXPECTED_TWO_FAKE_OWNERS")

    @classmethod
    def tearDownClass(cls):
        EFixture.tearDownClass.__func__(cls)

    def setUp(self):
        EFixture.setUp(self)
        self.expected_for_publication = self.before

    def tearDown(self):
        EFixture.tearDown(self)

    def backup(self):
        return EFixture.backup(self)

    def restored_engine(self, target):
        return EFixture.restored_engine(self, target)

    def read_preflight(self, connection=None, owners=None):
        actual = self.fake_owners if owners is None else owners
        if connection is not None:
            return synthetic_tenant_preflight(connection, actual)
        with self.engine.connect() as c:
            return synthetic_tenant_preflight(c, actual)

    def publish(self, backup, *, owners=None, race_hook=None):
        return verified_no_replace_lab_publish(
            self, backup, self.fake_owners if owners is None else owners,
            race_hook=race_hook,
        )

    def _wrong_relationship_backup(self, update, revert):
        from sqlalchemy import text
        with self.engine.begin() as c:
            c.execute(text(update))
        try:
            backup = self.backup()
            self.assertNotEqual(rows_digest(self.engine), self.before)
        finally:
            with self.engine.begin() as c:
                c.execute(text(revert))
        self.assertEqual(rows_digest(self.engine), self.before)
        return backup

    def test_01_real_backup_is_staged_verified_and_published_once(self):
        from backend.core.schema_runtime import assert_database_at_current_head
        backup = self.backup()
        dest = self.publish(backup)
        self.assertTrue(dest.is_file())
        self.assertNotEqual(dest.read_bytes()[:16], b"SQLite format 3\x00")
        engine = self.restored_engine(dest)
        try:
            assert_database_at_current_head(engine)
            self.assertEqual(rows_digest(engine), self.before)
            with engine.connect() as c:
                self.assertTrue(self.read_preflight(c))
        finally:
            engine.dispose()
        self.assertEqual(list(self.home.glob(".stage_fake_*.db")), [])

    def test_02_existing_destination_never_overwritten(self):
        backup = self.backup()
        dest = self.home / "restored_fake.db"
        dest.write_bytes(b"FAKE_SENTINEL_KEEP")
        with self.assertRaisesRegex(LabRefused, "DESTINATION_ALREADY_EXISTS"):
            self.publish(backup)
        self.assertEqual(dest.read_bytes(), b"FAKE_SENTINEL_KEEP")
        self.assertFalse(list(self.home.glob(".stage_fake_*.db")))

    def test_03_target_appears_between_verified_stage_and_link(self):
        backup = self.backup()
        def appear(dest):
            dest.write_bytes(b"RACE_SENTINEL")
        with self.assertRaisesRegex(LabRefused, "ATOMIC_DESTINATION_OCCUPIED"):
            self.publish(backup, race_hook=appear)
        self.assertEqual((self.home / "restored_fake.db").read_bytes(), b"RACE_SENTINEL")
        self.assertFalse(list(self.home.glob(".stage_fake_*.db")))

    def test_04_atomic_links_unavailable_fails_without_copy_fallback(self):
        backup = self.backup()
        with patch("os.link", side_effect=PermissionError(errno.EPERM, "blocked")):
            with self.assertRaisesRegex(LabRefused, "ATOMIC_LINK_UNSUPPORTED"):
                self.publish(backup)
        self.assertFalse((self.home / "restored_fake.db").exists())
        self.assertFalse(list(self.home.glob(".stage_fake_*.db")))

    def test_05_corrupt_encrypted_backup_fails_without_target(self):
        from cryptography.fernet import InvalidToken
        backup = self.backup()
        raw = bytearray(backup.read_bytes())
        raw[len(raw) // 2] ^= 1
        backup.write_bytes(raw)
        with self.assertRaises(InvalidToken):
            self.publish(backup)
        self.assertFalse((self.home / "restored_fake.db").exists())
        self.assertFalse(list(self.home.glob(".stage_fake_*.db")))

    def test_06_explicit_fake_owner_claims_required(self):
        backup = self.backup()
        with self.assertRaisesRegex(LabRefused, "EXPLICIT_SYNTHETIC_OWNERS_REQUIRED"):
            self.publish(backup, owners=())
        with self.assertRaisesRegex(LabRefused, "SYNTHETIC_OWNER_IDENTITY_MISMATCH"):
            self.publish(backup, owners=(self.fake_owners[0], 999999))
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_07_wrong_appointment_tenant_in_backup_refused(self):
        update = """UPDATE appointments SET employer_id=(
                       SELECT id FROM users WHERE employer_id IS NULL ORDER BY id DESC LIMIT 1)
                    WHERE id=(SELECT MIN(a.id) FROM appointments a JOIN patients p ON p.id=a.patient_id
                              WHERE p.employer_id=(SELECT MIN(id) FROM users WHERE employer_id IS NULL))"""
        revert = """UPDATE appointments SET employer_id=(
                       SELECT employer_id FROM patients WHERE id=appointments.patient_id)
                    WHERE patient_id IS NOT NULL"""
        backup = self._wrong_relationship_backup(update, revert)
        with self.assertRaisesRegex(LabRefused, "APPOINTMENT_PATIENT_TENANT"):
            self.publish(backup)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_08_acte_practitioner_wrong_tenant_denied(self):
        update = """UPDATE actes SET praticien_id=(
                       SELECT MAX(id) FROM users WHERE employer_id IS NULL)
                    WHERE id=(SELECT MIN(id) FROM actes)"""
        # Restore owner based on each patient's registered dentist in this
        # two-owner fake fixture; no real user/practitioner mapping is altered.
        revert = """UPDATE actes SET praticien_id=(
                       SELECT employer_id FROM patients WHERE id=actes.patient_id)"""
        backup = self._wrong_relationship_backup(update, revert)
        with self.assertRaisesRegex(LabRefused, "ACTE_PRACTITIONER_TENANT"):
            self.publish(backup)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_09_payment_to_another_patient_acte_denied(self):
        update = """UPDATE payments SET patient_id=(
                       SELECT p.id FROM patients p JOIN actes a ON a.id=(SELECT MIN(id) FROM actes)
                       WHERE p.employer_id <> (SELECT employer_id FROM patients WHERE id=a.patient_id)
                       ORDER BY p.id LIMIT 1)
                    WHERE id=(SELECT MIN(id) FROM payments)"""
        revert = """UPDATE payments SET patient_id=(
                       SELECT patient_id FROM actes WHERE id=payments.acte_id)
                    WHERE acte_id IS NOT NULL"""
        backup = self._wrong_relationship_backup(update, revert)
        with self.assertRaisesRegex(LabRefused, "PAYMENT_ACTE_PATIENT"):
            self.publish(backup)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_10_document_uploaded_by_other_cabinet_denied(self):
        update = """UPDATE document_archives SET uploaded_by_id=(
                      SELECT MAX(id) FROM users WHERE employer_id IS NULL)
                    WHERE id=(SELECT MIN(id) FROM document_archives)"""
        revert = "UPDATE document_archives SET uploaded_by_id=NULL"
        backup = self._wrong_relationship_backup(update, revert)
        with self.assertRaisesRegex(LabRefused, "DOCUMENT_UPLOADER_TENANT"):
            self.publish(backup)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_11_source_and_destination_must_be_exact_fake_files(self):
        backup = self.backup()
        outside = self.root / "external.enc"
        outside.write_bytes(backup.read_bytes())
        with self.assertRaisesRegex(LabRefused, "FOREIGN_ENCRYPTED_BACKUP"):
            self.publish(outside)
        target = self.home / "restored_fake.db"
        with self.assertRaisesRegex(LabRefused, "FOREIGN_RESTORE_DESTINATION"):
            _lab_paths(self.root, self.home, backup, self.home / "other.db")
        with self.assertRaisesRegex(LabRefused, "FOREIGN_RESTORE_DESTINATION"):
            _lab_paths(self.root, self.home, backup, self.root / "outside.db")
        self.assertFalse(target.exists())

    def test_12_uncommitted_cross_tenant_row_read_by_same_transaction(self):
        from sqlalchemy import text
        from sqlalchemy.orm import Session
        from backend import models
        with self.engine.connect() as c:
            trans = c.begin()
            try:
                p = c.execute(text(
                    "SELECT id,employer_id FROM patients ORDER BY id LIMIT 1"
                )).one()
                other = next(x for x in self.fake_owners if x != p.employer_id)
                with Session(bind=c) as s:
                    s.add(models.Appointment(
                        patient_id=p.id, employer_id=other,
                        datetime_start=datetime(2027, 1, 2, 9),
                        duration_minutes=30, motif="FAKE_WRONG_TENANT"
                    ))
                    s.flush()
                    with self.assertRaisesRegex(LabRefused, "APPOINTMENT_PATIENT_TENANT"):
                        self.read_preflight(c)
            finally:
                trans.rollback()
        self.assertTrue(self.read_preflight())
        self.assertEqual(rows_digest(self.engine), self.before)

    def test_13_replay_of_published_target_denied(self):
        backup = self.backup()
        target = self.publish(backup)
        old_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        with self.assertRaisesRegex(LabRefused, "DESTINATION_ALREADY_EXISTS"):
            self.publish(backup)
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), old_sha)

    def test_14_legitimate_standalone_appointment_without_patient_ok(self):
        from sqlalchemy import text
        with self.engine.begin() as c:
            c.execute(text("""
INSERT INTO appointments(
 employer_id,patient_id,patient_name,datetime_start,duration_minutes,
 reminder_sent,motif
) VALUES (:owner,NULL,'FAKE_STANDALONE','2027-05-01 10:00:00',30,0,'FAKE_ONLY')
"""), {"owner":self.fake_owners[0]})
        try:
            self.assertTrue(self.read_preflight())
            self.expected_for_publication = rows_digest(self.engine)
            backup = self.backup()
            target = self.publish(backup)
            engine = self.restored_engine(target)
            try:
                self.assertEqual(rows_digest(engine), self.expected_for_publication)
            finally:
                engine.dispose()
        finally:
            with self.engine.begin() as c:
                c.execute(text("""
DELETE FROM appointments
WHERE patient_id IS NULL AND patient_name='FAKE_STANDALONE'
"""))
        self.assertEqual(rows_digest(self.engine), self.before)


if __name__ == "__main__":
    unittest.main()
