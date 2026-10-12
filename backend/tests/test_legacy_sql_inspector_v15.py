"""V1.5-05.1 synthetic-only inspector regression suite."""
import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from backend.services.legacy_sql_inspector_v15 import UnsafeSource, inspect_staged_copy


class TestOfflineSqlInspector(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def sample(self, text: bytes, name: str = "copy.sql") -> Path:
        path = self.root / name
        path.write_bytes(text)
        return path

    def inspect(self, path: Path, dialect: str = "postgresql", **kwargs):
        return inspect_staged_copy(path, self.root, dialect=dialect, attested_offline_copy=True, **kwargs)

    def test_postgresql_sql_ddl_only_never_exposes_row_values(self):
        path = self.sample(
            b"CREATE TABLE public.patients (id bigint PRIMARY KEY, full_name varchar(40));\n"
            b"INSERT INTO public.patients VALUES (1, 'SECRET_SYNTHETIC_PATIENT');\n"
            b'CREATE TABLE "appointments" ("id" INTEGER, "patient_id" INT, '
            b'FOREIGN KEY ("patient_id") REFERENCES public.patients(id));'
        )
        raw = path.read_bytes()
        report = self.inspect(path)
        self.assertEqual([t.source_name for t in report.tables], ["public.patients", "appointments"])
        self.assertEqual([c.name for c in report.tables[1].columns], ["id", "patient_id"])
        self.assertEqual(report.sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(path.read_bytes(), raw)
        self.assertNotIn("SECRET_SYNTHETIC_PATIENT", str(report.to_dict()))
        self.assertIsNone(report.row_counts)
        self.assertFalse(report.mapping_approved)
        self.assertFalse(report.dry_run_completed)
        self.assertFalse(report.import_permitted)
        self.assertIn("OTHER_SQL_NOT_PARSED", report.warnings)

    def test_mysql_mariadb_quoted_columns_and_nested_type(self):
        path = self.sample(
            b"CREATE TABLE `records` (`id` bigint(20) NOT NULL, `price` decimal(10,2)); DROP TABLE records;"
        )
        report = self.inspect(path, dialect="mariadb")
        self.assertEqual(report.tables[0].source_name, "records")
        self.assertEqual([c.name for c in report.tables[0].columns], ["id", "price"])
        self.assertIn("OTHER_SQL_NOT_PARSED", report.warnings)

    def test_sqlite_offline_db_is_readonly_and_strips_patient_rows(self):
        path = self.root / "snapshot.sqlite"
        with closing(sqlite3.connect(path)) as conn:
            conn.execute('CREATE TABLE "patient details" (id INTEGER PRIMARY KEY, name TEXT)')
            conn.execute("INSERT INTO 'patient details' VALUES (1, 'SECRET_SYNTHETIC_PATIENT')")
            conn.commit()
        before = path.read_bytes()
        report = self.inspect(path, dialect="sqlite")
        self.assertEqual(report.source_format, "sqlite-copy")
        self.assertEqual(report.tables[0].source_name, "patient details")
        self.assertNotIn("SECRET_SYNTHETIC_PATIENT", str(report.to_dict()))
        self.assertEqual(path.read_bytes(), before)

    def test_explicit_attestation_required(self):
        path = self.sample(b"CREATE TABLE example (id INT);")
        with self.assertRaisesRegex(UnsafeSource, "ATTESTATION"):
            inspect_staged_copy(path, self.root, dialect="postgresql")

    def test_outside_root_denied(self):
        with tempfile.TemporaryDirectory() as other:
            path = Path(other) / "live.sql"
            path.write_text("CREATE TABLE dangerous (x INT);")
            with self.assertRaisesRegex(UnsafeSource, "OUTSIDE_STAGING_ROOT"):
                self.inspect(path)

    def test_symlink_denied(self):
        original = self.sample(b"CREATE TABLE x (id INT);")
        link = self.root / "link.sql"
        try:
            link.symlink_to(original)
        except (NotImplementedError, OSError):
            self.skipTest("symlinks not available")
        with self.assertRaisesRegex(UnsafeSource, "SYMLINK_FORBIDDEN"):
            self.inspect(link)

    def test_native_pg_dump_refused_not_claimed_supported(self):
        path = self.sample(b"PGDMP\x01\x00\x00synthetic", name="backup.dump")
        with self.assertRaisesRegex(UnsafeSource, "NATIVE_ADAPTER_NOT_IMPLEMENTED"):
            self.inspect(path)

    def test_binary_with_sql_extension_denied(self):
        path = self.sample(b"PGDMP\x01\x00\x00synthetic")
        with self.assertRaisesRegex(UnsafeSource, "FORMAT_MISMATCH"):
            self.inspect(path)

    def test_bad_sqlite_magic_denied(self):
        path = self.sample(b"not sqlite", name="copied.db")
        with self.assertRaisesRegex(UnsafeSource, "SQLITE_MAGIC_MISMATCH"):
            self.inspect(path, dialect="sqlite")

    def test_sql_without_create_table_refused(self):
        path = self.sample(b"DROP TABLE patients;")
        with self.assertRaisesRegex(UnsafeSource, "NO_SUPPORTED_TABLE_DDL"):
            self.inspect(path)

    def test_invalid_sql_create_table_fails_closed(self):
        for raw in (b"CREATE TABLE t AS SELECT * FROM records;", b"CREATE TABLE t (id INT",
                    b"CREATE TABLE t ();", b"CREATE TABLE t (id INT, id TEXT);"):
            with self.subTest(raw=raw), self.assertRaises(UnsafeSource):
                self.inspect(self.sample(raw))

    def test_explicit_encoding_only(self):
        path = self.sample(b"CREATE TABLE t (label TEXT); -- \xe9")
        with self.assertRaisesRegex(UnsafeSource, "ENCODING_INVALID"):
            self.inspect(path)
        self.assertEqual(self.inspect(path, encoding="cp1252").tables[0].source_name, "t")
        with self.assertRaisesRegex(UnsafeSource, "ENCODING_UNSUPPORTED"):
            self.inspect(path, encoding="utf-16")

    def test_dialect_must_be_explicit_known(self):
        path = self.sample(b"CREATE TABLE t (id INT);")
        with self.assertRaisesRegex(UnsafeSource, "DIALECT_MUST_BE_EXPLICIT"):
            self.inspect(path, dialect="postgresql://admin:secret@host/db")

    def test_report_is_never_approval(self):
        path = self.sample(b"CREATE TABLE t (legacy_id INTEGER);")
        report = self.inspect(path, dialect="mysql")
        self.assertEqual(report.to_dict()["import_permitted"], False)
        self.assertEqual(report.to_dict()["dry_run_completed"], False)
        self.assertEqual(report.to_dict()["mapping_approved"], False)


if __name__ == "__main__":
    unittest.main()
