"""LOT05.7B+ — physical temp SQLite checkpoint/replay/rollback: FAKE ONLY."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

BACKEND = Path(__file__).resolve().parents[1]
path = BACKEND / "tests" / "fixtures" / "lot05_7b_resume_recovery_lab.py"
spec = importlib.util.spec_from_file_location("_lot05b_disposable_recovery", path)
lab = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lab
spec.loader.exec_module(lab)


class RecoveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lot05b_synthetic_recovery_")
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / "SYNTHETIC_ONLY.sqlite"
        self.marker = "LOT05_7B_FAKE_ONLY"
        self.patients = [(str(i), "SYNTHETIC_ONLY_PATIENT_" + str(i)) for i in range(100)]
        self.visits = [(str(i), str(i // 2)) for i in range(200)]
        self.payments = [(str(i), str(i)) for i in range(20)]
        self.media = [(str(i), str(i)) for i in range(10)]
        self._write()

    def _write(self):
        self.source.unlink(missing_ok=True)
        with sqlite3.connect(self.source) as db:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("CREATE TABLE lot05_synthetic_marker (marker TEXT)")
            db.execute("INSERT INTO lot05_synthetic_marker VALUES (?)", (self.marker,))
            for table, fields, values in (
                ("legacy_patients", "legacy_id TEXT, first_name TEXT", self.patients),
                ("legacy_visits", "visit_id TEXT, patient_ref TEXT", self.visits),
                ("legacy_payments", "payment_id TEXT, visit_ref TEXT", self.payments),
                ("legacy_media", "media_id TEXT, patient_ref TEXT", self.media),
            ):
                db.execute("CREATE TABLE " + table + " (" + fields + ")")
                db.executemany("INSERT INTO " + table + " VALUES (?,?)", values)
            db.commit()

    def deny(self, code):
        with self.assertRaisesRegex(lab.LabRefused, code):
            lab.rehearse_disposable_batches(self.source)

    def test_01_100x200_plus_finance_media_batch_recovery(self):
        result = lab.rehearse_disposable_batches(self.source)
        self.assertEqual((
            result.source_patients, result.source_appointments,
            result.source_payments, result.source_media_metadata,
        ), (100, 200, 20, 10))
        self.assertEqual(result.written_rows, 330)
        self.assertEqual(result.idempotent_replay_rows, 330)
        self.assertTrue(result.recovered_after_checkpoint)
        self.assertTrue(result.rollback_restored_exact_baseline)
        self.assertTrue(result.source_unchanged)
        self.assertFalse(result.clinical_target_touched)
        self.assertFalse(result.clinical_import_permitted)
        self.assertFalse(result.target_backup_certified)
        self.assertFalse(result.genuine_tenant_verified)

    def test_02_uninterrupted_path_is_deterministic(self):
        result = lab.rehearse_disposable_batches(self.source, simulate_interruption=False)
        self.assertFalse(result.recovered_after_checkpoint)
        self.assertEqual(result.idempotent_replay_rows, 330)
        self.assertTrue(result.rollback_restored_exact_baseline)

    def test_03_duplicate_patient_key_denied(self):
        self.patients[1] = (self.patients[0][0], self.patients[1][1])
        self._write()
        self.deny("DUPLICATE_SOURCE_ID")

    def test_04_orphan_appointment_denied(self):
        self.visits[0] = (self.visits[0][0], "MISSING_PATIENT")
        self._write()
        self.deny("ORPHAN_APPOINTMENT")

    def test_05_orphan_payment_denied(self):
        self.payments[0] = (self.payments[0][0], "MISSING_APPOINTMENT")
        self._write()
        self.deny("ORPHAN_PAYMENT")

    def test_06_orphan_media_denied(self):
        self.media[0] = (self.media[0][0], "MISSING_PATIENT")
        self._write()
        self.deny("ORPHAN_MEDIA")

    def test_07_actual_patient_name_never_accepted(self):
        self.patients[0] = ("0", "A REALISTIC NAME")
        self._write()
        self.deny("REAL_PATIENT_VALUES_FORBIDDEN")

    def test_08_fake_data_without_official_marker_denied(self):
        self.marker = "ANYONE_CAN_SET_THIS"
        self._write()
        self.deny("SYNTHETIC_MARKER_REQUIRED")

    def test_09_source_hash_remains_constant(self):
        before = lab._file_digest(self.source)
        result = lab.rehearse_disposable_batches(self.source)
        self.assertTrue(result.source_unchanged)
        self.assertEqual(before, lab._file_digest(self.source))

    def test_10_wal_state_even_without_sidecars_denied(self):
        with sqlite3.connect(self.source) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.commit()
        self.deny("COLD_SYNTHETIC_SOURCE_REQUIRED")

    def test_11_recovery_helper_has_no_target_path_or_db_input(self):
        import inspect
        params = inspect.signature(lab.rehearse_disposable_batches).parameters
        self.assertEqual(set(params), {"source_path", "simulate_interruption"})
        self.assertFalse(hasattr(lab, "import_to_cabinet"))

    def test_12_zero_or_malformed_source_denied(self):
        self.source.write_bytes(b"NOT A DB")
        self.deny("COLD_SYNTHETIC_SOURCE_REQUIRED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
