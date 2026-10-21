"""LOT06-B synthetic staff-confirmation / receipt contract; NEVER clinical.

No API route, Patient/Appointment/ClinicalAsset tables, device registration,
network calls or real cryptographic staff authentication are connected here.
The synthetic fixture authority itself can mint staff sessions and captures;
therefore LAB receipt != server ACK and this cannot authorize an upload.
SQLite demonstrates local atomicity only, NOT a DB/blob distributed commit,
SCM/NTFS isolation, a remote server receipt or anti-rollback assurance.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
import tempfile


class LabReceiptRejected(ValueError):
    """Non-PHI reason code for an isolated contract rejection."""


@dataclass(frozen=True)
class LabReceipt:
    receipt_id: str
    state: str  # Always LAB_RECEIPT_COMMITTED; never clinical SERVER_CONFIRMED.


_MARKER = ".digitalcrown-ack-contract-lab-only"
_MARKER_BYTES = b"DC06B_SYNTHETIC_ACK_CONTRACT_V1\n"
_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")


def _check_id(value: object) -> str:
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise LabReceiptRejected("BAD_SYNTHETIC_ID")
    return value


def _check_digest(value: object) -> str:
    if type(value) is not str or _SHA.fullmatch(value) is None:
        raise LabReceiptRejected("BAD_DIGEST")
    return value


class SyntheticReceiptLedger:
    """Single-local-SQLite proof of ordering, replay, authorization rechecks.

    FIXTURE methods are a mock trust root, not an interface for product data.
    Even a successful receipt must not change a HotFolder item or ClinicalAsset.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self._guard()
        self.path = self.root / "synthetic-receipts.sqlite3"
        if self.path.is_symlink():
            raise LabReceiptRejected("UNSAFE_LAB_DB")
        with self._transaction() as db:
            ddl = """
                CREATE TABLE IF NOT EXISTS staff(
                  tenant TEXT NOT NULL, staff_id TEXT NOT NULL,
                  active INTEGER NOT NULL, can_confirm INTEGER NOT NULL,
                  PRIMARY KEY(tenant, staff_id));
                CREATE TABLE IF NOT EXISTS sessions(
                  token_hash TEXT PRIMARY KEY, tenant TEXT NOT NULL,
                  staff_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS stations(
                  tenant TEXT NOT NULL, station_id TEXT NOT NULL,
                  active INTEGER NOT NULL, PRIMARY KEY(tenant, station_id));
                CREATE TABLE IF NOT EXISTS patients(
                  tenant TEXT NOT NULL, patient_id TEXT NOT NULL,
                  active INTEGER NOT NULL, PRIMARY KEY(tenant, patient_id));
                CREATE TABLE IF NOT EXISTS appointments(
                  tenant TEXT NOT NULL, appointment_id TEXT NOT NULL,
                  patient_id TEXT NOT NULL, active INTEGER NOT NULL,
                  PRIMARY KEY(tenant, appointment_id));
                CREATE TABLE IF NOT EXISTS captures(
                  tenant TEXT NOT NULL, capture_id TEXT NOT NULL,
                  station_id TEXT NOT NULL, digest TEXT NOT NULL,
                  byte_size INTEGER NOT NULL,
                  PRIMARY KEY(tenant, capture_id));
                CREATE TABLE IF NOT EXISTS approvals(
                  approval_id TEXT PRIMARY KEY,
                  tenant TEXT NOT NULL, staff_id TEXT NOT NULL,
                  station_id TEXT NOT NULL, capture_id TEXT NOT NULL,
                  patient_id TEXT NOT NULL, appointment_id TEXT NOT NULL,
                  digest TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS receipts(
                  tenant TEXT NOT NULL, capture_id TEXT NOT NULL,
                  approval_id TEXT NOT NULL UNIQUE,
                  staff_id TEXT NOT NULL, station_id TEXT NOT NULL,
                  patient_id TEXT NOT NULL, appointment_id TEXT NOT NULL,
                  digest TEXT NOT NULL, receipt_id TEXT NOT NULL UNIQUE,
                  PRIMARY KEY(tenant, capture_id));
                CREATE TABLE IF NOT EXISTS audit(
                  audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tenant TEXT NOT NULL, capture_id TEXT NOT NULL,
                  event TEXT NOT NULL, ref_id TEXT NOT NULL);
            """
            for statement in ddl.split(";"):
                if statement.strip():
                    db.execute(statement)

    def _guard(self):
        if (os.environ.get("ENVIRONMENT") != "test"
                or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME", "").lower() not in {"true", "1"}
                or os.environ.get("DC_V15_06_ACK_CONTRACT_LAB") != "1"):
            raise LabReceiptRejected("LAB_DISABLED")
        tmp = Path(tempfile.gettempdir()).resolve()
        if (not self.root.is_dir() or self.root.is_symlink()
                or not self.root.resolve().is_relative_to(tmp)
                or not (self.root / _MARKER).is_file()
                or (self.root / _MARKER).is_symlink()
                or (self.root / _MARKER).read_bytes() != _MARKER_BYTES):
            raise LabReceiptRejected("INVALID_TEMP_LAB_MARKER")
        if (self.root / "synthetic-receipts.sqlite3").is_symlink():
            raise LabReceiptRejected("UNSAFE_LAB_DB")

    @contextmanager
    def _transaction(self):
        self._guard()
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=10000")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def fixture_staff(self, tenant: str, staff_id: str, *, active=True, can_confirm=True) -> str:
        """MOCK AUTHORITY: only synthetic fixtures may issue this session."""
        tenant, staff_id = _check_id(tenant), _check_id(staff_id)
        token = secrets.token_urlsafe(32)
        with self._transaction() as db:
            db.execute("INSERT OR REPLACE INTO staff VALUES(?,?,?,?)",
                       (tenant, staff_id, int(active), int(can_confirm)))
            db.execute("INSERT INTO sessions VALUES(?,?,?)",
                       (hashlib.sha256(token.encode()).hexdigest(), tenant, staff_id))
        return token

    def fixture_station(self, tenant: str, station_id: str, *, active=True) -> None:
        with self._transaction() as db:
            db.execute("INSERT OR REPLACE INTO stations VALUES(?,?,?)",
                       (_check_id(tenant), _check_id(station_id), int(active)))

    def fixture_patient(self, tenant: str, patient_id: str, *, active=True) -> None:
        with self._transaction() as db:
            db.execute("INSERT OR REPLACE INTO patients VALUES(?,?,?)",
                       (_check_id(tenant), _check_id(patient_id), int(active)))

    def fixture_appointment(self, tenant: str, appointment_id: str,
                            patient_id: str, *, active=True) -> None:
        with self._transaction() as db:
            db.execute("INSERT OR REPLACE INTO appointments VALUES(?,?,?,?)",
                       (_check_id(tenant), _check_id(appointment_id),
                        _check_id(patient_id), int(active)))

    def fixture_capture(self, tenant: str, capture_id: str,
                        station_id: str, verified_fixture_bytes: bytes) -> str:
        """Accept mock caller's bytes, not verified device provenance."""
        _check_id(tenant), _check_id(capture_id), _check_id(station_id)
        if type(verified_fixture_bytes) is not bytes or not 0 < len(verified_fixture_bytes) <= 1024 * 1024:
            raise LabReceiptRejected("BAD_FIXTURE_BYTES")
        digest = hashlib.sha256(verified_fixture_bytes).hexdigest()
        with self._transaction() as db:
            db.execute("INSERT INTO captures VALUES(?,?,?,?,?)",
                       (tenant, capture_id, station_id, digest, len(verified_fixture_bytes)))
        return digest

    @staticmethod
    def _check_authority(db, tenant: str, staff_id: str, session_token: str,
                         station_id: str, patient_id: str,
                         appointment_id: str, capture_id: str, digest: str) -> None:
        for val in (tenant, staff_id, station_id, patient_id, appointment_id, capture_id):
            _check_id(val)
        _check_digest(digest)
        if type(session_token) is not str or len(session_token) > 256 or not session_token:
            raise LabReceiptRejected("STAFF_SESSION_INVALID")
        user = db.execute("SELECT active,can_confirm FROM staff WHERE tenant=? AND staff_id=?",
                          (tenant, staff_id)).fetchone()
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        session = db.execute("SELECT token_hash FROM sessions WHERE tenant=? AND staff_id=?",
                             (tenant, staff_id)).fetchall()
        if (user != (1, 1) or not session
                or not any(hmac.compare_digest(token_hash, row[0]) for row in session)):
            raise LabReceiptRejected("STAFF_NOT_AUTHORIZED")
        if db.execute("SELECT active FROM stations WHERE tenant=? AND station_id=?",
                      (tenant, station_id)).fetchone() != (1,):
            raise LabReceiptRejected("STATION_NOT_AUTHORIZED")
        if db.execute("SELECT active FROM patients WHERE tenant=? AND patient_id=?",
                      (tenant, patient_id)).fetchone() != (1,):
            raise LabReceiptRejected("PATIENT_NOT_FOUND")
        if db.execute("SELECT patient_id,active FROM appointments WHERE tenant=? AND appointment_id=?",
                      (tenant, appointment_id)).fetchone() != (patient_id, 1):
            raise LabReceiptRejected("PATIENT_APPOINTMENT_CONFLICT")
        capture = db.execute("SELECT station_id,digest FROM captures WHERE tenant=? AND capture_id=?",
                             (tenant, capture_id)).fetchone()
        if capture != (station_id, digest):
            raise LabReceiptRejected("UNVERIFIED_CAPTURE_BINDING")

    def approve(self, *, tenant: str, staff_id: str, staff_token: str, station_id: str,
                capture_id: str, patient_id: str, appointment_id: str, digest: str,
                explicit_staff_action: bool) -> str:
        if explicit_staff_action is not True:
            raise LabReceiptRejected("EXPLICIT_STAFF_ACTION_REQUIRED")
        with self._transaction() as db:
            self._check_authority(db, tenant, staff_id, staff_token, station_id,
                                  patient_id, appointment_id, capture_id, digest)
            approval_id = secrets.token_hex(16)
            db.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?)",
                       (approval_id, tenant, staff_id, station_id, capture_id,
                        patient_id, appointment_id, digest))
            db.execute("INSERT INTO audit(tenant,capture_id,event,ref_id) VALUES(?,?,?,?)",
                       (tenant, capture_id, "SYNTHETIC_STAFF_APPROVED", approval_id))
            return approval_id

    def commit(self, approval_id: str, *, staff_token: str, fail_at: str | None = None) -> LabReceipt:
        """All receipt and commit-audit writes share one SQLite transaction.

        fail_at is a negative-test hook, not a recovery implementation.
        """
        _check_id(approval_id)
        with self._transaction() as db:
            approval = db.execute(
                "SELECT tenant,staff_id,station_id,capture_id,patient_id,appointment_id,digest "
                "FROM approvals WHERE approval_id=?", (approval_id,)
            ).fetchone()
            if approval is None:
                raise LabReceiptRejected("NO_EXPLICIT_APPROVAL")
            tenant, staff_id, station, capture, patient, appointment, digest = approval
            # TOCTOU closure: re-check current patient, RDV, tenant, station,
            # capture and staff permission while holding the writer lock.
            self._check_authority(db, tenant, staff_id, staff_token, station,
                                  patient, appointment, capture, digest)
            old = db.execute("SELECT approval_id,staff_id,station_id,patient_id,"
                             "appointment_id,digest,receipt_id FROM receipts "
                             "WHERE tenant=? AND capture_id=?", (tenant, capture)).fetchone()
            if old is not None:
                if old[:6] != (approval_id, staff_id, station, patient, appointment, digest):
                    raise LabReceiptRejected("CONFLICTING_CAPTURE_RECEIPT")
                return LabReceipt(old[6], "LAB_RECEIPT_COMMITTED")
            rid = "LAB-" + secrets.token_hex(16)
            db.execute("INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?,?)",
                       (tenant, capture, approval_id, staff_id, station,
                        patient, appointment, digest, rid))
            if fail_at == "after_receipt":
                raise LabReceiptRejected("INJECTED_TRANSACTION_ABORT")
            db.execute("INSERT INTO audit(tenant,capture_id,event,ref_id) VALUES(?,?,?,?)",
                       (tenant, capture, "SYNTHETIC_RECEIPT_COMMITTED", rid))
            if fail_at == "after_audit":
                raise LabReceiptRejected("INJECTED_TRANSACTION_ABORT")
            return LabReceipt(rid, "LAB_RECEIPT_COMMITTED")

    def inspect(self, tenant: str, capture_id: str) -> dict:
        """Synthetic observability, deliberately no clinical server ACK field."""
        with self._transaction() as db:
            receipts = db.execute("SELECT receipt_id FROM receipts WHERE tenant=? AND capture_id=?",
                                  (_check_id(tenant), _check_id(capture_id))).fetchall()
            events = db.execute("SELECT event FROM audit WHERE tenant=? AND capture_id=? ORDER BY audit_id",
                                (tenant, capture_id)).fetchall()
        return {"receipts": [r[0] for r in receipts], "audit": [r[0] for r in events]}
