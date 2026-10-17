"""Synthetic PostgreSQL F05: atomic Patient Companion remote receipts and controlled deadlock."""
import os
assert os.getenv("ENVIRONMENT")=="test"
assert os.getenv("DIGITALCROWN_ISOLATED_RUNTIME")=="1"
assert os.getenv("PG_CERT_LAB")=="1"
assert os.getenv("DATABASE_URL","").startswith("postgresql+psycopg://")
assert os.getenv("DATABASE_URL","").endswith("/dc_agenda_synthetic")

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from backend import database, models
from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionAgendaSlot, PatientCompanionIdentity,
    PatientCompanionRemoteReceipt,
)
from backend.services.agenda_write_lock import lock_cabinet_appointment_writes
from backend.services.patient_companion_remote_crypto import (
    decrypt_and_verify, generate_p256_keypair, sign_and_encrypt,
)
from backend.services.patient_companion_remote_keys import enroll_remote_keyset
from backend.services.patient_companion_remote_worker import process_remote_envelope
from relay.contract import RelayInnerMessage

def _protect(data):
    return b"f05-ci-protected:" + data

def _unprotect(data):
    return data.removeprefix(b"f05-ci-protected:")

def _main():
    engine=database.engine
    assert engine.dialect.name=="postgresql"
    with engine.connect() as c:
        assert c.scalar(text("SELECT current_database()"))=="dc_agenda_synthetic"
        version=c.scalar(text("SHOW server_version"))
        assert version.startswith("16."),version
    models.Base.metadata.create_all(bind=engine)
    Session=database.SessionLocal
    suffix=uuid.uuid4().hex[:10]
    with Session() as db:
        owner=models.User(
            email=f"f05-receipt-{suffix}@example.invalid", hashed_password="SYNTHETIC",
            role=models.UserRole.DENTISTE, is_active=True, is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        db.add(owner);db.flush()
        patient=models.Patient(
            numero_dossier=f"F05R-{suffix}",nom="F05",prenom="Synthetic",
            date_naissance=datetime(2010,1,1),sexe="F",employer_id=owner.id,
        )
        identity=PatientCompanionIdentity(provider="local_bridge",subject=f"f05-receipt:{suffix}")
        db.add_all([patient,identity]);db.flush()
        access=PatientCompanionAccess(
            identity_id=identity.id, employer_id=owner.id,
            patient_id=patient.id, relationship_type="SELF",
        )
        db.add(access);db.flush()
        signing_priv,signing_pub=generate_p256_keypair(kid=str(uuid.uuid4()),use="sig")
        decrypt_priv,decrypt_pub=generate_p256_keypair(kid=str(uuid.uuid4()),use="enc")
        keyset,cabinet_sig,cabinet_enc=enroll_remote_keyset(
            db, access=access, patient_signing_kid=signing_pub["kid"],
            patient_signing_public_jwk=signing_pub,
            patient_encryption_kid=decrypt_pub["kid"],
            patient_encryption_public_jwk=decrypt_pub,protect=_protect,
        )
        slot=PatientCompanionAgendaSlot(
            employer_id=owner.id,practitioner_id=owner.id,
            datetime_start=datetime(2030,1,2,19,0),duration_minutes=30,
            expires_at=datetime.utcnow()+timedelta(minutes=15),
        )
        db.add(slot);db.flush()
        owner_id,patient_id,access_id,keyset_id,slot_id=owner.id,patient.id,access.id,keyset.id,slot.id
        slot_public_id=slot.public_id
        access_public_id=access.public_id
        cabinet_enc_pub=json.loads(cabinet_enc.public_jwk_json)
        cabinet_sig_pub=json.loads(cabinet_sig.public_jwk_json)
        cab_enc_kid=keyset.cabinet_encryption_kid
        cab_sig_kid=keyset.cabinet_signing_kid
        db.commit()

    def signed(message):
        return sign_and_encrypt(
            message.model_dump(mode="json"),
            sender_signing_private_jwk=signing_priv,
            recipient_encryption_public_jwk=cabinet_enc_pub,
            sender_signing_kid=signing_pub["kid"],
            recipient_encryption_kid=cab_enc_kid,
        )
    def msg(slot_ref,idem):
        now=datetime.now(timezone.utc)
        return RelayInnerMessage(
            message_id=uuid.uuid4(), access_id=uuid.UUID(access_public_id),
            sent_at=now,expires_at=now+timedelta(minutes=10),
            idempotency_key=idem,operation="agenda.create",
            payload={"slot_ref":slot_ref},
        )
    def process(token,commit=True):
        with Session() as db:
            a=db.get(PatientCompanionAccess,access_id)
            from backend.models_patient_companion import PatientCompanionRemoteKeyset
            k=db.get(PatientCompanionRemoteKeyset,keyset_id)
            ack=process_remote_envelope(
                db,access=a,keyset=k,compact_jwe=token,
                unprotect=_unprotect,commit=commit,
            )
            decoded=decrypt_and_verify(
                ack,recipient_encryption_private_jwk=decrypt_priv,
                sender_signing_public_jwk=cabinet_sig_pub,
                expected_sender_signing_kid=cab_sig_kid,
                expected_recipient_encryption_kid=decrypt_pub["kid"],
            )
            if not commit:
                # Failure injection after all SQL writes and signed ACK, before COMMIT.
                db.rollback()
            return decoded
    idem=uuid.uuid4()
    first=process(signed(msg(slot_public_id,idem)))
    assert first["payload"]["status"]=="ACCEPTED",first
    assert first["payload"]["result"]["state"]=="confirmed"
    retry=process(signed(msg(slot_public_id,idem)))
    assert retry["payload"]["status"]=="ACCEPTED"
    assert retry["payload"]["result"]["appointment_ref"]==first["payload"]["result"]["appointment_ref"]
    with Session() as db:
        count=db.query(models.Appointment).filter(
            models.Appointment.patient_id==patient_id,
            models.Appointment.datetime_start==datetime(2030,1,2,19),
        ).count()
        receipts=db.query(PatientCompanionRemoteReceipt).filter(
            PatientCompanionRemoteReceipt.access_id==access_id,
        ).all()
        consumed=db.get(PatientCompanionAgendaSlot,slot_id).consumed_at
        assert count==1 and len(receipts)==1 and receipts[0].status=="ACCEPTED" and consumed
        print("F05_JWE_RECEIPT", "SIGNED_ENCRYPTED=YES","FIRST=ACCEPTED",
              "RETRY=ACCEPTED","SQL_APPOINTMENTS",count,"SQL_RECEIPTS",len(receipts),
              "SLOT_CONSUMED",bool(consumed),flush=True)

    with Session() as db:
        slot2=PatientCompanionAgendaSlot(
            employer_id=owner_id,practitioner_id=owner_id,
            datetime_start=datetime(2030,1,2,19,30),duration_minutes=30,
            expires_at=datetime.utcnow()+timedelta(minutes=15),
        )
        db.add(slot2);db.flush()
        slot2_id,slot2_ref=slot2.id,slot2.public_id
        db.commit()
    rollback_idem=uuid.uuid4()
    attempted=process(signed(msg(slot2_ref,rollback_idem)),commit=False)
    assert attempted["payload"]["status"]=="ACCEPTED"
    with Session() as db:
        slot_after=db.get(PatientCompanionAgendaSlot,slot2_id)
        count=db.query(models.Appointment).filter(
            models.Appointment.patient_id==patient_id,
            models.Appointment.datetime_start==datetime(2030,1,2,19,30),
        ).count()
        receipts=db.query(PatientCompanionRemoteReceipt).filter(
            PatientCompanionRemoteReceipt.access_id==access_id,
        ).count()
        assert count==0 and slot_after.consumed_at is None and receipts==1
        print("F05_JWE_ATOMIC_ROLLBACK",
              "SQL_APPOINTMENTS",count,"SQL_RECEIPTS",receipts,
              "SLOT_CONSUMED",bool(slot_after.consumed_at),flush=True)

    # Controlled advisory-lock cycle across two independent database sessions.
    k1=(0xFC07<<32)|owner_id
    k2=(0xFD07<<32)|owner_id
    barrier=Barrier(2)
    def deadlock(a,b):
        with Session() as db:
            db.execute(text("SET LOCAL statement_timeout = '8s'"))
            db.execute(text("SELECT pg_advisory_xact_lock(:key)"),{"key":a})
            barrier.wait(timeout=10)
            try:
                db.execute(text("SELECT pg_advisory_xact_lock(:key)"),{"key":b})
                db.commit()
                return "COMMIT"
            except OperationalError as exc:
                sqlstate=getattr(exc.orig,"sqlstate",None)
                db.rollback()
                assert sqlstate=="40P01",(sqlstate,str(exc)[:200])
                return "DEADLOCK_ROLLBACK"
    with ThreadPoolExecutor(max_workers=2) as executor:
        fa=executor.submit(deadlock,k1,k2)
        fb=executor.submit(deadlock,k2,k1)
        outcomes=[fa.result(timeout=20),fb.result(timeout=20)]
    assert sorted(outcomes)==["COMMIT","DEADLOCK_ROLLBACK"],outcomes
    with Session() as db:
        assert db.execute(text("SELECT pg_try_advisory_xact_lock(:key)"),{"key":k1}).scalar_one()
        assert db.execute(text("SELECT pg_try_advisory_xact_lock(:key)"),{"key":k2}).scalar_one()
        db.rollback()
    print("F05_PG_DEADLOCK_CONTROLLED",outcomes,"LOCKS_RELEASED_AFTER_COMMIT_ROLLBACK",flush=True)
    print("F05_FAULTS_RESULT","PASS_SYNTHETIC_DIRECT_WORKER_NOT_FULL_PATIENT_HTTP",flush=True)

if __name__=="__main__":
    _main()
