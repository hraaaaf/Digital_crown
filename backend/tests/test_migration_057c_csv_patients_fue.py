"""LOT05.7C-B — synthetic-only patient CSV source preview FUE (NO IMPORT).

No cabinet runtime, no backend DB, no patient data; all fixtures are generated
in disposable temporary directories. Both platforms exercise identical tests.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_lot05c_csv_synthetic_only"
if PACKAGE not in sys.modules:
    scope = types.ModuleType(PACKAGE)
    scope.__path__ = [str(BACKEND / "services")]
    sys.modules[PACKAGE] = scope


def load(module_name: str):
    fullname = PACKAGE + "." + module_name
    spec = importlib.util.spec_from_file_location(
        fullname, BACKEND / "services" / (module_name + ".py")
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = mod
    spec.loader.exec_module(mod)
    return mod


load("legacy_sql_inspector_v15")
preview = load("legacy_migration_csv_preview_v15")


class CsvPatientPreviewFUE(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="dc05_csv_FAKE_ONLY_")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.stage = self.root / "staged"
        self.stage.mkdir()
        self.source = self.stage / "FAKE_patients.csv"
        self.headers = ["legacy_id", "given_name", "family_name", "birth_date"]
        self.records = [
            [str(i).zfill(6), "FAKE_FIRST_" + str(i),
             "FAKE_LAST_" + str(i), "2010-01-01"]
            for i in range(100)
        ]
        self.write()

    def write(self, headers=None, records=None):
        with self.source.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(self.headers if headers is None else headers)
            writer.writerows(self.records if records is None else records)

    def check(self, source=None, **updates):
        kwargs = {
            "lab_only_synthetic_fixture": True,
            "attested_offline_copy": True,
        }
        kwargs.update(updates)
        return preview.preview_synthetic_patient_csv(
            self.source if source is None else source, self.stage, **kwargs
        )

    def denied(self, code, source=None, **updates):
        with self.assertRaises(preview.CsvPatientPreviewRefused) as failure:
            self.check(source, **updates)
        self.assertEqual(str(failure.exception), code)
        self.assertNotIn("FAKE_FIRST_", str(failure.exception))

    def test_01_100_patients_aggregate_only(self):
        before = self.source.read_bytes()
        result = self.check()
        report = result.to_public_dict()
        self.assertEqual(result.row_count, 100)
        self.assertEqual(result.source_sha256, hashlib.sha256(before).hexdigest())
        self.assertEqual(result.column_count, 4)
        self.assertEqual(before, self.source.read_bytes())
        self.assertTrue(result.lab_only)
        self.assertFalse(result.vendor_adapter_implemented)
        self.assertFalse(result.mapping_approved)
        self.assertFalse(result.dry_run_completed)
        self.assertFalse(result.import_permitted)
        self.assertFalse(result.full_schema_certified)
        self.assertFalse(result.schema_semantics_certified)
        self.assertEqual(result.target_rows_written, 0)
        self.assertNotIn("FAKE_FIRST", str(report))
        self.assertNotIn("FAKE_LAST", str(report))
        self.assertNotIn("000001", str(report))

    def test_02_different_column_order_allowed(self):
        self.write(
            ["family_name", "legacy_id", "given_name"],
            [["FAKE_LAST", "000001", "FAKE_FIRST"]],
        )
        result = self.check()
        self.assertEqual(result.row_count, 1)
        self.assertFalse(result.date_field_present)

    def test_03_optional_leap_birth_date(self):
        self.write(records=[["A1", "FAKE", "PERSON", "2000-02-29"]])
        self.assertTrue(self.check().date_field_present)

    def test_04_optional_empty_birth_date(self):
        self.write(records=[["A1", "FAKE", "PERSON", ""]])
        self.assertEqual(self.check().row_count, 1)

    def test_05_missing_attestation_refused(self):
        self.denied("OFFLINE_COPY_ATTESTATION_REQUIRED", attested_offline_copy=False)

    def test_06_int_is_not_boolean_attestation(self):
        self.denied("OFFLINE_COPY_ATTESTATION_REQUIRED", attested_offline_copy=1)

    def test_07_laboratory_flag_required(self):
        self.denied("LAB_SYNTHETIC_ONLY", lab_only_synthetic_fixture=False)

    def test_08_laboratory_int_is_not_boolean(self):
        self.denied("LAB_SYNTHETIC_ONLY", lab_only_synthetic_fixture=1)

    def test_09_wrong_extension_refused(self):
        other = self.stage / "fake.bin"
        other.write_bytes(self.source.read_bytes())
        self.denied("CSV_EXTENSION_REQUIRED", other)

    def test_10_outside_stage_refused(self):
        other = self.root / "outside.csv"
        other.write_bytes(self.source.read_bytes())
        self.denied("OUTSIDE_STAGING_ROOT", other)

    def test_11_symlink_refused_if_supported(self):
        link = self.stage / "alias.csv"
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("OS symlinks unavailable")
        self.addCleanup(link.unlink, missing_ok=True)
        self.denied("SYMLINK_FORBIDDEN", link)

    def test_12_hardlink_refused_if_supported(self):
        link = self.stage / "hardlink.csv"
        try:
            os.link(self.source, link)
        except (OSError, NotImplementedError):
            self.skipTest("OS hardlinks unavailable")
        self.addCleanup(link.unlink, missing_ok=True)
        self.denied("HARDLINK_SOURCE_FORBIDDEN", self.source)

    def test_13_duplicate_source_patient_refused(self):
        rows = self.records[:3]
        rows[2] = list(rows[1])
        self.write(records=rows)
        self.denied("DUPLICATE_SOURCE_PATIENT_ID")

    def test_14_missing_required_field_refused(self):
        self.write(
            ["legacy_id", "given_name", "birth_date"],
            [["A1", "FAKE", "2000-01-01"]],
        )
        self.denied("UNSUPPORTED_CSV_COLUMNS")

    def test_15_extra_sensitive_column_refused(self):
        self.write(
            ["legacy_id", "given_name", "family_name", "password"],
            [["A1", "FAKE", "PERSON", "SYNTHETIC_PASSWORD"]],
        )
        self.denied("UNSUPPORTED_CSV_COLUMNS")

    def test_16_duplicate_header_refused(self):
        self.write(
            ["legacy_id", "given_name", "given_name", "family_name"],
            [["A1", "FAKE", "FAKE", "PERSON"]],
        )
        self.denied("DUPLICATE_CSV_COLUMN")

    def test_17_empty_file_refused(self):
        self.source.write_bytes(b"")
        self.denied("INPUT_SIZE_UNSUPPORTED")

    def test_18_headers_only_refused(self):
        self.write(records=[])
        self.denied("EMPTY_PATIENT_CSV")

    def test_19_unbalanced_csv_row_refused(self):
        self.write(records=[["A1", "FAKE"]])
        self.denied("CSV_COLUMN_COUNT_MISMATCH")

    def test_20_excel_formula_refused(self):
        self.write(records=[["A1", "=HYPERLINK(1)", "PERSON", "2010-01-01"]])
        self.denied("UNSAFE_CSV_CELL")

    def test_21_whitespace_obfuscated_formula_refused(self):
        self.write(records=[["A1", "   @SUM(1)", "PERSON", "2010-01-01"]])
        self.denied("UNSAFE_CSV_CELL")

    def test_22_ambiguous_birth_date_refused(self):
        self.write(records=[["A1", "FAKE", "PERSON", "01/02/2010"]])
        self.denied("AMBIGUOUS_PATIENT_BIRTH_DATE")

    def test_23_invalid_calendar_date_refused(self):
        self.write(records=[["A1", "FAKE", "PERSON", "2026-02-30"]])
        self.denied("INVALID_PATIENT_BIRTH_DATE")

    def test_24_embedded_newline_refused(self):
        self.write(records=[["A1", "FAKE\nINJECTION", "PERSON", "2010-01-01"]])
        self.denied("UNSAFE_CSV_CELL")

    def test_25_invalid_utf8_refused(self):
        self.source.write_bytes(
            b"legacy_id,given_name,family_name\n1,\xff,FAKE\n"
        )
        self.denied("INVALID_OR_CHANGED_CSV")

    def test_26_invalid_id_refused(self):
        self.write(records=[["/../", "FAKE", "PERSON", "2010-01-01"]])
        self.denied("INVALID_SOURCE_PATIENT_ID")

    def test_27_large_name_refused(self):
        self.write(records=[["A1", "A"*257, "PERSON", "2010-01-01"]])
        self.denied("UNSAFE_CSV_CELL")

    def test_28_reject_truncated_quoted_csv(self):
        self.source.write_text(
            'legacy_id,given_name,family_name\nA1,"UNFINISHED,FAKE\n',
            encoding="utf-8",
        )
        self.denied("INVALID_OR_CHANGED_CSV")

    def test_29_reject_missing_source_path(self):
        self.denied("STAGED_FILE_UNAVAILABLE", self.stage / "missing.csv")

    def test_30_file_hash_changed_mid_preview_refused(self):
        original = preview._hash
        calls = [0]
        def mismatching_hash(file):
            calls[0] += 1
            return original(file) if calls[0] == 1 else "0" * 64
        with patch.object(preview, "_hash", side_effect=mismatching_hash):
            self.denied("SOURCE_CHANGED_DURING_PREVIEW")

    def test_31_bounded_number_of_rows(self):
        self.write(records=[
            [str(i), "FAKE", "PERSON", "2010-01-01"] for i in range(10_001)
        ])
        self.denied("CSV_ROW_LIMIT_EXCEEDED")

    def test_32_nonpath_inputs_refused(self):
        self.denied("STAGED_PATH_REQUIRED", "not-a-path.csv")


if __name__ == "__main__":
    unittest.main()
