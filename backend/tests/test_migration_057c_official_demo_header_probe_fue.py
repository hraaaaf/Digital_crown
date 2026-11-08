"""LOT05.7C-G — header-only official Open Dental trial-demo CSV QA, FAKE fixtures.

No real patients. The lab probe intentionally never parses patient record rows.
Passing these tests is NOT vendor origin, file authenticity, or import approval.
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


BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_lot05_7c_g_demo_header_probe_lab"
pkg = types.ModuleType(PACKAGE)
pkg.__path__ = [str(BACKEND / "services")]
sys.modules[PACKAGE] = pkg


def load(name):
    spec = importlib.util.spec_from_file_location(
        PACKAGE + "." + name, BACKEND / "services" / (name + ".py")
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


load("legacy_sql_inspector_v15")
lab = load("legacy_migration_vendor_demo_header_probe_lab_v15")


class OfficialDemoHeaderProbeFUE(unittest.TestCase):
    def setUp(self):
        area = tempfile.TemporaryDirectory(prefix="LOT05_7C_G_FAKE_")
        self.addCleanup(area.cleanup)
        self.root = Path(area.name)
        self.staging = self.root / "staging"
        self.staging.mkdir()
        self.file = self.staging / "FAKE_DEMO_selected_patients.csv"
        self.rows = [
            [str(i), f"FAKE_GIVEN_{i:04d}", f"FAKE_FAMILY_{i:04d}"]
            for i in range(1, 4)
        ]
        self.headers = ["PatNum", "FName", "LName"]
        self.write()

    def write(self, headers=None, rows=None, encoding="utf-8", delimiter=","):
        with self.file.open("w", encoding=encoding, newline="") as fp:
            wr = csv.writer(fp, delimiter=delimiter)
            wr.writerow(self.headers if headers is None else headers)
            wr.writerows(self.rows if rows is None else rows)

    def run_probe(self, path=None, **opts):
        kw = dict(
            operator_declared_demo_version="26.1.4",
            lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
            operator_declared_official_demo=True,
        )
        kw.update(opts)
        return lab.probe_offline_demo_csv_header(
            self.file if path is None else path,
            self.staging, **kw,
        )

    def denied(self, code, path=None, **opts):
        with self.assertRaises(lab.DemoExportHeaderRefused) as context:
            self.run_probe(path=path, **opts)
        self.assertEqual(str(context.exception), code)
        self.assertNotIn(str(self.file), str(context.exception))

    def test_01_exact_selected_header(self):
        r = self.run_probe()
        self.assertTrue(r.matched_project_projection)
        self.assertEqual(r.observed_header_field_count, 3)

    def test_02_permuted_columns(self):
        self.write(headers=["LName", "PatNum", "FName"])
        a = self.run_probe()
        self.write()
        b = self.run_probe()
        self.assertEqual(a.header_schema_sha256, b.header_schema_sha256)

    def test_03_utf8_bom(self):
        self.write(encoding="utf-8-sig")
        self.assertEqual(self.run_probe().observed_header_field_count, 3)

    def test_04_file_sha_matches_raw_bytes(self):
        r = self.run_probe()
        self.assertEqual(r.file_sha256, hashlib.sha256(self.file.read_bytes()).hexdigest())

    def test_05_file_is_unchanged(self):
        before = self.file.read_bytes()
        self.run_probe()
        self.assertEqual(before, self.file.read_bytes())

    def test_06_replay_is_deterministic(self):
        self.assertEqual(self.run_probe(), self.run_probe())

    def test_07_provenance_and_compatibility_remain_false(self):
        r = self.run_probe()
        self.assertFalse(r.actual_demo_source_verified)
        self.assertFalse(r.source_provenance_verified)
        self.assertFalse(r.vendor_format_compatible)
        self.assertFalse(r.mapping_human_approved)
        self.assertFalse(r.import_permitted)

    def test_08_no_target_or_row_count_claims(self):
        r = self.run_probe()
        self.assertIsNone(r.patient_row_count)
        self.assertIsNone(r.target_collisions)
        self.assertEqual(r.target_rows_written, 0)

    def test_09_public_report_excludes_fields_and_values(self):
        out = str(self.run_probe().public_dict())
        for value in (str(self.file), "FAKE_GIVEN_", "FAKE_FAMILY_",
                      "PatNum", "FName", "LName"):
            self.assertNotIn(value, out)

    def test_10_changed_row_alters_file_digest_not_schema_digest(self):
        old = self.run_probe()
        self.rows[0][1] = "FAKE_GIVEN_9999"
        self.write()
        new = self.run_probe()
        self.assertNotEqual(old.file_sha256, new.file_sha256)
        self.assertEqual(old.header_schema_sha256, new.header_schema_sha256)
        self.assertIsNone(new.patient_row_count)

    def test_11_non_utf8_row_is_not_interpreted(self):
        self.file.write_bytes(
            b"PatNum,FName,LName\n1,\xff,FAKE_FAMILY_0001\n"
        )
        result = self.run_probe()
        self.assertIsNone(result.patient_row_count)
        self.assertFalse(result.vendor_format_compatible)

    def test_12_missing_demo_gate(self):
        self.denied("OFFICIAL_DEMO_DECLARATION_REQUIRED",
                    operator_declared_official_demo=False)

    def test_13_missing_synthetic_gate(self):
        self.denied("LAB_SYNTHETIC_ONLY",
                    lab_only_synthetic_fixture=False)

    def test_14_gate_integer_not_boolean(self):
        self.denied("LAB_SYNTHETIC_ONLY",
                    lab_only_synthetic_fixture=1)

    def test_15_missing_staging_attestation(self):
        self.denied("OFFLINE_COPY_ATTESTATION_REQUIRED",
                    attested_offline_copy=False)

    def test_16_invalid_version_label(self):
        self.denied("INVALID_DECLARED_DEMO_VERSION",
                    operator_declared_demo_version="latest")

    def test_17_version_label_too_long(self):
        self.denied("INVALID_DECLARED_DEMO_VERSION",
                    operator_declared_demo_version="123456789.10.123456")

    def test_18_valid_short_version(self):
        self.assertEqual(
            self.run_probe(operator_declared_demo_version="24.4")
            .operator_declared_demo_version, "24.4"
        )

    def test_19_non_path_is_refused(self):
        self.denied("STAGED_PATH_REQUIRED", path=str(self.file))

    def test_20_wrong_file_extension(self):
        other = self.staging / "fake.tsv"
        other.write_bytes(self.file.read_bytes())
        self.denied("CSV_EXTENSION_REQUIRED", path=other)

    def test_21_outside_staging(self):
        other = self.root / "outside.csv"
        other.write_bytes(self.file.read_bytes())
        self.denied("OUTSIDE_STAGING_ROOT", path=other)

    def test_22_symlink_refused_if_supported(self):
        link = self.staging / "alias.csv"
        try:
            link.symlink_to(self.file)
        except (OSError, NotImplementedError):
            self.assertFalse(link.exists())
            return
        self.addCleanup(link.unlink, missing_ok=True)
        self.denied("SYMLINK_FORBIDDEN", path=link)

    def test_23_hardlink_refused_if_supported(self):
        link = self.staging / "hard.csv"
        try:
            os.link(self.file, link)
        except (OSError, NotImplementedError):
            self.assertFalse(link.exists())
            return
        self.addCleanup(link.unlink, missing_ok=True)
        self.denied("HARDLINK_SOURCE_FORBIDDEN", path=link)

    def test_24_header_extra_field(self):
        self.write(headers=self.headers + ["Birthdate"])
        self.denied("SELECTED_PROJECTION_HEADER_MISMATCH")

    def test_25_header_wrong_case(self):
        self.write(headers=["patnum", "FName", "LName"])
        self.denied("SELECTED_PROJECTION_HEADER_MISMATCH")

    def test_26_header_alias_refused(self):
        self.write(headers=["PatientNumber", "FName", "LName"])
        self.denied("SELECTED_PROJECTION_HEADER_MISMATCH")

    def test_27_duplicate_header_refused(self):
        self.write(headers=["PatNum", "PatNum", "LName"])
        self.denied("SELECTED_PROJECTION_HEADER_MISMATCH")

    def test_28_semicolon_header_refused(self):
        self.write(delimiter=";")
        self.denied("SELECTED_PROJECTION_HEADER_MISMATCH")

    def test_29_unterminated_header(self):
        self.file.write_bytes(b"PatNum,FName,LName")
        self.denied("UNTERMINATED_OR_MULTILINE_HEADER")

    def test_30_extremely_long_header(self):
        self.file.write_bytes(b"X" * 520 + b"\n")
        self.denied("HEADER_TOO_LARGE")

    def test_31_invalid_header_utf8(self):
        self.file.write_bytes(b"PatNum,\xff,LName\n1,F,N\n")
        self.denied("INVALID_CSV_HEADER")

    def test_32_empty_file(self):
        self.file.write_bytes(b"")
        self.denied("INPUT_SIZE_UNSUPPORTED")

    def test_33_adversarial_fake_row_not_exported(self):
        self.file.write_bytes(b"PatNum,FName,LName\n=1+2,SECRET_FAKE_ROW,FAKE\n")
        output = str(self.run_probe().public_dict())
        self.assertNotIn("SECRET_FAKE_ROW", output)
        self.assertIn("NO_ROWS_PARSED_OR_PATIENT_CONTENT_VALIDATED", output)

    def test_34_no_password_header(self):
        self.write(headers=["PatNum", "password", "LName"])
        self.denied("SELECTED_PROJECTION_HEADER_MISMATCH")


if __name__ == "__main__":
    unittest.main()
