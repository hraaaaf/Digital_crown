from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionAgendaSlot, PatientCompanionIdentity
from backend.services.patient_companion_remote_crypto import (
    decrypt_and_verify,
    generate_p256_keypair,
    sign_and_encrypt,
)
from backend.services.patient_companion_remote_keys import enroll_remote_keyset
from backend.services.patient_companion_remote_receipts import RemoteReplayDetected
from backend.services.patient_companion_remote_worker import RemoteDomainResult, process_remote_envelope
from relay.contract import RelayInnerMessage


def _protect(raw: bytes) -> bytes:
    return b"test-protected:" + raw


def _unprotect(raw: bytes) -> bytes:
    return raw.removeprefix(b"test-protected:")


def test_remote_worker_dispatches_once_and_rejects_exact_replay(db, dentiste):
    patient = models.Patient(
        numero_dossier=f"PCRW-{uuid.uuid4().hex[:8]}",
        nom="Remote",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    identity = PatientCompanionIdentity(
        provider="local_bridge",
        subject=f"device:{uuid.uuid4()}",
    )
    db.add_all([patient, identity])
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.flush()

    patient_sig_private, patient_sig_public = generate_p256_keypair(
        kid=str(uuid.uuid4()), use="sig"
    )
    patient_enc_private, patient_enc_public = generate_p256_keypair(
        kid=str(uuid.uuid4()), use="enc"
    )
    keyset, cabinet_sig, cabinet_enc = enroll_remote_keyset(
        db,
        access=access,
        patient_signing_kid=patient_sig_public["kid"],
        patient_signing_public_jwk=patient_sig_public,
        patient_encryption_kid=patient_enc_public["kid"],
        patient_encryption_public_jwk=patient_enc_public,
        protect=_protect,
    )
    db.commit()

    now = datetime.now(timezone.utc)
    operation = "x" * 64
    message = RelayInnerMessage(
        message_id=uuid.uuid4(),
        access_id=uuid.UUID(access.public_id),
        sent_at=now,
        expires_at=now + timedelta(minutes=10),
        idempotency_key=uuid.uuid4(),
        operation=operation,
        payload={"slot_ref": "opaque-slot"},
    )
    token = sign_and_encrypt(
        message.model_dump(mode="json"),
        sender_signing_private_jwk=patient_sig_private,
        recipient_encryption_public_jwk=json.loads(cabinet_enc.public_jwk_json),
        sender_signing_kid=keyset.patient_signing_kid,
        recipient_encryption_kid=keyset.cabinet_encryption_kid,
    )

    calls = []

    def handler(_db, _access, payload):
        calls.append(payload)
        return RemoteDomainResult(status="ACCEPTED", response={"state": "accepted"})

    ack_token = process_remote_envelope(
        db,
        access=access,
        keyset=keyset,
        compact_jwe=token,
        handlers={operation: handler},
        unprotect=_unprotect,
    )
    ack = decrypt_and_verify(
        ack_token,
        recipient_encryption_private_jwk=patient_enc_private,
        sender_signing_public_jwk=json.loads(cabinet_sig.public_jwk_json),
        expected_sender_signing_kid=keyset.cabinet_signing_kid,
        expected_recipient_encryption_kid=keyset.patient_encryption_kid,
    )

    assert calls == [{"slot_ref": "opaque-slot"}]
    assert ack["operation"] == "command.result"
    assert ack["payload"]["request_operation"] == operation
    assert ack["payload"]["status"] == "ACCEPTED"
    assert ack["idempotency_key"] == str(message.idempotency_key)

    with pytest.raises(RemoteReplayDetected):
        process_remote_envelope(
            db,
            access=access,
            keyset=keyset,
            compact_jwe=token,
            handlers={operation: handler},
            unprotect=_unprotect,
        )

    assert len(calls) == 1


def test_remote_worker_default_registry_executes_pc02_create_idempotently(db, dentiste):
    patient = models.Patient(
        numero_dossier=f"PCRW-PC02-{uuid.uuid4().hex[:8]}", nom="Remote", prenom="Agenda",
        date_naissance=datetime(2010, 1, 1), sexe="F", employer_id=dentiste.id,
    )
    identity = PatientCompanionIdentity(provider="local_bridge", subject=f"device:{uuid.uuid4()}")
    db.add_all([patient, identity]); db.flush()
    access = PatientCompanionAccess(identity_id=identity.id, employer_id=dentiste.id, patient_id=patient.id, relationship_type="SELF")
    db.add(access); db.flush()
    patient_sig_private, patient_sig_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
    patient_enc_private, patient_enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
    keyset, cabinet_sig, cabinet_enc = enroll_remote_keyset(
        db, access=access,
        patient_signing_kid=patient_sig_public["kid"], patient_signing_public_jwk=patient_sig_public,
        patient_encryption_kid=patient_enc_public["kid"], patient_encryption_public_jwk=patient_enc_public,
        protect=_protect,
    )
    slot = PatientCompanionAgendaSlot(
        public_id=str(uuid.uuid4()), employer_id=dentiste.id, practitioner_id=dentiste.id,
        datetime_start=datetime(2030, 1, 4, 10, 0), duration_minutes=30,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(slot); db.commit()

    now = datetime.now(timezone.utc)
    idem = uuid.uuid4()
    message = RelayInnerMessage(
        message_id=uuid.uuid4(), access_id=uuid.UUID(access.public_id), sent_at=now,
        expires_at=now + timedelta(minutes=10), idempotency_key=idem,
        operation="agenda.create", payload={"slot_ref": slot.public_id},
    )
    token = sign_and_encrypt(
        message.model_dump(mode="json"), sender_signing_private_jwk=patient_sig_private,
        recipient_encryption_public_jwk=json.loads(cabinet_enc.public_jwk_json),
        sender_signing_kid=keyset.patient_signing_kid,
        recipient_encryption_kid=keyset.cabinet_encryption_kid,
    )
    ack_token = process_remote_envelope(db, access=access, keyset=keyset, compact_jwe=token, unprotect=_unprotect)
    ack = decrypt_and_verify(
        ack_token, recipient_encryption_private_jwk=patient_enc_private,
        sender_signing_public_jwk=json.loads(cabinet_sig.public_jwk_json),
        expected_sender_signing_kid=keyset.cabinet_signing_kid,
        expected_recipient_encryption_kid=keyset.patient_encryption_kid,
    )
    assert ack["payload"]["status"] == "ACCEPTED"
    assert ack["payload"]["result"]["state"] == "confirmed"
    assert db.query(models.Appointment).filter(models.Appointment.patient_id == patient.id).count() == 1
    assert db.query(models.AuditLog).filter(
        models.AuditLog.action == "PATIENT_COMPANION_REMOTE_COMMAND",
        models.AuditLog.resource_id == access.public_id,
    ).count() == 1

    retry = RelayInnerMessage(
        message_id=uuid.uuid4(), access_id=message.access_id, sent_at=now,
        expires_at=message.expires_at, idempotency_key=idem,
        operation="agenda.create", payload={"slot_ref": slot.public_id},
    )
    retry_token = sign_and_encrypt(
        retry.model_dump(mode="json"), sender_signing_private_jwk=patient_sig_private,
        recipient_encryption_public_jwk=json.loads(cabinet_enc.public_jwk_json),
        sender_signing_kid=keyset.patient_signing_kid,
        recipient_encryption_kid=keyset.cabinet_encryption_kid,
    )
    retry_ack = process_remote_envelope(db, access=access, keyset=keyset, compact_jwe=retry_token, unprotect=_unprotect)
    decoded_retry = decrypt_and_verify(
        retry_ack, recipient_encryption_private_jwk=patient_enc_private,
        sender_signing_public_jwk=json.loads(cabinet_sig.public_jwk_json),
        expected_sender_signing_kid=keyset.cabinet_signing_kid,
        expected_recipient_encryption_kid=keyset.patient_encryption_kid,
    )
    assert decoded_retry["payload"]["status"] == "ACCEPTED"
    assert db.query(models.Appointment).filter(models.Appointment.patient_id == patient.id).count() == 1
    assert db.query(models.AuditLog).filter(
        models.AuditLog.action == "PATIENT_COMPANION_REMOTE_COMMAND",
        models.AuditLog.resource_id == access.public_id,
    ).count() == 1
