"""LOT05.7C-C — independent synthetic FUE: explicit mapping and zero-write CSV dry-run.

Only generated FAKE source values, no patient data. No database or network.
"""
from __future__ import annotations

from dataclasses import replace
import csv
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_lot05_7c_c_fake_mapping_lab"
scope = types.ModuleType(PACKAGE)
scope.__path__ = [str(BACKEND / "services")]
sys.modules[PACKAGE] = scope


def load(name):
    spec = importlib.util.spec_from_file_location(
        PACKAGE + "." + name, BACKEND / "services" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


load("legacy_sql_inspector_v15")
mapping = load("legacy_sql_mapping_v15")
load("legacy_migration_csv_preview_v15")
lab = load("legacy_migration_csv_mapping_lab_v15")


class SyntheticCsvMappingFUE(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="DC05C_FAKE_ONLY_")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.stage = self.root / "staging"
        self.stage.mkdir()
        self.source = self.stage / "patients_FAKE.csv"
        self.head = ["ancien_id", "prenom", "nom", "naissance", "extra"]
        self.rows = [
            [f"A{i:05d}", f"FAKE_FIRST_{i}", f"FAKE_LAST_{i}",
             "2000-02-29", "LAB_NON_PHI"]
            for i in range(100)
        ]
        self.write()

    def write(self, head=None, rows=None):
        with self.source.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(self.head if head is None else head)
            writer.writerows(self.rows if rows is None else rows)

    def choices(self):
        return (
            mapping.ColumnDecision("ancien_id", "legacy_id"),
            mapping.ColumnDecision("prenom", "given_name"),
            mapping.ColumnDecision("nom", "family_name"),
            mapping.ColumnDecision("naissance", "birth_date"),
            mapping.ColumnDecision("extra", None),
        )

    def draft(self, decisions=None, path=None, **kwargs):
        params = dict(
            decisions=self.choices() if decisions is None else decisions,
            source_software="FICTIONAL_VENDOR",
            source_version="FAKE-1",
            lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )
        params.update(kwargs)
        return lab.draft_synthetic_patient_mapping(
            self.source if path is None else path, self.stage, **params
        )

    def simulate(self, draft=None, path=None, **kwargs):
        if draft is None:
            draft = self.draft()
        params = dict(lab_only_synthetic_fixture=True, attested_offline_copy=True)
        params.update(kwargs)
        return lab.simulate_synthetic_patient_csv(
            self.source if path is None else path, self.stage, draft, **params
        )

    def refused(self, code, action, *args, **kwargs):
        with self.assertRaises(lab.SyntheticCsvMappingRefused) as err:
            action(*args, **kwargs)
        self.assertEqual(str(err.exception), code)
        self.assertNotIn("FAKE_FIRST_", str(err.exception))
        self.assertNotIn(str(self.source), str(err.exception))

    def test_01_hundred_fake_rows_count_only(self):
        before = self.source.read_bytes()
        draft = self.draft()
        r = self.simulate(draft)
        self.assertEqual(r.counts_by_entity, {"patients": 100})
        self.assertEqual(r.accepted_candidate_rows, 100)
        self.assertEqual(r.critical_count, 0)
        self.assertEqual(r.unmapped_columns, 1)
        self.assertEqual(r.ignored, 0)
        self.assertIsNone(r.collisions)  # No target DB = unknown, never a false zero
        self.assertEqual(r.target_rows_written, 0)
        self.assertFalse(r.import_permitted)
        self.assertFalse(r.mapping_approved)
        self.assertFalse(r.full_schema_certified)
        self.assertFalse(r.target_backup_verified)
        self.assertTrue(r.dry_run_completed)
        self.assertEqual(r.mapping_profile_sha256, draft.profile_sha256)
        self.assertEqual(before, self.source.read_bytes())
        public = str(r.to_public_dict())
        self.assertNotIn("FAKE_FIRST", public)
        self.assertNotIn("FAKE_LAST", public)
        self.assertNotIn("A00001", public)
        self.assertNotIn(str(self.source), public)
        self.assertNotIn("ancien_id", public)

    def test_02_draft_is_not_approved(self):
        draft = self.draft()
        self.assertFalse(draft.admin_approved)
        self.assertFalse(draft.import_permitted)
        self.assertFalse(draft.dry_run_completed)

    def test_03_deterministic_digest_and_report(self):
        a = self.draft()
        b = self.draft()
        self.assertEqual(a.profile_sha256, b.profile_sha256)
        self.assertEqual(self.simulate(a), self.simulate(b))

    def test_04_unmapped_source_column_reviewed(self):
        decisions = self.choices()[:-1]
        self.refused("MAPPING_DECISIONS_INVALID", self.draft, decisions)

    def test_05_missing_required_target_refused(self):
        decisions = tuple(
            replace(x, target_column=None) if x.source_column == "prenom" else x
            for x in self.choices()
        )
        self.refused("REQUIRED_PATIENT_MAPPING_INCOMPLETE", self.draft, decisions)

    def test_06_double_target_collision_refused(self):
        decisions = tuple(
            replace(x, target_column="given_name")
            if x.source_column == "nom" else x for x in self.choices()
        )
        self.refused("MAPPING_DECISIONS_INVALID", self.draft, decisions)

    def test_07_wrong_target_refused(self):
        decisions = tuple(
            replace(x, target_column="clinical_notes")
            if x.source_column == "nom" else x for x in self.choices()
        )
        self.refused("MAPPING_DECISIONS_INVALID", self.draft, decisions)

    def test_08_wrong_source_column_refused(self):
        decisions = tuple(
            replace(x, source_column="unknown_column")
            if x.source_column == "nom" else x for x in self.choices()
        )
        self.refused("MAPPING_DECISIONS_INVALID", self.draft, decisions)

    def test_09_no_implicit_mapping_or_suggestions(self):
        self.refused("MAPPING_DECISIONS_REQUIRED", self.draft, [])

    def test_10_tampered_draft_digest_refused(self):
        self.refused("MAPPING_DRAFT_INVALID", self.simulate,
                     replace(self.draft(), profile_sha256="0" * 64))

    def test_11_tampered_decision_after_digest_refused(self):
        d = self.draft()
        choices = d.decisions[0].columns
        changed = tuple(
            replace(x, target_column=None) if x.source_column == "naissance" else x
            for x in choices
        )
        self.refused("MAPPING_DRAFT_INVALID", self.simulate, replace(
            d, decisions=(replace(d.decisions[0], columns=changed),)
        ))

    def test_12_fake_admin_approval_refused(self):
        self.refused("MAPPING_DRAFT_INVALID", self.simulate,
                     replace(self.draft(), admin_approved=True))

    def test_13_fake_import_flag_refused(self):
        self.refused("MAPPING_DRAFT_INVALID", self.simulate,
                     replace(self.draft(), import_permitted=True))

    def test_14_changed_csv_source_digest_refused(self):
        d = self.draft()
        self.rows[0][1] = "FAKE_MODIFIED"
        self.write()
        self.refused("MAPPING_SOURCE_OR_TARGET_CHANGED", self.simulate, d)

    def test_15_changed_header_refused(self):
        d = self.draft()
        self.write(head=["ancien_id", "prenom", "nom", "extra", "naissance"])
        self.refused("MAPPING_SOURCE_OR_TARGET_CHANGED", self.simulate, d)

    def test_16_duplicate_ids_reported_not_merged(self):
        self.rows[1][0] = self.rows[0][0].lower()
        self.write()
        r = self.simulate()
        self.assertEqual(r.duplicates, 1)
        self.assertEqual(r.critical_count, 1)
        self.assertEqual(r.accepted_candidate_rows, 99)
        self.assertFalse(r.import_permitted)

    def test_17_invalid_source_ids_reported(self):
        self.rows[1][0] = "../SECRET"
        self.write()
        r = self.simulate()
        self.assertEqual(r.anomalies["invalid_source_id"], 1)
        self.assertEqual(r.critical_count, 1)

    def test_18_blank_given_name_reported(self):
        self.rows[3][1] = ""
        self.write()
        r = self.simulate()
        self.assertEqual(r.anomalies["invalid_name"], 1)
        self.assertEqual(r.critical_count, 1)

    def test_19_ambiguous_date_counted_without_coercion(self):
        self.rows[5][3] = "02/03/2020"
        self.write()
        r = self.simulate()
        self.assertEqual(r.ambiguous_dates, 1)
        self.assertEqual(r.critical_count, 1)

    def test_20_invalid_calendar_date_counted(self):
        self.rows[5][3] = "2026-02-30"
        self.write()
        self.assertEqual(self.simulate().ambiguous_dates, 1)

    def test_21_empty_optional_birth_date_accepted(self):
        self.rows[5][3] = ""
        self.write()
        self.assertEqual(self.simulate().critical_count, 0)

    def test_22_explicitly_unmapped_date_accepted(self):
        decisions = tuple(
            replace(x, target_column=None) if x.source_column == "naissance" else x
            for x in self.choices()
        )
        d = self.draft(decisions)
        r = self.simulate(d)
        self.assertEqual(r.unmapped_columns, 2)
        self.assertEqual(r.critical_count, 0)

    def test_23_no_double_count_for_multiple_errors_same_row(self):
        self.rows[1][0] = "INVALID/ID"
        self.rows[1][1] = ""
        self.rows[1][3] = "12/30/2010"
        self.write()
        r = self.simulate()
        self.assertEqual(r.critical_count, 1)
        self.assertEqual(r.accepted_candidate_rows, 99)

    def test_24_formula_in_mapped_field_rejected(self):
        self.rows[2][1] = "=CMD(1)"
        self.write()
        self.refused("UNSAFE_CSV_CELL", self.simulate)

    def test_25_formula_in_unmapped_field_rejected(self):
        self.rows[2][4] = "   @SUM(1)"
        self.write()
        self.refused("UNSAFE_CSV_CELL", self.simulate)

    def test_26_embedded_newline_rejected(self):
        self.rows[2][2] = "FAKE\nINJECTION"
        self.write()
        self.refused("UNSAFE_CSV_CELL", self.simulate)

    def test_27_missing_offline_attestation_refused(self):
        self.refused("OFFLINE_COPY_ATTESTATION_REQUIRED", self.draft,
                     attested_offline_copy=False)

    def test_28_requires_explicit_fake_lab_flag(self):
        self.refused("LAB_SYNTHETIC_ONLY", self.draft,
                     lab_only_synthetic_fixture=False)

    def test_29_fake_lab_int_not_boolean(self):
        self.refused("LAB_SYNTHETIC_ONLY", self.draft,
                     lab_only_synthetic_fixture=1)

    def test_30_outside_staging_refused(self):
        outside = self.root / "outside.csv"
        outside.write_bytes(self.source.read_bytes())
        self.refused("OUTSIDE_STAGING_ROOT", self.draft, path=outside)

    def test_31_symlink_refused_if_available(self):
        link = self.stage / "alias.csv"
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not available")
        self.addCleanup(link.unlink, missing_ok=True)
        self.refused("SYMLINK_FORBIDDEN", self.draft, path=link)

    def test_32_hardlink_refused_if_available(self):
        link = self.stage / "hardlink.csv"
        try:
            os.link(self.source, link)
        except (OSError, NotImplementedError):
            self.skipTest("hardlinks not available")
        self.addCleanup(link.unlink, missing_ok=True)
        self.refused("HARDLINK_SOURCE_FORBIDDEN", self.draft)

    def test_33_secret_header_refused_even_if_unmapped(self):
        self.write(head=["ancien_id", "prenom", "nom", "naissance", "password"])
        self.refused("UNSAFE_CSV_HEADER", self.draft)

    def test_34_nonascii_or_unsafe_header_refused(self):
        self.write(head=["ancien_id", "prénom", "nom", "naissance", "extra"])
        self.refused("UNSAFE_CSV_HEADER", self.draft)

    def test_35_casefold_duplicate_header_refused(self):
        self.write(head=["ancien_id", "prenom", "nom", "Prenom", "naissance"])
        self.refused("DUPLICATE_CSV_HEADER", self.draft)

    def test_36_too_many_headers_refused(self):
        columns = [f"field_{i}" for i in range(17)]
        self.write(head=columns)
        self.refused("UNSUPPORTED_CSV_HEADER", self.draft)

    def test_37_truncated_quoted_csv_rejected(self):
        d = self.draft()
        self.source.write_text(
            "ancien_id,prenom,nom,naissance,extra\nA1,\"UNFINISHED,FAKE\n",
            encoding="utf-8",
        )
        self.refused("MAPPING_SOURCE_OR_TARGET_CHANGED", self.simulate, d)

    def test_38_invalid_utf8_rejected(self):
        self.source.write_bytes(
            b"ancien_id,prenom,nom,naissance,extra\nA1,\xff,PERSON,2000-01-01,FAKE\n"
        )
        self.refused("INVALID_CSV_SOURCE", self.draft)

    def test_39_empty_csv_records_refused(self):
        self.write(rows=[])
        self.refused("EMPTY_PATIENT_CSV", self.simulate)

    def test_40_mismatched_row_length_refused(self):
        self.write(rows=[["A1", "FAKE"]])
        self.refused("INVALID_CSV_ROW_LENGTH", self.simulate)

    def test_41_max_rows_enforced(self):
        self.write(rows=[
            [f"A{i:05d}", "FAKE", "PERSON", "2010-01-01", "LAB"]
            for i in range(10_001)
        ])
        self.refused("CSV_ROW_LIMIT_EXCEEDED", self.simulate)

    def test_42_source_changed_during_simulation_refused(self):
        d = self.draft()
        real = lab._hash
        calls = [0]
        def change_hash(path):
            calls[0] += 1
            return real(path) if calls[0] <= 2 else "0" * 64
        with patch.object(lab, "_hash", side_effect=change_hash):
            self.refused("SOURCE_CHANGED_DURING_SIMULATION", self.simulate, d)

    def test_43_no_mapping_draft_refused(self):
        self.refused("MAPPING_DRAFT_REQUIRED", self.simulate, object())

    def test_44_wrong_extension_refused(self):
        file = self.stage / "FAKE.txt"
        file.write_bytes(self.source.read_bytes())
        self.refused("CSV_EXTENSION_REQUIRED", self.draft, path=file)


if __name__ == "__main__":
    unittest.main()
