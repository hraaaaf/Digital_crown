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


def test_remote_receipt_rejects_revoked_access(db, dentiste):
    access = _access(db, dentiste)
    access.revoked_at = datetime.utcnow()
    db.commit()

    with pytest.raises(ValueError, match="revoked"):
        claim_remote_command(db, access=access, message=_message(access))
