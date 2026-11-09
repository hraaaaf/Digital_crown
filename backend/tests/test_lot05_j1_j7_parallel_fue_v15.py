"""LOT05 J1-J7: seven independent, parallel fake-only integration oracles.

NO patient inputs, runtime router, real source files, production imports, or
clinic DB. Every test creates its own disposable synthetic SQLite + fake media.
Existing 05.1 inspector and 05.2 mapping are exercised, not reimplemented.
J4-J7 use a TEST-ONLY scratch schema, never the clinical destination.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import replace
import hashlib
import importlib.util
import re
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


_MARKER = "DC_LOT05_SEVEN_J_FAKE_ONLY_V1"
_TENANT = "FAKE_TENANT_001"
_BACKEND = Path(__file__).resolve().parents[1]


def _module(alias: str, name: str):
    spec = importlib.util.spec_from_file_location(alias, _BACKEND / "services" / name)
    if not spec or not spec.loader:
        raise RuntimeError("LAB_DEPENDENCY_MISSING")
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


inspector = _module("dc05_j7_inspector", "legacy_sql_inspector_v15.py")
mapping = _module("dc05_j7_mapping", "legacy_sql_mapping_v15.py")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LabRejected(ValueError):
    """Only stable non-patient error codes; never source values."""


class Lot05SevenJalons(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dc05_seven_j_fake_only_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / "staged"
        self.stage.mkdir()
        self.assets = self.root / "fake_assets"
        self.assets.mkdir()
        self.source = self.stage / "fake_source.db"
        self._build_source()
        self.seal = _digest(self.source)

    def _build_source(self):
        with closing(sqlite3.connect(self.source)) as db:
            db.executescript("""
                PRAGMA journal_mode=DELETE;
                CREATE TABLE fake_only_guard (marker TEXT NOT NULL);
                CREATE TABLE legacy_patients (
                    legacy_id TEXT PRIMARY KEY, given_name TEXT NOT NULL,
                    family_name TEXT NOT NULL, source_tenant TEXT NOT NULL);
                CREATE TABLE legacy_practitioners (
                    legacy_id TEXT PRIMARY KEY, label TEXT NOT NULL);
                CREATE TABLE legacy_appointments (
                    legacy_id TEXT PRIMARY KEY, patient_ref TEXT NOT NULL,
                    practitioner_ref TEXT NOT NULL, status TEXT NOT NULL);
                CREATE TABLE legacy_treatments (
                    legacy_id TEXT PRIMARY KEY, patient_ref TEXT NOT NULL,
                    appointment_ref TEXT NOT NULL, code TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL);
                CREATE TABLE legacy_payments (
                    legacy_id TEXT PRIMARY KEY, patient_ref TEXT NOT NULL,
                    treatment_ref TEXT NOT NULL, amount_cents INTEGER NOT NULL);
                CREATE TABLE legacy_documents (
                    legacy_id TEXT PRIMARY KEY, patient_ref TEXT NOT NULL,
                    file_name TEXT NOT NULL, expected_sha256 TEXT NOT NULL);
                CREATE TABLE legacy_media (
                    legacy_id TEXT PRIMARY KEY, patient_ref TEXT NOT NULL,
                    file_name TEXT NOT NULL, expected_sha256 TEXT NOT NULL);
            """)
            db.execute("INSERT INTO fake_only_guard VALUES (?)", (_MARKER,))
            db.executemany("INSERT INTO legacy_patients VALUES (?,?,?,?)", [
                (f"FP{i:03}", f"FAKE_GIVEN_{i:03}", f"FAKE_FAMILY_{i:03}", _TENANT)
                for i in range(1, 101)
            ])
            db.executemany("INSERT INTO legacy_practitioners VALUES (?,?)", [
                ("FD001", "FAKE_DENTIST_001"), ("FD002", "FAKE_DENTIST_002")
            ])
            db.executemany("INSERT INTO legacy_appointments VALUES (?,?,?,?)", [
                (f"FA{i:03}", f"FP{((i-1)//2)+1:03}",
                 f"FD{((i-1)%2)+1:03}", "FUTURE")
                for i in range(1, 201)
            ])
            db.executemany("INSERT INTO legacy_treatments VALUES (?,?,?,?,?)", [
                (f"FT{i:03}", f"FP{((i-1)//2)+1:03}", f"FA{i:03}", "FAKE_ACT", 10000)
                for i in range(1, 201)
            ])
            db.executemany("INSERT INTO legacy_payments VALUES (?,?,?,?)", [
                (f"FM{i:03}", f"FP{((i-1)//2)+1:03}", f"FT{i:03}", 5000)
                for i in range(1, 201)
            ])
            for category in ("DOCUMENT", "IMAGE"):
                table = "legacy_documents" if category == "DOCUMENT" else "legacy_media"
                for i in range(1, 21):
                    name = f"FAKE_{category}_{i:03}.bin"
                    payload = f"DC_LOT05_FAKE_ONLY_{category}_{i:03}".encode("ascii")
                    (self.assets / name).write_bytes(payload)
                    db.execute(f"INSERT INTO {table} VALUES (?,?,?,?)",
                               (f"{category[:2]}{i:03}", f"FP{i:03}", name,
                                hashlib.sha256(payload).hexdigest()))
            db.commit()

    def _sealed_readonly(self):
        if _digest(self.source) != self.seal:
            raise LabRejected("SOURCE_SHA_CHANGED")
        uri = self.source.as_uri() + "?mode=ro"
        db = sqlite3.connect(uri, uri=True)
        db.execute("PRAGMA query_only=ON")
        marker = db.execute("SELECT marker FROM fake_only_guard").fetchall()
        if marker != [(_MARKER,)]:
            db.close()
            raise LabRejected("SYNTHETIC_ORIGIN_REQUIRED")
        return db

    def _inspection(self):
        report = inspector.inspect_staged_copy(
            self.source, self.stage, dialect="sqlite", attested_offline_copy=True
        )
        if report.sha256 != self.seal or report.import_permitted:
            raise LabRejected("SOURCE_ATTESTATION_FAILED")
        return report

    def _mapping(self):
        report = self._inspection()
        target = mapping.TargetSnapshot(
            schema_revision="LOT05_TEST_ONLY_SCRATCH_V1",
            tables=tuple(
                mapping.TargetTable(table.source_name,
                    tuple(c.name for c in table.columns))
                for table in report.tables
                if table.source_name != "fake_only_guard"
            ),
        )
        proposal = mapping.propose_mapping(report, target)
        decisions = tuple(
            mapping.TableDecision(
                source_table=table.source_name,
                target_table=None if table.source_name == "fake_only_guard" else table.source_name,
                columns=tuple(
                    mapping.ColumnDecision(c.name,
                        None if table.source_name == "fake_only_guard" else c.name)
                    for c in table.columns
                ),
            ) for table in report.tables
        )
        draft = mapping.build_mapping_draft(
            report, target, decisions,
            source_software="DC_FAKE_FIXTURE_ONLY", source_version="1", profile_version=1,
        )
        return report, target, proposal, draft

    def _checked_media(self, name: str, sha256: str):
        if not isinstance(name, str) or not re.fullmatch(
                r"FAKE_(?:DOCUMENT|IMAGE)_[0-9]{3}\.bin", name):
            raise LabRejected("MEDIA_PATH_UNSAFE")
        candidate = self.assets / name
        if candidate.is_symlink() or not candidate.is_file():
            raise LabRejected("MEDIA_NOT_REGULAR")
        if candidate.resolve().parent != self.assets.resolve():
            raise LabRejected("MEDIA_ESCAPED_FAKE_VAULT")
        if candidate.stat().st_nlink != 1:
            raise LabRejected("MEDIA_HARDLINK_FORBIDDEN")
        if _digest(candidate) != sha256:
            raise LabRejected("MEDIA_DIGEST_MISMATCH")
        return candidate

    def _dryrun(self):
        with closing(self._sealed_readonly()) as source:
            patients = {r[0]: r for r in source.execute(
                "SELECT legacy_id,given_name,family_name,source_tenant FROM legacy_patients"
            )}
            practitioners = {r[0]: r for r in source.execute(
                "SELECT legacy_id,label FROM legacy_practitioners"
            )}
            if len(patients) != 100 or len(practitioners) != 2 or any(
                r[3] != _TENANT or not r[1].startswith("FAKE_") for r in patients.values()
            ):
                raise LabRejected("IDENTITY_SOURCE_INVALID")
            appointments = source.execute(
                "SELECT legacy_id,patient_ref,practitioner_ref,status FROM legacy_appointments"
            ).fetchall()
            treatments = source.execute(
                "SELECT legacy_id,patient_ref,appointment_ref,code,amount_cents FROM legacy_treatments"
            ).fetchall()
            payments = source.execute(
                "SELECT legacy_id,patient_ref,treatment_ref,amount_cents FROM legacy_payments"
            ).fetchall()
            if len(appointments) != 200 or len(treatments) != 200 or len(payments) != 200:
                raise LabRejected("EXPECTED_FAKE_VOLUMES_CHANGED")
            appointments_by_id = {r[0]: r for r in appointments}
            treatments_by_id = {r[0]: r for r in treatments}
            if len(appointments_by_id) != len(appointments) or len(treatments_by_id) != len(treatments):
                raise LabRejected("DUPLICATE_SOURCE_ID")
            for _, patient_id, clinician_id, status in appointments:
                if patient_id not in patients or clinician_id not in practitioners or status != "FUTURE":
                    raise LabRejected("ORPHAN_OR_UNMAPPED_APPOINTMENT")
            for _, patient_id, appt_id, code, cents in treatments:
                if patient_id not in patients or appt_id not in appointments_by_id:
                    raise LabRejected("ORPHAN_TREATMENT")
                if appointments_by_id[appt_id][1] != patient_id or code != "FAKE_ACT" or cents != 10000:
                    raise LabRejected("UNMAPPED_ACT_OR_AMOUNT")
            for _, patient_id, treatment_id, cents in payments:
                if treatment_id not in treatments_by_id or treatments_by_id[treatment_id][1] != patient_id:
                    raise LabRejected("ORPHAN_PAYMENT")
                if cents != 5000 or cents > treatments_by_id[treatment_id][4]:
                    raise LabRejected("FINANCIAL_RECONCILIATION_FAILED")
            files = []
            for table in ("legacy_documents", "legacy_media"):
                rows = source.execute(
                    f"SELECT legacy_id,patient_ref,file_name,expected_sha256 FROM {table}"
                ).fetchall()
                if len(rows) != 20:
                    raise LabRejected("MEDIA_MANIFEST_COUNT_CHANGED")
                for legacy_id, patient_id, name, digest in rows:
                    if patient_id not in patients:
                        raise LabRejected("ORPHAN_MEDIA")
                    self._checked_media(name, digest)
                    files.append((legacy_id, name, digest))
        return {
            "patients": 100, "practitioners": 2, "appointments": 200,
            "treatments": 200, "payments": 200, "files": len(files),
            "charge_cents": 2000000, "paid_cents": 1000000,
            "source_sha256": self.seal, "source_rows_modified": 0,
            "target_rows_written": 0, "import_permitted": False,
            "full_schema_certified": False, "human_mapping_approved": False,
            "clinical_target_verified": False,
        }

    def _target(self):
        target = self.root / "scratch_target.db"
        db = sqlite3.connect(target)
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("""
            CREATE TABLE fake_patients (
                tenant TEXT, legacy_id TEXT, given_name TEXT, PRIMARY KEY(tenant,legacy_id));
            CREATE TABLE fake_practitioners (
                tenant TEXT, legacy_id TEXT, label TEXT, PRIMARY KEY(tenant,legacy_id));
            CREATE TABLE fake_appointments (
                tenant TEXT, legacy_id TEXT, patient_ref TEXT, practitioner_ref TEXT,
                PRIMARY KEY(tenant,legacy_id),
                FOREIGN KEY(tenant,patient_ref) REFERENCES fake_patients(tenant,legacy_id),
                FOREIGN KEY(tenant,practitioner_ref) REFERENCES fake_practitioners(tenant,legacy_id));
            CREATE TABLE fake_treatments (
                tenant TEXT, legacy_id TEXT, patient_ref TEXT, appointment_ref TEXT, amount_cents INTEGER,
                PRIMARY KEY(tenant,legacy_id),
                FOREIGN KEY(tenant,patient_ref) REFERENCES fake_patients(tenant,legacy_id),
                FOREIGN KEY(tenant,appointment_ref) REFERENCES fake_appointments(tenant,legacy_id));
            CREATE TABLE fake_payments (
                tenant TEXT, legacy_id TEXT, treatment_ref TEXT, amount_cents INTEGER,
                PRIMARY KEY(tenant,legacy_id),
                FOREIGN KEY(tenant,treatment_ref) REFERENCES fake_treatments(tenant,legacy_id));
        """)
        return db

    def _identities(self, target):
        with closing(self._sealed_readonly()) as source:
            target.executemany("INSERT INTO fake_patients VALUES (?,?,?)", [
                (_TENANT, pid, given) for pid, given in source.execute(
                    "SELECT legacy_id,given_name FROM legacy_patients")
            ])
            target.executemany("INSERT INTO fake_practitioners VALUES (?,?,?)", [
                (_TENANT, pid, label) for pid, label in source.execute(
                    "SELECT legacy_id,label FROM legacy_practitioners")
            ])

    def _clinical(self, target):
        with closing(self._sealed_readonly()) as source:
            target.executemany("INSERT INTO fake_appointments VALUES (?,?,?,?)", [
                (_TENANT, aid, pat, practitioner) for aid, pat, practitioner in source.execute(
                    "SELECT legacy_id,patient_ref,practitioner_ref FROM legacy_appointments")
            ])
            target.executemany("INSERT INTO fake_treatments VALUES (?,?,?,?,?)", [
                (_TENANT, tid, pat, appt, cents) for tid, pat, appt, cents in source.execute(
                    "SELECT legacy_id,patient_ref,appointment_ref,amount_cents FROM legacy_treatments")
            ])
            target.executemany("INSERT INTO fake_payments VALUES (?,?,?,?)", [
                (_TENANT, pid, tr, cents) for pid, tr, cents in source.execute(
                    "SELECT legacy_id,treatment_ref,amount_cents FROM legacy_payments")
            ])

    def _copy_verified_assets(self, destination: Path):
        destination.mkdir(exist_ok=True)
        with closing(self._sealed_readonly()) as source:
            for table in ("legacy_documents", "legacy_media"):
                for name, digest in source.execute(f"SELECT file_name,expected_sha256 FROM {table}"):
                    original = self._checked_media(name, digest)
                    copy = destination / name
                    if copy.exists():
                        raise LabRejected("ASSET_DUPLICATE")
                    shutil.copyfile(original, copy)
                    if _digest(copy) != digest:
                        raise LabRejected("ASSET_COPY_FAILED")
        return len(list(destination.iterdir()))

    def test_j1_inspector(self):
        before = _digest(self.source)
        report = self._inspection()
        self.assertEqual(len(report.tables), 8)
        self.assertEqual(report.source_format, "sqlite-copy")
        self.assertEqual(report.row_counts, None)
        self.assertIs(report.import_permitted, False)
        self.assertEqual(before, _digest(self.source))
        with self.assertRaises(inspector.UnsafeSource):
            inspector.inspect_staged_copy(self.source, self.root / "different", dialect="sqlite",
                                          attested_offline_copy=True)

    def test_j2_mapping(self):
        report, target, proposal, draft = self._mapping()
        self.assertIs(proposal.mapping_approved, False)
        self.assertIs(proposal.import_permitted, False)
        self.assertIs(draft.admin_approved, False)
        self.assertIs(draft.import_permitted, False)
        self.assertEqual(len(draft.decisions), len(report.tables))
        self.assertTrue(mapping.revalidate_mapping_draft(draft, report, target).exact_source_and_target)
        with self.assertRaises(mapping.MappingRejected):
            mapping.revalidate_mapping_draft(replace(draft, admin_approved=True), report, target)

    def test_j3_dryrun(self):
        report = self._dryrun()
        self.assertEqual((report["patients"], report["appointments"], report["files"]), (100, 200, 40))
        self.assertEqual((report["charge_cents"], report["paid_cents"]), (2000000, 1000000))
        self.assertEqual(report["target_rows_written"], 0)
        with closing(sqlite3.connect(self.source)) as db:
            db.execute("UPDATE legacy_appointments SET patient_ref='FAKE_MISSING' WHERE legacy_id='FA001'")
            db.commit()
        self.seal = _digest(self.source)  # adversarial synthetic change, still fake
        with self.assertRaisesRegex(LabRejected, "ORPHAN_OR_UNMAPPED_APPOINTMENT"):
            self._dryrun()

    def test_j4_identities(self):
        self._dryrun()  # no target mutations before all source checks
        with closing(self._target()) as target:
            with target:
                self._identities(target)
            self.assertEqual(target.execute("SELECT COUNT(*) FROM fake_patients").fetchone()[0], 100)
            self.assertEqual(target.execute("SELECT COUNT(*) FROM fake_practitioners").fetchone()[0], 2)
            with self.assertRaises(sqlite3.IntegrityError):
                with target:
                    target.execute("INSERT INTO fake_patients VALUES (?,?,?)",
                                   (_TENANT, "FP001", "FAKE_COLLISION"))
            self.assertEqual(target.execute(
                "SELECT given_name FROM fake_patients WHERE tenant=? AND legacy_id=?",
                (_TENANT, "FP001")).fetchone()[0], "FAKE_GIVEN_001")

    def test_j5_agenda_acts_finances(self):
        self._dryrun()
        with closing(self._target()) as target:
            with target:
                self._identities(target)
                self._clinical(target)
            self.assertEqual(target.execute("SELECT COUNT(*) FROM fake_appointments").fetchone()[0], 200)
            self.assertEqual(target.execute("SELECT SUM(amount_cents) FROM fake_treatments").fetchone()[0], 2000000)
            self.assertEqual(target.execute("SELECT SUM(amount_cents) FROM fake_payments").fetchone()[0], 1000000)
            with self.assertRaises(sqlite3.IntegrityError):
                with target:
                    target.execute("INSERT INTO fake_payments VALUES (?,?,?,?)",
                                   (_TENANT, "FAKE_BAD", "FT_MISSING", 5000))
            self.assertEqual(target.execute("SELECT COUNT(*) FROM fake_payments").fetchone()[0], 200)
        with closing(sqlite3.connect(self.source)) as db:
            db.execute("UPDATE legacy_payments SET amount_cents=20000 WHERE legacy_id='FM001'")
            db.commit()
        self.seal = _digest(self.source)
        with self.assertRaisesRegex(LabRejected, "FINANCIAL_RECONCILIATION_FAILED"):
            self._dryrun()

    def test_j6_documents_and_media(self):
        self._dryrun()
        destination = self.root / "scratch_vault"
        self.assertEqual(self._copy_verified_assets(destination), 40)
        self.assertEqual(len(list(destination.glob("FAKE_DOCUMENT_*"))), 20)
        self.assertEqual(len(list(destination.glob("FAKE_IMAGE_*"))), 20)
        with self.assertRaisesRegex(LabRejected, "MEDIA_PATH_UNSAFE"):
            self._checked_media("../FAKE_DOCUMENT_001.bin", "0" * 64)
        (self.assets / "FAKE_IMAGE_001.bin").write_bytes(b"FAKE_CORRUPTED_ASSET")
        with self.assertRaisesRegex(LabRejected, "MEDIA_DIGEST_MISMATCH"):
            self._dryrun()

    def test_j7_backup_rollback_recovery(self):
        self._inspection()
        self._mapping()
        report = self._dryrun()
        self.assertIs(report["import_permitted"], False)
        target = self._target()
        target_path = self.root / "scratch_target.db"
        vault = self.root / "scratch_vault"
        vault.mkdir()
        sentinel = vault / "FAKE_PREEXISTING.bin"
        sentinel.write_bytes(b"FAKE_PREEXISTING_VAULT_ASSET")
        backup_path = self.root / "snapshot_before_fake_run.db"
        with closing(sqlite3.connect(backup_path)) as copy:
            target.backup(copy)
        snap_media = self.root / "snapshot_media"
        shutil.copytree(vault, snap_media)
        baseline_hash = _digest(backup_path)
        baseline_asset = _digest(sentinel)
        try:
            with self.assertRaisesRegex(RuntimeError, "SIMULATED_CRASH"):
                with target:
                    self._identities(target)
                    raise RuntimeError("SIMULATED_CRASH")
            self.assertEqual(target.execute("SELECT COUNT(*) FROM fake_patients").fetchone()[0], 0)
            with target:
                self._identities(target)
                self._clinical(target)
            self.assertEqual(self._copy_verified_assets(vault), 41)
            self.assertEqual(target.execute("SELECT COUNT(*) FROM fake_patients").fetchone()[0], 100)
            self.assertEqual(target.execute("SELECT COUNT(*) FROM fake_payments").fetchone()[0], 200)
            self.assertEqual(target.execute("SELECT SUM(amount_cents) FROM fake_payments").fetchone()[0], 1000000)
        finally:
            target.close()
        with closing(sqlite3.connect(backup_path)) as source_copy:
            with closing(sqlite3.connect(target_path)) as restored:
                source_copy.backup(restored)
        shutil.rmtree(vault)
        shutil.copytree(snap_media, vault)
        with closing(sqlite3.connect(target_path)) as restored:
            self.assertEqual(restored.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(restored.execute("SELECT COUNT(*) FROM fake_patients").fetchone()[0], 0)
            self.assertEqual(restored.execute("SELECT COUNT(*) FROM fake_payments").fetchone()[0], 0)
        self.assertEqual(_digest(backup_path), baseline_hash)
        self.assertEqual(_digest(vault / "FAKE_PREEXISTING.bin"), baseline_asset)
        self.assertEqual(sorted(p.name for p in vault.iterdir()), ["FAKE_PREEXISTING.bin"])
        self.assertEqual(_digest(self.source), self.seal)
        self.assertIs(report["clinical_target_verified"], False)


if __name__ == "__main__":
    unittest.main()
