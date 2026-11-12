"""LOT05/2E FUE-0: synthetic source vs disposable target identity collisions.

No real clinic target, importer, API, human identity approval or auto-merging.
A same-name/date candidate MUST NEVER establish an actual person match.
All fixture input values are synthetically generated and validated as FAKE.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
import csv
import importlib.util
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import types
import unittest

BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_dc_lot05_2e_fake_target_only"
if PACKAGE not in sys.modules:
    pkg = types.ModuleType(PACKAGE)
    pkg.__path__ = [str(BACKEND / "services")]
    sys.modules[PACKAGE] = pkg


def load(name):
    full = PACKAGE + "." + name
    spec = importlib.util.spec_from_file_location(
        full, BACKEND / "services" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[full] = module
    spec.loader.exec_module(module)
    return module


inspect = load("legacy_sql_inspector_v15")
mapping = load("legacy_sql_mapping_v15")
load("legacy_migration_csv_preview_v15")
lab = load("legacy_migration_csv_mapping_lab_v15")

HEADERS = ("ancien_id", "prenom", "nom", "naissance", "extra")
TARGET_FIELDS = ("legacy_id", "given_name", "family_name", "birth_date")
_FAKE_ID = re.compile(r"[ST][0-9]{4}\Z")
_FAKE_GIVEN = re.compile(r"FAKE_GIVEN_[0-9]{4}\Z")
_FAKE_FAMILY = re.compile(r"FAKE_FAMILY_[0-9]{4}\Z")


class SyntheticTargetRefused(ValueError):
    """Fixed error codes only; no values, names, rows, identifiers or paths."""


@dataclass(frozen=True)
class FakeTargetCollisionReport:
    source_rows: int
    target_rows: int
    source_id_links: int
    demographic_candidate_links: int
    affected_source_rows: int
    incomplete_birth_dates: int
    warnings: tuple[str, ...] = (
        "FAKE_LAB_ONLY_NOT_A_PATIENT_IDENTITY_DECISION",
        "DEMOGRAPHIC_SIMILARITY_IS_NOT_PROOF_OF_SAME_PERSON",
        "NO_TENANT_OR_REAL_TARGET_VERIFIED",
    )
    target_identity_verified: bool = False
    target_tenant_verified: bool = False
    source_provenance_verified: bool = False
    human_approved: bool = False
    target_backup_restore_verified: bool = False
    target_rows_written: int = 0
    import_permitted: bool = False

    def to_public_dict(self):
        return asdict(self)


def _fake_row(row):
    if (len(row) != 4 or not _FAKE_ID.fullmatch(row[0])
            or not _FAKE_GIVEN.fullmatch(row[1])
            or not _FAKE_FAMILY.fullmatch(row[2])
            or row[3] not in ("", "2000-02-29", "2001-01-01")):
        raise SyntheticTargetRefused("NON_FAKE_IDENTITY_FIXTURE_FORBIDDEN")


def inspect_fake_target_collisions(
    source, target, stage, *, lab_only_synthetic_fixture=False,
    attested_offline_copy=False,
):
    """Aggregate-only comparison of two independently created disposable fixtures.

    Reuses real CSV source gates and mapping validation; target has EXACT fake
    SQLite schema, opens query-only immutable, and is never modified by scan.
    """
    if lab_only_synthetic_fixture is not True:
        raise SyntheticTargetRefused("LAB_SYNTHETIC_ONLY")
    if attested_offline_copy is not True:
        raise SyntheticTargetRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
    if not all(type(p) is Path for p in (source, target, stage)):
        raise SyntheticTargetRefused("STAGED_PATH_REQUIRED")
    if source.suffix != ".csv" or target.suffix != ".sqlite":
        raise SyntheticTargetRefused("FAKE_FIXTURE_EXTENSION_REQUIRED")
    try:
        src, _ = inspect._copy_path(source, stage, True)
        dst, _ = inspect._copy_path(target, stage, True)
        if any(Path(str(dst) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
            raise SyntheticTargetRefused("ACTIVE_SQLITE_SIDECAR_FORBIDDEN")
        before_src, before_dst = inspect._hash(src), inspect._hash(dst)
        before_stats = (
            tuple((p.stat().st_dev, p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns))
            for p in (src, dst)
        )
        choices = tuple(mapping.ColumnDecision(h, {
            "ancien_id": "legacy_id", "prenom": "given_name",
            "nom": "family_name", "naissance": "birth_date",
        }.get(h)) for h in HEADERS)
        draft = lab.draft_synthetic_patient_mapping(
            src, stage, decisions=choices,
            source_software="FAKE_VENDOR_ONLY_NOT_ATTESTED",
            source_version="FAKE_V1", lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )
        sim = lab.simulate_synthetic_patient_csv(
            src, stage, draft, lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )
        if sim.critical_count or not sim.accepted_candidate_rows or sim.import_permitted:
            raise SyntheticTargetRefused("UNSAFE_SOURCE_CANDIDATES")
        with src.open("r", encoding="utf-8", newline="") as stream:
            csv_rows = csv.reader(stream, dialect="excel", strict=True)
            if tuple(next(csv_rows, ())) != HEADERS:
                raise SyntheticTargetRefused("UNEXPECTED_FAKE_SOURCE_SCHEMA")
            raw = [tuple(r[:4]) for r in csv_rows]
        if len(raw) != sim.accepted_candidate_rows or len(raw) > 1000:
            raise SyntheticTargetRefused("SOURCE_ROW_RECONCILIATION_FAILED")
        for row in raw:
            _fake_row(row)

        with closing(sqlite3.connect(
            dst.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=1
        )) as conn:
            conn.execute("PRAGMA query_only=ON")
            conn.execute("PRAGMA trusted_schema=OFF")
            if conn.execute("PRAGMA query_only").fetchone() != (1,):
                raise SyntheticTargetRefused("TARGET_NOT_READ_ONLY")
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
                " AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            if tables != [("patients",)]:
                raise SyntheticTargetRefused("UNEXPECTED_FAKE_TARGET_SCHEMA")
            columns = conn.execute("PRAGMA table_info(patients)").fetchall()
            if tuple(c[1] for c in columns) != TARGET_FIELDS:
                raise SyntheticTargetRefused("UNEXPECTED_FAKE_TARGET_SCHEMA")
            targets = [tuple(r) for r in conn.execute(
                "SELECT legacy_id, given_name, family_name, birth_date FROM patients"
            ).fetchmany(1001)]
            if len(targets) > 1000:
                raise SyntheticTargetRefused("TARGET_ROW_LIMIT_EXCEEDED")
        for row in targets:
            _fake_row(row)
        id_links, demographic_links, affected, missing = 0, 0, 0, 0
        for row in raw:
            unknown_dob = not row[3]
            missing += int(unknown_dob)
            id_matches = sum(t[0] == row[0] for t in targets)
            demo_matches = sum(
                bool(row[3]) and bool(t[3])
                and t[1:] == row[1:] for t in targets
            )
            id_links += id_matches
            demographic_links += demo_matches
            affected += int(bool(id_matches or demo_matches))
        after_stats = (
            tuple((p.stat().st_dev, p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns))
            for p in (src, dst)
        )
        if (list(before_stats) != list(after_stats)
                or before_src != inspect._hash(src)
                or before_dst != inspect._hash(dst)):
            raise SyntheticTargetRefused("FAKE_FIXTURE_CHANGED_DURING_SCAN")
        return FakeTargetCollisionReport(
            source_rows=len(raw), target_rows=len(targets),
            source_id_links=id_links, demographic_candidate_links=demographic_links,
            affected_source_rows=affected, incomplete_birth_dates=missing,
        )
    except SyntheticTargetRefused:
        raise
    except (inspect.UnsafeSource, lab.SyntheticCsvMappingRefused):
        raise SyntheticTargetRefused("UNSAFE_OR_UNSUPPORTED_FAKE_FIXTURE") from None
    except (OSError, sqlite3.DatabaseError, UnicodeError, csv.Error, ValueError):
        raise SyntheticTargetRefused("INVALID_FAKE_FIXTURE") from None


class FakeTargetIdentityFUE(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="LOT05_2E_FAKE_TARGET_")
        self.addCleanup(tmp.cleanup)
        self.stage = Path(tmp.name) / "stage"
        self.stage.mkdir()
        self.source = self.stage / "FAKE_source.csv"
        self.target = self.stage / "FAKE_target.sqlite"
        self.rows = [
            (f"S{i:04d}", f"FAKE_GIVEN_{i:04d}",
             f"FAKE_FAMILY_{i:04d}", "2000-02-29", "FAKE_UNUSED")
            for i in range(100)
        ]
        self.targets = [
            (f"T{i:04d}", f"FAKE_GIVEN_{5000+i:04d}",
             f"FAKE_FAMILY_{5000+i:04d}", "2000-02-29")
            for i in range(60)
        ]
        self.write()

    def write(self, extra_col=False):
        with self.source.open("w", encoding="utf-8", newline="") as fp:
            w = csv.writer(fp)
            w.writerow(HEADERS)
            w.writerows(self.rows)
        self.target.unlink(missing_ok=True)
        with closing(sqlite3.connect(self.target)) as conn:
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("CREATE TABLE patients (legacy_id TEXT, given_name TEXT,"
                         " family_name TEXT, birth_date TEXT"
                         + (", stray TEXT" if extra_col else "") + ")")
            if not extra_col:
                conn.executemany("INSERT INTO patients VALUES (?, ?, ?, ?)", self.targets)
            conn.commit()

    def assess(self, **kwargs):
        return inspect_fake_target_collisions(
            self.source, self.target, self.stage,
            lab_only_synthetic_fixture=True,
            attested_offline_copy=True, **kwargs,
        )

    def refused(self, expected, fn):
        with self.assertRaises(SyntheticTargetRefused) as cm:
            fn()
        self.assertEqual(str(cm.exception), expected)
        self.assertNotIn(str(self.stage), str(cm.exception))

    def test_01_disjoint_fixture_zero_candidate_links_no_authority(self):
        src_before, dst_before = self.source.read_bytes(), self.target.read_bytes()
        r = self.assess()
        self.assertEqual((r.source_rows, r.target_rows), (100, 60))
        self.assertEqual((r.source_id_links, r.demographic_candidate_links,
                          r.affected_source_rows), (0, 0, 0))
        self.assertFalse(r.import_permitted)
        self.assertFalse(r.human_approved)
        self.assertFalse(r.target_tenant_verified)
        self.assertFalse(r.target_backup_restore_verified)
        self.assertEqual(r.target_rows_written, 0)
        self.assertEqual(src_before, self.source.read_bytes())
        self.assertEqual(dst_before, self.target.read_bytes())

    def test_02_id_overlap_with_different_demographics_is_flagged(self):
        self.targets[0] = ("S0001", *self.targets[0][1:])
        self.write()
        r = self.assess()
        self.assertEqual((r.source_id_links, r.demographic_candidate_links,
                          r.affected_source_rows), (1, 0, 1))

    def test_03_exact_demographic_similarity_only_candidate_not_identity(self):
        self.targets[0] = ("T0000", *self.rows[1][1:4])
        self.write()
        r = self.assess()
        self.assertEqual((r.source_id_links, r.demographic_candidate_links,
                          r.affected_source_rows), (0, 1, 1))
        self.assertFalse(r.target_identity_verified)

    def test_04_double_collision_same_row_counted_once_affected(self):
        self.targets[0] = ("S0001", *self.rows[1][1:4])
        self.write()
        r = self.assess()
        self.assertEqual((r.source_id_links, r.demographic_candidate_links,
                          r.affected_source_rows), (1, 1, 1))

    def test_05_multiple_possible_target_matches_are_not_auto_merged(self):
        self.targets[0] = ("T0000", *self.rows[1][1:4])
        self.targets[1] = ("T0001", *self.rows[1][1:4])
        self.write()
        r = self.assess()
        self.assertEqual(r.demographic_candidate_links, 2)
        self.assertEqual(r.affected_source_rows, 1)
        self.assertFalse(r.import_permitted)

    def test_06_different_birth_date_not_matched(self):
        self.targets[0] = ("T0000", self.rows[1][1], self.rows[1][2], "2001-01-01")
        self.write()
        self.assertEqual(self.assess().demographic_candidate_links, 0)

    def test_07_missing_birth_date_is_unknown_not_invented(self):
        self.rows[1] = (*self.rows[1][:3], "", "FAKE_UNUSED")
        self.write()
        r = self.assess()
        self.assertEqual(r.incomplete_birth_dates, 1)
        self.assertEqual(r.demographic_candidate_links, 0)
        self.assertFalse(r.target_identity_verified)

    def test_08_non_fake_target_identity_rejected(self):
        self.targets[0] = ("T0000", "REAL_PERSON", "FAKE_FAMILY_5000", "2000-02-29")
        self.write()
        self.refused("NON_FAKE_IDENTITY_FIXTURE_FORBIDDEN", self.assess)

    def test_09_non_fake_source_identity_rejected(self):
        self.rows[0] = ("S0000", "REAL_PERSON", "FAKE_FAMILY_0000",
                        "2000-02-29", "FAKE_UNUSED")
        self.write()
        self.refused("NON_FAKE_IDENTITY_FIXTURE_FORBIDDEN", self.assess)

    def test_10_unexpected_target_schema_rejected(self):
        self.write(extra_col=True)
        self.refused("UNEXPECTED_FAKE_TARGET_SCHEMA", self.assess)

    def test_11_outside_staging_target_rejected(self):
        other = self.stage.parent / "FAKE_outside.sqlite"
        other.write_bytes(self.target.read_bytes())
        self.refused("UNSAFE_OR_UNSUPPORTED_FAKE_FIXTURE", lambda:
                     inspect_fake_target_collisions(
                         self.source, other, self.stage,
                         lab_only_synthetic_fixture=True,
                         attested_offline_copy=True))

    def test_12_offline_attestation_mandatory(self):
        self.refused("OFFLINE_COPY_ATTESTATION_REQUIRED", lambda:
                     inspect_fake_target_collisions(
                         self.source, self.target, self.stage,
                         lab_only_synthetic_fixture=True,
                         attested_offline_copy=False))

    def test_13_synthetic_flag_mandatory(self):
        self.refused("LAB_SYNTHETIC_ONLY", lambda:
                     inspect_fake_target_collisions(
                         self.source, self.target, self.stage,
                         lab_only_synthetic_fixture=False,
                         attested_offline_copy=True))

    def test_14_duplicate_source_id_refused_before_comparison(self):
        self.rows[1] = (self.rows[0][0], *self.rows[1][1:])
        self.write()
        self.refused("UNSAFE_SOURCE_CANDIDATES", self.assess)

    def test_15_invalid_target_file_refused(self):
        self.target.write_bytes(b"NOT_A_SQLITE_DATABASE")
        self.refused("INVALID_FAKE_FIXTURE", self.assess)

    def test_16_public_report_never_exposes_identity_values(self):
        r = self.assess()
        s = repr(r.to_public_dict())
        for forbidden in ("FAKE_GIVEN_", "FAKE_FAMILY_", "S0001", "T0001",
                          str(self.stage), "FAKE_UNUSED"):
            self.assertNotIn(forbidden, s)
        self.assertEqual(r.target_rows_written, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
