from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Response
from starlette.requests import Request

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionIdentity,
    PatientCompanionMessage,
)
from backend.routers.patient_companion_messages import (
    StaffMessageCreate,
    StaffMessageRead,
    staff_mark_messages_read,
    staff_send_message,
)
from backend.services.patient_companion_messages import (
    PC08_MAX_BODY_BYTES,
    PC08_PATIENT_SENDS_PER_HOUR,
    handle_message_read,
    handle_message_received,
    handle_message_send,
    handle_message_sync,
)
from backend.services.patient_companion_remote_crypto import (
    decrypt_and_verify,
    generate_p256_keypair,
    sign_and_encrypt,
)
from backend.services.patient_companion_remote_keys import enroll_remote_keyset
from backend.services.patient_companion_remote_worker import process_remote_envelope
from relay.contract import RelayInnerMessage, RELAY_MAX_BLOB_BYTES
from backend.utils import rate_limit as rate_limit_module


def _patient(db, dentiste, suffix: str):
    patient = models.Patient(
        numero_dossier=f"PC08-{suffix}-{uuid.uuid4().hex[:6]}",
        nom=f"Messaging-{suffix}",
        prenom="Aya",
        date_naissance=datetime(2012, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    return patient


def _access(db, dentiste, patient, relationship: str):
    identity = PatientCompanionIdentity(
        provider="local_bridge",
        subject=f"device:{relationship}:{uuid.uuid4()}",
    )
    db.add(identity)
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        relationship_type=relationship,
    )
    db.add(access)
    db.flush()
    return identity, access


def test_pc08_threads_are_isolated_per_access_even_for_same_patient(db, dentiste):
    patient = _patient(db, dentiste, "ACCESS")
    _identity_a, access_a = _access(db, dentiste, patient, "SELF")
    _identity_b, access_b = _access(db, dentiste, patient, "PARENT")

    result_a = handle_message_send(
        db,
        access_a,
        {"client_message_id": str(uuid.uuid4()), "body": "Message du patient."},
    )
    result_b = handle_message_send(
        db,
        access_b,
        {"client_message_id": str(uuid.uuid4()), "body": "Message du parent."},
    )
    assert result_a.status == result_b.status == "ACCEPTED"
    db.commit()

    sync_a = handle_message_sync(db, access_a, {})
    sync_b = handle_message_sync(db, access_b, {})
    assert [item["body"] for item in sync_a.response["items"]] == ["Message du patient."]
    assert [item["body"] for item in sync_b.response["items"]] == ["Message du parent."]


def test_pc08_patient_send_is_domain_idempotent_and_conflict_safe(db, dentiste):
    patient = _patient(db, dentiste, "IDEM")
    _identity, access = _access(db, dentiste, patient, "SELF")
    client_message_id = str(uuid.uuid4())

    first = handle_message_send(
        db,
        access,
        {"client_message_id": client_message_id, "body": "Bonjour cabinet"},
    )
    second = handle_message_send(
        db,
        access,
        {"client_message_id": client_message_id, "body": "Bonjour cabinet"},
    )
    conflict = handle_message_send(
        db,
        access,
        {"client_message_id": client_message_id, "body": "Texte différent"},
    )

    assert first.status == "ACCEPTED"
    assert second.status == "ACCEPTED"
    assert first.response["message"]["message_id"] == second.response["message"]["message_id"]
    assert conflict.status == "REJECTED"
    assert conflict.response["code"] == "CLIENT_MESSAGE_CONFLICT"
    assert db.query(PatientCompanionMessage).filter(
        PatientCompanionMessage.access_id == access.id
    ).count() == 1


def test_pc08_cross_access_cursor_is_rejected(db, dentiste):
    patient = _patient(db, dentiste, "CURSOR")
    _identity_a, access_a = _access(db, dentiste, patient, "SELF")
    _identity_b, access_b = _access(db, dentiste, patient, "GUARDIAN")

    sent = handle_message_send(
        db,
        access_a,
        {"client_message_id": str(uuid.uuid4()), "body": "A"},
    )
    db.commit()
    cursor = sent.response["message"]["message_id"]

    result = handle_message_sync(db, access_b, {"before_message_id": cursor})
    assert result.status == "REJECTED"
    assert result.response["code"] == "MESSAGE_CURSOR_NOT_FOUND"


def test_pc08_received_and_read_are_explicit_truth_boundaries(db, dentiste):
    patient = _patient(db, dentiste, "RECEIPT")
    _identity, access = _access(db, dentiste, patient, "SELF")
    row = PatientCompanionMessage(
        access_id=access.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        client_message_id=str(uuid.uuid4()),
        sender_kind="STAFF",
        sender_user_id=dentiste.id,
        body="Votre contrôle est prêt à être planifié.",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    sync = handle_message_sync(db, access, {})
    assert sync.status == "ACCEPTED"
    assert sync.response["items"][0]["patient_received_at"] is None
    assert sync.response["items"][0]["patient_read_at"] is None

    received = handle_message_received(db, access, {"message_ids": [row.public_id]})
    assert received.status == "ACCEPTED"
    db.commit()
    db.refresh(row)
    assert row.patient_received_at is not None
    assert row.patient_read_at is None

    read = handle_message_read(db, access, {"message_ids": [row.public_id]})
    assert read.status == "ACCEPTED"
    db.commit()
    db.refresh(row)
    assert row.patient_received_at is not None
    assert row.patient_read_at is not None


def test_pc08_patient_rate_limit_is_persistent_and_retry_does_not_double_count(db, dentiste):
    patient = _patient(db, dentiste, "RATE")
    _identity, access = _access(db, dentiste, patient, "SELF")
    now = datetime.utcnow()
    for index in range(PC08_PATIENT_SENDS_PER_HOUR):
        db.add(PatientCompanionMessage(
            access_id=access.id,
            employer_id=dentiste.id,
            patient_id=patient.id,
            client_message_id=str(uuid.uuid4()),
            sender_kind="PATIENT",
            body=f"m{index}",
            created_at=now - timedelta(minutes=1),
        ))
    db.commit()

    blocked = handle_message_send(
        db,
        access,
        {"client_message_id": str(uuid.uuid4()), "body": "Encore un"},
    )
    assert blocked.status == "REJECTED"
    assert blocked.response["code"] == "MESSAGE_RATE_LIMITED"

    existing = db.query(PatientCompanionMessage).filter(
        PatientCompanionMessage.access_id == access.id
    ).first()
    replay = handle_message_send(
        db,
        access,
        {"client_message_id": existing.client_message_id, "body": existing.body},
    )
    assert replay.status == "ACCEPTED"
    assert db.query(PatientCompanionMessage).filter(
        PatientCompanionMessage.access_id == access.id
    ).count() == PC08_PATIENT_SENDS_PER_HOUR


def test_pc08_body_limit_is_utf8_bytes_not_characters(db, dentiste):
    patient = _patient(db, dentiste, "BODY")
    _identity, access = _access(db, dentiste, patient, "SELF")
    body = "é" * (PC08_MAX_BODY_BYTES // 2 + 1)

    result = handle_message_send(
        db,
        access,
        {"client_message_id": str(uuid.uuid4()), "body": body},
    )
    assert result.status == "REJECTED"
    assert result.response["code"] == "MESSAGE_BODY_TOO_LARGE"
    assert db.query(PatientCompanionMessage).count() == 0


def test_pc08_staff_send_is_scoped_and_staff_read_is_explicit(db, dentiste):
    patient = _patient(db, dentiste, "STAFF")
    _identity, access = _access(db, dentiste, patient, "SELF")

    response = Response()
    created = staff_send_message(
        patient.id,
        StaffMessageCreate(
            access_id=access.public_id,
            client_message_id=str(uuid.uuid4()),
            body="Bonjour depuis le cabinet",
        ),
        response,
        db,
        dentiste,
    )
    assert created["message"]["sender_kind"] == "STAFF"
    assert created["message"]["patient_received_at"] is None
    assert created["message"]["patient_read_at"] is None

    patient_message = PatientCompanionMessage(
        access_id=access.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        client_message_id=str(uuid.uuid4()),
        sender_kind="PATIENT",
        body="Merci",
    )
    db.add(patient_message)
    db.commit()
    db.refresh(patient_message)

    marked = staff_mark_messages_read(
        patient.id,
        StaffMessageRead(
            access_id=access.public_id,
            message_ids=[patient_message.public_id],
        ),
        Response(),
        db,
        dentiste,
    )
    assert marked["status"] == "read"
    db.refresh(patient_message)
    assert patient_message.staff_read_at is not None
    assert patient_message.staff_read_by_user_id == dentiste.id


def test_pc08_staff_cannot_send_to_access_of_another_patient(db, dentiste):
    patient_a = _patient(db, dentiste, "A")
    patient_b = _patient(db, dentiste, "B")
    _identity, access_b = _access(db, dentiste, patient_b, "SELF")

    try:
        staff_send_message(
            patient_a.id,
            StaffMessageCreate(
                access_id=access_b.public_id,
                client_message_id=str(uuid.uuid4()),
                body="Doit échouer",
            ),
            Response(),
            db,
            dentiste,
        )
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("cross-patient access unexpectedly accepted")


def _protect_remote(raw: bytes) -> bytes:
    return b"pc08-test-protected:" + raw


def _unprotect_remote(raw: bytes) -> bytes:
    return raw.removeprefix(b"pc08-test-protected:")


def test_pc08_remote_registry_dispatches_message_sync_through_real_crypto(db, dentiste):
    patient = _patient(db, dentiste, "REMOTE")
    _identity, access = _access(db, dentiste, patient, "SELF")
    db.add(PatientCompanionMessage(
        access_id=access.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        client_message_id=str(uuid.uuid4()),
        sender_kind="STAFF",
        sender_user_id=dentiste.id,
        body="Message chiffré de test",
    ))
    patient_sig_private, patient_sig_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
    patient_enc_private, patient_enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
    keyset, cabinet_sig, cabinet_enc = enroll_remote_keyset(
        db,
        access=access,
        patient_signing_kid=patient_sig_public["kid"],
        patient_signing_public_jwk=patient_sig_public,
        patient_encryption_kid=patient_enc_public["kid"],
        patient_encryption_public_jwk=patient_enc_public,
        protect=_protect_remote,
    )
    db.commit()

    now = datetime.now(timezone.utc)
    request = RelayInnerMessage(
        message_id=uuid.uuid4(),
        access_id=uuid.UUID(access.public_id),
        sent_at=now,
        expires_at=now + timedelta(minutes=10),
        idempotency_key=uuid.uuid4(),
        operation="message.sync",
        payload={},
    )
    token = sign_and_encrypt(
        request.model_dump(mode="json"),
        sender_signing_private_jwk=patient_sig_private,
        recipient_encryption_public_jwk=json.loads(cabinet_enc.public_jwk_json),
        sender_signing_kid=keyset.patient_signing_kid,
        recipient_encryption_kid=keyset.cabinet_encryption_kid,
    )
    ack_token = process_remote_envelope(
        db,
        access=access,
        keyset=keyset,
        compact_jwe=token,
        unprotect=_unprotect_remote,
    )
    ack = decrypt_and_verify(
        ack_token,
        recipient_encryption_private_jwk=patient_enc_private,
        sender_signing_public_jwk=json.loads(cabinet_sig.public_jwk_json),
        expected_sender_signing_kid=keyset.cabinet_signing_kid,
        expected_recipient_encryption_kid=keyset.patient_encryption_kid,
    )
    assert ack["payload"]["status"] == "ACCEPTED"
    assert ack["payload"]["result"]["code"] == "MESSAGE_SYNC"
    assert ack["payload"]["result"]["items"][0]["body"] == "Message chiffré de test"


def test_pc08_twenty_max_messages_fit_real_jose_relay_envelope():
    cabinet_sig_private, cabinet_sig_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
    _patient_enc_private, patient_enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
    now = datetime.now(timezone.utc)
    messages = [
        {
            "message_id": str(uuid.uuid4()),
            "client_message_id": str(uuid.uuid4()),
            "sender_kind": "STAFF",
            "body": "x" * PC08_MAX_BODY_BYTES,
            "created_at": now.isoformat(),
            "staff_read_at": None,
            "patient_received_at": None,
            "patient_read_at": None,
        }
        for _ in range(20)
    ]
    ack = RelayInnerMessage(
        message_id=uuid.uuid4(),
        access_id=uuid.uuid4(),
        sent_at=now,
        expires_at=now + timedelta(minutes=10),
        idempotency_key=uuid.uuid4(),
        operation="command.result",
        payload={
            "request_message_id": str(uuid.uuid4()),
            "request_operation": "message.sync",
            "status": "ACCEPTED",
            "result": {
                "code": "MESSAGE_SYNC",
                "items": messages,
                "before_cursor": messages[0]["message_id"],
                "has_more": True,
                "limit": 20,
            },
        },
    )
    blob = sign_and_encrypt(
        ack.model_dump(mode="json"),
        sender_signing_private_jwk=cabinet_sig_private,
        recipient_encryption_public_jwk=patient_enc_public,
        sender_signing_kid=cabinet_sig_public["kid"],
        recipient_encryption_kid=patient_enc_public["kid"],
    )
    assert len(blob.encode("utf-8")) < RELAY_MAX_BLOB_BYTES


def test_pc08_staff_send_fails_closed_after_access_revocation(db, dentiste):
    patient = _patient(db, dentiste, "REVOKED")
    _identity, access = _access(db, dentiste, patient, "SELF")
    access.revoked_at = datetime.utcnow()
    db.commit()

    try:
        staff_send_message(
            patient.id,
            StaffMessageCreate(
                access_id=access.public_id,
                client_message_id=str(uuid.uuid4()),
                body="Ne doit pas partir",
            ),
            Response(),
            db,
            dentiste,
        )
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("revoked Patient Companion access unexpectedly accepted")


def test_pc08_shared_rate_limiter_keeps_default_but_accepts_custom_ceiling(monkeypatch):
    monkeypatch.setattr(rate_limit_module, "_attempts", {})
    monkeypatch.setattr(rate_limit_module, "_loaded", True)
    monkeypatch.setattr(rate_limit_module, "_save", lambda: None)

    request = Request({
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
        "query_string": b"",
    })
    rate_limit_module.check_rate_limit(request, scope="pc08-test", max_attempts=2)
    rate_limit_module.check_rate_limit(request, scope="pc08-test", max_attempts=2)
    try:
        rate_limit_module.check_rate_limit(request, scope="pc08-test", max_attempts=2)
    except HTTPException as exc:
        assert exc.status_code == 429
        assert "Retry-After" in exc.headers
    else:
        raise AssertionError("custom PC-08 rate limit did not fail closed")

    # Existing callers retain the repository default contract.
    assert rate_limit_module.MAX_ATTEMPTS == 5
    assert rate_limit_module.LIMIT_WINDOW == 600
