"""LOT05.3 LAB: synthetic VALUES through declared mapping into rollback-only SQLite.

Three green paths S01/S02/S03 and adversarial failures; NO real clinic data,
SQL dump execution, target DB engine or runtime import of this test-only helper.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import replace
from pathlib import Path
import sqlite3
import unittest

from test_legacy_sql_migration_scenarios_v15 import (
    _staged, _inspect, _target, _real_declared_model_only, mapping
)
from lab_legacy_sql_synthetic_data_v15 import LabRejected, run_synthetic_dryrun


_FIELDS = {
    "S01": {
        "patients": ("legacy_patients", "patient_id", {
            "first_name": "prenom", "last_name": "nom", "birth_date": "date_naissance",
            "sex": "sexe", "email": "email"
        }),
        "appointments": ("legacy_appointments", {
            "patient_ref": "patient_id", "scheduled_at": "datetime_start",
            "status": "status"
        }),
        "date_format": "iso-date", "datetime_format": "iso-minute", "status": "planned",
    },
    "S02": {
        "patients": ("dossiers", "id", {
            "numero_dossier": "numero_dossier", "nom": "nom", "prenom": "prenom",
            "date_naissance": "date_naissance", "sexe": "sexe", "telephone": "telephone"
        }),
        "appointments": ("rdv", {
            "patient_id": "patient_id", "date_rdv": "datetime_start", "status": "status"
        }),
        "date_format": "iso-date", "datetime_format": "french-minute", "status": "prévu",
    },
    "S03": {
        "patients": ("personas", "id", {
            "nombre": "prenom", "apellido": "nom",
            "fecha_nacimiento": "date_naissance", "sexo": "sexe",
            "correo": "email"
        }),
        "appointments": ("citas", {
            "persona_id": "patient_id", "fecha": "datetime_start", "estado": "status"
        }),
        "date_format": "spanish-date", "datetime_format": "spanish-minute",
        "status": "programada",
    },
}


def _declared_columns():
    base = _real_declared_model_only()
    return {
        name: frozenset(base.tables[name].columns.keys())
        for name in ("patients", "appointments")
    }


def _draft(report, target, scenario):
    spec = _FIELDS[scenario]
    patient_table, _legacy_id, patient_map = spec["patients"]
    appt_table, appointment_map = spec["appointments"]
    decisions = []
    for table in report.tables:
        if table.source_name == patient_table:
            name, translations = "patients", patient_map
        elif table.source_name == appt_table:
            name, translations = "appointments", appointment_map
        else:
            raise AssertionError("UNEXPECTED_SYNTHETIC_SOURCE_TABLE")
        decisions.append(mapping.TableDecision(
            table.source_name, name,
            tuple(mapping.ColumnDecision(c.name, translations.get(c.name)) for c in table.columns),
        ))
    return mapping.build_mapping_draft(
        report, target, tuple(decisions),
        source_software="LAB_" + scenario,
        source_version="SYNTHETIC_ONLY",
        profile_version=1,
    )


def _rows(scenario, source_path: Path):
    if scenario == "S01":
        return (
            (
                {"patient_id":"101", "first_name":"SYNTHETIC_ONLY_ALICE", "last_name":"SYNTHETIC_ONLY_EXAMPLE", "birth_date":"2001-03-04", "sex":"F", "email":"fake1@example.invalid", "password_hash":"FAKE_DO_NOT_IMPORT", "legacy_notes":"FAKE_DO_NOT_EXPORT"},
                {"patient_id":"102", "first_name":"SYNTHETIC_ONLY_BOB", "last_name":"SYNTHETIC_ONLY_EXAMPLE", "birth_date":"1997-09-08", "sex":"M", "email":"fake2@example.invalid", "password_hash":"FAKE_DO_NOT_IMPORT", "legacy_notes":"FAKE_DO_NOT_EXPORT"},
            ),
            (
                {"appointment_id":"501", "patient_ref":"101", "scheduled_at":"2026-10-14 09:30", "status":"planned"},
                {"appointment_id":"502", "patient_ref":"102", "scheduled_at":"2026-10-15 14:00", "status":"planned"},
            ),
        )
    if scenario == "S03":
        return (
            (
                {"id":"202", "nombre":"SYNTHETIC_ONLY_LUCIA", "apellido":"SYNTHETIC_ONLY_DEMO", "fecha_nacimiento":"15-01-2000", "sexo":"F", "correo":"fake3@example.invalid", "comentario":"FAKE_DO_NOT_EXPORT"},
                {"id":"203", "nombre":"SYNTHETIC_ONLY_CARLOS", "apellido":"SYNTHETIC_ONLY_DEMO", "fecha_nacimiento":"09-09-1999", "sexo":"M", "correo":"fake4@example.invalid", "comentario":"FAKE_DO_NOT_EXPORT"},
            ),
            (
                {"id":"503", "persona_id":"202", "fecha":"14-10-2026 11:45", "estado":"programada"},
            ),
        )
    if scenario == "S02":
        # This SOURCE is a real SQLite file, but it is created inside _staged()
        # from entirely fake values. Read ONLY the two fixed test tables.
        with sqlite3.connect(source_path) as writer:
            writer.execute("ALTER TABLE rdv ADD COLUMN status TEXT")
            writer.execute(
                "INSERT INTO rdv (id, patient_id, date_rdv, status) VALUES (?, ?, ?, ?)",
                (5, 1, "14/10/2026 10:30", "prévu"),
            )
            writer.commit()
        with closing(sqlite3.connect(source_path.as_uri() + "?mode=ro&immutable=1", uri=True)) as reader:
            reader.execute("PRAGMA query_only=ON")
            patient_columns = ("id", "numero_dossier", "nom", "prenom", "date_naissance", "sexe", "telephone", "legacy_password")
            appt_columns = ("id", "patient_id", "date_rdv", "status")
            patients = tuple(
                dict(zip(patient_columns, tuple(str(v) for v in record)))
                for record in reader.execute("SELECT id, numero_dossier, nom, prenom, date_naissance, sexe, telephone, legacy_password FROM dossiers").fetchall()
            )
            appointments = tuple(
                dict(zip(appt_columns, tuple(str(v) for v in record)))
                for record in reader.execute("SELECT id, patient_id, date_rdv, status FROM rdv").fetchall()
            )
        return patients, appointments
    raise AssertionError("UNKNOWN_TEST_FIXTURE")


def _context(scenario):
    # The helper is used only inside a _staged() synthetic tempfile context.
    raise AssertionError("USE _run_with_staged")


def _run(scenario, source_path, root, *, changes=None):
    spec = _FIELDS[scenario]
    p_rows, a_rows = _rows(scenario, source_path)
    report = _inspect(scenario, source_path, root)
    _declared, target = _target()
    draft = _draft(report, target, scenario)
    opts = {
        "scenario": scenario,
        "source_report": report,
        "target_snapshot": target,
        "draft": draft,
        "revalidate_mapping": mapping.revalidate_mapping_draft,
        "source_patient_table": spec["patients"][0],
        "source_appointment_table": spec["appointments"][0],
        "patient_id_column": spec["patients"][1],
        "patient_rows": p_rows,
        "appointment_rows": a_rows,
        "date_format": spec["date_format"],
        "datetime_format": spec["datetime_format"],
        "accepted_source_status": spec["status"],
        "target_declared_fields": _declared_columns(),
    }
    if changes:
        opts.update(changes(opts))
    return run_synthetic_dryrun(**opts)


class ValidSyntheticDataDryRun(unittest.TestCase):
    def _valid(self, scenario, expected_patients, expected_appointments):
        with _staged(scenario) as (source, root):
            result = _run(scenario, source, root)
        self.assertEqual(result.scenario, scenario)
        self.assertEqual(result.patient_count, expected_patients)
        self.assertEqual(result.appointment_count, expected_appointments)
        self.assertEqual(result.mapped_reference_count, expected_appointments)
        self.assertEqual(result.duplicate_candidates, 0)
        self.assertTrue(result.scratch_fk_checked)
        self.assertTrue(result.scratch_rollback_zero_rows)
        self.assertTrue(result.all_values_synthetic)
        self.assertFalse(result.physical_target_verified)
        self.assertFalse(result.tenant_authenticated)
        self.assertFalse(result.human_approved)
        self.assertFalse(result.real_dry_run_completed)
        self.assertFalse(result.import_permitted)
        self.assertNotIn("SYNTHETIC_ONLY_ALICE", str(result))
        self.assertNotIn("FAKE_DO_NOT_IMPORT", str(result))

    def test_s01_english_sql_fixture_values_into_rollback_only_scratch(self):
        self._valid("S01", 2, 2)

    def test_s02_read_actual_fictitious_sqlite_rows_and_rollback_target(self):
        self._valid("S02", 1, 1)

    def test_s03_spanish_sql_fixture_values_into_rollback_only_scratch(self):
        self._valid("S03", 2, 1)


class FailClosedSyntheticDataDryRun(unittest.TestCase):
    def _reject(self, scenario, code, changes):
        with _staged(scenario) as (source, root):
            with self.assertRaisesRegex(LabRejected, "^" + code + "$"):
                _run(scenario, source, root, changes=changes)

    def test_s04_orphan_appointment_reference(self):
        def change(opts):
            a = list(opts["appointment_rows"])
            a[0] = {**a[0], "patient_ref":"NO_SUCH_PATIENT"}
            return {"appointment_rows":tuple(a)}
        self._reject("S01", "ORPHAN_APPOINTMENT_PATIENT_REFERENCE", change)

    def test_s05_duplicate_patient_identity_is_human_review_not_auto_merge(self):
        def change(opts):
            p = list(opts["patient_rows"])
            p[1] = {**p[0], "patient_id":"999"}
            return {"patient_rows":tuple(p)}
        self._reject("S01", "POTENTIAL_DUPLICATE_REQUIRES_HUMAN_REVIEW", change)

    def test_s06_repeated_legacy_primary_key(self):
        def change(opts):
            p = list(opts["patient_rows"])
            p[1] = {**p[1], "patient_id":p[0]["patient_id"]}
            return {"patient_rows":tuple(p)}
        self._reject("S01", "DUPLICATE_OR_MISSING_SOURCE_PATIENT_ID", change)

    def test_s07_invalid_calendar_date(self):
        def change(opts):
            p = list(opts["patient_rows"])
            p[0] = {**p[0], "birth_date":"2026-02-30"}
            return {"patient_rows":tuple(p)}
        self._reject("S01", "INVALID_DATE_VALUE", change)

    def test_s08_undeclared_date_format_not_guessed(self):
        self._reject("S01", "EXPLICIT_DATE_FORMAT_REQUIRED", lambda opts: {"date_format": "guess"})

    def test_s09_legacy_status_needs_explicit_translation(self):
        def change(opts):
            a = list(opts["appointment_rows"])
            a[0] = {**a[0], "status":"completed"}
            return {"appointment_rows":tuple(a)}
        self._reject("S01", "UNKNOWN_APPOINTMENT_STATUS_REQUIRES_REVIEW", change)

    def test_s10_non_synthetic_name_cannot_enter_lab(self):
        def change(opts):
            p = list(opts["patient_rows"])
            p[0] = {**p[0], "first_name":"PLAUSIBLE_REAL_PERSON"}
            return {"patient_rows":tuple(p)}
        self._reject("S01", "NON_SYNTHETIC_PATIENT_FORBIDDEN", change)

    def test_s11_flag_forgery_disallowed_even_in_lab(self):
        self._reject(
            "S01", "APPROVED_MAPPING_CANNOT_ENTER_LAB",
            lambda opts: {"draft":replace(opts["draft"], admin_approved=True)},
        )

    def test_s12_changed_source_fingerprint_disallowed(self):
        self._reject(
            "S01", "DRAFT_CHANGED_OR_AUTOMATICALLY_APPROVED",
            lambda opts: {"source_report":replace(opts["source_report"], sha256="b" * 64)},
        )

    def test_s13_missing_source_column_refused(self):
        def change(opts):
            p = list(opts["patient_rows"])
            p[0] = {k:v for k,v in p[0].items() if k != "last_name"}
            return {"patient_rows":tuple(p)}
        self._reject("S01", "SOURCE_ROW_SCHEMA_MISMATCH", change)

    def test_s14_noncannonical_date_refused(self):
        def change(opts):
            p = list(opts["patient_rows"])
            p[0] = {**p[0], "birth_date":"2001-3-4"}
            return {"patient_rows":tuple(p)}
        self._reject("S01", "AMBIGUOUS_OR_NONCANONICAL_DATE", change)

    def test_s15_excessive_rows_refused(self):
        self._reject("S01", "EMPTY_OR_EXCESSIVE_SYNTHETIC_BATCH",
                     lambda opts: {"patient_rows":tuple(opts["patient_rows"][0] for _ in range(33))})

    def test_s16_invalid_declared_model_disallowed(self):
        self._reject("S01", "REAL_DECLARED_COLUMNS_UNAVAILABLE",
                     lambda opts: {"target_declared_fields":{"patients":frozenset(), "appointments":frozenset()}})

    def test_s17_unsupported_status_translation_refused(self):
        self._reject("S01", "EXPLICIT_STATUS_TRANSLATION_REQUIRED",
                     lambda opts: {"accepted_source_status":""})

    def test_s18_duplicate_appointment_candidate_requires_human_review(self):
        def change(opts):
            appointments = list(opts["appointment_rows"])
            appointments.append({**appointments[0], "appointment_id":"999"})
            return {"appointment_rows":tuple(appointments)}
        self._reject("S01", "POTENTIAL_DUPLICATE_APPOINTMENT_REQUIRES_HUMAN_REVIEW", change)

    def test_s19_invalid_appointment_datetime_is_rejected(self):
        def change(opts):
            appointments = list(opts["appointment_rows"])
            appointments[0] = {**appointments[0], "scheduled_at":"2026-10-14 25:30"}
            return {"appointment_rows":tuple(appointments)}
        self._reject("S01", "INVALID_DATE_VALUE", change)


if __name__ == "__main__":
    unittest.main()
