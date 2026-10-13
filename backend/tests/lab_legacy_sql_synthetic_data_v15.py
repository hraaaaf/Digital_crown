"""STRICT TEST-ONLY LOT05.3 rehearsal. NEVER import or wire into backend runtime.

All records must be conspicuously synthetic, target is sqlite3 ':memory:'.
Use with the existing *non-approved* offline 05.1/05.2 mapping drafts.
The scratch target models a tiny subset, NOT the real schema or permission gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Any


class LabRejected(ValueError):
    """Stable error code only: no source values or patient-identifying data."""


@dataclass(frozen=True)
class LabReport:
    scenario: str
    patient_count: int
    appointment_count: int
    mapped_reference_count: int
    duplicate_candidates: int
    scratch_fk_checked: bool
    scratch_rollback_zero_rows: bool
    all_values_synthetic: bool = True
    physical_target_verified: bool = False
    tenant_authenticated: bool = False
    human_approved: bool = False
    real_dry_run_completed: bool = False
    import_permitted: bool = False


_DATE_FORMATS = {
    "iso-date": "%Y-%m-%d",
    "french-date": "%d/%m/%Y",
    "spanish-date": "%d-%m-%Y",
}
_DATETIME_FORMATS = {
    "iso-minute": "%Y-%m-%d %H:%M",
    "french-minute": "%d/%m/%Y %H:%M",
    "spanish-minute": "%d-%m-%Y %H:%M",
}
_TARGET_PATIENT_COLUMNS = frozenset(("nom", "prenom", "date_naissance", "sexe", "email", "telephone", "numero_dossier"))
_TARGET_APPOINTMENT_COLUMNS = frozenset(("patient_id", "datetime_start", "status"))
_RESTRICTED = frozenset(("id", "employer_id", "hashed_password", "password_hash", "role", "permissions"))
_MAX_ROWS_PER_TABLE = 32


def _date(value: Any, pattern: str, *, timestamp: bool = False) -> str:
    choices = _DATETIME_FORMATS if timestamp else _DATE_FORMATS
    if pattern not in choices:
        raise LabRejected("EXPLICIT_DATE_FORMAT_REQUIRED")
    if not isinstance(value, str) or not 0 < len(value) <= 32:
        raise LabRejected("INVALID_DATE_VALUE")
    fmt = choices[pattern]
    try:
        parsed = datetime.strptime(value, fmt)
    except ValueError as exc:
        raise LabRejected("INVALID_DATE_VALUE") from exc
    # Never silently accept dates/times parsed by strptime's forgiving padding.
    if parsed.strftime(fmt) != value:
        raise LabRejected("AMBIGUOUS_OR_NONCANONICAL_DATE")
    return parsed.strftime("%Y-%m-%d %H:%M:00" if timestamp else "%Y-%m-%d 00:00:00")


def _bounded_rows(rows: Any) -> tuple[dict[str, Any], ...]:
    if (not isinstance(rows, tuple) or not 0 < len(rows) <= _MAX_ROWS_PER_TABLE):
        raise LabRejected("EMPTY_OR_EXCESSIVE_SYNTHETIC_BATCH")
    for row in rows:
        if not isinstance(row, dict) or len(row) > 100:
            raise LabRejected("INVALID_SYNTHETIC_ROW")
        for key, value in row.items():
            if not isinstance(key, str) or not isinstance(value, str) or len(value) > 255:
                raise LabRejected("INVALID_SYNTHETIC_ROW")
    return rows


def _column_choices(decision: Any, allowed: frozenset[str]) -> dict[str, str]:
    used: set[str] = set()
    choices: dict[str, str] = {}
    for c in decision.columns:
        if c.target_column is None:
            continue
        if c.target_column in used or c.target_column not in allowed:
            raise LabRejected("UNSAFE_OR_COLLIDING_LAB_MAPPING")
        if c.source_column.casefold() in _RESTRICTED:
            raise LabRejected("SOURCE_ID_OR_CREDENTIAL_MAPPING_FORBIDDEN")
        used.add(c.target_column)
        choices[c.target_column] = c.source_column
    return choices


def _extract(row: dict[str, Any], names: dict[str, str], field: str) -> str:
    key = names.get(field)
    if key is None or key not in row:
        raise LabRejected("REQUIRED_FIELD_UNMAPPED")
    return row[key]


def run_synthetic_dryrun(
    *,
    scenario: str,
    source_report: Any,
    target_snapshot: Any,
    draft: Any,
    revalidate_mapping: Any,
    source_patient_table: str,
    source_appointment_table: str,
    patient_id_column: str,
    patient_rows: tuple[dict[str, str], ...],
    appointment_rows: tuple[dict[str, str], ...],
    date_format: str,
    datetime_format: str,
    accepted_source_status: str,
    target_declared_fields: dict[str, frozenset[str]],
) -> LabReport:
    """Rehearse transformed FAKE rows in disposable SQLite, then ROLLBACK.

    Never accepts an engine, path, DATABASE_URL, tenant ID or real DB connection.
    Caller-supplied rows are validated for conspicuous synthetic names.
    A verified local draft is still not an approved clinical mapping.
    """
    if scenario not in ("S01", "S02", "S03"):
        raise LabRejected("SYNTHETIC_SCENARIO_ALLOWLIST_REQUIRED")
    if any(bool(getattr(draft, flag, False))
           for flag in ("admin_approved", "dry_run_completed", "import_permitted")):
        raise LabRejected("APPROVED_MAPPING_CANNOT_ENTER_LAB")
    if bool(getattr(source_report, "import_permitted", True)):
        raise LabRejected("SOURCE_IMPORT_FLAG_FORBIDDEN")
    if not callable(revalidate_mapping):
        raise LabRejected("DRAFT_REVALIDATION_REQUIRED")
    try:
        validation = revalidate_mapping(draft, source_report, target_snapshot)
    except (TypeError, ValueError, AttributeError) as exc:
        raise LabRejected("INVALID_MAPPING_DRAFT") from exc
    if (not validation.exact_source_and_target
            or not validation.requires_human_review
            or validation.import_permitted):
        raise LabRejected("DRAFT_CHANGED_OR_AUTOMATICALLY_APPROVED")

    if not isinstance(target_declared_fields, dict) or (
        _TARGET_PATIENT_COLUMNS - target_declared_fields.get("patients", frozenset())
    ) or (_TARGET_APPOINTMENT_COLUMNS - target_declared_fields.get("appointments", frozenset())):
        raise LabRejected("REAL_DECLARED_COLUMNS_UNAVAILABLE")
    chosen = {d.target_table: d for d in draft.decisions if d.target_table is not None}
    if set(chosen) != {"patients", "appointments"}:
        raise LabRejected("PATIENT_AND_APPOINTMENT_MAPPING_REQUIRED")
    if (chosen["patients"].source_table != source_patient_table
            or chosen["appointments"].source_table != source_appointment_table):
        raise LabRejected("UNEXPECTED_SOURCE_MAPPING")
    patients = _column_choices(chosen["patients"], _TARGET_PATIENT_COLUMNS)
    appointments = _column_choices(chosen["appointments"], _TARGET_APPOINTMENT_COLUMNS)
    if not {"nom", "prenom", "date_naissance", "sexe"}.issubset(patients):
        raise LabRejected("REQUIRED_PATIENT_MAPPING_INCOMPLETE")
    if set(appointments) != _TARGET_APPOINTMENT_COLUMNS:
        raise LabRejected("REQUIRED_APPOINTMENT_MAPPING_INCOMPLETE")
    if not isinstance(patient_id_column, str) or not patient_id_column:
        raise LabRejected("SOURCE_ID_REQUIRED")
    if patient_id_column in patients.values():
        raise LabRejected("SOURCE_PRIMARY_KEY_MUST_NOT_BE_COPIED")
    if not isinstance(accepted_source_status, str) or not accepted_source_status:
        raise LabRejected("EXPLICIT_STATUS_TRANSLATION_REQUIRED")
    patient_rows = _bounded_rows(patient_rows)
    appointment_rows = _bounded_rows(appointment_rows)

    # Enforce every selected row comes with exactly the declared source fields.
    inventory = {t.source_name: {c.name for c in t.columns}
                 for t in source_report.tables}
    for table_name, rows in ((source_patient_table, patient_rows),
                             (source_appointment_table, appointment_rows)):
        if table_name not in inventory:
            raise LabRejected("SOURCE_SCHEMA_TABLE_MISSING")
        for row in rows:
            if set(row) != inventory[table_name]:
                raise LabRejected("SOURCE_ROW_SCHEMA_MISMATCH")

    normalized_patients: list[tuple[str, str, str, str, str | None, str | None, str | None]] = []
    normalized_appointments: list[tuple[str, str, str]] = []
    source_ids: set[str] = set()
    similarity_keys: set[tuple[str, str, str]] = set()
    for row in patient_rows:
        src_id = row.get(patient_id_column)
        if not src_id or src_id in source_ids:
            raise LabRejected("DUPLICATE_OR_MISSING_SOURCE_PATIENT_ID")
        source_ids.add(src_id)
        nom, prenom = _extract(row, patients, "nom"), _extract(row, patients, "prenom")
        if not nom.startswith("SYNTHETIC_ONLY_") or not prenom.startswith("SYNTHETIC_ONLY_"):
            raise LabRejected("NON_SYNTHETIC_PATIENT_FORBIDDEN")
        dob = _date(_extract(row, patients, "date_naissance"), date_format)
        sexe = _extract(row, patients, "sexe")
        if sexe not in ("M", "F"):
            raise LabRejected("UNSUPPORTED_PATIENT_SEX")
        duplicate_key = (nom.casefold(), prenom.casefold(), dob)
        if duplicate_key in similarity_keys:
            raise LabRejected("POTENTIAL_DUPLICATE_REQUIRES_HUMAN_REVIEW")
        similarity_keys.add(duplicate_key)
        email = row.get(patients["email"]) if "email" in patients else None
        telephone = row.get(patients["telephone"]) if "telephone" in patients else None
        dossier = row.get(patients["numero_dossier"]) if "numero_dossier" in patients else None
        normalized_patients.append((src_id, nom, prenom, dob, sexe, email, telephone, dossier))

    for row in appointment_rows:
        ref = _extract(row, appointments, "patient_id")
        if ref not in source_ids:
            raise LabRejected("ORPHAN_APPOINTMENT_PATIENT_REFERENCE")
        when = _date(_extract(row, appointments, "datetime_start"), datetime_format, timestamp=True)
        if _extract(row, appointments, "status") != accepted_source_status:
            raise LabRejected("UNKNOWN_APPOINTMENT_STATUS_REQUIRES_REVIEW")
        normalized_appointments.append((ref, when, "PREVU"))

    # ONLY in-memory SQLite; never accept connections/paths provided by caller.
    db = sqlite3.connect(":memory:")
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, employer_id INTEGER NOT NULL, nom TEXT NOT NULL, prenom TEXT NOT NULL, date_naissance TEXT NOT NULL, sexe TEXT NOT NULL, email TEXT, telephone TEXT, numero_dossier TEXT, UNIQUE(employer_id, nom, prenom, date_naissance))")
        db.execute("CREATE TABLE appointments (id INTEGER PRIMARY KEY, employer_id INTEGER NOT NULL, patient_id INTEGER NOT NULL REFERENCES patients(id), datetime_start TEXT NOT NULL, status TEXT NOT NULL CHECK(status = 'PREVU'))")
        db.execute("CREATE TRIGGER tenant_guard BEFORE INSERT ON appointments WHEN (SELECT employer_id FROM patients WHERE id=NEW.patient_id) != NEW.employer_id BEGIN SELECT RAISE(ABORT, 'tenant_mismatch'); END")
        db.execute("SAVEPOINT synthetic_rehearsal")
        ref_to_new_id: dict[str, int] = {}
        # Fixed synthetic lab tenant, NOT derived from user data; no real auth.
        synthetic_owner = 777
        for src_id, nom, prenom, dob, sexe, email, telephone, dossier in normalized_patients:
            cursor = db.execute(
                "INSERT INTO patients (employer_id, nom, prenom, date_naissance, sexe, email, telephone, numero_dossier) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (synthetic_owner, nom, prenom, dob, sexe, email, telephone, dossier),
            )
            ref_to_new_id[src_id] = cursor.lastrowid
        for ref, when, status in normalized_appointments:
            db.execute(
                "INSERT INTO appointments (employer_id, patient_id, datetime_start, status) VALUES (?, ?, ?, ?)",
                (synthetic_owner, ref_to_new_id[ref], when, status),
            )
        staged_p = db.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        staged_a = db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        fk = db.execute("PRAGMA foreign_key_check").fetchall()
        mismatched_tenant = db.execute(
            "SELECT COUNT(*) FROM appointments a JOIN patients p ON p.id=a.patient_id WHERE a.employer_id != p.employer_id"
        ).fetchone()[0]
        if fk or mismatched_tenant or staged_p != len(patient_rows) or staged_a != len(appointment_rows):
            raise LabRejected("SYNTHETIC_INTEGRITY_MISMATCH")
        db.execute("ROLLBACK TO synthetic_rehearsal")
        db.execute("RELEASE synthetic_rehearsal")
        counts = db.execute(
            "SELECT (SELECT COUNT(*) FROM patients), (SELECT COUNT(*) FROM appointments)"
        ).fetchone()
        if counts != (0, 0):
            raise LabRejected("SCRATCH_ROLLBACK_FAILED")
        return LabReport(
            scenario, staged_p, staged_a, len(normalized_appointments),
            0, True, True,
        )
    except sqlite3.DatabaseError as exc:
        raise LabRejected("SCRATCH_SQLITE_INTEGRITY_REJECTED") from exc
    finally:
        db.rollback()
        db.close()
