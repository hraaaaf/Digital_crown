"""LOT05.7C-A FUE: vendor-neutral, non-PHI, READ-ONLY source inventory.

All source data is generated inside a disposable directory; never load cabinet
runtime, connect to a target database, or export any legacy patient data.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import importlib.util
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest

BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_lot05c_lab_readonly"
if PACKAGE not in sys.modules:
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(BACKEND / "services")]
    sys.modules[PACKAGE] = package


def load(module_name: str):
    qualified = PACKAGE + "." + module_name
    if qualified in sys.modules:
        return sys.modules[qualified]
    spec = importlib.util.spec_from_file_location(
        qualified, BACKEND / "services" / (module_name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)
    return module


load("legacy_sql_inspector_v15")
inventory = load("legacy_sql_vendor_inventory_v15")


class ReadOnlyVendorInventoryFUE(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="dc05c_FAKE_only_")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.stage = self.root / "staged"
        self.stage.mkdir()
        self.sqlite = self.stage / "FAKE_export.sqlite"
        with closing(sqlite3.connect(self.sqlite)) as db:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("CREATE TABLE legacy_patients (id TEXT, fake_name TEXT)")
            db.executemany(
                "INSERT INTO legacy_patients VALUES (?,?)",
                [(str(i), f"FAKE_PATIENT_SECRET_{i}") for i in range(100)],
            )
            db.commit()
        self.sql = self.stage / "FAKE_structure.sql"
        self.sql.write_text(
            "CREATE TABLE legacy_visits (id INTEGER, starts_at TEXT);\n",
            encoding="utf-8",
        )

    def check(self, path=None, *, format="sqlite-copy", dialect="sqlite", **overrides):
        kwargs = dict(
            source_software="FAKE_VENDOR",
            source_version="0.0-synthetic",
            dialect=dialect,
            export_format=format,
            attested_offline_copy=True,
        )
        kwargs.update(overrides)
        return inventory.inventory_declared_legacy_copy(
            self.sqlite if path is None else path, self.stage, **kwargs
        )

    def assert_refused(self, code, path=None, **changes):
        with self.assertRaises(inventory.VendorInventoryRefused) as ctx:
            self.check(path, **changes)
        self.assertEqual(str(ctx.exception), code)
        self.assertNotIn("FAKE_PATIENT_SECRET", str(ctx.exception))

    def test_01_sqlite_cold_copy_metadata_only(self):
        before = self.sqlite.read_bytes()
        result = self.check()
        report = result.to_public_dict()
        self.assertEqual(result.source_sha256, hashlib.sha256(before).hexdigest())
        self.assertEqual(result.table_count, 1)
        self.assertEqual(result.column_count, 2)
        self.assertEqual(result.source_format, "sqlite-copy")
        self.assertEqual(self.sqlite.read_bytes(), before)
        self.assertFalse(result.vendor_adapter_implemented)
        self.assertFalse(result.human_mapping_approved)
        self.assertFalse(result.full_schema_certified)
        self.assertFalse(result.import_permitted)
        self.assertEqual(result.target_rows_written, 0)
        self.assertNotIn("FAKE_PATIENT_SECRET", str(report))
        self.assertNotIn("legacy_patients", str(report))
        self.assertNotIn("FAKE_VENDOR", str(report))
        self.assertNotIn("id", report)

    def test_02_schema_only_plain_ddl(self):
        result = self.check(self.sql, format="sql-text-ddl", dialect="postgresql")
        self.assertEqual(result.table_count, 1)
        self.assertEqual(result.column_count, 2)
        self.assertEqual(result.source_format, "sql-text-ddl")
        self.assertFalse(result.import_permitted)

    def test_03_unknown_vendor_refused(self):
        self.assert_refused("SOURCE_SOFTWARE_REQUIRED", source_software="")

    def test_04_vendor_label_type_refused(self):
        self.assert_refused("SOURCE_SOFTWARE_REQUIRED", source_software=("fake",))

    def test_05_unknown_version_refused(self):
        self.assert_refused("SOURCE_VERSION_REQUIRED", source_version=None)

    def test_06_control_characters_refused_no_value_leak(self):
        self.assert_refused("SOURCE_SOFTWARE_REQUIRED", source_software="Vendor\nPERSON")

    def test_07_unattested_copy_refused(self):
        self.assert_refused("OFFLINE_COPY_ATTESTATION_REQUIRED", attested_offline_copy=False)
        self.assert_refused("OFFLINE_COPY_ATTESTATION_REQUIRED", attested_offline_copy=1)

    def test_08_unknown_dialect_refused(self):
        self.assert_refused("DIALECT_UNSUPPORTED", dialect="mssql")

    def test_09_unknown_export_format_refused(self):
        self.assert_refused("EXPORT_FORMAT_UNSUPPORTED", export_format="native-archive")

    def test_10_suffix_mismatch_refused(self):
        self.assert_refused("EXPORT_FORMAT_MISMATCH", format="sql-text-ddl")
        self.assert_refused(
            "EXPORT_FORMAT_MISMATCH", self.sql, format="sqlite-copy"
        )

    def test_11_non_ddl_insert_refused(self):
        self.sql.write_text(
            "CREATE TABLE t (id INTEGER);\n"
            "INSERT INTO t VALUES (123);\n", encoding="utf-8",
        )
        self.assert_refused("NON_DDL_SQL_FORBIDDEN", self.sql,
                            format="sql-text-ddl", dialect="mysql")

    def test_12_non_ddl_copy_refused(self):
        self.sql.write_text(
            "CREATE TABLE t (id INTEGER);\n"
            "COPY t FROM STDIN;\n", encoding="utf-8",
        )
        self.assert_refused("NON_DDL_SQL_FORBIDDEN", self.sql,
                            format="sql-text-ddl", dialect="postgresql")

    def test_13_native_pg_dump_refused(self):
        native = self.stage / "FAKE.dump"
        native.write_bytes(b"PGDMP" + b"\x00" * 64)
        self.assert_refused("EXPORT_FORMAT_MISMATCH", native,
                            format="sql-text-ddl", dialect="postgresql")

    def test_14_sqlite_fake_header_refused(self):
        invalid = self.stage / "malformed.sqlite"
        invalid.write_bytes(b"NOT A SQLITE DB")
        self.assert_refused("SQLITE_MAGIC_MISMATCH", invalid)

    def test_15_wrong_dialect_for_sqlite_refused(self):
        self.assert_refused("SQLITE_REQUIRES_SQLITE_DIALECT", dialect="postgresql")

    def test_16_outside_stage_refused(self):
        other = self.root / "not_in_staging.sqlite"
        other.write_bytes(self.sqlite.read_bytes())
        self.assert_refused("OUTSIDE_STAGING_ROOT", other)

    def test_17_sqlite_wal_sidecar_refused(self):
        sidecar = self.stage / (self.sqlite.name + "-wal")
        sidecar.write_bytes(b"FAKE")
        self.addCleanup(sidecar.unlink, missing_ok=True)
        self.assert_refused("SQLITE_SIDECAR_REQUIRES_COLD_COPY")

    def test_18_nonexistent_source_refused(self):
        self.assert_refused("STAGED_FILE_UNAVAILABLE", self.stage / "missing.sqlite")

    def test_19_symlink_refused_when_supported(self):
        target = self.stage / "softlink.sqlite"
        try:
            target.symlink_to(self.sqlite)
        except (OSError, NotImplementedError):
            self.skipTest("OS does not allow creating test symlinks")
        self.addCleanup(target.unlink, missing_ok=True)
        self.assert_refused("SYMLINK_FORBIDDEN", target)

    def test_20_vendors_not_claimed_certified(self):
        result = self.check(source_software="FAKE Dental + Demo")
        self.assertEqual(
            result.warnings,
            ("SOURCE_VENDOR_DECLARATION_NOT_VERIFIED",
             "SOURCE_SCHEMA_ONLY_NO_SEMANTIC_MAPPING"),
        )
        self.assertFalse(result.source_vendor_verified)
        self.assertFalse(result.target_backup_verified)
        self.assertEqual(result.target_rows_written, 0)

    def test_21_case_insensitive_sqlite_extension(self):
        copied = self.stage / "FAKE_EXPORT.SQLITE"
        copied.write_bytes(self.sqlite.read_bytes())
        self.assertEqual(self.check(copied).source_format, "sqlite-copy")

    def test_22_sql_with_sensitive_default_only_aggregates(self):
        self.sql.write_text(
            "CREATE TABLE t (id INTEGER, memo TEXT DEFAULT 'FAKE_SECRET');",
            encoding="utf-8",
        )
        result = self.check(self.sql, format="sql-text-ddl")
        self.assertNotIn("FAKE_SECRET", str(result.to_public_dict()))
        self.assertEqual(result.table_count, 1)


if __name__ == "__main__":
    unittest.main()
