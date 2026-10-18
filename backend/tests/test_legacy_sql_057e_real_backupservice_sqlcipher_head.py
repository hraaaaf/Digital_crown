"""LOT05.7-E, test-only. Real SQLCipher + Alembic + BackupService, FAKE only.

An explicit operator "alembic upgrade head" runs on a newly created encrypted
temporary database, then the actual BackupService public route produces a
Fernet-wrapped SQLCipher export. A separate disposable file is restored using
the actual BackupService.restore_backup and verified with the current schema
gate. NOTHING is imported from a patient source. Never install as runtime code.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import hashlib
import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import unittest


HEAD = "neo000000031"
FLAG = "LOT05E_REAL_SQLCIPHER_FAKE_ONLY"
REPO = Path(__file__).resolve().parents[2]
COUNTS = {"users": 2, "patients": 6, "appointments": 12,
          "actes": 4, "payments": 4, "document_archives": 2}
AUDIT_TABLES = ("station_print_config_audit", "station_print_claim_events",
                "station_print_device_evidence", "station_print_uncertain_reviews")


class LabRefused(ValueError):
    pass


def verified_lab(root, db_path, key):
    if os.getenv(FLAG) != "1":
        raise LabRefused("SYNTHETIC_LAB_DISABLED")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise LabRefused("NONISOLATED_SOURCE")
    if not root.name.startswith("lot05e_fake_sqlcipher_"):
        raise LabRefused("NONISOLATED_SOURCE")
    if not isinstance(db_path, Path) or db_path != root / "fake_source.db":
        raise LabRefused("FOREIGN_SOURCE_DB")
    if db_path.is_symlink() or not db_path.is_file():
        raise LabRefused("FOREIGN_SOURCE_DB")
    if type(key) is not str or len(key) != 64 or set(key) - set("0123456789abcdef"):
        raise LabRefused("FAKE_STORAGE_KEY_REQUIRED")
    from backend.database import engine
    if (str(engine.url.database) != str(db_path)
            or engine.dialect.name != "sqlite" or engine.driver != "pysqlcipher"):
        raise LabRefused("FAKE_ACTIVE_ENGINE_MISMATCH")


def sqlcipher_connection(path: Path, key: str):
    from sqlcipher3 import dbapi2
    db = dbapi2.connect(str(path))
    db.execute("PRAGMA key = '" + key + "'")
    db.execute("PRAGMA foreign_keys = ON")
    return db


def rows_digest(engine):
    from sqlalchemy import text
    with engine.connect() as c:
        rows = {}
        for table in COUNTS:
            # Fixture table names are a fixed code allowlist, never user input.
            result = c.execute(text('SELECT * FROM "' + table + '" ORDER BY id'))
            rows[table] = sorted(tuple(str(x) if x is not None else None for x in row)
                                 for row in result.fetchall())
        counts = {table: len(rows[table]) for table in COUNTS}
        amount = c.execute(text("SELECT COALESCE(SUM(amount),0) FROM payments")).scalar_one()
    payload = repr(sorted(rows.items())).encode()
    return hashlib.sha256(payload).hexdigest(), counts, str(amount)


def assert_no_cross_tenant_appointments(engine, *, connection=None):
    """Read-only additional LAB gate; not connected to runtime or authorization."""
    from sqlalchemy import text
    from contextlib import nullcontext
    scope = nullcontext(connection) if connection is not None else engine.connect()
    with scope as c:
        mismatched = c.execute(text("""
SELECT COUNT(*) FROM appointments AS a
JOIN patients AS p ON p.id = a.patient_id
WHERE a.employer_id IS NULL OR p.employer_id IS NULL
   OR a.employer_id <> p.employer_id
""")).scalar_one()
        orphans = c.execute(text("""
SELECT COUNT(*) FROM appointments AS a
LEFT JOIN patients AS p ON p.id = a.patient_id
WHERE p.id IS NULL
""")).scalar_one()
    if mismatched or orphans:
        raise LabRefused("CROSS_TENANT_APPOINTMENT_OR_ORPHAN")
    return True


def require_empty_fake_destination(path: Path, home: Path):
    if (not isinstance(path, Path) or not isinstance(home, Path)
            or home.is_symlink() or not home.is_dir()
            or home.parent.name.startswith("lot05e_fake_sqlcipher_") is False
            or path.parent != home or path.name != "restored_fake.db"
            or path.is_symlink() or path.exists()):
        raise LabRefused("FAKE_DESTINATION_MUST_NOT_EXIST")


class RealEncryptedBackupServiceLab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get(FLAG) != "1":
            raise LabRefused("SYNTHETIC_LAB_DISABLED")
        cls.temp = tempfile.TemporaryDirectory(prefix="lot05e_fake_sqlcipher_")
        cls.root = Path(cls.temp.name)
        cls.source = cls.root / "fake_source.db"
        cls.fake_key = secrets.token_hex(32)
        cls.expected_env = {
            "DATABASE_URL": "sqlite:///" + cls.source.as_posix(),
            "ENVIRONMENT": "cabinet",
            "SQLCIPHER_KEY_HEX": cls.fake_key,
            "SECRET_KEY": "lot05e-unusable-fake-auth-key-only",
            "CABINET_MASTER_KEY_HEX": "e1" * 32,
        }
        cls.previous = {k: os.environ.get(k) for k in cls.expected_env}
        os.environ.update(cls.expected_env)

        # A real operator invocation, NOT an Alembic-version stamp or
        # an in-memory metadata.create_all substitution.
        proc = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=REPO, env=os.environ.copy(), capture_output=True,
            text=True, timeout=170,
        )
        if proc.returncode:
            raise LabRefused(
                "EXPLICIT_SQLCIPHER_ALEMBIC_OPERATOR_FAILED "
                + (proc.stdout + "\n" + proc.stderr)[-2400:]
            )
        from backend.database import engine
        from backend.core.schema_runtime import assert_database_at_current_head
        verified_lab(cls.root, cls.source, cls.fake_key)
        assert_database_at_current_head(engine)
        with closing(sqlcipher_connection(cls.source, cls.fake_key)) as db:
            version = db.execute("SELECT version_num FROM alembic_version").fetchone()
            if version != (HEAD,):
                raise LabRefused("REAL_SQLCIPHER_ALEMBIC_HEAD_MISMATCH")
        cls.engine = engine
        cls._seed_fake_orm()
        cls.before = rows_digest(engine)
        if cls.before[1] != COUNTS:
            raise LabRefused("WRONG_FAKE_ROWS")
        assert_no_cross_tenant_appointments(engine)

    @classmethod
    def _seed_fake_orm(cls):
        from sqlalchemy.orm import Session
        from backend import models

        with Session(cls.engine) as s:
            owners = [
                models.User(
                    email=f"lot05e-fake-{i}@invalid.example",
                    hashed_password="NOT_AN_AUTH_CREDENTIAL",
                    role=models.UserRole.DENTISTE, is_active=True,
                )
                for i in range(2)
            ]
            s.add_all(owners)
            s.flush()
            patients = []
            for n in range(6):
                owner = owners[n // 3]
                person = models.Patient(
                    numero_dossier=f"FAKE-E-{n}",
                    nom="SYNTHETIC_ONLY", prenom=f"FAKE_{n}",
                    date_naissance=datetime(2000, 1, n + 1), sexe="M",
                    employer_id=owner.id,
                )
                s.add(person)
                patients.append(person)
            s.flush()
            for n, p in enumerate(patients):
                for hour in (9, 10):
                    s.add(models.Appointment(
                        patient_id=p.id, employer_id=p.employer_id,
                        datetime_start=datetime(2026, 11, n + 1, hour),
                        duration_minutes=30, motif="FAKE_ONLY",
                    ))
            for i in range(4):
                person = patients[i]
                act = models.Acte(
                    patient_id=person.id, praticien_id=owners[i // 3].id,
                    type_acte=models.ActeType.SOIN,
                    libelle="FAKE_ACT", montant=float(140 + i),
                    notes_cliniques="FICTION_ONLY",
                )
                s.add(act)
                s.flush()
                s.add(models.Payment(
                    patient_id=person.id, acte_id=act.id, amount=float(80 + i)
                ))
            for i in (0, 3):
                person = patients[i]
                data = f"FAKE_MEDIA_E_{i}".encode()
                s.add(models.DocumentArchive(
                    patient_id=person.id,
                    document_type=list(models.DocumentType)[0],
                    filename=f"fake_doc_{i}.bin",
                    original_filename=f"fake_doc_{i}.bin",
                    file_path=f"/ONLY-FAKE-MISSING/fake_doc_{i}.bin",
                    file_hash=hashlib.sha256(data).hexdigest(),
                    file_size=len(data), document_group_id=f"FAKE_E_{i}",
                ))
            s.commit()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine"):
            cls.engine.dispose()
        for k, v in getattr(cls, "previous", {}).items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def setUp(self):
        from backend.core.paths import AppPaths
        verified_lab(self.root, self.source, self.fake_key)
        self.home = self.root / self._testMethodName
        self.home.mkdir()
        self.patch_home = patch.object(AppPaths, "get_user_data_dir", return_value=self.home)
        self.patch_home.start()

    def tearDown(self):
        self.patch_home.stop()

    def backup(self):
        from backend.services.backup_service import BackupService
        result = BackupService.backup_active_database()  # ACTUAL public route
        self.assertEqual(result["engine"], "sqlite")
        self.assertEqual(result["status"], "SUCCESS", result.get("error_code"))
        self.assertIsNone(result.get("error_code"))
        backup = self.home / "backups" / result["backup_filename"]
        self.assertTrue(backup.is_file())
        self.assertEqual(result["checksum"], hashlib.sha256(backup.read_bytes()).hexdigest())
        return backup

    def restore(self, backup, *, passphrase=None):
        from backend.services.backup_service import BackupService
        target = self.home / "restored_fake.db"
        require_empty_fake_destination(target, self.home)
        BackupService.restore_backup(
            backup, target,
            verify_sqlcipher=True,
            passphrase=self.fake_key if passphrase is None else passphrase,
        )  # ACTUAL production method, but with a lab-only destination guard
        return target

    def restored_engine(self, target):
        import sys
        import sqlcipher3
        from sqlalchemy import create_engine
        sys.modules["pysqlcipher3"] = sqlcipher3
        url = f"sqlite+pysqlcipher://:{self.fake_key}@/{target.as_posix()}"
        return create_engine(url)

    def test_01_true_sqlcipher_alembic_head_and_schema(self):
        from backend.core.schema_runtime import assert_database_at_current_head
        from sqlalchemy import inspect
        assert_database_at_current_head(self.engine)
        tables = set(inspect(self.engine).get_table_names())
        self.assertGreater(len(tables), 70)
        self.assertTrue(set(COUNTS) | {"alembic_version"} <= tables)
        with closing(sqlcipher_connection(self.source, self.fake_key)) as db:
            self.assertNotEqual(self.source.read_bytes()[:16], b"SQLite format 3\x00")
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone(), ("ok",))

    def test_02_real_backupservice_encrypted_roundtrip_full_head(self):
        from backend.core.schema_runtime import assert_database_at_current_head
        from cryptography.fernet import Fernet
        backup = self.backup()
        # Outer ciphertext is Fernet, NOT raw SQLite/SQLCipher.
        self.assertTrue(backup.read_bytes().startswith(b"gAAAA"))
        key = (self.home / "backup.key").read_bytes()
        exported = Fernet(key).decrypt(backup.read_bytes())
        self.assertNotEqual(exported[:16], b"SQLite format 3\x00")
        target = self.restore(backup)
        with closing(sqlcipher_connection(target, self.fake_key)) as db:
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone(), ("ok",))
        engine = self.restored_engine(target)
        try:
            assert_database_at_current_head(engine)
            self.assertEqual(rows_digest(engine), self.before)
            self.assertTrue(assert_no_cross_tenant_appointments(engine))
        finally:
            engine.dispose()

    def test_03_wrong_outer_fernet_key_denied(self):
        from cryptography.fernet import Fernet, InvalidToken
        from backend.services.backup_service import BackupService
        backup = self.backup()
        with patch.object(BackupService, "_get_or_create_key",
                          return_value=Fernet(Fernet.generate_key())):
            with self.assertRaises(InvalidToken):
                self.restore(backup)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_04_encrypted_backup_byte_tamper_denied(self):
        from cryptography.fernet import InvalidToken
        backup = self.backup()
        raw = bytearray(backup.read_bytes())
        raw[len(raw) // 2] ^= 1
        backup.write_bytes(raw)
        with self.assertRaises(InvalidToken):
            self.restore(backup)
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_05_wrong_inner_sqlcipher_key_denied(self):
        backup = self.backup()
        from sqlcipher3 import dbapi2
        with self.assertRaises(dbapi2.DatabaseError):
            self.restore(backup, passphrase=secrets.token_hex(32))
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_06_real_schema_cross_tenant_veto_read_only(self):
        from sqlalchemy import text
        from sqlalchemy.orm import Session
        from backend import models
        with self.engine.connect() as c:
            transaction = c.begin()
            try:
                p = c.execute(text("SELECT id, employer_id FROM patients ORDER BY id LIMIT 1")).one()
                other = c.execute(
                    text("SELECT id FROM users WHERE id <> :v ORDER BY id LIMIT 1"),
                    {"v": p.employer_id},
                ).scalar_one()
                with Session(bind=c) as session:
                    session.add(models.Appointment(
                        patient_id=p.id, employer_id=other,
                        datetime_start=datetime(2027, 1, 1, 8),
                        duration_minutes=30, motif="FAKE_CROSS_TENANT",
                    ))
                    session.flush()
                    with self.assertRaisesRegex(LabRefused, "CROSS_TENANT"):
                        assert_no_cross_tenant_appointments(self.engine, connection=c)
            finally:
                transaction.rollback()
        self.assertTrue(assert_no_cross_tenant_appointments(self.engine))
        self.assertEqual(rows_digest(self.engine), self.before)

    def test_07_snapshot_precedes_subsequent_committed_changes(self):
        from sqlalchemy import text
        backup = self.backup()
        with self.engine.begin() as c:
            c.execute(text("UPDATE patients SET nom='FAKE_LATER' WHERE id=(SELECT MIN(id) FROM patients)"))
        self.assertNotEqual(rows_digest(self.engine), self.before)
        try:
            target = self.restore(backup)
            engine = self.restored_engine(target)
            try:
                self.assertEqual(rows_digest(engine), self.before)
            finally:
                engine.dispose()
        finally:
            with self.engine.begin() as c:
                c.execute(text("UPDATE patients SET nom='SYNTHETIC_ONLY' WHERE id=(SELECT MIN(id) FROM patients)"))
        self.assertEqual(rows_digest(self.engine), self.before)

    def test_08_restored_print_audit_guards_exist(self):
        backup = self.backup()
        target = self.restore(backup)
        with closing(sqlcipher_connection(target, self.fake_key)) as db:
            rows = db.execute(
                "SELECT name, tbl_name FROM sqlite_master WHERE type='trigger'"
            ).fetchall()
        guards = set(rows)
        for table in AUDIT_TABLES:
            for op in ("update", "delete"):
                self.assertIn((f"dc_immutable_{table}_{op}", table), guards)

    def test_09_outer_fernet_backup_missing_refused(self):
        from backend.services.backup_service import BackupService
        with self.assertRaises(FileNotFoundError):
            self.restore(self.home / "not-existing.enc")
        self.assertFalse((self.home / "restored_fake.db").exists())

    def test_10_never_overwrite_lab_target_even_if_service_can_replace(self):
        backup = self.backup()
        target = self.restore(backup)
        before = target.read_bytes()
        with self.assertRaisesRegex(LabRefused, "FAKE_DESTINATION_MUST_NOT_EXIST"):
            self.restore(backup)
        self.assertEqual(target.read_bytes(), before)

    def test_11_fake_source_and_destination_guards_reject_external_paths(self):
        foreign = self.root / "foreign.db"
        foreign.write_bytes(b"NOT_A_CABINET")
        with self.assertRaisesRegex(LabRefused, "FOREIGN_SOURCE_DB"):
            verified_lab(self.root, foreign, self.fake_key)
        for other in (self.root / "restored_fake.db", self.home / "clinic.db",
                      self.home / ".." / "outside.db"):
            with self.subTest(other=other):
                with self.assertRaisesRegex(LabRefused, "FAKE_DESTINATION_MUST_NOT_EXIST"):
                    require_empty_fake_destination(other, self.home)

    def test_12_live_committed_wal_is_in_actual_export(self):
        from sqlalchemy import text
        from backend.core.schema_runtime import assert_database_at_current_head
        # Keep this writer connected while BackupService exports SQLCipher.
        with self.engine.connect() as writer:
            self.assertEqual(writer.exec_driver_sql("PRAGMA journal_mode=WAL").scalar(), "wal")
            writer.commit()
            with writer.begin():
                writer.execute(text(
                    "UPDATE patients SET nom='FAKE_WAL_COMMITTED' "
                    "WHERE id=(SELECT MIN(id) FROM patients)"
                ))
            snapshot_expected = rows_digest(self.engine)
            self.assertNotEqual(snapshot_expected, self.before)
            try:
                backup = self.backup()
                target = self.restore(backup)
                restored = self.restored_engine(target)
                try:
                    assert_database_at_current_head(restored)
                    self.assertEqual(rows_digest(restored), snapshot_expected)
                finally:
                    restored.dispose()
            finally:
                with self.engine.begin() as c:
                    c.execute(text(
                        "UPDATE patients SET nom='SYNTHETIC_ONLY' "
                        "WHERE id=(SELECT MIN(id) FROM patients)"
                    ))
        self.assertEqual(rows_digest(self.engine), self.before)


if __name__ == "__main__":
    unittest.main()
