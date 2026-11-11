"""LOT05/2D — FAKE-only semantic mapping oracle; never an import or approval.

Adversarially demonstrates that structural mapping can accept surname/given-name
inversion. The FIXTURE-SPECIFIC independent oracle detects it in the lab.
Do not mistake fixture-name semantics for real vendor provenance or human review.
"""
from __future__ import annotations

from dataclasses import replace
import csv
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest

BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_dc_lot05_2d_semantic_fake"
if PACKAGE not in sys.modules:
    pkg = types.ModuleType(PACKAGE)
    pkg.__path__ = [str(BACKEND / "services")]
    sys.modules[PACKAGE] = pkg


def load(name):
    full = PACKAGE + "." + name
    spec = importlib.util.spec_from_file_location(
        full, BACKEND / "services" / (name + ".py")
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full] = mod
    spec.loader.exec_module(mod)
    return mod


load("legacy_sql_inspector_v15")
mapping = load("legacy_sql_mapping_v15")
load("legacy_migration_csv_preview_v15")
lab = load("legacy_migration_csv_mapping_lab_v15")

# Independent, project-generated CSV fixture contract — NOT a vendor schema.
EXPECTED = {
    "ancien_id": "legacy_id",
    "prenom": "given_name",
    "nom": "family_name",
    "naissance": "birth_date",
    "extra": None,
}


def fixture_semantic_discrepancies(draft):
    """Count mismatch against this synthetic fixture specification only.

    An empty list never constitutes human approval or source attestation.
    Do not export raw column names, rows, values or sensitive identifiers.
    """
    if type(draft) is not mapping.MappingDraft:
        return ("INVALID_DRAFT",)
    decisions = draft.decisions
    if len(decisions) != 1 or decisions[0].source_table != "csv_patients":
        return ("INVALID_TABLE_SCOPE",)
    actual = {c.source_column: c.target_column for c in decisions[0].columns}
    if len(actual) != len(decisions[0].columns) or set(actual) != set(EXPECTED):
        return ("FIXTURE_FIELD_COVERAGE_MISMATCH",)
    return tuple(
        "FIXTURE_SEMANTIC_BINDING_MISMATCH"
        for key in sorted(EXPECTED) if actual[key] != EXPECTED[key]
    )


class SyntheticSemanticOracleFUE(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="DC_LOT05_2D_FAKE_ONLY_")
        self.addCleanup(tmp.cleanup)
        self.stage = Path(tmp.name) / "staged"
        self.stage.mkdir()
        self.source = self.stage / "FAKE_patient_projection.csv"
        self.rows = [
            [f"S{i:04d}", f"FAKE_GIVEN_{i:04d}", f"FAKE_FAMILY_{i:04d}",
             "2000-02-29", "FAKE_UNUSED"]
            for i in range(100)
        ]
        self.write()

    def write(self):
        with self.source.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(tuple(EXPECTED))
            writer.writerows(self.rows)

    def draft(self, bindings=None):
        values = EXPECTED if bindings is None else bindings
        choices = tuple(mapping.ColumnDecision(key, values[key]) for key in EXPECTED)
        return lab.draft_synthetic_patient_mapping(
            self.source, self.stage, decisions=choices,
            source_software="FICTIONAL_VENDOR_NOT_ATTESTED",
            source_version="FAKE_FIXTURE_V1",
            lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )

    def simulate(self, draft):
        return lab.simulate_synthetic_patient_csv(
            self.source, self.stage, draft,
            lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )

    def test_01_correct_fixture_mapping_and_zero_write(self):
        before = self.source.read_bytes()
        draft = self.draft()
        self.assertEqual(fixture_semantic_discrepancies(draft), ())
        report = self.simulate(draft)
        self.assertEqual(report.counts_by_entity, {"patients": 100})
        self.assertEqual(report.accepted_candidate_rows, 100)
        self.assertEqual(report.critical_count, 0)
        self.assertEqual(report.unmapped_columns, 1)
        self.assertIsNone(report.collisions)
        self.assertFalse(report.import_permitted)
        self.assertFalse(report.mapping_approved)
        self.assertFalse(report.target_backup_verified)
        self.assertEqual(report.target_rows_written, 0)
        self.assertEqual(self.source.read_bytes(), before)

    def test_02_swapped_given_family_is_structurally_accepted_but_oracle_flags(self):
        swapped = dict(EXPECTED, prenom="family_name", nom="given_name")
        draft = self.draft(swapped)
        self.assertEqual(self.simulate(draft).critical_count, 0)
        self.assertEqual(
            fixture_semantic_discrepancies(draft),
            ("FIXTURE_SEMANTIC_BINDING_MISMATCH",) * 2,
        )
        self.assertFalse(draft.admin_approved)
        self.assertFalse(draft.import_permitted)

    def test_03_birth_date_silent_omission_flagged(self):
        incomplete = dict(EXPECTED, naissance=None)
        draft = self.draft(incomplete)
        self.assertEqual(self.simulate(draft).critical_count, 0)
        self.assertEqual(fixture_semantic_discrepancies(draft),
                         ("FIXTURE_SEMANTIC_BINDING_MISMATCH",))
        self.assertFalse(draft.import_permitted)

    def test_04_ambiguous_day_month_date_remains_critical(self):
        self.rows[0][3] = "03/04/2020"
        self.write()
        report = self.simulate(self.draft())
        self.assertEqual(report.ambiguous_dates, 1)
        self.assertEqual(report.accepted_candidate_rows, 99)
        self.assertEqual(report.critical_count, 1)
        self.assertFalse(report.import_permitted)

    def test_05_calendar_invalid_date_remains_critical(self):
        self.rows[0][3] = "2026-02-30"
        self.write()
        report = self.simulate(self.draft())
        self.assertEqual(report.ambiguous_dates, 1)
        self.assertEqual(report.critical_count, 1)

    def test_06_empty_birth_date_is_missing_not_invented(self):
        self.rows[0][3] = ""
        self.write()
        report = self.simulate(self.draft())
        self.assertEqual(report.critical_count, 0)
        self.assertFalse(report.mapping_approved)
        self.assertFalse(report.import_permitted)

    def test_07_collision_is_structurally_refused(self):
        collision = dict(EXPECTED, nom="given_name")
        with self.assertRaisesRegex(lab.SyntheticCsvMappingRefused, "MAPPING_DECISIONS_INVALID"):
            self.draft(collision)

    def test_08_missing_source_column_decision_is_refused(self):
        choices = tuple(mapping.ColumnDecision(k, EXPECTED[k])
                        for k in EXPECTED if k != "extra")
        with self.assertRaisesRegex(lab.SyntheticCsvMappingRefused, "MAPPING_DECISIONS_INVALID"):
            lab.draft_synthetic_patient_mapping(
                self.source, self.stage, decisions=choices,
                source_software="FICTIONAL_VENDOR_NOT_ATTESTED",
                source_version="FAKE_FIXTURE_V1",
                lab_only_synthetic_fixture=True,
                attested_offline_copy=True,
            )

    def test_09_stale_draft_after_birth_date_change_is_refused(self):
        old_draft = self.draft()
        self.rows[0][3] = "2001-01-01"
        self.write()
        with self.assertRaisesRegex(lab.SyntheticCsvMappingRefused,
                                    "MAPPING_SOURCE_OR_TARGET_CHANGED"):
            self.simulate(old_draft)

    def test_10_forged_approval_is_refused_by_existing_gate(self):
        with self.assertRaisesRegex(lab.SyntheticCsvMappingRefused, "MAPPING_DRAFT_INVALID"):
            self.simulate(replace(self.draft(), admin_approved=True))

    def test_11_non_phi_aggregate_never_exposes_rows(self):
        report = self.simulate(self.draft())
        public = repr(report.to_public_dict())
        for marker in ("FAKE_GIVEN_", "FAKE_FAMILY_", "FAKE_UNUSED",
                       str(self.stage), "ancien_id", "prenom", "nom"):
            self.assertNotIn(marker, public)
        self.assertFalse(report.import_permitted)

    def test_12_oracle_is_not_a_vendor_or_human_authority(self):
        draft = self.draft()
        self.assertEqual(fixture_semantic_discrepancies(draft), ())
        self.assertFalse(draft.admin_approved)
        self.assertFalse(draft.dry_run_completed)
        self.assertFalse(draft.import_permitted)
        self.assertFalse(self.simulate(draft).full_schema_certified)


if __name__ == "__main__":
    unittest.main(verbosity=2)
