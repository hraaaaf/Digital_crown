"""LOT05.7C-E: 30 FAKE-only syntax-envelope regression tests.

All files are created within disposable staging; no patient or vendor data.
No backend app/runtime dependencies, database, network, or target writer.
"""
from __future__ import annotations

import csv
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import tempfile
import types

import unittest


BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_lot05_7c_e_export_envelope_lab"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(BACKEND / "services")]
sys.modules[PACKAGE] = package


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
lab = load("legacy_migration_csv_envelope_lab_v15")


class SyntheticExportEnvelopeFUE(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="LOT05_7C_E_FAKE_")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.stage = self.root / "staged"
        self.stage.mkdir()
        self.source = self.stage / "FAKE_export.csv"
        self.headers = ["legacy_id", "given_name", "family_name"]
        self.rows = [
            [f"FAKE{i:04d}", f"FAKE_GIVEN_{i}", f"FAKE_FAMILY_{i}"]
            for i in range(3)
        ]
        self.write()

    def write(self, *, delimiter=",", headers=None, rows=None,
              encoding="utf-8", path=None):
        with (path or self.source).open("w", newline="", encoding=encoding) as fd:
            writer = csv.writer(fd, delimiter=delimiter)
            writer.writerow(self.headers if headers is None else headers)
            writer.writerows(self.rows if rows is None else rows)

    def inspect(self, profile="csv-comma-utf8", *, path=None, **overrides):
        kw = dict(syntax_profile=profile, lab_only_synthetic_fixture=True,
                  attested_offline_copy=True)
        kw.update(overrides)
        return lab.inspect_synthetic_csv_envelope(
            self.source if path is None else path, self.stage, **kw
        )

    def denied(self, code, fn, *args, **kwargs):
        with self.assertRaises(lab.SyntheticExportEnvelopeRefused) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(str(ctx.exception), code)
        self.assertNotIn(str(self.source), str(ctx.exception))
        self.assertNotIn("FAKE_GIVEN", str(ctx.exception))

    def test_01_comma_utf8_syntax(self):
        r = self.inspect()
        self.assertEqual((r.row_count, r.column_count), (3, 3))
        self.assertEqual(r.syntax_profile_declared, "csv-comma-utf8")

    def test_02_semicolon_utf8_with_quoted_comma(self):
        self.rows[0][1] = "FAKE,NAME"
        self.write(delimiter=";")
        r = self.inspect("csv-semicolon-utf8")
        self.assertEqual(r.row_count, 3)

    def test_03_tab_utf8_syntax(self):
        self.source = self.stage / "FAKE_export.tsv"
        self.write(delimiter="\t")
        self.assertEqual(self.inspect("tsv-tab-utf8").row_count, 3)

    def test_04_utf8_bom_accepted(self):
        self.write(encoding="utf-8-sig")
        self.assertEqual(self.inspect().row_count, 3)

    def test_05_header_digest_stable_across_separators(self):
        a = self.inspect()
        self.write(delimiter=";")
        b = self.inspect("csv-semicolon-utf8")
        self.assertEqual(a.header_schema_sha256, b.header_schema_sha256)
        self.assertNotEqual(a.source_sha256, b.source_sha256)

    def test_06_source_bytes_unchanged(self):
        before = self.source.read_bytes()
        self.inspect()
        self.assertEqual(self.source.read_bytes(), before)

    def test_07_public_report_no_headers_or_fake_values(self):
        report = str(self.inspect().public_dict())
        for forbidden in ("FAKE0000", "FAKE_GIVEN", "legacy_id",
                          "family_name", str(self.source)):
            self.assertNotIn(forbidden, report)

    def test_08_no_vendor_or_clinical_approval(self):
        r = self.inspect()
        self.assertFalse(r.source_provenance_verified)
        self.assertFalse(r.vendor_format_compatible)
        self.assertFalse(r.mapping_human_approved)
        self.assertFalse(r.real_target_verified)
        self.assertFalse(r.backup_restore_verified)
        self.assertFalse(r.import_permitted)
        self.assertEqual(r.target_rows_written, 0)
        self.assertIsNone(r.target_collisions)

    def test_09_unknown_syntax_denied(self):
        self.denied("UNSUPPORTED_SYNTAX_PROFILE", self.inspect, "csv-auto")

    def test_10_nonstring_syntax_denied(self):
        self.denied("UNSUPPORTED_SYNTAX_PROFILE", self.inspect, 1)

    def test_11_missing_lab_gate_denied(self):
        self.denied("LAB_SYNTHETIC_ONLY", self.inspect,
                    lab_only_synthetic_fixture=False)

    def test_12_integer_lab_gate_denied(self):
        self.denied("LAB_SYNTHETIC_ONLY", self.inspect,
                    lab_only_synthetic_fixture=1)

    def test_13_missing_offline_attestation_denied(self):
        self.denied("OFFLINE_COPY_ATTESTATION_REQUIRED", self.inspect,
                    attested_offline_copy=False)

    def test_14_outside_staging_denied(self):
        outside = self.root / "outside.csv"
        outside.write_bytes(self.source.read_bytes())
        self.denied("OUTSIDE_STAGING_ROOT", self.inspect, path=outside)

    def test_15_symlink_denied_if_available(self):
        link = self.stage / "alias.csv"
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable on this runner")
        self.addCleanup(link.unlink, missing_ok=True)
        self.denied("SYMLINK_FORBIDDEN", self.inspect, path=link)

    def test_16_hardlink_denied_if_available(self):
        link = self.stage / "alias.csv"
        try:
            import os
            os.link(self.source, link)
        except (OSError, NotImplementedError):
            self.skipTest("Hardlinks unavailable on this runner")
        self.addCleanup(link.unlink, missing_ok=True)
        self.denied("HARDLINK_SOURCE_FORBIDDEN", self.inspect, path=link)

    def test_17_wrong_extension_denied(self):
        self.denied("EXPORT_EXTENSION_MISMATCH", self.inspect, "tsv-tab-utf8")

    def test_18_wrong_delimiter_denied(self):
        self.write(delimiter=";")
        self.denied("UNSUPPORTED_EXPORT_HEADER", self.inspect)

    def test_19_formula_in_unmapped_field_denied(self):
        self.rows[0].append("=1+1")
        self.rows[1].append("FAKE_FIELD")
        self.rows[2].append("FAKE_FIELD")
        self.write(headers=self.headers + ["other"])
        self.denied("UNSAFE_EXPORT_CELL", self.inspect)

    def test_20_duplicate_casefolded_header_denied(self):
        self.write(headers=["legacy_id", "Legacy_Id", "name"])
        self.denied("DUPLICATE_EXPORT_HEADER", self.inspect)

    def test_21_credential_column_denied(self):
        self.write(headers=["legacy_id", "password", "family_name"])
        self.denied("UNSAFE_EXPORT_HEADER", self.inspect)

    def test_22_newline_inside_quoted_cell_denied(self):
        self.rows[0][1] = "FAKE\nNAME"
        self.write()
        self.denied("UNSAFE_EXPORT_CELL", self.inspect)

    def test_23_invalid_utf8_denied(self):
        self.source.write_bytes(b"legacy_id,given_name,family_name\nFAKE001,\xff,FAKE\n")
        self.denied("INVALID_OR_CHANGED_EXPORT", self.inspect)

    def test_24_empty_data_denied(self):
        self.write(rows=[])
        self.denied("EMPTY_EXPORT", self.inspect)

    def test_25_large_cell_denied(self):
        self.rows[0][1] = "F" * 257
        self.write()
        self.denied("UNSAFE_EXPORT_CELL", self.inspect)

    def test_26_column_mismatch_denied(self):
        self.rows[0].pop()
        self.write()
        self.denied("EXPORT_COLUMN_MISMATCH", self.inspect)

    def test_27_invalid_quoted_cell_denied(self):
        self.source.write_text(
            'legacy_id,given_name,family_name\nFAKE001,"FAKE"tail,FAKE\n',
            encoding="utf-8",
        )
        self.denied("INVALID_OR_CHANGED_EXPORT", self.inspect)

    def test_28_deterministic_digest_and_counts(self):
        a, b = self.inspect(), self.inspect()
        self.assertEqual(a, b)

    def test_29_invalid_header_whitespace_denied(self):
        self.write(headers=["legacy id", "given_name", "family_name"])
        self.denied("UNSAFE_EXPORT_HEADER", self.inspect)

    def test_30_too_many_columns_denied(self):
        headers = ["header_" + str(i) for i in range(17)]
        rows = [["FAKE"] * 17]
        self.write(headers=headers, rows=rows)
        self.denied("UNSUPPORTED_EXPORT_HEADER", self.inspect)


if __name__ == "__main__":
    unittest.main()
