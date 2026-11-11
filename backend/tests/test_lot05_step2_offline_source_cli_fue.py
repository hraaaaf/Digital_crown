"""LOT05 Étape 2 — FUE-0: exact offline CLI, 100% synthetic, no target writes.

The operator attestation is NOT provenance verification, and passing this lab
cannot authorize an import of real patient records.
"""
from __future__ import annotations

import hashlib
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


CLI = (
    Path(__file__).resolve().parents[1]
    / "services"
    / "legacy_sql_vendor_inventory_v15.py"
)


class OfflineSourceIntakeCliFUE(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="DC05_STEP2_FAKE_ONLY_")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.stage = self.root / "staging"
        self.stage.mkdir()
        self.db = self.stage / "FAKE_legacy.sqlite"
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("CREATE TABLE fake_patients (id TEXT, fake_name TEXT)")
            db.execute(
                "INSERT INTO fake_patients VALUES (?, ?)",
                ("FAKE_ID_1", "FAKE_SECRET_PATIENT_X"),
            )
            db.commit()
        self.sql = self.stage / "FAKE_schema.sql"
        self.sql.write_text(
            "CREATE TABLE fake_appointments (id INTEGER, note TEXT);\n",
            encoding="utf-8",
        )

    def cli(
        self,
        *,
        source=None,
        dialect="sqlite",
        export_format="sqlite-copy",
        software="FAKE_VENDOR",
        version="FAKE_0",
        offline=True,
        synthetic=True,
        extra=(),
    ):
        command = [
            sys.executable, "-B", str(CLI),
            "--source", str(self.db if source is None else source),
            "--staging-root", str(self.stage),
            "--source-software", software,
            "--source-version", version,
            "--dialect", dialect,
            "--export-format", export_format,
        ]
        if offline:
            command.append("--attest-offline-copy")
        if synthetic:
            command.append("--lab-synthetic-fixture")
        command.extend(extra)
        return subprocess.run(
            command,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=20, check=False,
        )

    def check_refusal(self, expected, **changes):
        result = self.cli(**changes)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(result.stdout.strip(), "REFUSED: " + expected)
        self.assertNotIn(str(self.db), result.stdout + result.stderr)
        self.assertNotIn("FAKE_SECRET_PATIENT_X", result.stdout + result.stderr)

    def test_01_help_is_static_and_harmless(self):
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), "--help"],
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("NO PATIENT IMPORT", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_02_sqlite_readonly_aggregates(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        document = json.loads(result.stdout)
        self.assertTrue(document["lab_synthetic_operator_attestation_not_verified"])
        summary = document["source_summary"]
        self.assertEqual(summary["table_count"], 1)
        self.assertEqual(summary["column_count"], 2)
        self.assertEqual(summary["source_format"], "sqlite-copy")
        self.assertFalse(summary["source_vendor_verified"])
        self.assertFalse(summary["vendor_adapter_implemented"])
        self.assertFalse(summary["human_mapping_approved"])
        self.assertFalse(summary["import_permitted"])
        self.assertEqual(summary["target_rows_written"], 0)

    def test_03_ddl_mysql_schema_only(self):
        result = self.cli(
            source=self.sql, dialect="mysql", export_format="sql-text-ddl",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads(result.stdout)["source_summary"]
        self.assertEqual(summary["table_count"], 1)
        self.assertEqual(summary["column_count"], 2)
        self.assertFalse(summary["import_permitted"])

    def test_04_schema_and_record_values_not_exported(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0)
        for forbidden in (
            str(self.db), str(self.stage), "fake_patients", "fake_name",
            "FAKE_SECRET_PATIENT_X", "FAKE_ID_1", "FAKE_VENDOR",
        ):
            self.assertNotIn(forbidden, result.stdout + result.stderr)

    def test_05_cli_is_deterministic(self):
        a = self.cli()
        b = self.cli()
        self.assertEqual(a.returncode, 0)
        self.assertEqual((a.stdout, a.stderr), (b.stdout, b.stderr))

    def test_06_synthetic_gate_required(self):
        self.check_refusal("LAB_SYNTHETIC_ONLY", synthetic=False)

    def test_07_offline_copy_gate_required(self):
        self.check_refusal("OFFLINE_COPY_ATTESTATION_REQUIRED", offline=False)

    def test_08_malformed_cli_arguments_refused_without_echo(self):
        self.check_refusal(
            "INVALID_CLI_ARGUMENTS",
            extra=["--unrecognized", "FAKE_PRIVATE_SOURCE_VALUE"],
        )

    def test_09_extension_mismatch_refused(self):
        self.check_refusal(
            "EXPORT_FORMAT_MISMATCH",
            source=self.db, dialect="mysql", export_format="sql-text-ddl",
        )

    def test_10_mismatched_sqlite_dialect_refused(self):
        self.check_refusal(
            "SQLITE_REQUIRES_SQLITE_DIALECT", dialect="postgresql",
        )

    def test_11_sql_data_statements_refused(self):
        self.sql.write_text(
            "CREATE TABLE fake_patients (id INTEGER);\n"
            "INSERT INTO fake_patients VALUES (1);\n",
            encoding="utf-8",
        )
        self.check_refusal(
            "NON_DDL_SQL_FORBIDDEN",
            source=self.sql, dialect="mysql", export_format="sql-text-ddl",
        )

    def test_12_source_outside_staging_refused(self):
        file = self.root / "FAKE_outside.sqlite"
        file.write_bytes(self.db.read_bytes())
        self.check_refusal("OUTSIDE_STAGING_ROOT", source=file)

    def test_13_invalid_sqlite_copy_refused(self):
        file = self.stage / "FAKE_invalid.sqlite"
        file.write_bytes(b"THIS_IS_NOT_SQLITE")
        self.check_refusal("SQLITE_MAGIC_MISMATCH", source=file)

    def test_14_invalid_operator_label_is_not_echoed(self):
        self.check_refusal(
            "SOURCE_SOFTWARE_REQUIRED",
            software="FAKE_PII_NAME\nFAKE_PRIVATE_SOURCE_VALUE",
        )

    def test_15_source_file_unchanged_and_hash_matches(self):
        before = self.db.read_bytes()
        result = self.cli()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(
            json.loads(result.stdout)["source_summary"]["source_sha256"],
            hashlib.sha256(before).hexdigest(),
        )

    def test_16_sqlite_wal_sidecar_refused(self):
        sidecar = self.stage / (self.db.name + "-wal")
        sidecar.write_bytes(b"FAKE_WAL_SIDECAR")
        self.check_refusal("SQLITE_SIDECAR_REQUIRES_COLD_COPY")


if __name__ == "__main__":
    unittest.main()
