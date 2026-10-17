from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionRemoteReceipt,
)
from relay.contract import RelayInnerMessage


class RemoteReplayDetected(ValueError):
    pass


class RemoteCommandBusy(ValueError):
    pass


@dataclass(frozen=True)
class RemoteCommandClaim:
    kind: Literal["new", "idempotent_result"]
    receipt: PatientCompanionRemoteReceipt


def _json(value: dict) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _intent_sha256(message: RelayInnerMessage) -> str:
    """Bind one idempotency key to the operation and canonical JSON payload.

    Transport-level message_id, sent_at and expires_at vary on a legitimate
    retry, but are not part of the clinical request intent.
    """
    canonical = json.dumps(
        {"operation": message.operation, "payload": message.payload},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def claim_remote_command(
    db: Session,
    *,
    access: PatientCompanionAccess,
    message: RelayInnerMessage,
    now: datetime | None = None,
) -> RemoteCommandClaim:
    message.assert_fresh(now=now)

    if str(message.access_id) != access.public_id:
        raise ValueError("remote message access does not match authenticated access")
    if access.revoked_at is not None:
        raise ValueError("remote access is revoked")

    receipt = PatientCompanionRemoteReceipt(
        access_id=access.id,
        message_id=str(message.message_id),
        idempotency_key=str(message.idempotency_key),
        operation=message.operation,
        intent_sha256=_intent_sha256(message),
        status="PROCESSING",
    )

    try:
        with db.begin_nested():
            db.add(receipt)
            db.flush()
        return RemoteCommandClaim(kind="new", receipt=receipt)
    except IntegrityError:
        # SAVEPOINT rollback preserves the surrounding transaction so we can
        # safely inspect the already-recorded message/idempotency key.
        pass

    same_message = (
        db.query(PatientCompanionRemoteReceipt)
        .filter(
            PatientCompanionRemoteReceipt.access_id == access.id,
            PatientCompanionRemoteReceipt.message_id == str(message.message_id),
        )
        .first()
    )
    if same_message is not None:
        raise RemoteReplayDetected("duplicate remote message_id")

    same_intent = (
        db.query(PatientCompanionRemoteReceipt)
        .filter(
            PatientCompanionRemoteReceipt.access_id == access.id,
            PatientCompanionRemoteReceipt.idempotency_key == str(message.idempotency_key),
        )
        .first()
    )
    if same_intent is None:
        raise RuntimeError("remote idempotency constraint conflict without matching receipt")
    if same_intent.operation != message.operation:
        raise RemoteReplayDetected("idempotency key reused for a different operation")
    if same_intent.intent_sha256 is None:
        # No reliable request fingerprint exists for a pre-upgrade receipt.
        # Fail closed; never guess or return an old clinical ACK as new.
        raise RemoteReplayDetected("legacy remote command intent unverifiable")
    if not hmac.compare_digest(same_intent.intent_sha256, _intent_sha256(message)):
        raise RemoteReplayDetected("idempotency key reused for a different request intent")
    if same_intent.status == "PROCESSING":
        raise RemoteCommandBusy("remote command with this idempotency key is already processing")
    return RemoteCommandClaim(kind="idempotent_result", receipt=same_intent)


def complete_remote_command(
    receipt: PatientCompanionRemoteReceipt,
    *,
    status: Literal["ACCEPTED", "REJECTED"],
    response: dict,
) -> None:
    if receipt.status != "PROCESSING":
        raise ValueError("remote command receipt is already completed")
    receipt.status = status
    receipt.response_json = _json(response)
    receipt.completed_at = datetime.utcnow()


def receipt_response(receipt: PatientCompanionRemoteReceipt) -> dict:
    if receipt.status == "PROCESSING":
        raise ValueError("remote command result is not complete")
    payload = {}
    if receipt.response_json:
        value = json.loads(receipt.response_json)
        if not isinstance(value, dict):
            raise ValueError("stored remote command response must be an object")
        payload = value
    return {
        "status": receipt.status,
        "response": payload,
    }
