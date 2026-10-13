"""LOT05.4 TEST-ONLY: 100x200 TRUE SQLite row-level synthetic E2E transfer.

Reads a COLD SQLite source with 100 fake patients and 200 fake appointments,
uses actual 05.1 inspection / 05.2 explicit mapping and real SQLAlchemy
declared target tables. Commits ONLY into a freshly generated tempfile
SQLite target and checks recovery. This is NOT a runtime clinic importer.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest

from sqlalchemy import create_engine, select, func, text
from sqlalchemy.exc import IntegrityError

from test_legacy_sql_migration_scenarios_v15 import inspector, mapping, _target
from test_legacy_sql_real_orm_scratch_v15 import _physical_subset, _owner_row
from lab_legacy_sql_synthetic_data_v15 import _date


_OWNER = 777
_OTHER = 778
_N_PATIENTS = 100
_N_APPOINTMENTS = 200
_SNAPSHOT_COLUMNS = {
    "legacy_patients": ("id", "first_name", "last_name", "birth_date", "sex", "email", "password_hash", "legacy_notes"),
    "legacy_appointments": ("id", "patient_ref", "scheduled_at", "status"),
}
_CHOICES = {
    "legacy_patients": ("patients", {
        "first_name": "prenom", "last_name": "nom",
        "birth_date": "date_naissance", "sex": "sexe", "email": "email",
    }),
    "legacy_appointments": ("appointments", {
        "patient_ref": "patient_id", "scheduled_at": "datetime_start", "status": "status",
    }),
}


class SyntheticE2ERefused(ValueError):
    """Safe error code only, no source row values in messages."""


@dataclass(frozen=True)
class SyntheticE2EResult:
    outcome: str
    patient_count: int
    appointment_count: int
    correct_appointment_links: int
    orphan_count: int
    tenant_mismatch_count: int
    source_unchanged: bool
    physical_target_subset: bool = True
    alembic_migrated: bool = False
    actual_staff_authenticated: bool = False
    clinical_backup_certified: bool = False
    human_approved: bool = False
    import_permitted: bool = False


def _sha(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@contextmanager
def _synthetic_source():
    with tempfile.TemporaryDirectory(prefix="dc05_e2e_fake_only_") as work:
        root = Path(work)
        stage = root / "staged"
        stage.mkdir()
        path = stage / "synthetic_legacy.db"
        with closing(sqlite3.connect(path)) as c:
            c.execute("PRAGMA journal_mode=DELETE")
            c.execute(
                "CREATE TABLE legacy_patients (id INTEGER PRIMARY KEY, first_name TEXT NOT NULL,"
                "last_name TEXT NOT NULL, birth_date TEXT NOT NULL, sex TEXT NOT NULL,"
                "email TEXT, password_hash TEXT NOT NULL, legacy_notes TEXT)"
            )
            c.execute(
                "CREATE TABLE legacy_appointments (id INTEGER PRIMARY KEY,"
                "patient_ref INTEGER NOT NULL, scheduled_at TEXT NOT NULL, status TEXT NOT NULL)"
            )
            c.executemany(
                "INSERT INTO legacy_patients VALUES (?,?,?,?,?,?,?,?)",
                [
                    (10001 + i, "SYNTHETIC_ONLY_FIRST_%03d" % i,
                     "SYNTHETIC_ONLY_LAST_%03d" % i, "2000-03-%02d" % (1 + i % 28),
                     "F" if i % 2 else "M", "synthetic%03d@example.invalid" % i,
                     "FAKE_CREDENTIAL_NEVER_IMPORT", "FAKE_SENSITIVE_NOTE_NEVER_IMPORT")
                    for i in range(_N_PATIENTS)
                ],
            )
            c.executemany(
                "INSERT INTO legacy_appointments VALUES (?,?,?,?)",
                [
                    (50001 + i, 10001 + i // 2,
                     "2026-11-%02d %02d:30" % (1 + i % 28, 8 + i % 9),
                     "planned")
                    for i in range(_N_APPOINTMENTS)
                ],
            )
            c.commit()
            assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        yield path, stage, root


def _inspect_and_map(source: Path, stage: Path):
    report = inspector.inspect_staged_copy(
        source, stage, dialect="sqlite", attested_offline_copy=True
    )
    if {x.source_name for x in report.tables} != set(_SNAPSHOT_COLUMNS):
        raise SyntheticE2ERefused("UNEXPECTED_SOURCE_TABLE_SET")
    for t in report.tables:
        if {c.name for c in t.columns} != set(_SNAPSHOT_COLUMNS[t.source_name]):
            raise SyntheticE2ERefused("UNEXPECTED_SOURCE_COLUMNS")
    _, target = _target()
    choices = tuple(
        mapping.TableDecision(
            t.source_name, _CHOICES[t.source_name][0],
            tuple(mapping.ColumnDecision(c.name, _CHOICES[t.source_name][1].get(c.name))
                  for c in t.columns)
        )
        for t in report.tables
    )
    draft = mapping.build_mapping_draft(
        report, target, choices,
        source_software="SYNTHETIC_E2E_SQLITE_ONLY", source_version="1",
        profile_version=1,
    )
    if any((draft.admin_approved, draft.import_permitted, draft.dry_run_completed)):
        raise SyntheticE2ERefused("NON_AUTHORIZING_DRAFT_REQUIRED")
    return report, target, draft


def _read_fake_rows(source: Path, report, target, draft):
    try:
        checked = mapping.revalidate_mapping_draft(draft, report, target)
    except (ValueError, AttributeError, TypeError) as exc:
        raise SyntheticE2ERefused("INVALID_MAPPING_DRAFT") from exc
    if not checked.exact_source_and_target or not checked.requires_human_review or checked.import_permitted:
        raise SyntheticE2ERefused("SOURCE_OR_TARGET_FINGERPRINT_CHANGED")
    # The source is a generated cold copy; inspection SHA is pinned before
    # opening it to read rows. Never execute any source-provided SQL.
    if _sha(source) != report.sha256:
        raise SyntheticE2ERefused("SOURCE_FILE_CHANGED")
    decision = {d.target_table: d for d in draft.decisions}
    if set(decision) != {"patients", "appointments"}:
        raise SyntheticE2ERefused("MAPPING_TABLE_DECISIONS_MISSING")
    for table_name, (target_name, expected) in _CHOICES.items():
        choices = {c.source_column: c.target_column
                   for c in decision[target_name].columns}
        if choices != {col: expected.get(col) for col in _SNAPSHOT_COLUMNS[table_name]}:
            raise SyntheticE2ERefused("MAPPING_COLUMNS_NOT_EXPLICIT")
    try:
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro&immutable=1",
                                     uri=True, timeout=1)) as c:
            c.execute("PRAGMA query_only=ON")
            c.execute("PRAGMA trusted_schema=OFF")
            if c.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise SyntheticE2ERefused("SOURCE_SQLITE_INTEGRITY_FAILURE")
            # Explicit column allowlist: password_hash / clinical legacy_notes
            # NEVER SELECTed or transformed into the target.
            patients = c.execute(
                "SELECT id, first_name, last_name, birth_date, sex, email "
                "FROM legacy_patients ORDER BY id"
            ).fetchall()
            appointments = c.execute(
                "SELECT id, patient_ref, scheduled_at, status "
                "FROM legacy_appointments ORDER BY id"
            ).fetchall()
            if c.execute("SELECT COUNT(*) FROM legacy_patients").fetchone()[0] != len(patients):
                raise SyntheticE2ERefused("UNSTABLE_PATIENT_SOURCE")
            if c.execute("SELECT COUNT(*) FROM legacy_appointments").fetchone()[0] != len(appointments):
                raise SyntheticE2ERefused("UNSTABLE_APPOINTMENT_SOURCE")
    except sqlite3.DatabaseError as exc:
        raise SyntheticE2ERefused("SOURCE_READ_FAILED") from exc
    if _sha(source) != report.sha256:
        raise SyntheticE2ERefused("SOURCE_CHANGED_DURING_READ")
    if len(patients) != _N_PATIENTS or len(appointments) != _N_APPOINTMENTS:
        raise SyntheticE2ERefused("SOURCE_ROW_COUNT_NOT_CERTIFIED")
    normalized_patients = []
    normalized_appointments = []
    patient_source_ids = set()
    identities = set()
    appointment_keys = set()
    for source_id, first, last, birth, sex, email in patients:
        if type(source_id) is not int or source_id in patient_source_ids:
            raise SyntheticE2ERefused("DUPLICATE_SOURCE_PATIENT_ID")
        if not isinstance(first, str) or not first.startswith("SYNTHETIC_ONLY_") or (
                not isinstance(last, str) or not last.startswith("SYNTHETIC_ONLY_")):
            raise SyntheticE2ERefused("NON_SYNTHETIC_PATIENT_REFUSED")
        if sex not in {"M", "F"}:
            raise SyntheticE2ERefused("UNREVIEWED_PATIENT_SEX")
        if not isinstance(email, str) or not email.endswith("@example.invalid"):
            raise SyntheticE2ERefused("NON_SYNTHETIC_EMAIL_REFUSED")
        dob = datetime.strptime(_date(birth, "iso-date"), "%Y-%m-%d %H:%M:%S")
        identity = (first.casefold(), last.casefold(), dob)
        if identity in identities:
            raise SyntheticE2ERefused("CANDIDATE_PATIENT_DUPLICATE")
        identities.add(identity)
        patient_source_ids.add(source_id)
        normalized_patients.append(
            (source_id, {
                "employer_id": _OWNER,
                "numero_dossier": "SYN-%05d" % source_id,
                "prenom": first, "nom": last,
                "date_naissance": dob, "sexe": sex, "email": email,
            })
        )
    for appointment_id, reference, when, status in appointments:
        if type(appointment_id) is not int or reference not in patient_source_ids:
            raise SyntheticE2ERefused("ORPHAN_APPOINTMENT_REFUSED")
        if status != "planned":
            raise SyntheticE2ERefused("UNREVIEWED_APPOINTMENT_STATUS")
        moment = datetime.strptime(_date(when, "iso-minute", timestamp=True),
                                   "%Y-%m-%d %H:%M:%S")
        key = (reference, moment)
        if key in appointment_keys:
            raise SyntheticE2ERefused("CANDIDATE_DUPLICATE_APPOINTMENT")
        appointment_keys.add(key)
        normalized_appointments.append((reference, moment))
    return normalized_patients, normalized_appointments


def _lab_target(root: Path):
    path = root / "synthetic_digital_crown_target.db"
    # A caller NEVER chooses a DB URL; root is a tempfile generated above.
    engine = create_engine("sqlite+pysqlite:///" + str(path), future=True)
    md = _physical_subset()  # actual backend.models SQLAlchemy table declarations
    with engine.begin() as con:
        con.exec_driver_sql("PRAGMA foreign_keys=ON")
        md.create_all(con)
        con.execute(text(
            "CREATE TABLE synthetic_import_journal "
            "(batch_id TEXT PRIMARY KEY, source_sha TEXT NOT NULL, "
            "patients INTEGER NOT NULL, appointments INTEGER NOT NULL)"
        ))
        con.execute(md.tables["users"].insert(), [
            _owner_row(_OWNER), _owner_row(_OTHER)
        ])
        con.execute(md.tables["patients"].insert().values(
            id=900, employer_id=_OWNER, numero_dossier="LAB-PRIOR",
            nom="SYNTHETIC_ONLY_PREEXISTING", prenom="SYNTHETIC_ONLY_EXAMPLE",
            date_naissance=datetime(1980,1,2), sexe="F"
        ))
    return engine, md, path


def _audit(con, md, count_patients, count_appointments):
    p, a = md.tables["patients"], md.tables["appointments"]
    if con.execute(select(func.count()).select_from(p)).scalar_one() != count_patients + 1:
        raise SyntheticE2ERefused("TARGET_PATIENT_COUNT_MISMATCH")
    if con.execute(select(func.count()).select_from(a)).scalar_one() != count_appointments:
        raise SyntheticE2ERefused("TARGET_APPOINTMENT_COUNT_MISMATCH")
    orphans = con.execute(text(
        "SELECT COUNT(*) FROM appointments a LEFT JOIN patients p ON p.id=a.patient_id "
        "WHERE p.id IS NULL"
    )).scalar_one()
    mismatch = con.execute(text(
        "SELECT COUNT(*) FROM appointments a JOIN patients p ON p.id=a.patient_id "
        "WHERE a.employer_id <> p.employer_id"
    )).scalar_one()
    if orphans or mismatch or con.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
        raise SyntheticE2ERefused("FOREIGN_KEY_OR_TENANT_MISMATCH")
    return orphans, mismatch


def _import_to_temporary_target(*, source, report, target, draft, engine, md,
                                 batch_id="SYNTH-E2E-BATCH-001", dry_run=False,
                                 force_error_after=None, principal_owner=_OWNER):
    """100/200 real rows → real declared ORM tables in temp file only.

    No database path can be provided; the caller must generate the temporary
    engine in _lab_target. This helper is under backend/tests/, not a service.
    """
    if principal_owner != _OWNER:
        raise SyntheticE2ERefused("UNTRUSTED_CABINET_ID_REFUSED")
    if not isinstance(batch_id, str) or not batch_id.startswith("SYNTH-E2E-BATCH-"):
        raise SyntheticE2ERefused("INVALID_SYNTHETIC_BATCH")
    patients, appointments = _read_fake_rows(source, report, target, draft)
    with engine.connect() as con:
        if con.exec_driver_sql("PRAGMA foreign_keys").scalar() != 1:
            raise SyntheticE2ERefused("TARGET_FOREIGN_KEYS_DISABLED")
        con.commit()
        trans = con.begin()
        try:
            previous = con.execute(text(
                "SELECT source_sha, patients, appointments FROM synthetic_import_journal "
                "WHERE batch_id=:batch"
            ), {"batch":batch_id}).fetchone()
            if previous is not None:
                if previous[0] != report.sha256:
                    raise SyntheticE2ERefused("BATCH_REPLAY_HASH_CONFLICT")
                _audit(con, md, _N_PATIENTS, _N_APPOINTMENTS)
                trans.rollback()
                return SyntheticE2EResult("EXACT_SYNTHETIC_REPLAY_NOOP", 100, 200, 200, 0, 0, True)
            if con.execute(text("SELECT COUNT(*) FROM synthetic_import_journal")).scalar_one():
                raise SyntheticE2ERefused("CROSS_BATCH_RECONCILIATION_REQUIRED")
            ptable, atable = md.tables["patients"], md.tables["appointments"]
            source_to_dest = {}
            expected_patients = []
            for source_id, payload in patients:
                if con.execute(select(ptable.c.id).where(
                    ptable.c.employer_id == _OWNER,
                    ptable.c.numero_dossier == payload["numero_dossier"]
                )).first():
                    raise SyntheticE2ERefused("PREEXISTING_PATIENT_CONFLICT")
                new_id = con.execute(ptable.insert().values(**payload)).inserted_primary_key[0]
                if new_id in source_to_dest.values():
                    raise SyntheticE2ERefused("NON_UNIQUE_NEW_ID")
                source_to_dest[source_id] = new_id
                expected_patients.append((
                    payload["numero_dossier"], payload["prenom"], payload["nom"],
                    payload["date_naissance"], payload["sexe"], payload["email"]
                ))
                if force_error_after == len(source_to_dest):
                    raise SyntheticE2ERefused("INJECTED_ATOMIC_FAILURE")
            expected_appointments = []
            for ref, when in appointments:
                if ref not in source_to_dest:
                    raise SyntheticE2ERefused("ORPHAN_APPOINTMENT_REFUSED")
                dest_id = source_to_dest[ref]
                cabinet_id = con.execute(select(ptable.c.employer_id).where(
                    ptable.c.id == dest_id, ptable.c.deleted_at.is_(None)
                )).scalar_one_or_none()
                if cabinet_id != _OWNER:
                    raise SyntheticE2ERefused("CROSS_TENANT_LINK_REFUSED")
                con.execute(atable.insert().values(
                    patient_id=dest_id, employer_id=_OWNER,
                    datetime_start=when, status="PREVU"
                ))
                expected_appointments.append(("SYN-%05d" % ref, when))
            orphans, mismatches = _audit(con, md, _N_PATIENTS, _N_APPOINTMENTS)
            actual_patients = con.execute(text(
                "SELECT numero_dossier,prenom,nom,date_naissance,sexe,email FROM patients "
                "WHERE employer_id=:owner AND numero_dossier LIKE 'SYN-%' "
                "ORDER BY numero_dossier"
            ), {"owner":_OWNER}).fetchall()
            expected_patients.sort(key=lambda row: row[0])
            if [(x[0],x[1],x[2],str(x[3]),x[4],x[5]) for x in actual_patients] != [
                (x[0],x[1],x[2],str(x[3]),x[4],x[5]) for x in expected_patients
            ]:
                raise SyntheticE2ERefused("PATIENT_ROW_PARITY_FAILURE")
            actual_appointments = con.execute(text(
                "SELECT p.numero_dossier,a.datetime_start "
                "FROM appointments a JOIN patients p ON p.id=a.patient_id "
                "WHERE a.employer_id=:owner ORDER BY p.numero_dossier,a.datetime_start"
            ), {"owner":_OWNER}).fetchall()
            if sorted((x[0],str(x[1])) for x in actual_appointments) != sorted(
                (x[0],str(x[1])) for x in expected_appointments
            ):
                raise SyntheticE2ERefused("APPOINTMENT_ROW_PARITY_FAILURE")
            if dry_run:
                trans.rollback()
                outcome = "DRY_RUN_ROLLBACK_ZERO_IMPORTED"
            else:
                con.execute(text(
                    "INSERT INTO synthetic_import_journal "
                    "(batch_id,source_sha,patients,appointments) VALUES (:batch,:sha,100,200)"
                ), {"batch":batch_id, "sha":report.sha256})
                trans.commit()
                outcome = "COMMITTED_SYNTHETIC_TEMP_DB_ONLY"
            return SyntheticE2EResult(
                outcome, _N_PATIENTS, _N_APPOINTMENTS,
                _N_APPOINTMENTS, orphans, mismatches, _sha(source)==report.sha256
            )
        except Exception:
            if trans.is_active:
                trans.rollback()
            raise


def _logical_fingerprint(path: Path) -> tuple[str, tuple[int,int,int]]:
    with closing(sqlite3.connect(path)) as c:
        c.execute("PRAGMA foreign_keys=ON")
        if c.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SyntheticE2ERefused("BACKUP_INTEGRITY_FAILURE")
        if c.execute("PRAGMA foreign_key_check").fetchall():
            raise SyntheticE2ERefused("BACKUP_FOREIGN_KEY_FAILURE")
        state = {
            "users": c.execute("SELECT id,email FROM users ORDER BY id").fetchall(),
            "patients": c.execute(
                "SELECT id,employer_id,numero_dossier,nom,prenom,date_naissance,sexe,email "
                "FROM patients ORDER BY id"
            ).fetchall(),
            "appointments": c.execute(
                "SELECT id,employer_id,patient_id,datetime_start,status "
                "FROM appointments ORDER BY id"
            ).fetchall(),
            "journal": c.execute(
                "SELECT batch_id,source_sha,patients,appointments FROM synthetic_import_journal "
                "ORDER BY batch_id"
            ).fetchall(),
        }
        counters = (len(state["patients"]),len(state["appointments"]),len(state["journal"]))
    digest = sha256(json.dumps(state,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return digest,counters


def _synthetic_backup_and_restore(source: Path, backup: Path, restored: Path):
    # All paths supplied by the same TemporaryDirectory fixture, never cabinet.
    with closing(sqlite3.connect(source)) as original:
        with closing(sqlite3.connect(backup)) as dest:
            original.backup(dest)
    with closing(sqlite3.connect(backup)) as backed:
        with closing(sqlite3.connect(restored)) as dest:
            backed.backup(dest)
    before = _logical_fingerprint(source)
    if before != _logical_fingerprint(backup) or before != _logical_fingerprint(restored):
        raise SyntheticE2ERefused("BACKUP_RESTORE_PARITY_FAILURE")
    return before


class SQLite100x200E2E(unittest.TestCase):
    def _env(self):
        return _synthetic_source()

    def test_01_full_sqlite_actual_rows_100_patients_200_appointments(self):
        with self._env() as (source,stage,root):
            inspection,target,draft = _inspect_and_map(source,stage)
            engine,md,destination=_lab_target(root)
            try:
                result=_import_to_temporary_target(
                    source=source,report=inspection,target=target,draft=draft,
                    engine=engine,md=md
                )
                self.assertEqual(result.outcome,"COMMITTED_SYNTHETIC_TEMP_DB_ONLY")
                self.assertEqual((result.patient_count,result.appointment_count,
                    result.correct_appointment_links,result.orphan_count,
                    result.tenant_mismatch_count),(100,200,200,0,0))
                self.assertTrue(result.source_unchanged)
                for key in ("alembic_migrated","actual_staff_authenticated",
                            "clinical_backup_certified","human_approved","import_permitted"):
                    self.assertFalse(getattr(result,key))
                digest,counts=_logical_fingerprint(destination)
                self.assertEqual(counts,(101,200,1)) # 1 preexisting fake patient
                self.assertEqual(len(digest),64)
            finally:
                engine.dispose()

    def test_02_dryrun_zero_imported_and_target_unchanged(self):
        with self._env() as (source,stage,root):
            report,target,draft=_inspect_and_map(source,stage)
            engine,md,dbpath=_lab_target(root)
            try:
                before=_logical_fingerprint(dbpath)
                result=_import_to_temporary_target(
                    source=source,report=report,target=target,draft=draft,
                    engine=engine,md=md,dry_run=True
                )
                self.assertEqual(result.outcome,"DRY_RUN_ROLLBACK_ZERO_IMPORTED")
                self.assertEqual(_logical_fingerprint(dbpath),before)
                self.assertEqual(before[1],(1,0,0))
            finally: engine.dispose()

    def test_03_same_source_same_batch_is_idempotent_noop(self):
        with self._env() as (source,stage,root):
            report,target,draft=_inspect_and_map(source,stage)
            engine,md,p=_lab_target(root)
            try:
                _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md)
                before=_logical_fingerprint(p)
                result=_import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md)
                self.assertEqual(result.outcome,"EXACT_SYNTHETIC_REPLAY_NOOP")
                self.assertEqual(_logical_fingerprint(p),before)
            finally: engine.dispose()

    def test_04_second_batch_without_review_does_not_duplicate(self):
        with self._env() as (source,stage,root):
            report,target,draft=_inspect_and_map(source,stage)
            engine,md,p=_lab_target(root)
            try:
                _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md)
                before=_logical_fingerprint(p)
                with self.assertRaisesRegex(SyntheticE2ERefused,"CROSS_BATCH_RECONCILIATION_REQUIRED"):
                    _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md,batch_id="SYNTH-E2E-BATCH-002")
                self.assertEqual(_logical_fingerprint(p),before)
            finally: engine.dispose()

    def test_05_failure_after_73_patients_is_atomic(self):
        with self._env() as (source,stage,root):
            report,target,draft=_inspect_and_map(source,stage)
            engine,md,p=_lab_target(root)
            try:
                before=_logical_fingerprint(p)
                with self.assertRaisesRegex(SyntheticE2ERefused,"INJECTED_ATOMIC_FAILURE"):
                    _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md,force_error_after=73)
                self.assertEqual(_logical_fingerprint(p),before)
                self.assertEqual(before[1],(1,0,0))
            finally: engine.dispose()

    def test_06_backup_restore_full_synthetic_target(self):
        with self._env() as (source,stage,root):
            report,target,draft=_inspect_and_map(source,stage)
            engine,md,p=_lab_target(root)
            try:
                _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md)
            finally: engine.dispose()
            state=_synthetic_backup_and_restore(
                p,root/"synthetic_verified_backup.db",root/"synthetic_restored.db"
            )
            self.assertEqual(state[1],(101,200,1))

    def test_07_source_has_secret_columns_but_never_imports_values(self):
        with self._env() as (source,stage,root):
            report,target,draft=_inspect_and_map(source,stage)
            decisions = [c for d in draft.decisions for c in d.columns
                         if c.source_column in ("password_hash","legacy_notes")]
            self.assertTrue(decisions)
            self.assertTrue(all(c.target_column is None for c in decisions))
            engine,md,p=_lab_target(root)
            try:
                _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md)
                with closing(sqlite3.connect(p)) as c:
                    rows=c.execute("SELECT nom,prenom,email FROM patients").fetchall()
                    self.assertNotIn("FAKE_CREDENTIAL_NEVER_IMPORT",str(rows))
                    self.assertNotIn("FAKE_SENSITIVE_NOTE_NEVER_IMPORT",str(rows))
            finally: engine.dispose()

    def test_08_orphan_source_appointment_causes_zero_import(self):
        with self._env() as (source,stage,root):
            with closing(sqlite3.connect(source)) as c:
                c.execute("UPDATE legacy_appointments SET patient_ref=999999 WHERE id=50001")
                c.commit()
            report,target,draft=_inspect_and_map(source,stage)
            engine,md,p=_lab_target(root)
            try:
                before=_logical_fingerprint(p)
                with self.assertRaisesRegex(SyntheticE2ERefused,"ORPHAN_APPOINTMENT_REFUSED"):
                    _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md)
                self.assertEqual(_logical_fingerprint(p),before)
            finally: engine.dispose()

    def test_09_unreviewed_status_causes_zero_import(self):
        with self._env() as (source,stage,root):
            with closing(sqlite3.connect(source)) as c:
                c.execute("UPDATE legacy_appointments SET status='unexpected' WHERE id=50099")
                c.commit()
            report,target,draft=_inspect_and_map(source,stage)
            engine,md,p=_lab_target(root)
            try:
                before=_logical_fingerprint(p)
                with self.assertRaisesRegex(SyntheticE2ERefused,"UNREVIEWED_APPOINTMENT_STATUS"):
                    _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md)
                self.assertEqual(_logical_fingerprint(p),before)
            finally: engine.dispose()

    def test_10_changed_source_fingerprint_rejected(self):
        with self._env() as (source,stage,root):
            report,target,draft=_inspect_and_map(source,stage)
            with closing(sqlite3.connect(source)) as c:
                c.execute("UPDATE legacy_patients SET birth_date='2002-01-01' WHERE id=10001")
                c.commit()
            engine,md,p=_lab_target(root)
            try:
                with self.assertRaisesRegex(SyntheticE2ERefused,"SOURCE_FILE_CHANGED"):
                    _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md)
                self.assertEqual(_logical_fingerprint(p)[1],(1,0,0))
            finally: engine.dispose()

    def test_11_invalid_cabinet_claim_rejected(self):
        with self._env() as (source,stage,root):
            report,target,draft=_inspect_and_map(source,stage)
            engine,md,p=_lab_target(root)
            try:
                with self.assertRaisesRegex(SyntheticE2ERefused,"UNTRUSTED_CABINET_ID_REFUSED"):
                    _import_to_temporary_target(source=source,report=report,target=target,draft=draft,engine=engine,md=md,principal_owner=_OTHER)
                self.assertEqual(_logical_fingerprint(p)[1],(1,0,0))
            finally: engine.dispose()


if __name__=="__main__":
    unittest.main()
