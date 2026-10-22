"""LOT05.5 staff-facing *preflight and synthetic rehearsal ONLY*.

NO patient-row reading on cabinet DB, NO source uploads, NO real import.
The 100x200 rehearsal uses a separate SQLite :memory: engine built from the
real declared ORM subset, always rolled back and never installed in runtime DB.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re

from sqlalchemy import MetaData, create_engine, event, inspect, select, func, text
from sqlalchemy.exc import SQLAlchemyError

_TABLES = ("users", "patients", "agenda_resources", "appointments")
_EXPECTED = "neo000000032"
_PREVIEW = ("patients", "appointments")
_DENIED_COLUMNS = {
    "id", "employer_id", "deleted_by", "deleted_at",
    "created_at", "updated_at", "confirmed_by_id", "confirmed_at",
    "reminder_sent", "reminder_sent_at", "expires_at",
}
_DENIED_FRAGMENTS = re.compile(
    r"password|passwd|secret|token|credential|hash|permission|licen[sc]|"
    r"role|private|oauth|otp|approval", re.IGNORECASE,
)


class MigrationPreflightRefused(ValueError):
    pass


@dataclass(frozen=True)
class SyntheticRehearsalReport:
    mode: str
    source_patients: int
    source_appointments: int
    verified_patients: int
    verified_appointments: int
    verified_patient_links: int
    orphan_appointments: int
    cross_tenant_links: int
    after_rollback_patients: int
    after_rollback_appointments: int
    cabinet_rows_read: bool = False
    cabinet_rows_written: bool = False
    schema_migrated_by_alembic: bool = False
    import_permitted: bool = False

    def to_dict(self):
        return asdict(self)


def _columns(table):
    return {column.name: bool(column.nullable) for column in table.columns}


def inspect_cabinet_schema_read_only(connection, declared_metadata):
    """Read schema metadata and alembic_version ONLY; no clinical SELECT.

    A partial subset match cannot be treated as complete Alembic certification.
    Real auth/Workstation and tenant validation are handled by the API dependency.
    """
    try:
        inspector = inspect(connection)
        present = set(inspector.get_table_names())
        try:
            revision_rows = tuple(connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalars().all()) if "alembic_version" in present else ()
        except SQLAlchemyError:
            revision_rows = ()
        revision_ok = revision_rows == (_EXPECTED,)
        subset_ok = all(name in present and name in declared_metadata.tables
                        for name in _TABLES)
        if subset_ok:
            for name in _TABLES:
                table = declared_metadata.tables[name]
                if _columns(table) != {
                    c["name"]: bool(c["nullable"]) for c in inspector.get_columns(name)
                }:
                    subset_ok = False
                    break
                declared_fks = sorted((
                    tuple(c.name for c in fk.columns),
                    next(iter(fk.elements)).column.table.name,
                    tuple(e.column.name for e in fk.elements)
                ) for fk in table.foreign_key_constraints)
                actual_fks = sorted((
                    tuple(fk["constrained_columns"]), fk["referred_table"],
                    tuple(fk["referred_columns"])
                ) for fk in inspector.get_foreign_keys(name))
                if declared_fks != actual_fks:
                    subset_ok = False
                    break
        physical_ok = revision_ok and subset_ok
        allowed_tables = []
        if physical_ok:
            for name in _PREVIEW:
                fields = [
                    {"name": column.name}
                    for column in declared_metadata.tables[name].columns
                    if column.name not in _DENIED_COLUMNS
                    and not _DENIED_FRAGMENTS.search(column.name)
                ]
                allowed_tables.append({"name": name, "columns": fields})
        return {
            "status": "construction",
            "schema_revision_matches": revision_ok,
            "declared_subset_matches": subset_ok,
            "physical_subset_checked": physical_ok,
            "full_schema_certified": False,
            "authenticated_cabinet_scope": True,  # only after API principal gate
            "dry_run_real_data_available": False,
            "import_permitted": False,
            "target_preview": {
                "schema_revision": "observed-read-only:" + _EXPECTED,
                "tables": allowed_tables,
            } if physical_ok else None,
            "blockers": [
                "REAL_IMPORT_NOT_IMPLEMENTED",
                "FULL_ALEMBIC_SCHEMA_NOT_ATTESTED",
                "REAL_BACKUP_AND_RESTORE_NOT_CERTIFIED",
                "HUMAN_APPROVAL_REQUIRED",
            ] + ([] if physical_ok else ["PHYSICAL_SCHEMA_OR_ALEMBIC_HEAD_MISMATCH"]),
        }
    except SQLAlchemyError:
        # Fail closed without leaking schema SQL or underlying DB error strings.
        return {
            "status": "construction", "schema_revision_matches": False,
            "declared_subset_matches": False, "physical_subset_checked": False,
            "full_schema_certified": False, "authenticated_cabinet_scope": True,
            "dry_run_real_data_available": False, "import_permitted": False,
            "target_preview": None,
            "blockers": ["SCHEMA_INSPECTION_FAILED", "REAL_IMPORT_NOT_IMPLEMENTED"],
        }


def require_cabinet_owner(user):
    """Owner-only; no settings-permission or superadmin bypass of tenancy."""
    if user is None or not getattr(user, "is_active", False):
        raise MigrationPreflightRefused("AUTHENTICATED_OWNER_REQUIRED")
    role = getattr(getattr(user, "role", None), "value", getattr(user, "role", None))
    if role not in ("ADMIN", "DENTISTE") or getattr(user, "employer_id", None) is not None:
        raise MigrationPreflightRefused("CABINET_OWNER_ONLY")
    if getattr(user, "approval_status", "approved") != "approved":
        raise MigrationPreflightRefused("OWNER_APPROVAL_REQUIRED")
    if type(getattr(user, "id", None)) is not int or user.id < 1:
        raise MigrationPreflightRefused("VALID_OWNER_ID_REQUIRED")
    return user.id


def _declared_subset(metadata):
    subset = MetaData()
    for table in _TABLES:
        if table not in metadata.tables:
            raise MigrationPreflightRefused("DECLARED_TABLE_MISSING")
        metadata.tables[table].to_metadata(subset)
    return subset


def run_fixed_synthetic_rehearsal(metadata):
    """Run exactly 100/200 artificial rows and rollback ALL writes.

    Accepts metadata only, never a source DB connection, a user engine, a path,
    a file upload, a staff-supplied tenant ID, or patient data.
    """
    subset = _declared_subset(metadata)
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    @event.listens_for(engine, "connect")
    def _foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    try:
        with engine.connect() as db:
            subset.create_all(db)
            db.commit()
            if db.exec_driver_sql("PRAGMA foreign_keys").scalar() != 1:
                raise MigrationPreflightRefused("SCRATCH_FK_DISABLED")
            db.commit()
            tx = db.begin()
            try:
                users = subset.tables["users"]
                patients = subset.tables["patients"]
                appointments = subset.tables["appointments"]
                db.execute(users.insert().values(
                    id=777, email="synthetic-owner-777@example.invalid",
                    hashed_password="FAKE_NO_LOGIN", role="DENTISTE",
                    is_active=True, is_licensed=False,
                ))
                ids = []
                for i in range(100):
                    dest = db.execute(patients.insert().values(
                        employer_id=777, numero_dossier="SYN-%05d" % (10001+i),
                        nom="SYNTHETIC_ONLY_LAST_%03d" % i,
                        prenom="SYNTHETIC_ONLY_FIRST_%03d" % i,
                        date_naissance=datetime(2000,3,1+i%28),
                        sexe="F" if i%2 else "M",
                        email="synthetic%03d@example.invalid" % i,
                    )).inserted_primary_key[0]
                    ids.append(dest)
                for j in range(200):
                    owner_id = ids[j//2]
                    db.execute(appointments.insert().values(
                        patient_id=owner_id, employer_id=777,
                        datetime_start=datetime(2026,11,1+j%28,8+j%9,30),
                        status="PREVU",
                    ))
                p_count = db.execute(select(func.count()).select_from(patients)).scalar_one()
                a_count = db.execute(select(func.count()).select_from(appointments)).scalar_one()
                linked = db.execute(text(
                    "SELECT COUNT(*) FROM appointments a JOIN patients p "
                    "ON a.patient_id=p.id WHERE p.employer_id=a.employer_id"
                )).scalar_one()
                orphans = db.execute(text(
                    "SELECT COUNT(*) FROM appointments a LEFT JOIN patients p "
                    "ON a.patient_id=p.id WHERE p.id IS NULL"
                )).scalar_one()
                cross_tenant = db.execute(text(
                    "SELECT COUNT(*) FROM appointments a JOIN patients p "
                    "ON a.patient_id=p.id WHERE p.employer_id!=a.employer_id"
                )).scalar_one()
                if (p_count,a_count,linked,orphans,cross_tenant)!=(100,200,200,0,0):
                    raise MigrationPreflightRefused("SYNTHETIC_PARITY_MISMATCH")
                if db.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
                    raise MigrationPreflightRefused("SYNTHETIC_FK_MISMATCH")
            finally:
                tx.rollback()
            # Verify actual rollback, not just SQLAlchemy tx status.
            left_patients = db.execute(select(func.count()).select_from(
                subset.tables["patients"])).scalar_one()
            left_appointments = db.execute(select(func.count()).select_from(
                subset.tables["appointments"])).scalar_one()
            left_users = db.execute(select(func.count()).select_from(
                subset.tables["users"])).scalar_one()
            if (left_patients,left_appointments,left_users)!=(0,0,0):
                raise MigrationPreflightRefused("SCRATCH_ROLLBACK_FAILED")
            return SyntheticRehearsalReport(
                "SYNTHETIC_MEMORY_ONLY", 100,200,100,200,200,0,0,0,0
            )
    finally:
        engine.dispose()
