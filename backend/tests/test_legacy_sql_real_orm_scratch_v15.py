"""V1.5 LOT05.3: physically execute *real declared* ORM table definitions in an isolated SQLite LAB.

S01/S02/S03 use only conspicuously fake values and the existing 05.2 draft.
This is NOT a copy of a cabinet DB or a complete Alembic-managed schema.
No runtime import, no actual tenant, no real data, no persistent DB or API.
"""
from __future__ import annotations

from datetime import datetime
from contextlib import contextmanager
import sqlite3
import sys
import unittest

from sqlalchemy import MetaData, create_engine, inspect, select, func, text
from sqlalchemy.exc import IntegrityError

from test_legacy_sql_migration_scenarios_v15 import (
    _staged, _inspect, _target, _real_declared_model_only, mapping
)
from test_legacy_sql_synthetic_dryrun_v15 import _FIELDS, _rows, _draft, _declared_columns
from lab_legacy_sql_synthetic_data_v15 import (
    _date, run_synthetic_dryrun, LabRejected
)


_TABLE_SCOPE = ("users", "agenda_resources", "patients", "appointments")
_OWNER = 777
_OTHER_OWNER = 778
_FORMAT = "%Y-%m-%d %H:%M:%S"


class RealORMGuardRefused(ValueError):
    """Non-PHI rejection code for laboratory ownership checks."""


def _physical_subset():
    """Copy real SQLAlchemy columns/FKs/checks/uniques for explicit minimal scope."""
    declared = _real_declared_model_only()
    metadata = MetaData()
    for name in _TABLE_SCOPE:
        if name not in declared.tables:
            raise AssertionError("REAL_ORM_TABLE_MISSING")
        declared.tables[name].to_metadata(metadata)
    return metadata


@contextmanager
def _physical_scratch():
    metadata = _physical_subset()
    # Hard-coded, disposable in-memory only; NO user-supplied DB URL.
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    if engine.url.database != ":memory:" or engine.dialect.name != "sqlite":
        raise AssertionError("SCRATCH_TARGET_MUST_BE_MEMORY")
    try:
        with engine.connect() as con:
            con.exec_driver_sql("PRAGMA foreign_keys = ON")
            if not con.exec_driver_sql("PRAGMA foreign_keys").scalar():
                raise AssertionError("SCRATCH_FOREIGN_KEYS_DISABLED")
            con.commit()
            metadata.create_all(con)
            con.commit()
            # Exact physical table/columns, including nullability, from *real*
            # ORM subset definitions, not from the miniature hand-coded scratch.
            i = inspect(con)
            assert set(i.get_table_names()) == set(_TABLE_SCOPE)
            for name in _TABLE_SCOPE:
                expected = {col.name: bool(col.nullable)
                            for col in metadata.tables[name].columns}
                actual = {col["name"]: bool(col["nullable"])
                          for col in i.get_columns(name)}
                if expected != actual:
                    raise AssertionError("REAL_ORM_PHYSICAL_COLUMN_DRIFT")
            if i.has_table("alembic_version"):
                raise AssertionError("NOT_A_CABINET_ALEMBIC_DB")
            # SQLAlchemy reflection starts an implicit transaction; close it
            # explicitly BEFORE opening the rollback-only rehearsal transaction.
            con.commit()
            tx = con.begin()
            try:
                yield metadata, con
            finally:
                # ABSOLUTE rollback on success, constraint failure or exception.
                tx.rollback()
                for name in ("appointments", "patients", "agenda_resources", "users"):
                    count = con.execute(select(func.count()).select_from(metadata.tables[name])).scalar_one()
                    if count != 0:
                        raise AssertionError("REAL_ORM_SCRATCH_ROLLBACK_FAILED")
    finally:
        engine.dispose()


def _owner_row(owner_id):
    return {
        "id": owner_id,
        "email": "synthetic-%s@example.invalid" % owner_id,
        "hashed_password": "SYNTHETIC_NEVER_AUTHENTICATE",
        "role": "DENTISTE",
        "is_active": True,
        "is_licensed": False,
    }


def _patient_row(*, owner=_OWNER, number="LAB-ORIGINAL", patient_id=None):
    row = {
        "employer_id": owner,
        "numero_dossier": number,
        "nom": "SYNTHETIC_ONLY_TEST",
        "prenom": "SYNTHETIC_ONLY_BASE",
        "date_naissance": datetime(1980, 1, 2),
        "sexe": "F",
    }
    if patient_id is not None:
        row["id"] = patient_id
    return row


def _appointment_row(patient_id, owner=_OWNER, when=None):
    return {
        "patient_id": patient_id,
        "employer_id": owner,
        "datetime_start": when or datetime(2026, 10, 14, 9, 30),
        "status": "PREVU",
    }


def _guarded_appointment_insert(metadata, con, values):
    """Fail-closed LAB policy until app has a certified real import-specific gate."""
    patients = metadata.tables["patients"]
    patient_owner = con.execute(
        select(patients.c.employer_id).where(patients.c.id == values["patient_id"])
    ).scalar_one_or_none()
    if patient_owner is None or patient_owner != values.get("employer_id"):
        raise RealORMGuardRefused("CROSS_TENANT_PATIENT_RDV_LINK_FORBIDDEN")
    return con.execute(metadata.tables["appointments"].insert().values(**values)).inserted_primary_key[0]


def _source_to_real_orm(scenario, report, target, draft, patient_rows, appointment_rows):
    """Read chosen fake-data mapping; no import functionality outside this test."""
    spec = _FIELDS[scenario]
    decisions = {d.target_table: d for d in draft.decisions if d.target_table is not None}
    assert set(decisions) == {"patients", "appointments"}
    pm = {c.target_column: c.source_column for c in decisions["patients"].columns
          if c.target_column is not None}
    am = {c.target_column: c.source_column for c in decisions["appointments"].columns
          if c.target_column is not None}
    assert {"nom", "prenom", "date_naissance", "sexe"}.issubset(pm)
    assert {"datetime_start", "patient_id", "status"} == set(am)
    # Required: exercise existing scratch dry-run policy on the *same* fake
    # rows & draft first; it issues zero persisted writes.
    report_of_dryrun = run_synthetic_dryrun(
        scenario=scenario, source_report=report,
        target_snapshot=target, draft=draft,
        revalidate_mapping=mapping.revalidate_mapping_draft,
        source_patient_table=spec["patients"][0],
        source_appointment_table=spec["appointments"][0],
        patient_id_column=spec["patients"][1],
        patient_rows=patient_rows, appointment_rows=appointment_rows,
        date_format=spec["date_format"], datetime_format=spec["datetime_format"],
        accepted_source_status=spec["status"],
        target_declared_fields=_declared_columns(),
    )
    assert report_of_dryrun.scratch_rollback_zero_rows
    normalized = []
    seen = set()
    for original in patient_rows:
        old_id = original[spec["patients"][1]]
        assert old_id not in seen
        seen.add(old_id)
        name = original[pm["nom"]]
        first_name = original[pm["prenom"]]
        assert name.startswith("SYNTHETIC_ONLY_") and first_name.startswith("SYNTHETIC_ONLY_")
        dob = datetime.strptime(_date(original[pm["date_naissance"]], spec["date_format"]), _FORMAT)
        row = {
            "employer_id": _OWNER, "nom": name, "prenom": first_name,
            "date_naissance": dob, "sexe": original[pm["sexe"]],
            "numero_dossier": "LAB-" + scenario + "-" + old_id,
        }
        for field in ("email", "telephone"):
            if field in pm:
                row[field] = original[pm[field]]
        normalized.append((old_id, row))
    appointments = []
    for original in appointment_rows:
        old_id = original[am["patient_id"]]
        when = datetime.strptime(
            _date(original[am["datetime_start"]], spec["datetime_format"], timestamp=True), _FORMAT
        )
        assert original[am["status"]] == spec["status"]
        appointments.append((old_id, when))
    return normalized, appointments


class RealORMPhysicalSubset(unittest.TestCase):
    def _run_case(self, scenario, expected_patients, expected_appointments):
        with _staged(scenario) as (source, root):
            # S02 creates the extra synthetic RDV/status column before inspection.
            rows_p, rows_a = _rows(scenario, source)
            report = _inspect(scenario, source, root)
            _declared, target = _target()
            draft = _draft(report, target, scenario)
            patients, appointments = _source_to_real_orm(
                scenario, report, target, draft, rows_p, rows_a
            )
            with _physical_scratch() as (md, con):
                users = md.tables["users"]
                patient_table = md.tables["patients"]
                app = md.tables["appointments"]
                con.execute(users.insert(), [_owner_row(_OWNER), _owner_row(_OTHER_OWNER)])
                # Preexisting lab record forces new target IDs away from source
                # values and distinguishes replay/existing-data behavior.
                con.execute(patient_table.insert().values(
                    **_patient_row(patient_id=900, number="LAB-ALREADY-EXISTING")
                ))
                new_ids = {}
                for old_id, payload in patients:
                    created = con.execute(patient_table.insert().values(**payload))
                    target_id = created.inserted_primary_key[0]
                    self.assertNotEqual(str(target_id), old_id)
                    new_ids[old_id] = target_id
                for old_id, when in appointments:
                    _guarded_appointment_insert(
                        md, con, _appointment_row(new_ids[old_id], when=when)
                    )
                self.assertEqual(
                    con.execute(select(func.count()).select_from(patient_table)).scalar_one(),
                    expected_patients + 1,
                )
                self.assertEqual(
                    con.execute(select(func.count()).select_from(app)).scalar_one(),
                    expected_appointments,
                )
                self.assertEqual(con.exec_driver_sql("PRAGMA foreign_key_check").fetchall(), [])
                ids = con.execute(select(app.c.patient_id)).scalars().all()
                self.assertEqual(set(ids), set(new_ids.values()))
                self.assertEqual(con.execute(
                    select(func.count()).select_from(app.join(
                        patient_table, app.c.patient_id == patient_table.c.id
                    )).where(app.c.employer_id != patient_table.c.employer_id)
                ).scalar_one(), 0)
            # _physical_scratch() verifies ZERO rows in all tables AFTER rollback.

    def test_s01_english_two_patients_two_appointments_real_orm(self):
        self._run_case("S01", 2, 2)

    def test_s02_french_real_synthetic_sqlite_source_to_real_orm(self):
        self._run_case("S02", 1, 1)

    def test_s03_spanish_two_patients_one_appointment_real_orm(self):
        self._run_case("S03", 2, 1)

    def test_real_patient_unique_dossier_within_same_tenant(self):
        with _physical_scratch() as (md, con):
            con.execute(md.tables["users"].insert(), [
                _owner_row(_OWNER), _owner_row(_OTHER_OWNER)
            ])
            patient = md.tables["patients"]
            con.execute(patient.insert().values(**_patient_row(number="LAB-SAME")))
            with self.assertRaises(IntegrityError):
                with con.begin_nested():
                    con.execute(patient.insert().values(**_patient_row(number="LAB-SAME")))
            # Same human-visible dossier number permitted for separate tenant.
            con.execute(patient.insert().values(
                **_patient_row(owner=_OTHER_OWNER, number="LAB-SAME")
            ))
            self.assertEqual(
                con.execute(select(func.count()).select_from(patient)).scalar_one(), 2
            )

    def test_real_patient_missing_required_column_is_rejected(self):
        with _physical_scratch() as (md, con):
            con.execute(md.tables["users"].insert(), _owner_row(_OWNER))
            values = _patient_row()
            del values["sexe"]
            with self.assertRaises(IntegrityError):
                with con.begin_nested():
                    con.execute(md.tables["patients"].insert().values(**values))

    def test_real_appointment_foreign_key_refuses_unknown_patient(self):
        with _physical_scratch() as (md, con):
            con.execute(md.tables["users"].insert(), _owner_row(_OWNER))
            with self.assertRaises(IntegrityError):
                with con.begin_nested():
                    con.execute(md.tables["appointments"].insert().values(
                        **_appointment_row(123456)
                    ))

    def test_explicit_lab_guard_refuses_cross_tenant_link(self):
        with _physical_scratch() as (md, con):
            con.execute(md.tables["users"].insert(), [
                _owner_row(_OWNER), _owner_row(_OTHER_OWNER)
            ])
            one = con.execute(md.tables["patients"].insert().values(
                **_patient_row(owner=_OWNER)
            )).inserted_primary_key[0]
            with self.assertRaisesRegex(
                RealORMGuardRefused, "CROSS_TENANT_PATIENT_RDV_LINK_FORBIDDEN"
            ):
                _guarded_appointment_insert(md, con, _appointment_row(one, owner=_OTHER_OWNER))
            self.assertEqual(
                con.execute(select(func.count()).select_from(md.tables["appointments"])).scalar_one(),
                0,
            )

    def test_real_orm_schema_lacks_composite_patient_tenant_foreign_key(self):
        # This is an intentionally UNRESOLVED security gap. DB foreign keys
        # verify patient_id existence and employer_id existence separately,
        # not equality of patient/appointment employers. In production an
        # authenticated server policy must also reject cross-tenant links.
        with _physical_scratch() as (md, con):
            fks = inspect(con).get_foreign_keys("appointments")
            self.assertFalse(any(
                set(fk.get("constrained_columns") or ()) >= {"patient_id", "employer_id"}
                and fk.get("referred_table") == "patients" for fk in fks
            ))
            con.execute(md.tables["users"].insert(), [
                _owner_row(_OWNER), _owner_row(_OTHER_OWNER)
            ])
            patient_id = con.execute(md.tables["patients"].insert().values(
                **_patient_row(owner=_OWNER)
            )).inserted_primary_key[0]
            # Demonstrate actual DB constraint alone fails to enforce tenant.
            con.execute(md.tables["appointments"].insert().values(
                **_appointment_row(patient_id, owner=_OTHER_OWNER)
            ))
            self.assertEqual(con.exec_driver_sql("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(con.execute(text(
                "SELECT COUNT(*) FROM appointments a JOIN patients p ON "
                "p.id=a.patient_id WHERE a.employer_id != p.employer_id"
            )).scalar_one(), 1)

    def test_real_orm_appointment_has_no_duplicate_scheduling_constraint(self):
        # Full import must add a certified idempotency/duplicate decision gate
        # rather than misreport an ORM-level unique index that does not exist.
        with _physical_scratch() as (md, con):
            con.execute(md.tables["users"].insert(), _owner_row(_OWNER))
            patient_id = con.execute(md.tables["patients"].insert().values(
                **_patient_row()
            )).inserted_primary_key[0]
            _guarded_appointment_insert(md, con, _appointment_row(patient_id))
            _guarded_appointment_insert(md, con, _appointment_row(patient_id))
            self.assertEqual(con.execute(
                select(func.count()).select_from(md.tables["appointments"])
            ).scalar_one(), 2)

    def test_untrusted_source_draft_cannot_be_approved(self):
        with _staged("S01") as (source, root):
            rows_p, rows_a = _rows("S01", source)
            report = _inspect("S01", source, root)
            _, target = _target()
            draft = _draft(report, target, "S01")
            self.assertFalse(draft.admin_approved)
            self.assertFalse(draft.import_permitted)
            self.assertFalse(draft.dry_run_completed)
            self.assertTrue(mapping.revalidate_mapping_draft(
                draft, report, target
            ).requires_human_review)
            with _physical_scratch() as (md, con):
                self.assertFalse(inspect(con).has_table("alembic_version"))

if __name__ == "__main__":
    unittest.main()
