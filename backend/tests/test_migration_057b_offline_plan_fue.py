"""LOT05.7B: real COLD source SQLite read-only planning FUE, FAKE patient data.

Never open a cabinet runtime connection. All source files are created solely by
this suite in a disposable temp dir, no HTTP/target import/network involved.
The source mapping/inspection modules are loaded verbatim without booting
backend/__init__.py or backend.database.
"""
from __future__ import annotations

from dataclasses import replace
import importlib.util
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest

BACKEND = Path(__file__).resolve().parents[1]
LAB_PACKAGE = "_lot05b_offline_readonly"
if LAB_PACKAGE not in sys.modules:
    namespace = types.ModuleType(LAB_PACKAGE)
    namespace.__path__ = [str(BACKEND / "services")]
    sys.modules[LAB_PACKAGE] = namespace


def load(name: str):
    # Private module namespace: never replace backend.* in global sys.modules.
    fullname = LAB_PACKAGE + "." + name
    spec = importlib.util.spec_from_file_location(
        fullname, BACKEND / "services" / (name + ".py")
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = mod
    spec.loader.exec_module(mod)
    return mod


inspector = load("legacy_sql_inspector_v15")
mapping = load("legacy_sql_mapping_v15")
planner = load("legacy_sql_offline_plan_v15")


class ColdSourceCase(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(prefix="dc05b_fake_source_")
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.stage = self.root / "offline-copies"
        self.stage.mkdir()
        self.source = self.stage / "synthetic_legacy.sqlite"
        self._patients = [
            (str(i), "SYNTHETIC_ONLY_FIRST_" + str(i),
             "SYNTHETIC_ONLY_LAST_" + str(i), "FAKE_PWD_DO_NOT_COPY")
            for i in range(100)
        ]
        self._visits = [(str(i), str(i // 2), "2026-11-08") for i in range(200)]
        self._payments = [(str(i), str(i), "500") for i in range(20)]
        self._media = [(str(i), str(i), "FAKE_PATH_NOT_USED") for i in range(10)]
        self.write_db()

    def write_db(self):
        self.source.unlink(missing_ok=True)
        with sqlite3.connect(self.source) as connection:
            connection.execute("PRAGMA journal_mode=DELETE")
            connection.execute(
                "CREATE TABLE legacy_patients (legacy_id TEXT, first_name TEXT,"
                "last_name TEXT, password_hash TEXT)"
            )
            connection.execute(
                "CREATE TABLE legacy_visits (visit_id TEXT, patient_ref TEXT, starts TEXT)"
            )
            connection.execute(
                "CREATE TABLE legacy_payments (payment_id TEXT, visit_ref TEXT, amount TEXT)"
            )
            connection.execute(
                "CREATE TABLE legacy_media (media_id TEXT, patient_ref TEXT, asset_path TEXT)"
            )
            connection.executemany(
                "INSERT INTO legacy_patients VALUES (?,?,?,?)", self._patients
            )
            connection.executemany(
                "INSERT INTO legacy_visits VALUES (?,?,?)", self._visits
            )
            connection.executemany(
                "INSERT INTO legacy_payments VALUES (?,?,?)", self._payments
            )
            connection.executemany(
                "INSERT INTO legacy_media VALUES (?,?,?)", self._media
            )
            connection.commit()

    def mapping(self):
        report = inspector.inspect_staged_copy(
            self.source, self.stage, dialect="sqlite", attested_offline_copy=True
        )
        snapshot = mapping.TargetSnapshot(
            schema_revision="orm-declared:neo000000033",
            tables=(
                mapping.TargetTable("patients", ("nom", "prenom")),
                mapping.TargetTable("appointments", ("patient_id", "datetime_start")),
                mapping.TargetTable("payments", ("amount",)),
                mapping.TargetTable("clinical_assets", ("source_path",)),
            ),
        )
        targets = {
            "legacy_patients": ("patients", {
                "first_name": "prenom", "last_name": "nom",
            }),
            "legacy_visits": ("appointments", {
                "patient_ref": "patient_id", "starts": "datetime_start",
            }),
            "legacy_payments": ("payments", {"amount": "amount"}),
            "legacy_media": ("clinical_assets", {"asset_path": "source_path"}),
        }
        decisions = tuple(
            mapping.TableDecision(
                t.source_name, targets[t.source_name][0],
                tuple(mapping.ColumnDecision(
                    c.name, targets[t.source_name][1].get(c.name)
                ) for c in t.columns),
            )
            for t in report.tables
        )
        draft = mapping.build_mapping_draft(
            report, snapshot, decisions,
            source_software="FICTITIOUS_VENDOR",
            source_version="TEST_ONLY",
            profile_version=1,
        )
        return draft, snapshot

    def kwargs(self):
        draft, target = self.mapping()
        return dict(
            source_path=self.source, staging_root=self.stage, draft=draft,
            target_snapshot=target, attested_offline_copy=True, dialect="sqlite",
            source_id_columns={
                "legacy_patients": "legacy_id",
                "legacy_visits": "visit_id",
                "legacy_payments": "payment_id",
                "legacy_media": "media_id",
            },
            reference_rules=(
                planner.ReferenceRule("legacy_visits", "patient_ref", "legacy_patients"),
                planner.ReferenceRule("legacy_payments", "visit_ref", "legacy_visits"),
                planner.ReferenceRule("legacy_media", "patient_ref", "legacy_patients"),
            ),
        )

    def deny(self, message, kwargs):
        with self.assertRaisesRegex(planner.OfflinePlanRefused, message):
            planner.assess_cold_sqlite_copy(**kwargs)

    def test_01_all_entity_counts_and_references_are_real_read_only(self):
        result = planner.assess_cold_sqlite_copy(**self.kwargs())
        self.assertEqual(result.counts_by_entity, {
            "patients": 100, "appointments": 200,
            "payments": 20, "clinical_assets": 10,
        })
        self.assertEqual(result.reference_count, 230)
        self.assertEqual((result.duplicate_legacy_ids, result.missing_legacy_ids,
                          result.orphan_references), (0, 0, 0))
        self.assertTrue(result.source_unchanged)
        self.assertTrue(result.source_only_copy)
        self.assertEqual(result.target_rows_written, 0)
        self.assertFalse(result.import_permitted)
        self.assertFalse(result.full_schema_certified)
        self.assertFalse(result.target_backup_verified)
        self.assertFalse(result.clinical_records_reconciled)
        self.assertGreater(result.unmapped_columns, 0)

    def test_02_repeat_plan_digest_is_deterministic_and_source_unchanged(self):
        kw = self.kwargs()
        original = inspector._hash(self.source)
        first = planner.assess_cold_sqlite_copy(**kw)
        second = planner.assess_cold_sqlite_copy(**kw)
        self.assertEqual(first, second)
        self.assertEqual(first.source_sha256, original)
        self.assertEqual(inspector._hash(self.source), original)

    def test_03_report_never_contains_row_values_or_original_paths(self):
        output = repr(planner.assess_cold_sqlite_copy(**self.kwargs()).to_dict())
        self.assertNotIn("FAKE_PWD", output)
        self.assertNotIn("SYNTHETIC_ONLY_", output)
        self.assertNotIn(str(self.stage), output)
        self.assertNotIn("FAKE_PATH_NOT_USED", output)
        self.assertNotIn("legacy_patients", output)

    def test_04_real_source_byte_change_invalidates_profile(self):
        kw = self.kwargs()
        with sqlite3.connect(self.source) as db:
            db.execute("INSERT INTO legacy_patients VALUES (?,?,?,?)",
                       ("1000", "SYNTHETIC_ONLY_NEW", "SYNTHETIC_ONLY_NEW", "FAKE_PWD"))
            db.commit()
        self.deny("SOURCE_OR_TARGET_DRAFT_CHANGED", kw)

    def test_05_attestation_is_mandatory(self):
        kw = self.kwargs()
        kw["attested_offline_copy"] = False
        self.deny("OFFLINE_COPY_ATTESTATION_REQUIRED", kw)

    def test_06_refuse_non_sqlite_dump_adapter(self):
        kw = self.kwargs()
        kw["dialect"] = "mysql"
        self.deny("NATIVE_ROW_ADAPTER_NOT_IMPLEMENTED", kw)

    def test_07_reject_source_outside_staging_root(self):
        kw = self.kwargs()
        kw["staging_root"] = self.root / "other"
        kw["staging_root"].mkdir()
        self.deny("OUTSIDE_STAGING_ROOT", kw)

    def test_08_reject_symlink_copy(self):
        kw = self.kwargs()
        link = self.stage / "link.sqlite"
        try:
            link.symlink_to(self.source)
        except (NotImplementedError, OSError):
            self.skipTest("Symlinks require Windows developer privileges")
        kw["source_path"] = link
        self.deny("SYMLINK_FORBIDDEN", kw)

    def test_09_reject_hardlink_copy(self):
        kw = self.kwargs()
        link = self.stage / "hardlink.sqlite"
        try:
            os.link(self.source, link)
        except (NotImplementedError, OSError):
            self.skipTest("Hardlink unavailable")
        self.deny("HARDLINK_SOURCE_FORBIDDEN", kw)

    def test_10_reject_missing_patient_appointment_relationship(self):
        kw = self.kwargs()
        kw["reference_rules"] = kw["reference_rules"][1:]
        self.deny("PATIENT_APPOINTMENT_REFERENCE_REQUIRED", kw)

    def test_11_orphan_reference_reported_not_silently_fixed(self):
        self._visits[0] = ("0", "not-a-patient", "2026-11-08")
        self.write_db()
        result = planner.assess_cold_sqlite_copy(**self.kwargs())
        self.assertEqual(result.orphan_references, 1)
        self.assertIn("ORPHAN_REFERENCE", result.anomalies)
        self.assertFalse(result.import_permitted)

    def test_12_duplicate_legacy_id_reported_not_merged(self):
        self._patients[1] = (self._patients[0][0],) + self._patients[1][1:]
        self.write_db()
        result = planner.assess_cold_sqlite_copy(**self.kwargs())
        self.assertEqual(result.duplicate_legacy_ids, 1)
        self.assertIn("DUPLICATE_LEGACY_ID", result.anomalies)

    def test_13_missing_legacy_id_reported_not_generated(self):
        self._patients[0] = (None,) + self._patients[0][1:]
        self.write_db()
        result = planner.assess_cold_sqlite_copy(**self.kwargs())
        self.assertEqual(result.missing_legacy_ids, 1)
        self.assertIn("MISSING_LEGACY_ID", result.anomalies)

    def test_14_manually_flipped_approval_flag_refused(self):
        kw = self.kwargs()
        kw["draft"] = replace(kw["draft"], admin_approved=True)
        self.deny("DRAFT_CANNOT_AUTHORIZE", kw)

    def test_15_mutated_mapping_decision_refused(self):
        kw = self.kwargs()
        kw["draft"] = replace(kw["draft"], profile_sha256="b" * 64)
        self.deny("DRAFT_TAMPERED", kw)

    def test_16_no_implicit_source_identity_or_foreign_key(self):
        kw = self.kwargs()
        kw["source_id_columns"].pop("legacy_visits")
        self.deny("EXPLICIT_ID_FOR_EVERY_MAPPED_TABLE_REQUIRED", kw)
        kw = self.kwargs()
        kw["source_id_columns"]["legacy_visits"] = "nonexistent"
        self.deny("EXPLICIT_SOURCE_IDENTIFIER_REQUIRED", kw)

    def test_17_duplicate_reference_rule_refused(self):
        kw = self.kwargs()
        kw["reference_rules"] += kw["reference_rules"][:1]
        self.deny("DUPLICATE_REFERENCE_RULE", kw)

    def test_18_invalid_and_wal_sqlite_copy_refused(self):
        kw = self.kwargs()
        with sqlite3.connect(self.source) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.commit()
        # The existing cold-inspector requires rollback-journal copies.
        self.deny("SQLITE_ROLLBACK_JOURNAL_COPY_REQUIRED", kw)

    def test_19_no_credential_or_target_database_adapters_in_api(self):
        import inspect
        parameters = inspect.signature(planner.assess_cold_sqlite_copy).parameters
        self.assertFalse(set(parameters).intersection({
            "DATABASE_URL", "database", "engine", "session", "target_db",
            "password", "credentials", "tenant", "commit",
        }))
        self.assertFalse(hasattr(planner, "import_clinical"))
        self.assertFalse(hasattr(planner, "apply_to_cabinet"))

    def test_20_unsupported_mixed_or_missing_source_rules_fail_closed(self):
        kw = self.kwargs()
        kw["reference_rules"] = (planner.ReferenceRule("legacy_visits", "patient_ref", "missing"),)
        self.deny("EXPLICIT_SOURCE_IDENTIFIER_REQUIRED", kw)


    def test_21_password_column_never_accepted_as_identity(self):
        kw = self.kwargs()
        kw["source_id_columns"]["legacy_patients"] = "password_hash"
        self.deny("SENSITIVE_SOURCE_ID_FORBIDDEN", kw)

    def test_22_password_column_never_accepted_as_reference(self):
        kw = self.kwargs()
        kw["reference_rules"] = (
            planner.ReferenceRule("legacy_patients", "password_hash", "legacy_visits"),
        ) + kw["reference_rules"]
        self.deny("SENSITIVE_REFERENCE_COLUMN_FORBIDDEN", kw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
