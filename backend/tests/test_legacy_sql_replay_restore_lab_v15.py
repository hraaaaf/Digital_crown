"""LOT05-C test-only SQLite full backup/restore & cross-batch replay laboratory.

Hard-coded tempdir creates synthetic SQLite db only. NOT clinic backup,
not SQLCipher/PG, not source data import or authorization.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest


class SyntheticImportRefused(ValueError):
    pass


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _open(path):
    con=sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys=ON")
    assert con.execute("PRAGMA foreign_keys").fetchone() == (1,)
    return con


def _schema(con):
    con.executescript("""
CREATE TABLE patients (
 id INTEGER PRIMARY KEY, employer_id INTEGER NOT NULL, external_id TEXT NOT NULL,
 nom TEXT NOT NULL, dob TEXT NOT NULL,
 UNIQUE(employer_id, external_id), UNIQUE(employer_id, nom, dob)
);
CREATE TABLE appointments (
 id INTEGER PRIMARY KEY, employer_id INTEGER NOT NULL, patient_id INTEGER NOT NULL,
 datetime_start TEXT NOT NULL,
 FOREIGN KEY (patient_id) REFERENCES patients(id)
);
CREATE TABLE ledger (
 batch_id TEXT PRIMARY KEY, payload_sha TEXT NOT NULL, done INTEGER NOT NULL CHECK(done=1)
);
""")
    con.commit()


def _batch(con, *, batch_id, patient, slots, tenant_id=777):
    """Test-only atomic replay/collision and schedule guard, no data export."""
    if not isinstance(batch_id, str) or not batch_id.startswith("SYNTH-BATCH-") or len(batch_id)>60:
        raise SyntheticImportRefused("INVALID_TEST_BATCH")
    if type(tenant_id) is not int or tenant_id != 777:
        raise SyntheticImportRefused("UNTRUSTED_TENANT")
    if not isinstance(patient, dict) or set(patient) != {"external_id", "nom", "dob"}:
        raise SyntheticImportRefused("INVALID_TEST_PATIENT")
    if (not patient["external_id"].startswith("SYNTH-")
            or not patient["nom"].startswith("SYNTHETIC_ONLY_")):
        raise SyntheticImportRefused("ONLY_SYNTHETIC_RECORDS")
    if not isinstance(slots, tuple) or not slots or any(
        not isinstance(s, str) or len(s) != 16 for s in slots
    ):
        raise SyntheticImportRefused("INVALID_TEST_APPOINTMENTS")
    fingerprint=_digest({"patient":patient,"slots":slots})
    row=con.execute("SELECT payload_sha FROM ledger WHERE batch_id=?", (batch_id,)).fetchone()
    if row:
        if row[0] != fingerprint:
            raise SyntheticImportRefused("REUSED_BATCH_WITH_DIFFERENT_CONTENT")
        return "EXACT_REPLAY_NOOP"
    # SQLite transaction, no partial mutation if constraint or validation fails.
    try:
        con.execute("BEGIN IMMEDIATE")
        if con.execute("SELECT 1 FROM patients WHERE employer_id=? AND external_id=?",
                       (tenant_id, patient["external_id"])).fetchone():
            raise SyntheticImportRefused("EXTERNAL_ID_ALREADY_IMPORTED_IN_ANOTHER_BATCH")
        if con.execute("SELECT 1 FROM patients WHERE employer_id=? AND nom=? AND dob=?",
                       (tenant_id, patient["nom"], patient["dob"])).fetchone():
            raise SyntheticImportRefused("POTENTIAL_CROSS_BATCH_PATIENT_DUPLICATE")
        cur=con.execute(
            "INSERT INTO patients(employer_id,external_id,nom,dob) VALUES(?,?,?,?)",
            (tenant_id,patient["external_id"],patient["nom"],patient["dob"]),
        )
        for when in slots:
            if con.execute(
                "SELECT 1 FROM appointments WHERE employer_id=? AND patient_id=? AND datetime_start=?",
                (tenant_id,cur.lastrowid,when)
            ).fetchone():
                raise SyntheticImportRefused("DUPLICATE_APPOINTMENT_IN_BATCH")
            con.execute("INSERT INTO appointments(employer_id,patient_id,datetime_start) VALUES(?,?,?)",
                        (tenant_id,cur.lastrowid,when))
        con.execute("INSERT INTO ledger(batch_id,payload_sha,done) VALUES(?,?,1)",
                    (batch_id,fingerprint))
        if con.execute("PRAGMA foreign_key_check").fetchall():
            raise SyntheticImportRefused("FOREIGN_KEY_CHECK_FAILED")
        con.commit()
    except Exception:
        con.rollback()
        raise
    return "COMMITTED_TO_SYNTHETIC_LAB_ONLY"


def _evidence(con):
    rows = {
        "patients":con.execute("SELECT employer_id,external_id,nom,dob FROM patients ORDER BY id").fetchall(),
        "appointments":con.execute("SELECT employer_id,patient_id,datetime_start FROM appointments ORDER BY id").fetchall(),
        "ledger":con.execute("SELECT batch_id,payload_sha,done FROM ledger ORDER BY batch_id").fetchall()
    }
    return (_digest(rows),*(len(rows[k]) for k in ("patients","appointments","ledger")))


def _backup_and_restore(src, destination):
    """SQLite Backup API ONLY from an isolated synthetic test connection."""
    with sqlite3.connect(destination) as backup_con:
        src.backup(backup_con)
        backup_con.execute("PRAGMA quick_check")
        assert backup_con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@contextmanager
def _lab():
    with tempfile.TemporaryDirectory(prefix="lot05c_synthetic_only_") as folder:
        root=Path(folder)
        source=root/"synthetic_source.db"
        con=_open(str(source))
        try:
            _schema(con)
            yield con,root
        finally:
            con.close()


PATIENT_A={"external_id":"SYNTH-PAT-A","nom":"SYNTHETIC_ONLY_ALICE","dob":"2001-03-04"}
PATIENT_B={"external_id":"SYNTH-PAT-B","nom":"SYNTHETIC_ONLY_BOB","dob":"1999-02-05"}
SLOT=("2026-10-14 09:30",)


class SyntheticLedgerRestoreTests(unittest.TestCase):
    def test_01_exact_replay_is_a_noop(self):
        with _lab() as (con, _):
            self.assertEqual(_batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,slots=SLOT),
                             "COMMITTED_TO_SYNTHETIC_LAB_ONLY")
            digest=_evidence(con)
            self.assertEqual(_batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,slots=SLOT),
                             "EXACT_REPLAY_NOOP")
            self.assertEqual(_evidence(con),digest)
            self.assertEqual(digest[1:],(1,1,1))

    def test_02_reused_batch_with_changed_payload_refused(self):
        with _lab() as (con,_):
            _batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,slots=SLOT)
            evidence=_evidence(con)
            with self.assertRaisesRegex(SyntheticImportRefused, "REUSED_BATCH_WITH_DIFFERENT_CONTENT"):
                _batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,
                       slots=("2026-10-14 10:30",))
            self.assertEqual(_evidence(con),evidence)

    def test_03_same_patient_in_different_batch_refused(self):
        with _lab() as (con,_):
            _batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,slots=SLOT)
            evidence=_evidence(con)
            with self.assertRaisesRegex(SyntheticImportRefused, "EXTERNAL_ID_ALREADY_IMPORTED_IN_ANOTHER_BATCH"):
                _batch(con,batch_id="SYNTH-BATCH-2",patient=PATIENT_A,slots=SLOT)
            self.assertEqual(_evidence(con),evidence)

    def test_04_likely_cross_batch_duplicate_requires_human_review(self):
        with _lab() as (con,_):
            _batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,slots=SLOT)
            altered={**PATIENT_A,"external_id":"SYNTH-NEW-ALIAS"}
            with self.assertRaisesRegex(SyntheticImportRefused, "POTENTIAL_CROSS_BATCH_PATIENT_DUPLICATE"):
                _batch(con,batch_id="SYNTH-BATCH-2",patient=altered,slots=SLOT)
            self.assertEqual(_evidence(con)[1:],(1,1,1))

    def test_05_backup_restore_replays_identical_digest_and_rows(self):
        with _lab() as (con,root):
            _batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,slots=SLOT)
            _batch(con,batch_id="SYNTH-BATCH-2",patient=PATIENT_B,slots=("2026-10-15 11:30",))
            before=_evidence(con)
            backup=root/"verified_backup.db"
            _backup_and_restore(con,str(backup))
            with _open(str(backup)) as restored:
                self.assertEqual(_evidence(restored),before)
                self.assertEqual(restored.execute("PRAGMA integrity_check").fetchone()[0],"ok")
                self.assertEqual(restored.execute("PRAGMA foreign_key_check").fetchall(),[])
            self.assertEqual(before[1:],(2,2,2))

    def test_06_restore_to_fresh_db_recovers_after_deliberate_loss(self):
        with _lab() as (con,root):
            _batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,slots=SLOT)
            baseline=_evidence(con)
            backup=root/"backup.db"
            _backup_and_restore(con,str(backup))
            # Only mutate a separate synthetic sandbox DB; never delete source.
            isolated_copy=root/"scratch_recovery.db"
            with _open(str(isolated_copy)) as dest:
                _schema(dest)
                _batch(dest,batch_id="SYNTH-BATCH-2",patient=PATIENT_B,slots=SLOT)
                self.assertNotEqual(_evidence(dest),baseline)
            with _open(str(backup)) as verified:
                _backup_and_restore(verified,str(isolated_copy))
            with _open(str(isolated_copy)) as recovered:
                self.assertEqual(_evidence(recovered),baseline)
            self.assertEqual(_evidence(con),baseline)

    def test_07_untrusted_tenant_and_non_synthetic_values_denied(self):
        with _lab() as (con,_):
            with self.assertRaisesRegex(SyntheticImportRefused, "UNTRUSTED_TENANT"):
                _batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,slots=SLOT,tenant_id=778)
            with self.assertRaisesRegex(SyntheticImportRefused, "ONLY_SYNTHETIC_RECORDS"):
                _batch(con,batch_id="SYNTH-BATCH-1",patient={**PATIENT_A,"nom":"REAL"},slots=SLOT)
            self.assertEqual(_evidence(con)[1:],(0,0,0))

    def test_08_atomic_rollback_on_same_batch_duplicate_slots(self):
        with _lab() as (con,_):
            with self.assertRaisesRegex(SyntheticImportRefused, "DUPLICATE_APPOINTMENT_IN_BATCH"):
                _batch(con,batch_id="SYNTH-BATCH-1",patient=PATIENT_A,slots=(SLOT[0],SLOT[0]))
            self.assertEqual(_evidence(con)[1:],(0,0,0))


if __name__ == "__main__":
    unittest.main()
