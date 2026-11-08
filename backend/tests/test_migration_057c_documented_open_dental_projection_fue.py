"""LOT05.7C-F: 30 deterministic FAKE-only Open Dental query projection FUE.

The public documentation establishes a configurable Patients-Raw report and
comma-CSV export, not a fixed vendor-issued file schema. No actual vendor
data, clinic DB, network, runtime endpoint, API token, patient or import.
"""
from __future__ import annotations

import csv
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest


BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_lot05_7c_f_doc_projection_only"
pkg = types.ModuleType(PACKAGE)
pkg.__path__ = [str(BACKEND / "services")]
sys.modules[PACKAGE] = pkg


def load(name):
    spec = importlib.util.spec_from_file_location(
        PACKAGE + "." + name, BACKEND / "services" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


load("legacy_sql_inspector_v15")
load("legacy_sql_mapping_v15")
load("legacy_migration_csv_preview_v15")
load("legacy_migration_csv_envelope_lab_v15")
load("legacy_migration_csv_mapping_lab_v15")
lab = load("legacy_migration_open_dental_projection_lab_v15")


class DocumentedOpenDentalProjectionFUE(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="LOT05_7C_F_FAKE_")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.stage = self.root / "staging"
        self.stage.mkdir()
        self.source = self.stage / "FAKE_patients_raw.csv"
        self.headers = ["PatNum", "FName", "LName"]
        self.rows = [
            [str(i), f"FAKE_GIVEN_{i:04d}", f"FAKE_FAMILY_{i:04d}"]
            for i in range(1, 5)
        ]
        self.write()

    def write(self, *, headers=None, rows=None, delimiter=",", encoding="utf-8"):
        with self.source.open("w", encoding=encoding, newline="") as fd:
            writer = csv.writer(fd, delimiter=delimiter)
            writer.writerow(self.headers if headers is None else headers)
            writer.writerows(self.rows if rows is None else rows)

    def assess(self, *, source=None, **kw):
        opts = dict(lab_only_synthetic_fixture=True, attested_offline_copy=True)
        opts.update(kw)
        return lab.assess_synthetic_open_dental_patient_projection(
            self.source if source is None else source,
            self.stage,
            **opts,
        )

    def denied(self, code, *, source=None, **kw):
        with self.assertRaises(lab.DocumentedDentalProjectionRefused) as ctx:
            self.assess(source=source, **kw)
        self.assertEqual(str(ctx.exception), code)
        self.assertNotIn(str(self.source), str(ctx.exception))
        self.assertNotIn("FAKE_GIVEN", str(ctx.exception))

    def test_01_documented_three_field_projection(self):
        r = self.assess()
        self.assertEqual(r.candidate_patient_count, 4)
        self.assertEqual(r.critical_count, 0)

    def test_02_permuted_explicit_headers(self):
        order = [2, 0, 1]
        self.write(headers=[self.headers[i] for i in order],
                   rows=[[row[i] for i in order] for row in self.rows])
        r = self.assess()
        self.assertEqual(r.candidate_patient_count, 4)

    def test_03_utf8_bom(self):
        self.write(encoding="utf-8-sig")
        self.assertEqual(self.assess().candidate_patient_count, 4)

    def test_04_source_bytes_immutable(self):
        before = self.source.read_bytes()
        self.assess()
        self.assertEqual(self.source.read_bytes(), before)

    def test_05_replay_stable(self):
        self.assertEqual(self.assess(), self.assess())

    def test_06_public_output_no_source_fields_or_values(self):
        out = str(self.assess().public_dict())
        for forbidden in ("FAKE_GIVEN_", "FAKE_FAMILY_", "PatNum",
                          "FName", "LName", str(self.source), "'1'"):
            self.assertNotIn(forbidden, out)

    def test_07_all_vendor_and_clinical_gates_false(self):
        result = self.assess()
        self.assertFalse(result.source_provenance_verified)
        self.assertFalse(result.vendor_format_compatible)
        self.assertFalse(result.mapping_human_approved)
        self.assertFalse(result.real_target_verified)
        self.assertFalse(result.backup_restore_verified)
        self.assertFalse(result.import_permitted)
        self.assertIsNone(result.target_collisions)
        self.assertEqual(result.target_rows_written, 0)

    def test_08_mapping_sha_bound_to_source(self):
        old = self.assess()
        self.rows[0][1] = "FAKE_GIVEN_9999"
        self.write()
        new = self.assess()
        self.assertNotEqual(old.source_sha256, new.source_sha256)
        self.assertNotEqual(old.mapping_profile_sha256, new.mapping_profile_sha256)

    def test_09_human_readable_patnum_refused(self):
        self.rows[0][0] = "Jane Doe"
        self.write()
        self.denied("PATNUM_NOT_NUMERIC_RAW")

    def test_10_patnum_zero_refused(self):
        self.rows[0][0] = "0"
        self.write()
        self.denied("PATNUM_NOT_NUMERIC_RAW")

    def test_11_patnum_leading_zero_refused(self):
        self.rows[0][0] = "001"
        self.write()
        self.denied("PATNUM_NOT_NUMERIC_RAW")

    def test_12_duplicate_patnum_refused(self):
        self.rows[1][0] = "1"
        self.write()
        self.denied("DUPLICATE_SOURCE_PATNUM")

    def test_13_alphabetic_patnum_refused(self):
        self.rows[0][0] = "FAKE123"
        self.write()
        self.denied("PATNUM_NOT_NUMERIC_RAW")

    def test_14_realish_first_name_refused(self):
        self.rows[0][1] = "John"
        self.write()
        self.denied("NON_FAKE_PATIENT_VALUES_FORBIDDEN")

    def test_15_realish_family_name_refused(self):
        self.rows[0][2] = "Smith"
        self.write()
        self.denied("NON_FAKE_PATIENT_VALUES_FORBIDDEN")

    def test_16_missing_required_column_refused(self):
        self.write(headers=["PatNum", "FName"],
                   rows=[row[:2] for row in self.rows])
        self.denied("DOCUMENTED_PROJECTION_FIELDS_MISMATCH")

    def test_17_extra_column_refused(self):
        self.write(headers=self.headers + ["Birthdate"],
                   rows=[row + ["2001-01-01"] for row in self.rows])
        self.denied("DOCUMENTED_PROJECTION_FIELDS_MISMATCH")

    def test_18_unapproved_column_alias_refused(self):
        self.write(headers=["PatNumber", "FName", "LName"])
        self.denied("DOCUMENTED_PROJECTION_FIELDS_MISMATCH")

    def test_19_semicolon_export_not_this_profile(self):
        self.write(delimiter=";")
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT")

    def test_20_tab_extension_not_this_profile(self):
        other = self.stage / "FAKE_patients_raw.tsv"
        other.write_bytes(self.source.read_bytes())
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT", source=other)

    def test_21_outside_staging_refused(self):
        outside = self.root / "other.csv"
        outside.write_bytes(self.source.read_bytes())
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT", source=outside)

    def test_22_symlink_refused_when_supported(self):
        link = self.stage / "alias.csv"
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.assertFalse(link.exists())
            return
        self.addCleanup(link.unlink, missing_ok=True)
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT", source=link)

    def test_23_hardlink_refused_when_supported(self):
        link = self.stage / "alias.csv"
        try:
            os.link(self.source, link)
        except (OSError, NotImplementedError):
            self.assertFalse(link.exists())
            return
        self.addCleanup(link.unlink, missing_ok=True)
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT", source=link)

    def test_24_formula_cell_rejected(self):
        self.rows[0][1] = "=1+1"
        self.write()
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT")

    def test_25_credential_column_refused(self):
        self.write(headers=["PatNum", "FName", "password"])
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT")

    def test_26_invalid_utf8_refused(self):
        self.source.write_bytes(b"PatNum,FName,LName\n1,\xff,FAKE_FAMILY_0001\n")
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT")

    def test_27_duplicate_header_refused(self):
        self.write(headers=["PatNum", "PatNum", "LName"])
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT")

    def test_28_empty_export_refused(self):
        self.write(rows=[])
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT")

    def test_29_bad_csv_quotes_refused(self):
        self.source.write_text(
            'PatNum,FName,LName\n1,"FAKE_GIVEN_0001"tail,FAKE_FAMILY_0001\n',
            encoding="utf-8",
        )
        self.denied("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT")

    def test_30_missing_lab_gate_refused(self):
        self.denied("LAB_SYNTHETIC_ONLY", lab_only_synthetic_fixture=False)


if __name__ == "__main__":
    unittest.main()
