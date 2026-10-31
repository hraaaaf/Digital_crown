"""LOT06 Windows: actual SQLCipher encrypted durable receipt + current-user DPAPI.

Synthetic patients only; zero network; the actual receipt service/SQLAlchemy
model and SQLCipher driver are used. No full mobile/Windows HTTP claim.
"""
import os
from pathlib import Path
import secrets
import sys
import tempfile
import types
import uuid
from datetime import datetime, timedelta, timezone

# GitHub Windows invokes this as "python scripts/ci/...", which otherwise
# puts scripts/ci (not the repository root) on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
# Import real model/service modules without executing the cabinet's unrelated
# application startup and UI/honoraires schema dependency graph.
# Same technique as the existing Windows DPAPI transport certification.
root = Path(__file__).resolve().parents[2]
for package_name, location in (
    ("backend", root / "backend"),
    ("backend.core", root / "backend" / "core"),
):
    package = types.ModuleType(package_name)
    package.__path__ = [str(location)]
    sys.modules[package_name] = package

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlcipher3 import dbapi2 as cipher

if sys.platform != "win32":
    raise RuntimeError("WINDOWS_NATIVE_ONLY")
if os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true":
    raise RuntimeError("ISOLATION_REQUIRED")
if os.environ.get("C05B03H_NETWORK_POLICY_APPROVED") != "false":
    raise RuntimeError("TAILNET_FORBIDDEN")

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionIdentity,
    PatientCompanionMessage, PatientCompanionRemoteReceipt,
)
from backend.services.patient_companion_key_protection import (
    protect_os_bound, unprotect_os_bound,
)
from backend.services.patient_companion_remote_receipts import (
    claim_remote_command, complete_remote_command,
)
from relay.contract import RelayInnerMessage

plain = b"LOT06-DPAPI-current-Windows-user-only"
protected = protect_os_bound(plain)
assert protected != plain and plain not in protected
assert unprotect_os_bound(protected) == plain
print("LOT06_P0_WINDOWS_REAL_USER_DPAPI_PASS")

with tempfile.TemporaryDirectory(prefix="dc06l-real-sqlcipher-") as directory:
    filename = Path(directory) / "encrypted-clinic.db"
    master_key = secrets.token_hex(32)

    def connect(key=master_key):
        raw = cipher.connect(str(filename), check_same_thread=False, timeout=15)
        raw.execute("PRAGMA key = \"x'%s'\"" % key)
        raw.execute("PRAGMA busy_timeout=15000")
        raw.execute("PRAGMA foreign_keys=ON")
        return raw

    assert connect().execute("PRAGMA cipher_version").fetchone()[0]
    engine = create_engine("sqlite://", creator=connect, poolclass=NullPool)
    # Use actual ORM schema and FK constraints for the six Patient Companion
    # entities exercised here, rather than unrelated orthodontics tables whose
    # optional model modules are intentionally not imported in this isolated
    # Windows/SQLCipher harness.
    models.Base.metadata.create_all(
        bind=engine,
        tables=[
            models.User.__table__, models.Patient.__table__,
            PatientCompanionIdentity.__table__, PatientCompanionAccess.__table__,
            PatientCompanionMessage.__table__, PatientCompanionRemoteReceipt.__table__,
        ],
    )
    assert filename.is_file()
    assert not filename.read_bytes().startswith(b"SQLite format 3"), "PLAINTEXT_DB"

    with Session(engine) as db:
        doctor = models.User(
            email="dc06-windows-only@example.invalid", hashed_password="disabled",
            role="DENTISTE", nom_complet="Synthetic Doctor",
            is_active=True, is_licensed=True,
        )
        db.add(doctor)
        db.flush()
        patient = models.Patient(
            numero_dossier="DC06-LAB-PATIENT", nom="Synthetic",
            prenom="A", date_naissance=datetime(2010, 1, 1),
            sexe="F", employer_id=doctor.id,
        )
        identity = PatientCompanionIdentity(
            provider="local_bridge", subject="test:" + str(uuid.uuid4()),
        )
        db.add_all([patient, identity])
        db.flush()
        access = PatientCompanionAccess(
            identity_id=identity.id, employer_id=doctor.id,
            patient_id=patient.id, relationship_type="SELF",
        )
        db.add(access)
        db.commit()
        access_id, patient_id, employer_id = access.id, access.patient_id, access.employer_id
        public_id = access.public_id

    message_uuid = uuid.uuid4()
    intent_uuid = uuid.uuid4()
    now = datetime.now(timezone.utc)
    message = RelayInnerMessage(
        message_id=message_uuid, idempotency_key=intent_uuid,
        access_id=uuid.UUID(public_id),
        sent_at=now, expires_at=now + timedelta(minutes=10),
        operation="message.send", payload={
            "client_message_id": str(uuid.uuid4()), "body": "Windows SQLCipher"},
    )

    # Genuine product claim/SQLite SAVEPOINT plus real domain model flush,
    # followed by failure before commit. Neither row may become persistent.
    with Session(engine) as db:
        access = db.get(PatientCompanionAccess, access_id)
        claim = claim_remote_command(db, access=access, message=message)
        assert claim.kind == "new"
        db.add(PatientCompanionMessage(
            access_id=access_id, employer_id=employer_id,
            patient_id=patient_id, client_message_id=str(uuid.uuid4()),
            sender_kind="PATIENT", body="UNCOMMITTED-MUST-DISAPPEAR",
        ))
        db.flush()
        try:
            raise OSError("synthetic I/O failure before SQLCipher commit")
        except OSError:
            db.rollback()

    with Session(engine) as db:
        assert db.query(PatientCompanionRemoteReceipt).count() == 0
        assert db.query(PatientCompanionMessage).count() == 0

    # Same message after failed transaction must be claimable and commit once.
    with Session(engine) as db:
        claim = claim_remote_command(
            db, access=db.get(PatientCompanionAccess, access_id), message=message)
        assert claim.kind == "new"
        db.add(PatientCompanionMessage(
            access_id=access_id, employer_id=employer_id,
            patient_id=patient_id, client_message_id=str(uuid.uuid4()),
            sender_kind="PATIENT", body="ONE-DURABLE-MESSAGE",
        ))
        complete_remote_command(
            claim.receipt, status="ACCEPTED", response={"code": "MESSAGE_STORED"})
        db.commit()

    engine.dispose()
    fresh = connect()
    assert fresh.execute("PRAGMA cipher_version").fetchone()[0]
    assert fresh.execute("SELECT COUNT(*) FROM patient_companion_remote_receipts").fetchone()[0] == 1
    assert fresh.execute("SELECT COUNT(*) FROM patient_companion_messages").fetchone()[0] == 1
    fresh.close()

    wrong = connect(secrets.token_hex(32))
    wrong_key_rejected = False
    try:
        wrong.execute("SELECT COUNT(*) FROM patient_companion_remote_receipts").fetchone()
    except cipher.DatabaseError:
        wrong_key_rejected = True
    finally:
        wrong.close()
    assert wrong_key_rejected, "WRONG_KEY_ACCESS_MUST_FAIL"
    print("LOT06_P0_WINDOWS_REAL_SQLCIPHER_PERSIST_ROLLBACK_WRONG_KEY_PASS")
