"""LOT06 C05B-03I — deterministic OFFLINE concurrency preflight.

Simulates 5 ACTOR ROLES as threads against isolated stdlib SQLite.
It DOES NOT invoke Digital Crown backend routes, real devices, mobile OS,
Tailnet, production database, or real clinical acknowledgements.
Use product-domain pytest and real 5-VM E2E for eventual certification.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import time

SLOT = "2030-01-02T10:00:00"
TENANT = "synthetic-cabinet"
PHOTO = b"synthetic-png-not-clinical-data"


def require_offline() -> None:
    assert os.getenv("C05B03H_NETWORK_POLICY_APPROVED", "false").lower() == "false", "NETWORK_GATE_MUST_REMAIN_FALSE"
    assert os.getenv("ENVIRONMENT", "test") == "test", "TEST_ONLY"
    assert os.getenv("DIGITALCROWN_ISOLATED_RUNTIME", "true") == "true", "ISOLATED_RUNTIME_REQUIRED"


class LocalLab:
    def __init__(self, path: Path):
        self.path = str(path)
        with self.connection() as c:
            c.executescript("""
                CREATE TABLE patients (id TEXT PRIMARY KEY, tenant TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE messages (tenant TEXT NOT NULL, patient TEXT NOT NULL, client_id TEXT NOT NULL,
                    body TEXT NOT NULL, PRIMARY KEY (tenant,patient,client_id));
                CREATE TABLE appointments (tenant TEXT NOT NULL, slot TEXT NOT NULL, patient TEXT NOT NULL,
                    PRIMARY KEY (tenant,slot));
                CREATE TABLE observations (tenant TEXT NOT NULL, patient TEXT NOT NULL, note TEXT NOT NULL);
                CREATE TABLE photo_requests (id TEXT PRIMARY KEY, tenant TEXT NOT NULL, patient TEXT NOT NULL,
                    status TEXT NOT NULL);
                CREATE TABLE photos (request_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, patient TEXT NOT NULL,
                    sha256 TEXT NOT NULL);
                INSERT INTO patients(id,tenant) VALUES('patient-a','synthetic-cabinet'),('patient-b','synthetic-cabinet');
                INSERT INTO photo_requests(id,tenant,patient,status)
                    VALUES('request-fault','synthetic-cabinet','patient-a','REQUESTED');
            """)

    def connection(self):
        c = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        c.execute("PRAGMA busy_timeout=10000")
        return c

    @staticmethod
    def authorized(c, patient):
        return c.execute("SELECT 1 FROM patients WHERE tenant=? AND id=? AND revoked=0", (TENANT, patient)).fetchone() is not None

    def send(self, patient, client_id, body):
        with self.connection() as c:
            c.execute("BEGIN IMMEDIATE")
            if not self.authorized(c, patient):
                c.rollback()
                return "DENIED"
            existing = c.execute("SELECT body FROM messages WHERE tenant=? AND patient=? AND client_id=?",
                                 (TENANT, patient, client_id)).fetchone()
            if existing:
                c.commit()
                return "IDEMPOTENT" if existing[0] == body else "CONFLICT"
            c.execute("INSERT INTO messages VALUES(?,?,?,?)", (TENANT, patient, client_id, body))
            c.commit()
            return "COMMITTED"

    def book(self, patient, barrier):
        barrier.wait(timeout=10)  # Both clients first reach the same transaction boundary.
        with self.connection() as c:
            c.execute("BEGIN IMMEDIATE")
            if not self.authorized(c, patient):
                c.rollback()
                return "DENIED"
            try:
                c.execute("INSERT INTO appointments VALUES(?,?,?)", (TENANT, SLOT, patient))
            except sqlite3.IntegrityError:
                c.rollback()
                return "SLOT_CONFLICT"
            c.commit()
            return "CONFIRMED_AFTER_COMMIT"

    def doctor(self):
        with self.connection() as c:
            c.execute("BEGIN IMMEDIATE")
            seen = c.execute("SELECT COUNT(*) FROM patients WHERE tenant=?", (TENANT,)).fetchone()[0]
            c.execute("INSERT INTO observations VALUES(?,?,?)", (TENANT, "patient-a", "synthetic visit"))
            c.execute("INSERT INTO photo_requests VALUES(?,?,?,?)", ("request-1", TENANT, "patient-a", "REQUESTED"))
            c.commit()
        return seen

    def photo(self, patient, request_id, payload, fault=False):
        with self.connection() as c:
            c.execute("BEGIN IMMEDIATE")
            if not self.authorized(c, patient):
                c.rollback()
                return "DENIED"
            req = c.execute("SELECT patient,status FROM photo_requests WHERE id=? AND tenant=?",
                            (request_id, TENANT)).fetchone()
            if not req or req[0] != patient:
                c.rollback()
                return "UNSOLICITED_OR_WRONG_PATIENT"
            digest = hashlib.sha256(payload).hexdigest()
            existing = c.execute("SELECT sha256 FROM photos WHERE request_id=?", (request_id,)).fetchone()
            if existing:
                c.commit()
                return "IDEMPOTENT" if existing[0] == digest else "CONFLICT"
            c.execute("INSERT INTO photos VALUES(?,?,?,?)", (request_id, TENANT, patient, digest))
            c.execute("UPDATE photo_requests SET status='RECEIVED' WHERE id=?", (request_id,))
            if fault:
                c.rollback()
                return "ROLLED_BACK_NO_ACK"
            c.commit()
            return "ACK_AFTER_COMMIT"

    def rows(self, sql, args=()):
        with self.connection() as c:
            return c.execute(sql, args).fetchall()


def run() -> dict:
    require_offline()
    with tempfile.TemporaryDirectory(prefix="dc06i-local-test-") as tmp:
        lab = LocalLab(Path(tmp) / "isolated.sqlite")
        barrier = threading.Barrier(2)
        go_photo = threading.Event()
        timing = {}

        def mobile(patient):
            t = time.monotonic()
            assert lab.send(patient, "msg-" + patient, "synthetic: hello") == "COMMITTED"
            assert lab.send(patient, "msg-" + patient, "synthetic: hello") == "IDEMPOTENT"
            assert lab.send(patient, "msg-" + patient, "different") == "CONFLICT"
            outcome = lab.book(patient, barrier)
            timing[patient] = round((time.monotonic() - t) * 1000, 3)
            return outcome

        def dentist():
            patients = lab.doctor()
            go_photo.set()  # Doctor committed request before waking the camera.
            return patients

        def camera():
            assert lab.photo("patient-b", "request-1", PHOTO) == "UNSOLICITED_OR_WRONG_PATIENT"
            assert lab.photo("patient-a", "not-requested", PHOTO) == "UNSOLICITED_OR_WRONG_PATIENT"
            assert go_photo.wait(timeout=10)
            assert lab.photo("patient-a", "request-1", PHOTO) == "ACK_AFTER_COMMIT"
            assert lab.photo("patient-a", "request-1", PHOTO) == "IDEMPOTENT"
            return hashlib.sha256(PHOTO).hexdigest()

        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="dc06i") as pool:
            fa = pool.submit(mobile, "patient-a")
            fb = pool.submit(mobile, "patient-b")
            fd = pool.submit(dentist)
            fc = pool.submit(camera)
            bookings = [fa.result(timeout=20), fb.result(timeout=20)]
            dentist_count = fd.result(timeout=20)
            photo_sha = fc.result(timeout=20)

        assert sorted(bookings) == ["CONFIRMED_AFTER_COMMIT", "SLOT_CONFLICT"], bookings
        assert lab.rows("SELECT COUNT(*) FROM appointments")[0][0] == 1
        assert dentist_count == 2
        assert lab.rows("SELECT COUNT(*) FROM observations")[0][0] == 1
        assert lab.rows("SELECT COUNT(*) FROM messages")[0][0] == 2
        for patient in ("patient-a", "patient-b"):
            assert lab.rows("SELECT client_id FROM messages WHERE patient=?", (patient,)) == [("msg-" + patient,)]
        assert lab.rows("SELECT patient,sha256 FROM photos WHERE request_id='request-1'") == [("patient-a", photo_sha)]
        assert lab.photo("patient-a", "request-fault", PHOTO, fault=True) == "ROLLED_BACK_NO_ACK"
        assert not lab.rows("SELECT 1 FROM photos WHERE request_id='request-fault'")
        assert lab.rows("SELECT status FROM photo_requests WHERE id='request-fault'") == [("REQUESTED",)]
        with lab.connection() as c:
            c.execute("UPDATE patients SET revoked=1 WHERE id='patient-b'")
        assert lab.send("patient-b", "revoked", "deny") == "DENIED"
        assert lab.photo("patient-b", "request-1", PHOTO) == "DENIED"

    return {
        "marker": "C05B03I_LOCAL_SYNTHETIC_CONTRACT_PREFLIGHT_PASS",
        "mode": "LOCAL_4_THREADS_1_SQLITE_DB_FIVE_LOGICAL_ROLES",
        "checks": {
            "two_clients_same_slot_one_commit": "PASS",
            "two_patients_message_isolation_idempotence": "PASS",
            "dentist_db_access_during_other_actors": "PASS",
            "photo_requested_scoped_checksum_ack_after_commit": "PASS",
            "fault_rollback_revocation_and_replay": "PASS",
        },
        "mobile_elapsed_ms": timing,
        "real_digital_crown_backend_used": False,
        "real_five_vm_network_used": False,
        "physical_mobile_or_dental_device_used": False,
        "clinical_ack_issued": False,
        "product_ready": False,
    }


if __name__ == "__main__":
    try:
        result = run()
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"marker": "C05B03I_LOCAL_PREFLIGHT_FAIL", "error": str(exc)}, sort_keys=True))
        raise
