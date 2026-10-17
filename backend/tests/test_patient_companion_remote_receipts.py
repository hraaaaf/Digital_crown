from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.services.patient_companion_remote_receipts import (
    RemoteCommandBusy,
    RemoteReplayDetected,
    claim_remote_command,
    complete_remote_command,
    receipt_response,
)
from relay.contract import RelayInnerMessage


def _access(db, owner):
    patient = models.Patient(
        numero_dossier=f"PCRCP-{uuid.uuid4().hex[:8]}",
        nom="Remote",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=owner.id,
    )
    identity = PatientCompanionIdentity(
        provider="local_bridge",
        subject=f"device:{uuid.uuid4()}",
    )
    db.add_all([patient, identity])
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=owner.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    return access


def _message(access, *, message_id=None, idempotency_key=None, operation="appointment.request"):
    now = datetime.now(timezone.utc)
    return RelayInnerMessage(
        message_id=message_id or uuid.uuid4(),
        access_id=uuid.UUID(access.public_id),
        sent_at=now,
        expires_at=now + timedelta(minutes=10),
        idempotency_key=idempotency_key or uuid.uuid4(),
        operation=operation,
        payload={"slot_ref": "opaque-test-slot"},
    )


def test_remote_receipt_rejects_message_replay_and_reuses_completed_idempotent_result(db, dentiste):
    access = _access(db, dentiste)
    idem = uuid.uuid4()
    original = _message(access, idempotency_key=idem)

    claim = claim_remote_command(db, access=access, message=original)
    assert claim.kind == "new"
    complete_remote_command(claim.receipt, status="ACCEPTED", response={"result": "accepted"})
    db.commit()

    with pytest.raises(RemoteReplayDetected, match="message_id"):
        claim_remote_command(db, access=access, message=original)

    retry = claim_remote_command(
        db,
        access=access,
        message=_message(access, idempotency_key=idem),
    )
    assert retry.kind == "idempotent_result"
    assert receipt_response(retry.receipt) == {
        "status": "ACCEPTED",
        "response": {"result": "accepted"},
    }


def test_remote_receipt_rejects_idempotency_reuse_for_other_operation(db, dentiste):
    access = _access(db, dentiste)
    idem = uuid.uuid4()
    first = claim_remote_command(db, access=access, message=_message(access, idempotency_key=idem))
    complete_remote_command(first.receipt, status="REJECTED", response={"reason": "conflict"})
    db.commit()

    with pytest.raises(RemoteReplayDetected, match="different operation"):
        claim_remote_command(
            db,
            access=access,
            message=_message(access, idempotency_key=idem, operation="questionnaire.submit"),
        )


def test_remote_receipt_rejects_parallel_duplicate_intent(db, dentiste):
    access = _access(db, dentiste)
    idem = uuid.uuid4()
    first = claim_remote_command(db, access=access, message=_message(access, idempotency_key=idem))
    db.commit()
    assert first.receipt.status == "PROCESSING"

    with pytest.raises(RemoteCommandBusy, match="already processing"):
        claim_remote_command(db, access=access, message=_message(access, idempotency_key=idem))


def test_remote_receipt_rejects_changed_payload_for_same_idempotency_key(db, dentiste):
    access = _access(db, dentiste)
    idem = uuid.uuid4()
    original = _message(access, idempotency_key=idem, operation="agenda.create")
    original.payload = {"slot_ref": "slot-A"}
    first = claim_remote_command(db, access=access, message=original)
    assert len(first.receipt.intent_sha256) == 64
    complete_remote_command(first.receipt, status="ACCEPTED", response={"slot": "slot-A"})
    db.commit()

    changed = _message(access, idempotency_key=idem, operation="agenda.create")
    changed.payload = {"slot_ref": "slot-B"}
    with pytest.raises(RemoteReplayDetected, match="different request intent"):
        claim_remote_command(db, access=access, message=changed)

    same_payload = _message(access, idempotency_key=idem, operation="agenda.create")
    same_payload.payload = {"slot_ref": "slot-A"}
    replay = claim_remote_command(db, access=access, message=same_payload)
    assert replay.kind == "idempotent_result"
    assert receipt_response(replay.receipt)["response"] == {"slot": "slot-A"}


def test_remote_receipt_canonical_payload_order_preserves_legitimate_retries(db, dentiste):
    access = _access(db, dentiste)
    idem = uuid.uuid4()
    first = _message(access, idempotency_key=idem, operation="agenda.reschedule")
    first.payload = {"appointment_ref": "old", "slot_ref": "new"}
    receipt = claim_remote_command(db, access=access, message=first).receipt
    complete_remote_command(receipt, status="ACCEPTED", response={"status": "moved"})
    db.commit()

    retry = _message(access, idempotency_key=idem, operation="agenda.reschedule")
    retry.payload = {"slot_ref": "new", "appointment_ref": "old"}
    assert claim_remote_command(db, access=access, message=retry).kind == "idempotent_result"


def test_remote_receipt_legacy_without_intent_digest_fails_closed(db, dentiste):
    access = _access(db, dentiste)
    idem = uuid.uuid4()
    first = _message(access, idempotency_key=idem, operation="agenda.create")
    row = claim_remote_command(db, access=access, message=first).receipt
    complete_remote_command(row, status="ACCEPTED", response={"status": "confirmed"})
    # Simulate a row predating the additive revision. Its payload was never
    # stored and cannot be safely reconstructed from its ACK.
    row.intent_sha256 = None
    db.commit()

    retry = _message(access, idempotency_key=idem, operation="agenda.create")
    with pytest.raises(RemoteReplayDetected, match="unverifiable"):
        claim_remote_command(db, access=access, message=retry)
    assert row.intent_sha256 is None


def test_remote_receipt_rejects_revoked_access(db, dentiste):
    access = _access(db, dentiste)
    access.revoked_at = datetime.utcnow()
    db.commit()

    with pytest.raises(ValueError, match="revoked"):
        claim_remote_command(db, access=access, message=_message(access))
