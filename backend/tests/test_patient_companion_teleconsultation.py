from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionIdentity,
    PatientCompanionTeleconsultSession,
    PatientCompanionTeleconsultSignal,
)
from backend.services.patient_companion_teleconsultation import (
    PC09_MAX_SIGNAL_BYTES,
    PC09_SIGNAL_SYNC_LIMIT,
    add_signal,
    handle_teleconsult_join,
    handle_teleconsult_sync,
    mark_connected,
    mark_joined,
    purge_signals,
    sync_signals,
)
from backend.services.patient_companion_remote_crypto import generate_p256_keypair, sign_and_encrypt
from relay.contract import RelayInnerMessage, RELAY_MAX_BLOB_BYTES


def _patient(db, dentiste, suffix: str):
    patient = models.Patient(
        numero_dossier=f"PC09-{suffix}-{uuid.uuid4().hex[:6]}",
        nom=f"Teleconsult-{suffix}",
        prenom="Aya",
        date_naissance=datetime(2012, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    return patient


def _access(db, dentiste, patient, relationship: str = "SELF"):
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


def _session(db, dentiste, patient, access, *, minutes: int = 60):
    row = PatientCompanionTeleconsultSession(
        access_id=access.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        created_by_user_id=dentiste.id,
        state="WAITING_PATIENT",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=minutes),
        staff_joined_at=datetime.utcnow(),
    )
    db.add(row)
    db.flush()
    return row


def test_pc09_connected_requires_both_real_peer_reports(db, dentiste):
    patient = _patient(db, dentiste, "CONNECTED")
    _identity, access = _access(db, dentiste, patient)
    row = _session(db, dentiste, patient, access)

    mark_joined(row, "PATIENT")
    assert row.state == "NEGOTIATING"

    mark_connected(row, "PATIENT")
    assert row.state == "NEGOTIATING"
    assert row.connected_at is None
    assert row.patient_connected_at is not None
    assert row.staff_connected_at is None

    mark_connected(row, "STAFF")
    assert row.state == "CONNECTED"
    assert row.connected_at is not None
    assert row.patient_connected_at is not None
    assert row.staff_connected_at is not None


def test_pc09_connected_before_both_joined_fails_closed(db, dentiste):
    patient = _patient(db, dentiste, "EARLY")
    _identity, access = _access(db, dentiste, patient)
    row = _session(db, dentiste, patient, access)
    row.staff_joined_at = None

    with pytest.raises(ValueError, match="SESSION_NOT_NEGOTIATING"):
        mark_connected(row, "PATIENT")


def test_pc09_session_is_access_scoped(db, dentiste):
    patient = _patient(db, dentiste, "SCOPE")
    _identity_a, access_a = _access(db, dentiste, patient, "SELF")
    _identity_b, access_b = _access(db, dentiste, patient, "PARENT")
    row = _session(db, dentiste, patient, access_a)

    result = handle_teleconsult_join(db, access_b, {"session_id": row.public_id})
    assert result.status == "REJECTED"
    assert result.response["code"] == "SESSION_NOT_FOUND"


def test_pc09_expired_session_cannot_join(db, dentiste):
    patient = _patient(db, dentiste, "EXPIRED")
    _identity, access = _access(db, dentiste, patient)
    row = _session(db, dentiste, patient, access, minutes=-1)

    result = handle_teleconsult_join(db, access, {"session_id": row.public_id})
    assert result.status == "REJECTED"
    assert result.response["code"] == "SESSION_EXPIRED"
    assert row.state == "EXPIRED"
    assert row.ended_at is not None


def test_pc09_signal_idempotency_and_conflict_detection(db, dentiste):
    patient = _patient(db, dentiste, "SIGNAL")
    _identity, access = _access(db, dentiste, patient)
    row = _session(db, dentiste, patient, access)
    mark_joined(row, "PATIENT")
    client_id = str(uuid.uuid4())

    first = add_signal(
        db, row,
        sender_kind="PATIENT",
        sender_user_id=None,
        client_signal_id=client_id,
        signal_type="offer",
        payload={"type": "offer", "sdp": "v=0"},
    )
    second = add_signal(
        db, row,
        sender_kind="PATIENT",
        sender_user_id=None,
        client_signal_id=client_id,
        signal_type="offer",
        payload={"type": "offer", "sdp": "v=0"},
    )
    assert first.id == second.id

    with pytest.raises(ValueError, match="CLIENT_SIGNAL_CONFLICT"):
        add_signal(
            db, row,
            sender_kind="PATIENT",
            sender_user_id=None,
            client_signal_id=client_id,
            signal_type="offer",
            payload={"type": "offer", "sdp": "different"},
        )

    assert db.query(PatientCompanionTeleconsultSignal).filter(
        PatientCompanionTeleconsultSignal.session_id == row.id
    ).count() == 1


def test_pc09_signal_sync_returns_only_peer_signals(db, dentiste):
    patient = _patient(db, dentiste, "SYNC")
    _identity, access = _access(db, dentiste, patient)
    row = _session(db, dentiste, patient, access)
    mark_joined(row, "PATIENT")

    add_signal(
        db, row,
        sender_kind="PATIENT",
        sender_user_id=None,
        client_signal_id=str(uuid.uuid4()),
        signal_type="offer",
        payload={"type": "offer", "sdp": "patient"},
    )
    staff_signal = add_signal(
        db, row,
        sender_kind="STAFF",
        sender_user_id=dentiste.id,
        client_signal_id=str(uuid.uuid4()),
        signal_type="answer",
        payload={"type": "answer", "sdp": "staff"},
    )

    patient_view = sync_signals(db, row, recipient_kind="PATIENT", after_signal_id=None)
    staff_view = sync_signals(db, row, recipient_kind="STAFF", after_signal_id=None)
    assert [item.id for item in patient_view] == [staff_signal.id]
    assert len(staff_view) == 1
    assert staff_view[0].sender_kind == "PATIENT"


def test_pc09_remote_sync_never_claims_connected_from_signaling_only(db, dentiste):
    patient = _patient(db, dentiste, "TRUTH")
    _identity, access = _access(db, dentiste, patient)
    row = _session(db, dentiste, patient, access)
    mark_joined(row, "PATIENT")
    add_signal(
        db, row,
        sender_kind="STAFF",
        sender_user_id=dentiste.id,
        client_signal_id=str(uuid.uuid4()),
        signal_type="offer",
        payload={"type": "offer", "sdp": "v=0"},
    )

    result = handle_teleconsult_sync(db, access, {"session_id": row.public_id})
    assert result.status == "ACCEPTED"
    assert result.response["session"]["state"] == "NEGOTIATING"
    assert result.response["session"]["connected_at"] is None
    assert result.response["signals"][0]["signal_type"] == "offer"


def test_pc09_max_signal_batch_fits_real_jose_relay_envelope():
    cabinet_sig_private, cabinet_sig_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
    _patient_enc_private, patient_enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
    now = datetime.now(timezone.utc)
    signals = [
        {
            "signal_id": str(uuid.uuid4()),
            "client_signal_id": str(uuid.uuid4()),
            "sender_kind": "STAFF",
            "signal_type": "offer" if index == 0 else "ice",
            "payload": {"sdp": "x" * (PC09_MAX_SIGNAL_BYTES - 1024)},
            "created_at": now.isoformat(),
        }
        for index in range(PC09_SIGNAL_SYNC_LIMIT)
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
            "request_operation": "teleconsult.sync",
            "status": "ACCEPTED",
            "result": {
                "code": "SESSION_SYNC",
                "session": {
                    "session_id": str(uuid.uuid4()),
                    "state": "NEGOTIATING",
                    "created_at": now.isoformat(),
                    "expires_at": (now + timedelta(hours=1)).isoformat(),
                    "patient_joined_at": now.isoformat(),
                    "staff_joined_at": now.isoformat(),
                    "connected_at": None,
                    "ended_at": None,
                    "ended_by": None,
                    "failure_code": None,
                },
                "signals": signals,
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


def test_pc09_signaling_is_purged_after_terminal_session(db, dentiste):
    patient = _patient(db, dentiste, "PURGE")
    _identity, access = _access(db, dentiste, patient)
    row = _session(db, dentiste, patient, access)
    mark_joined(row, "PATIENT")
    add_signal(
        db, row,
        sender_kind="PATIENT",
        sender_user_id=None,
        client_signal_id=str(uuid.uuid4()),
        signal_type="offer",
        payload={"type": "offer", "sdp": "v=0"},
    )
    assert db.query(PatientCompanionTeleconsultSignal).filter(
        PatientCompanionTeleconsultSignal.session_id == row.id
    ).count() == 1
    purge_signals(db, row)
    assert db.query(PatientCompanionTeleconsultSignal).filter(
        PatientCompanionTeleconsultSignal.session_id == row.id
    ).count() == 0


def test_pc09_patient_only_join_truthfully_waits_for_staff(db, dentiste):
    patient = _patient(db, dentiste, "WAITSTAFF")
    _identity, access = _access(db, dentiste, patient)
    row = _session(db, dentiste, patient, access)
    row.staff_joined_at = None

    mark_joined(row, "PATIENT")
    assert row.state == "WAITING_STAFF"
    assert row.patient_joined_at is not None
    assert row.staff_joined_at is None
