"""F05: real Patient Companion agenda HTTP route across two Uvicorn PIDs on disposable PG.

This is a synthetic integration lab: real device-token dependency, JOSE envelope,
domain handler, durable receipt, PostgreSQL, and real HTTP; lab-only key unprotect
stands in for Windows DPAPI, which is tested in its separate Windows gate.
"""
from __future__ import annotations

import json
import os

assert os.environ.get("ENVIRONMENT") == "test"
assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
assert os.environ.get("PG_CERT_LAB") == "1"
assert os.environ.get("DATABASE_URL", "").startswith("postgresql+psycopg://")
assert os.environ["DATABASE_URL"].endswith("/dc_agenda_synthetic")

from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from sqlalchemy import text

from backend import database, models
from backend.routers import appointments, auth
from backend.routers import patient_companion_agenda as pc_router
from backend.routers.patient_companion_common import create_patient_device_token
from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionAgendaSlot,
    PatientCompanionAppointmentRef, PatientCompanionIdentity,
    PatientCompanionRemoteReceipt,
)
from backend.services.patient_companion_remote_crypto import (
    decrypt_and_verify, generate_p256_keypair, sign_and_encrypt,
)
from backend.services.patient_companion_remote_keys import enroll_remote_keyset
from backend.services.patient_companion_remote_worker import (
    process_remote_envelope as actual_worker,
)
from relay.contract import RelayInnerMessage


def _protect(value: bytes) -> bytes:
    return b"f05-ci-protected:" + value


def _unprotect(value: bytes) -> bytes:
    if not value.startswith(b"f05-ci-protected:"):
        raise ValueError("not a synthetic laboratory-protected key")
    return value[len(b"f05-ci-protected:"):]


def _worker_with_lab_key_protection(db, **kwargs):
    # Do not change the production endpoint or OS key provider.
    # Only this synthetic server process substitutes DPAPI on Ubuntu.
    return actual_worker(db, unprotect=_unprotect, **kwargs)


pc_router.process_remote_envelope = _worker_with_lab_key_protection

app = FastAPI(title="F05 synthetic Patient Companion actual HTTP route")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(appointments.router, prefix="/api/appointments")
app.include_router(pc_router.router, prefix="/api/patient-companion")


@app.get("/_f05/pid")
def pid():
    return {"pid": os.getpid()}


def exercise():
    import socket
    import subprocess
    import sys
    import time
    import uuid
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    import httpx
    from backend.security import get_password_hash

    with database.engine.connect() as conn:
        assert conn.scalar(text("SELECT current_database()")) == "dc_agenda_synthetic"
        assert conn.scalar(text("SHOW server_version")).startswith("16.")
    models.Base.metadata.create_all(bind=database.engine)
    Session = database.SessionLocal
    suffix = uuid.uuid4().hex[:10]
    password = "F05_SYNTHETIC_PASSWORD_NEVER_PRODUCTION"

    with Session() as db:
        owner = models.User(
            email=f"f05pc-owner-{suffix}@example.invalid",
            hashed_password=get_password_hash(password),
            role=models.UserRole.DENTISTE, is_active=True, is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        other = models.User(
            email=f"f05pc-other-{suffix}@example.invalid",
            hashed_password=get_password_hash(password),
            role=models.UserRole.DENTISTE, is_active=True, is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        db.add_all([owner, other])
        db.flush()
        patient = models.Patient(
            numero_dossier=f"F05PC-{suffix}", nom="Synthetic", prenom="F05",
            date_naissance=datetime(2010, 1, 1), sexe="F", employer_id=owner.id,
        )
        identity = PatientCompanionIdentity(
            provider="local_bridge", subject=f"f05pc:{suffix}",
        )
        db.add_all([patient, identity])
        db.flush()
        access = PatientCompanionAccess(
            identity_id=identity.id, employer_id=owner.id,
            patient_id=patient.id, relationship_type="SELF",
        )
        db.add(access)
        db.flush()

        sign_priv, sign_pub = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
        dec_priv, dec_pub = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
        keyset, cabinet_sign, cabinet_enc = enroll_remote_keyset(
            db, access=access,
            patient_signing_kid=sign_pub["kid"],
            patient_signing_public_jwk=sign_pub,
            patient_encryption_kid=dec_pub["kid"],
            patient_encryption_public_jwk=dec_pub,
            protect=_protect,
        )
        owner_id, other_id, patient_id, access_id = owner.id, other.id, patient.id, access.id
        access_ref = access.public_id
        device_token = create_patient_device_token(identity, access)
        enc_pub = json.loads(cabinet_enc.public_jwk_json)
        sig_pub = json.loads(cabinet_sign.public_jwk_json)
        enc_kid = keyset.cabinet_encryption_kid
        sig_kid = keyset.cabinet_signing_kid
        db.commit()

    def new_slot(hour):
        with Session() as db:
            slot = PatientCompanionAgendaSlot(
                employer_id=owner_id, practitioner_id=owner_id,
                datetime_start=datetime(2030, 1, 3, hour),
                duration_minutes=30,
                expires_at=datetime.utcnow() + timedelta(minutes=15),
            )
            db.add(slot)
            db.flush()
            public, slot_id = slot.public_id, slot.id
            db.commit()
            return public, slot_id

    def count(hour):
        with Session() as db:
            return db.query(models.Appointment).filter(
                models.Appointment.employer_id == owner_id,
                models.Appointment.datetime_start == datetime(2030, 1, 3, hour),
                models.Appointment.deleted_at.is_(None),
            ).count()

    def receipt_count(idem):
        with Session() as db:
            return db.query(PatientCompanionRemoteReceipt).filter(
                PatientCompanionRemoteReceipt.access_id == access_id,
                PatientCompanionRemoteReceipt.idempotency_key == str(idem),
            ).count()

    def consumed(slot_id):
        with Session() as db:
            return db.get(PatientCompanionAgendaSlot, slot_id).consumed_at is not None

    def sign_command(operation, payload, idem=None):
        now = datetime.now(timezone.utc)
        idem = idem or uuid.uuid4()
        inner = RelayInnerMessage(
            message_id=uuid.uuid4(), access_id=uuid.UUID(access_ref),
            sent_at=now, expires_at=now + timedelta(minutes=8),
            idempotency_key=idem, operation=operation, payload=payload,
        )
        compact = sign_and_encrypt(
            inner.model_dump(mode="json"),
            sender_signing_private_jwk=sign_priv,
            recipient_encryption_public_jwk=enc_pub,
            sender_signing_kid=sign_pub["kid"],
            recipient_encryption_kid=enc_kid,
        )
        return compact, idem

    def ack_payload(blob):
        return decrypt_and_verify(
            blob,
            recipient_encryption_private_jwk=dec_priv,
            sender_signing_public_jwk=sig_pub,
            expected_sender_signing_kid=sig_kid,
            expected_recipient_encryption_kid=dec_pub["kid"],
        )["payload"]

    def port():
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    ports = [port(), port()]
    assert ports[0] != ports[1]
    urls = [f"http://127.0.0.1:{p}" for p in ports]
    procs = []
    try:
        for p in ports:
            procs.append(subprocess.Popen(
                [sys.executable, "-m", "uvicorn",
                 "scripts.verification.lot07_07a_f05_pc_http:app",
                 "--host", "127.0.0.1", "--port", str(p), "--no-access-log"],
                env=os.environ.copy(), stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            ))
        for process, base in zip(procs, urls):
            for _ in range(150):
                if process.poll() is not None:
                    raise AssertionError(f"child exited: {process.returncode}")
                try:
                    response = httpx.get(base + "/_f05/pid", timeout=1)
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.1)
            else:
                raise AssertionError("two-process patient HTTP lab failed startup")
        pids = [httpx.get(url + "/_f05/pid").json()["pid"] for url in urls]
        assert pids[0] != pids[1]
        print("F05_PC_HTTP_PIDS", pids, "DISTINCT", True, flush=True)

        def login(base, email):
            response = httpx.post(base + "/api/auth/login",
                data={"username": email, "password": password}, timeout=10)
            assert response.status_code == 200, (response.status_code, response.text[:150])
            return response.json()["access_token"]

        owner_jwt = login(urls[0], f"f05pc-owner-{suffix}@example.invalid")
        other_jwt = login(urls[1], f"f05pc-other-{suffix}@example.invalid")
        route = f"/api/patient-companion/contexts/{access_ref}/agenda/remote-command"

        def remote(worker, blob, bearer=device_token):
            headers = {"Authorization": f"Bearer {bearer}"} if bearer else {}
            with httpx.Client(timeout=25) as client:
                response = client.post(
                    urls[worker] + route,
                    json={"blob": blob}, headers=headers,
                )
            if response.status_code == 200:
                return response.status_code, ack_payload(response.json()["blob"])
            return response.status_code, response.text[:200]

        def book(worker, hour, token=owner_jwt):
            with httpx.Client(timeout=25) as client:
                response = client.post(
                    urls[worker] + "/api/appointments/",
                    json={"patient_name": "F05 HTTP synthetic",
                          "datetime_start": f"2030-01-03T{hour:02}:00:00",
                          "duration_minutes": 30, "praticien_id": owner_id},
                    headers={"Authorization": f"Bearer {token}"},
                )
            return response.status_code, response.text[:200]

        def race(left, right):
            barrier = Barrier(2)
            def invoke(call):
                barrier.wait(timeout=10)
                return call()
            with ThreadPoolExecutor(max_workers=2) as pool:
                a = pool.submit(invoke, left)
                b = pool.submit(invoke, right)
                return a.result(timeout=35), b.result(timeout=35)

        # The actual Patient Companion HTTP endpoint checks its real bearer
        # dependency and identity/access binding BEFORE decrypting the JWE.
        slot_ref, slot_id = new_slot(10)
        token, idem = sign_command("agenda.create", {"slot_ref": slot_ref})
        denied = remote(0, token, bearer=None)
        malformed = remote(0, token, bearer="malformed")
        assert denied[0] == 401 and malformed[0] == 401, (denied, malformed)
        print("F05_PC_HTTP_PATIENT_AUTH", denied[0], malformed[0], flush=True)

        # Different FastAPI processes and genuinely encrypted requests compete
        # against the actual canonical appointment API. Both paths share PG lock.
        for hour in (10, 11, 12):
            if hour != 10:
                slot_ref, slot_id = new_slot(hour)
                token, idem = sign_command("agenda.create", {"slot_ref": slot_ref})
            pc_response, staff = race(lambda: remote(0, token), lambda: book(1, hour))
            assert pc_response[0] == 200, pc_response
            remote_state = pc_response[1]["status"]
            accepted = remote_state == "ACCEPTED"
            assert remote_state in {"ACCEPTED", "REJECTED"}, pc_response
            assert staff[0] == (409 if accepted else 200), (pc_response, staff)
            if not accepted:
                assert pc_response[1]["result"]["code"] == "SLOT_CONFLICT", pc_response
            assert count(hour) == 1 and receipt_count(idem) == 1
            assert consumed(slot_id) == accepted, (pc_response, staff)
            print("F05_PC_HTTP_AGENDA_RACE", hour, "REMOTE", remote_state,
                  "STAFF", staff[0], "SQL", count(hour),
                  "RECEIPTS", receipt_count(idem), flush=True)

        # Two different signed JWE message IDs with the same idempotency key
        # race across independent HTTP workers: 1 booking, 1 durable receipt.
        slot_ref, slot_id = new_slot(13)
        idem = uuid.uuid4()
        token_a, _ = sign_command("agenda.create", {"slot_ref": slot_ref}, idem)
        token_b, _ = sign_command("agenda.create", {"slot_ref": slot_ref}, idem)
        a, b = race(lambda: remote(0, token_a), lambda: remote(1, token_b))
        assert a[0] == b[0] == 200, (a, b)
        assert a[1]["status"] == b[1]["status"] == "ACCEPTED", (a, b)
        assert a[1]["result"]["appointment_ref"] == b[1]["result"]["appointment_ref"]
        assert count(13) == receipt_count(idem) == 1 and consumed(slot_id)
        print("F05_PC_HTTP_IDEMPOTENT_JWE_RACE", "HTTP", a[0], b[0],
              "SQL", count(13), "RECEIPTS", receipt_count(idem), flush=True)

        # Reprogramming of an existing patient reservation participates in the
        # same lock as a new staff booking in the other FastAPI process.
        with Session() as db:
            original = models.Appointment(
                employer_id=owner_id, patient_id=patient_id, praticien_id=owner_id,
                datetime_start=datetime(2030, 1, 3, 8), duration_minutes=30,
                scheduling_type=models.SchedulingType.EXACT_TIME,
                status=models.AppointmentStatus.CONFIRME,
            )
            db.add(original)
            db.flush()
            ref = PatientCompanionAppointmentRef(
                employer_id=owner_id, patient_id=patient_id,
                appointment_id=original.id,
            )
            db.add(ref)
            db.flush()
            original_id, appointment_ref = original.id, ref.public_id
            db.commit()
        slot_ref, slot_id = new_slot(14)
        signed, idem = sign_command(
            "agenda.reschedule",
            {"appointment_ref": appointment_ref, "slot_ref": slot_ref},
        )
        pc, staff = race(lambda: remote(0, signed), lambda: book(1, 14))
        assert pc[0] == 200 and pc[1]["status"] in {"ACCEPTED", "REJECTED"}, (pc, staff)
        accepted = pc[1]["status"] == "ACCEPTED"
        assert staff[0] == (409 if accepted else 200), (pc, staff)
        assert count(14) == receipt_count(idem) == 1 and consumed(slot_id) == accepted
        with Session() as db:
            moved = db.get(models.Appointment, original_id)
            assert moved.datetime_start == datetime(2030, 1, 3, 14 if accepted else 8)
        print("F05_PC_HTTP_RESCHEDULE_RACE", pc[1]["status"],
              staff[0], "SQL", count(14), flush=True)

        # Signed staff JWT cannot be substituted for patient credentials.
        token, _ = sign_command("agenda.create", {"slot_ref": slot_ref})
        assert remote(0, token, bearer=owner_jwt)[0] == 401
        assert remote(0, token, bearer=other_jwt)[0] == 401
        print("F05_PC_HTTP_STAFF_CANNOT_IMPERSONATE_DEVICE", True, flush=True)
        print("F05_PC_HTTP_RESULT",
              "PASS_SYNTHETIC_REAL_ROUTE_REAL_PATIENT_JWT_JWE_2PIDS_PG_RECEIPTS",
              "DPAPI_LINUX_SUBSTITUTED", flush=True)
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    exercise()
