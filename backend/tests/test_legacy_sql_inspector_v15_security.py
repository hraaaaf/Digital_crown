"""Adversarial LOT05.1 tests. Synthetic copies only, no actual patient data."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Load only the standalone stdlib module, never backend/__init__.py.
import importlib.util
import sys

module_path = Path(__file__).resolve().parents[1] / "services" / "legacy_sql_inspector_v15.py"
spec = importlib.util.spec_from_file_location("legacy_sql_inspector_v15", module_path)
inspector = sys.modules.get(spec.name)
if inspector is None:
    inspector = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = inspector
    spec.loader.exec_module(inspector)


class TestLegacyInspectorSecurity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def source(self, content, name="copy.sql"):
        path = self.root / name
        path.write_bytes(content)
        return path

    def inspect(self, path, dialect="postgresql"):
        return inspector.inspect_staged_copy(
            path, self.root, dialect=dialect, attested_offline_copy=True
        )

    def test_ddl_default_values_never_enter_report(self):
        path = self.source(
            b"CREATE TABLE t (id INTEGER, name VARCHAR(32) DEFAULT 'PHI_SYNTHETIC_SECRET', "
            b"cost DECIMAL(10,2) DEFAULT 57.38, note TEXT DEFAULT 'a,b,c');"
        )
        report = self.inspect(path).to_dict()
        self.assertNotIn("PHI_SYNTHETIC_SECRET", str(report))
        self.assertNotIn("57.38", str(report))
        self.assertEqual([col["declared_type"] for col in report["tables"][0]["columns"]],
                         ["INTEGER", "VARCHAR(32)", "DECIMAL(10,2)", "TEXT"])
        self.assertFalse(report["import_permitted"])

    def test_pg_default_password_stays_in_staging(self):
        path = self.source(b"CREATE TABLE users (hashed_password TEXT DEFAULT 'HASH_SYNTHETIC');")
        self.assertNotIn("HASH_SYNTHETIC", str(self.inspect(path).to_dict()))

    def test_mysql_unsigned_is_not_invented_or_dropped(self):
        path = self.source(b"CREATE TABLE accounts (account_id BIGINT UNSIGNED NOT NULL);")
        self.assertEqual(self.inspect(path, "mysql").tables[0].columns[0].declared_type,
                         "BIGINT UNSIGNED")

    def test_custom_type_does_not_disclose_potential_private_identifier(self):
        path = self.source(b"CREATE TABLE patients (id SECRET_PATIENT_IDENTIFIED_TYPE);")
        with self.assertRaisesRegex(inspector.UnsafeSource, "UNSUPPORTED_COLUMN_TYPE"):
            self.inspect(path)

    def test_unsupported_trailing_sql_is_not_treated_as_table_ddl(self):
        for ddl in (b"CREATE TABLE t (id INTEGER) AS SELECT 1;",
                    b"CREATE TABLE t (id INTEGER) PARTITION BY RANGE (id);"):
            with self.subTest(ddl=ddl), self.assertRaisesRegex(
                inspector.UnsafeSource, "UNSUPPORTED_TABLE_OPTIONS"
            ):
                self.inspect(self.source(ddl))

    def test_hardlink_to_an_external_original_is_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            original = Path(other) / "original.sql"
            original.write_bytes(b"CREATE TABLE x (id INTEGER);")
            link = self.root / "copy.sql"
            try:
                os.link(original, link)
            except (OSError, NotImplementedError):
                self.skipTest("Hardlinks unavailable")
            with self.assertRaisesRegex(inspector.UnsafeSource, "HARDLINK_SOURCE_FORBIDDEN"):
                self.inspect(link)
            self.assertEqual(original.read_bytes(), b"CREATE TABLE x (id INTEGER);")

    def test_symlinked_parent_directory_is_refused(self):
        real = self.root / "real"
        real.mkdir()
        (real / "copy.sql").write_bytes(b"CREATE TABLE x (id INTEGER);")
        alias = self.root / "alias"
        try:
            alias.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(inspector.UnsafeSource, "SYMLINK_FORBIDDEN"):
            self.inspect(alias / "copy.sql")

    def test_sqlite_wal_sidecar_requires_cold_copy(self):
        db = self.root / "copy.sqlite"
        with sqlite3.connect(db) as cx:
            cx.execute("CREATE TABLE people (id INTEGER PRIMARY KEY, name TEXT)")
            cx.commit()
        sidecar = self.root / "copy.sqlite-wal"
        sidecar.write_bytes(b"synthetic WAL placeholder")
        before = db.read_bytes()
        with self.assertRaisesRegex(inspector.UnsafeSource,
                                    "SQLITE_SIDECAR_REQUIRES_COLD_COPY"):
            self.inspect(db, "sqlite")
        self.assertEqual(db.read_bytes(), before)

    def test_sqlite_inspection_does_not_create_sidecars(self):
        db = self.root / "copy.sqlite"
        with sqlite3.connect(db) as cx:
            cx.execute("CREATE TABLE people (id INTEGER PRIMARY KEY)")
            cx.commit()
        before = db.read_bytes()
        report = self.inspect(db, "sqlite")
        self.assertEqual(report.tables[0].source_name, "people")
        self.assertEqual(before, db.read_bytes())
        self.assertFalse((self.root / "copy.sqlite-wal").exists())
        self.assertFalse((self.root / "copy.sqlite-shm").exists())

    def test_same_length_mutation_during_inspection_is_detected(self):
        db = self.source(b"CREATE TABLE test (id INTEGER);")
        original = inspector._sql
        def changed(sql):
            out = original(sql)
            db.write_bytes(db.read_bytes().replace(b"INTEGER", b"DECIMAL"))
            return out
        with patch.object(inspector, "_sql", changed):
            with self.assertRaisesRegex(inspector.UnsafeSource, "SOURCE_CHANGED_DURING_INSPECTION"):
                self.inspect(db)

    def test_report_cannot_be_approving_migration(self):
        report = self.inspect(self.source(b"CREATE TABLE t (id INT);")).to_dict()
        for gate in ("import_permitted", "mapping_approved", "dry_run_completed"):
            self.assertIs(report[gate], False)
        self.assertIsNone(report["row_counts"])


if __name__ == "__main__":
    unittest.main()
