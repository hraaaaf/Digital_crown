"""LOT05 LAB ONLY: multilingual synthetic source formats to metadata mapping.

S01 MySQL-flavored .sql (EN); S02 SQLite cold .db (FR);
S03 PostgreSQL-flavored .sql (ES); S04+ negative security cases.
The existing inspector NEVER executes source SQL or reads rows. This suite
does NOT test migration/import, real clinic auth, a physical target DB or tenancy.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager
from dataclasses import replace

_BACKEND = pathlib.Path(__file__).resolve().parents[1]
_FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "lot05_scenarios"


def _load_source(alias: str, filename: str):
    spec = importlib.util.spec_from_file_location(alias, _BACKEND / "services" / filename)
    if spec is None or spec.loader is None:
        raise AssertionError("LAB_MODULE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


inspector = _load_source("lot05_lab_inspector", "legacy_sql_inspector_v15.py")
mapping = _load_source("lot05_lab_mapping", "legacy_sql_mapping_v15.py")
manifest = _load_source("lot05_lab_orm_manifest", "legacy_sql_target_manifest_v15.py")


def _real_declared_model_only():
    """Borrow real ORM declarations; do not initialize backend or its database."""
    if "backend" not in sys.modules:
        package = types.ModuleType("backend")
        package.__path__ = [str(_BACKEND)]
        sys.modules["backend"] = package
    elif getattr(sys.modules["backend"], "__file__", None):
        raise AssertionError("BACKEND_RUNTIME_IMPORT_FORBIDDEN")
    imported = importlib.import_module("backend.models")
    base = importlib.import_module("backend.models_base")
    if "backend.database" in sys.modules:
        raise AssertionError("DATABASE_RUNTIME_IMPORT_FORBIDDEN")
    assert imported.Patient.__tablename__ == "patients"
    return base.Base.metadata


def _target():
    declared = manifest.build_declared_target_manifest(
        _real_declared_model_only(),
        requested_tables=("patients", "appointments"),
        declared_revision=manifest.DECLARED_EXPECTED_ALEMBIC_HEAD,
    )
    return declared, declared.as_mapping_target(
        snapshot_type=mapping.TargetSnapshot, table_type=mapping.TargetTable
    )


_SCENARIOS = {
    "S01": ("S01_mysql_english.sql", "mysql", "legacy_patients", {
        "first_name": "prenom", "last_name": "nom",
        "birth_date": "date_naissance", "sex": "sexe", "email": "email",
    }),
    "S02": ("S02_sqlite_french.db", "sqlite", "dossiers", {
        "nom": "nom", "prenom": "prenom", "date_naissance": "date_naissance",
        "sexe": "sexe", "numero_dossier": "numero_dossier", "telephone": "telephone",
    }),
    "S03": ("S03_postgresql_spanish.sql", "postgresql", "personas", {
        "nombre": "prenom", "apellido": "nom", "fecha_nacimiento": "date_naissance",
        "sexo": "sexe", "correo": "email",
    }),
}


@contextmanager
def _staged(scenario: str):
    filename, _dialect, _patient_table, _columns = _SCENARIOS[scenario]
    with tempfile.TemporaryDirectory(prefix="lot05_synthetic_") as directory:
        root = pathlib.Path(directory)
        staged = root / "staged"
        staged.mkdir()
        source = staged / filename
        if scenario == "S02":
            # Deliberately use a new, CLOSED SQLite copy. No live cabinet DB.
            with sqlite3.connect(source) as db:
                db.execute("PRAGMA journal_mode=DELETE")
                db.execute(
                    "CREATE TABLE dossiers (id INTEGER PRIMARY KEY, "
                    "numero_dossier TEXT, nom TEXT, prenom TEXT, "
                    "date_naissance TEXT, sexe TEXT, telephone TEXT, "
                    "legacy_password TEXT)"
                )
                db.execute(
                    "CREATE TABLE rdv (id INTEGER PRIMARY KEY, "
                    "patient_id INTEGER, date_rdv TEXT)"
                )
                db.execute(
                    "INSERT INTO dossiers VALUES "
                    "(1, 'FAKE-001', 'SYNTHETIC_ONLY_MARTIN', "
                    "'SYNTHETIC_ONLY_LEA', '2001-12-15', 'F', '0000000000', "
                    "'FAKE_SECRET_NEVER_IMPORT')"
                )
                db.commit()
        else:
            source.write_bytes((_FIXTURES / filename).read_bytes())
        yield source, staged


def _inspect(scenario: str, source: pathlib.Path, root: pathlib.Path):
    return inspector.inspect_staged_copy(
        source, root, dialect=_SCENARIOS[scenario][1],
        attested_offline_copy=True,
    )


def _explicit_draft(scenario: str, report, target):
    patient_table, field_choices = _SCENARIOS[scenario][2:]
    decisions = tuple(
        mapping.TableDecision(
            t.source_name,
            "patients" if t.source_name == patient_table else None,
            tuple(mapping.ColumnDecision(
                c.name, field_choices.get(c.name)
                if t.source_name == patient_table else None
            ) for c in t.columns),
        ) for t in report.tables
    )
    return mapping.build_mapping_draft(
        report, target, decisions,
        source_software="LAB-FICTITIOUS-" + scenario,
        source_version="synthetic-1",
        profile_version=1,
    )


def _chain(scenario: str, source: pathlib.Path, root: pathlib.Path):
    report = _inspect(scenario, source, root)
    declared, target = _target()
    proposal = mapping.propose_mapping(report, target)
    draft = _explicit_draft(scenario, report, target)
    checked = mapping.revalidate_mapping_draft(draft, report, target)
    return report, declared, target, proposal, draft, checked


class MigrationScenarios(unittest.TestCase):
    def _assert_safe_chain(self, scenario: str):
        with _staged(scenario) as (source, root):
            report, declared, target, proposal, draft, checked = _chain(
                scenario, source, root
            )
            patient_table = _SCENARIOS[scenario][2]
            self.assertIn(patient_table, [t.source_name for t in report.tables])
            self.assertEqual(len(report.sha256), 64)
            self.assertEqual(declared.provenance, "SQLALCHEMY_DECLARED_METADATA_ONLY")
            self.assertFalse(declared.physical_schema_verified)
            self.assertFalse(declared.tenant_verified)
            self.assertFalse(declared.admin_approved)
            self.assertFalse(declared.import_permitted)
            self.assertEqual(target.schema_revision, "orm-declared:neo000000027")
            self.assertFalse(report.import_permitted)
            self.assertFalse(proposal.mapping_approved)
            self.assertFalse(proposal.import_permitted)
            self.assertFalse(draft.admin_approved)
            self.assertFalse(draft.dry_run_completed)
            self.assertFalse(draft.import_permitted)
            self.assertTrue(checked.exact_source_and_target)
            self.assertTrue(checked.requires_human_review)
            self.assertFalse(checked.import_permitted)
            # Different-language / legacy table names never auto-bind.
            self.assertTrue(all(t.suggested_target_table is None for t in proposal.tables))
            self.assertEqual(
                [d.target_table for d in draft.decisions if d.source_table == patient_table],
                ["patients"],
            )
            self.assertTrue(
                all(d.target_table is None for d in draft.decisions
                    if d.source_table != patient_table)
            )
            # Clinic ownership and imported credentials MUST NOT be copied.
            selected = next(d for d in draft.decisions if d.source_table == patient_table)
            # Assert every explicit EN/FR/ES synonym is mapped to the correct
            # REAL declared Digital Crown patient field, not merely a table.
            actual_columns = {c.source_column: c.target_column for c in selected.columns}
            expected_columns = _SCENARIOS[scenario][3]
            for source_field, expected_target_field in expected_columns.items():
                self.assertIn(source_field, actual_columns)
                self.assertEqual(actual_columns[source_field], expected_target_field)
            self.assertEqual(
                {target_field for target_field in actual_columns.values()
                 if target_field is not None},
                set(expected_columns.values()),
            )
            self.assertNotIn("employer_id", [
                c.target_column for c in selected.columns if c.target_column
            ])
            self.assertNotIn("id", [
                c.target_column for c in selected.columns if c.target_column
            ])
            for column in selected.columns:
                if "password" in column.source_column:
                    self.assertIsNone(column.target_column)
            public_metadata = json.dumps(
                [report.to_dict(), declared.as_ui_json(), draft.to_dict()],
                ensure_ascii=False,
            )
            self.assertNotIn("SYNTHETIC_ONLY_", public_metadata)
            self.assertNotIn("FAKE_SECRET_NEVER_IMPORT", public_metadata)
            self.assertNotIn("FAKE-001", public_metadata)
            return report

    def test_s01_mysql_english_sql_schema_to_draft(self):
        report = self._assert_safe_chain("S01")
        self.assertEqual(report.source_format, "sql-text-ddl")
        self.assertIn("OTHER_SQL_NOT_PARSED", report.warnings)
        self.assertEqual(len(report.tables), 2)

    def test_s02_sqlite_french_cold_copy_to_draft(self):
        report = self._assert_safe_chain("S02")
        self.assertEqual(report.source_format, "sqlite-copy")
        self.assertEqual(len(report.tables), 2)
        self.assertEqual(report.row_counts, None)

    def test_s03_postgresql_spanish_sql_schema_to_draft(self):
        report = self._assert_safe_chain("S03")
        self.assertEqual(report.source_format, "sql-text-ddl")
        self.assertIn("OTHER_SQL_NOT_PARSED", report.warnings)
        self.assertEqual(len(report.tables), 2)


class MigrationScenarioAdversarial(unittest.TestCase):
    def test_s04_native_backup_not_misidentified_as_sql(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = pathlib.Path(temp)
            path = folder / "sample.bak"
            path.write_bytes(b"FAKE_NATIVE_BACKUP_NOT_A_TEXT_SQL_DUMP")
            with self.assertRaisesRegex(inspector.UnsafeSource, "NATIVE_ADAPTER_NOT_IMPLEMENTED"):
                inspector.inspect_staged_copy(
                    path, folder, dialect="postgresql", attested_offline_copy=True
                )

    def test_s05_secret_field_cannot_be_forced_into_patient_column(self):
        with _staged("S01") as (source, root):
            report = _inspect("S01", source, root)
            _, target = _target()
            good = _explicit_draft("S01", report, target)
            bad = tuple(
                mapping.TableDecision(
                    t.source_table, t.target_table,
                    tuple(mapping.ColumnDecision(
                        c.source_column,
                        "telephone" if c.source_column == "password_hash" else c.target_column,
                    ) for c in t.columns),
                ) for t in good.decisions
            )
            with self.assertRaisesRegex(mapping.MappingRejected, "CREDENTIAL_MAPPING_FORBIDDEN"):
                mapping.build_mapping_draft(
                    report, target, bad, source_software="LAB",
                    source_version=None, profile_version=1,
                )

    def test_s06_modified_source_file_needs_new_human_review(self):
        with _staged("S03") as (source, root):
            report, _, target, _, draft, _ = _chain("S03", source, root)
            source.write_text(source.read_text(encoding="utf-8") + "\n-- changed synthetic source\n", encoding="utf-8")
            after = _inspect("S03", source, root)
            self.assertNotEqual(report.sha256, after.sha256)
            checked = mapping.revalidate_mapping_draft(draft, after, target)
            self.assertFalse(checked.exact_source_and_target)
            self.assertIn("SOURCE_DUMP_CHANGED", checked.mismatches)
            self.assertTrue(checked.requires_human_review)

    def test_s07_client_side_flag_cannot_authorize_import(self):
        with _staged("S02") as (source, root):
            report, _, target, _, draft, _ = _chain("S02", source, root)
            tampered = replace(draft, admin_approved=True, import_permitted=True)
            with self.assertRaisesRegex(mapping.MappingRejected, "DRAFT_CANNOT_AUTHORIZE"):
                mapping.revalidate_mapping_draft(tampered, report, target)

    def test_s08_unsupported_sql_type_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            path = root / "bad.sql"
            path.write_text("CREATE TABLE x (id INTEGER, suspect VARCHAR(20) ZEROFILL);")
            with self.assertRaisesRegex(inspector.UnsafeSource, "UNSUPPORTED_COLUMN_TYPE_SUFFIX"):
                inspector.inspect_staged_copy(
                    path, root, dialect="mysql", attested_offline_copy=True
                )

    def test_s09_csv_requires_future_adapter(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            path = root / "export.csv"
            path.write_text("first_name,last_name\nFAKE,FAKE\n")
            with self.assertRaisesRegex(inspector.UnsafeSource, "NATIVE_ADAPTER_NOT_IMPLEMENTED"):
                inspector.inspect_staged_copy(
                    path, root, dialect="sqlite", attested_offline_copy=True
                )

    def test_s10_sql_commands_not_executed_on_inspection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            path = root / "fake.sql"
            path.write_text(
                "CREATE TABLE witness (id INTEGER); "
                "DROP TABLE witness; INSERT INTO witness VALUES (1);"
            )
            report = inspector.inspect_staged_copy(
                path, root, dialect="sqlite", attested_offline_copy=True
            )
            self.assertEqual([t.source_name for t in report.tables], ["witness"])
            self.assertIn("SQL_NOT_EXECUTED", report.warnings)
            self.assertIn("OTHER_SQL_NOT_PARSED", report.warnings)

    def test_s11_wal_mode_sqlite_requires_cold_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            path = root / "warm.db"
            with sqlite3.connect(path) as db:
                mode = db.execute("PRAGMA journal_mode=WAL").fetchone()[0]
                self.assertEqual(mode.lower(), "wal")
                db.execute("CREATE TABLE fake (id INTEGER)")
                db.commit()
            with self.assertRaisesRegex(inspector.UnsafeSource, "SQLITE_ROLLBACK_JOURNAL_COPY_REQUIRED"):
                inspector.inspect_staged_copy(
                    path, root, dialect="sqlite", attested_offline_copy=True
                )

    def test_s12_source_must_be_attested_offline_copy(self):
        with _staged("S01") as (source, root):
            with self.assertRaisesRegex(inspector.UnsafeSource, "OFFLINE_COPY_ATTESTATION_REQUIRED"):
                inspector.inspect_staged_copy(
                    source, root, dialect="mysql", attested_offline_copy=False
                )


if __name__ == "__main__":
    unittest.main()
