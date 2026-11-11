"""LOT05/2C FUE-0 — mapping and cold SQLite plan, GENERATED FAKE DATA ONLY.

No clinic DB, remote service, patient media, source credentials or target writer.
This test integrates existing inspection + mapping + offline planning contracts;
it does not authorize clinical migration or establish vendor compatibility.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import replace
import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest

BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_dc_lot05_2c_generated_fake_only"
if PACKAGE not in sys.modules:
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(BACKEND / "services")]
    sys.modules[PACKAGE] = package


def load(name):
    fullname = PACKAGE + "." + name
    spec = importlib.util.spec_from_file_location(
        fullname, BACKEND / "services" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return module


inspect = load("legacy_sql_inspector_v15")
mapping = load("legacy_sql_mapping_v15")
planner = load("legacy_sql_offline_plan_v15")


class MappingAndPlanSyntheticFUE(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="DC_LOT05_2C_FAKE_")
        self.addCleanup(temp.cleanup)
        self.stage = Path(temp.name) / "staging"
        self.stage.mkdir()
        self.source = self.stage / "FAKE_ONLY.sqlite"
        self.patients = [
            (f"P{i:03d}", f"FAKE_FIRST_{i}", f"FAKE_LAST_{i}",
             "FAKE_SECRET_NEVER_EXPORT")
            for i in range(100)
        ]
        self.visits = [
            (f"V{i:03d}", f"P{i % 100:03d}", "2026-11-11")
            for i in range(200)
        ]
        self.write_fixture()

    def write_fixture(self):
        self.source.unlink(missing_ok=True)
        with closing(sqlite3.connect(self.source)) as conn:
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute(
                "CREATE TABLE legacy_patients (legacy_id TEXT, first_name TEXT, "
                "last_name TEXT, password_hash TEXT)"
            )
            conn.execute(
                "CREATE TABLE legacy_visits (visit_id TEXT, patient_ref TEXT, starts TEXT)"
            )
            conn.executemany(
                "INSERT INTO legacy_patients VALUES (?, ?, ?, ?)", self.patients
            )
            conn.executemany(
                "INSERT INTO legacy_visits VALUES (?, ?, ?)", self.visits
            )
            conn.commit()

    def configuration(self):
        report = inspect.inspect_staged_copy(
            self.source, self.stage, dialect="sqlite", attested_offline_copy=True
        )
        target = mapping.TargetSnapshot(
            schema_revision="FAKE_DECLARED_NO_PHYSICAL_TARGET",
            tables=(
                mapping.TargetTable("patients", ("prenom", "nom")),
                mapping.TargetTable("appointments", ("patient_id", "datetime_start")),
            ),
        )
        choices = {
            "legacy_patients": ("patients", {
                "first_name": "prenom", "last_name": "nom",
            }),
            "legacy_visits": ("appointments", {
                "patient_ref": "patient_id", "starts": "datetime_start",
            }),
        }
        decisions = tuple(
            mapping.TableDecision(
                table.source_name, choices[table.source_name][0],
                tuple(mapping.ColumnDecision(
                    col.name, choices[table.source_name][1].get(col.name)
                ) for col in table.columns),
            ) for table in report.tables
        )
        draft = mapping.build_mapping_draft(
            report, target, decisions,
            source_software="FAKE_VENDOR_NOT_VERIFIED",
            source_version="FAKE_0",
            profile_version=1,
        )
        params = dict(
            source_path=self.source, staging_root=self.stage, draft=draft,
            target_snapshot=target, attested_offline_copy=True, dialect="sqlite",
            source_id_columns={
                "legacy_patients": "legacy_id",
                "legacy_visits": "visit_id",
            },
            reference_rules=(
                planner.ReferenceRule(
                    "legacy_visits", "patient_ref", "legacy_patients"
                ),
            ),
        )
        return report, target, draft, params

    def test_01_exact_100_patients_200_appointments_no_import(self):
        _, _, _, params = self.configuration()
        result = planner.assess_cold_sqlite_copy(**params)
        self.assertEqual(
            result.counts_by_entity, {"patients": 100, "appointments": 200}
        )
        self.assertEqual(result.reference_count, 200)
        self.assertEqual(result.duplicate_legacy_ids, 0)
        self.assertEqual(result.orphan_references, 0)
        self.assertEqual(result.unmapped_columns, 3)
        self.assertIn("UNMAPPED_REQUIRES_HUMAN_DISPOSITION", result.anomalies)
        self.assertFalse(result.import_permitted)
        self.assertFalse(result.human_mapping_approved)
        self.assertFalse(result.target_restore_verified)
        self.assertEqual(result.target_rows_written, 0)

    def test_02_deterministic_digest_source_immutability_and_privacy(self):
        _, _, _, params = self.configuration()
        original = self.source.read_bytes()
        first = planner.assess_cold_sqlite_copy(**params)
        second = planner.assess_cold_sqlite_copy(**params)
        self.assertEqual(first, second)
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(first.source_sha256, hashlib.sha256(original).hexdigest())
        public = repr(first.to_dict())
        for secret in (
            "FAKE_SECRET_NEVER_EXPORT", "FAKE_FIRST_",
            "FAKE_VENDOR_NOT_VERIFIED", str(self.stage), "legacy_patients",
        ):
            self.assertNotIn(secret, public)
        self.assertIn("NO_CLINICAL_MEDIA_OR_FINANCE_SEMANTIC_RECONCILIATION", first.warnings)

    def test_03_duplicate_and_orphan_are_not_silently_repaired(self):
        self.patients.append(self.patients[0])  # one extra duplicate, preserve P001 references
        self.visits[0] = ("V000", "UNKNOWN_FAKE_ID", "2026-11-11")
        self.write_fixture()
        _, _, _, params = self.configuration()
        result = planner.assess_cold_sqlite_copy(**params)
        self.assertEqual(result.duplicate_legacy_ids, 1)
        self.assertEqual(result.orphan_references, 1)
        self.assertIn("DUPLICATE_LEGACY_ID", result.anomalies)
        self.assertIn("ORPHAN_REFERENCE", result.anomalies)
        self.assertGreater(result.critical_count, 0)
        self.assertFalse(result.import_permitted)

    def test_04_source_byte_change_invalidates_prior_mapping(self):
        _, _, _, params = self.configuration()
        with closing(sqlite3.connect(self.source)) as conn:
            conn.execute(
                "INSERT INTO legacy_visits VALUES (?, ?, ?)",
                ("V_NEW", "P000", "2026-11-11"),
            )
            conn.commit()
        with self.assertRaisesRegex(
            planner.OfflinePlanRefused, "SOURCE_OR_TARGET_DRAFT_CHANGED"
        ):
            planner.assess_cold_sqlite_copy(**params)

    def test_05_every_source_column_requires_explicit_decision(self):
        report, target, draft, _ = self.configuration()
        incomplete = tuple(
            replace(choice, columns=choice.columns[:-1])
            if choice.source_table == "legacy_patients" else choice
            for choice in draft.decisions
        )
        with self.assertRaisesRegex(
            mapping.MappingRejected, "COLUMN_REVIEW_INCOMPLETE"
        ):
            mapping.build_mapping_draft(
                report, target, incomplete,
                source_software="FAKE_VENDOR_NOT_VERIFIED",
                source_version="FAKE_0", profile_version=1,
            )

    def test_06_double_destination_column_collision_refused(self):
        report, target, draft, _ = self.configuration()
        collided = tuple(
            replace(choice, columns=tuple(
                replace(col, target_column="prenom")
                if col.source_column == "last_name" else col
                for col in choice.columns
            )) if choice.source_table == "legacy_patients" else choice
            for choice in draft.decisions
        )
        with self.assertRaisesRegex(
            mapping.MappingRejected, "TARGET_COLUMN_COLLISION"
        ):
            mapping.build_mapping_draft(
                report, target, collided,
                source_software="FAKE_VENDOR_NOT_VERIFIED",
                source_version="FAKE_0", profile_version=1,
            )

    def test_07_forged_admin_approval_is_not_authority(self):
        _, _, _, params = self.configuration()
        params["draft"] = replace(params["draft"], admin_approved=True)
        with self.assertRaisesRegex(
            planner.OfflinePlanRefused, "DRAFT_CANNOT_AUTHORIZE"
        ):
            planner.assess_cold_sqlite_copy(**params)

    def test_08_offline_copy_attestation_required(self):
        _, _, _, params = self.configuration()
        params["attested_offline_copy"] = False
        with self.assertRaisesRegex(
            planner.OfflinePlanRefused, "OFFLINE_COPY_ATTESTATION_REQUIRED"
        ):
            planner.assess_cold_sqlite_copy(**params)

    def test_09_wrong_target_schema_cannot_reuse_mapping(self):
        _, _, _, params = self.configuration()
        params["target_snapshot"] = mapping.TargetSnapshot(
            schema_revision="DIFFERENT_FAKE_SCHEMA",
            tables=params["target_snapshot"].tables,
        )
        with self.assertRaisesRegex(
            planner.OfflinePlanRefused, "SOURCE_OR_TARGET_DRAFT_CHANGED"
        ):
            planner.assess_cold_sqlite_copy(**params)


if __name__ == "__main__":
    unittest.main(verbosity=2)
