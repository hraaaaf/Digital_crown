from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Literal

from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionCabinetRemoteKey,
    PatientCompanionRemoteKeyset,
)
from backend.services.patient_companion_key_protection import (
    unprotect_os_bound,
)
from backend.services.patient_companion_remote_crypto import (
    decrypt_and_verify,
    sign_and_encrypt,
)
from backend.services.patient_companion_remote_keys import load_cabinet_private_jwk
from backend.services.patient_companion_remote_receipts import (
    RemoteCommandBusy,
    RemoteReplayDetected,
    claim_remote_command,
    complete_remote_command,
    receipt_response,
)
from relay.contract import RelayInnerMessage

RemoteOutcome = Literal["ACCEPTED", "REJECTED"]


@dataclass(frozen=True)
class RemoteDomainResult:
    status: RemoteOutcome
    response: dict


RemoteDomainHandler = Callable[[Session, PatientCompanionAccess, dict], RemoteDomainResult]


class RemoteTransportRejected(ValueError):
    pass


def _public_jwk(raw: str) -> dict:
    value = json.loads(raw)
    if not isinstance(value, dict) or "d" in value:
        raise RemoteTransportRejected("invalid pinned patient public key")
    return value


def _cabinet_key(
    db: Session,
    *,
    employer_id: int,
    kid: str,
    key_use: str,
) -> PatientCompanionCabinetRemoteKey:
    row = (
        db.query(PatientCompanionCabinetRemoteKey)
        .filter(
            PatientCompanionCabinetRemoteKey.employer_id == employer_id,
            PatientCompanionCabinetRemoteKey.kid == kid,
            PatientCompanionCabinetRemoteKey.key_use == key_use,
            PatientCompanionCabinetRemoteKey.revoked_at.is_(None),
            PatientCompanionCabinetRemoteKey.status.in_(["ACTIVE", "RETIRED"]),
        )
        .first()
    )
    if row is None:
        raise RemoteTransportRejected("cabinet remote key unavailable or revoked")
    return row


def _ack_payload(
    message: RelayInnerMessage,
    *,
    status: RemoteOutcome,
    response: dict,
) -> RelayInnerMessage:
    now = datetime.now(timezone.utc)
    return RelayInnerMessage(
        message_id=uuid.uuid4(),
        access_id=message.access_id,
        sent_at=now,
        expires_at=now + timedelta(minutes=15),
        idempotency_key=message.idempotency_key,
        operation="command.result",
        payload={
            "request_message_id": str(message.message_id),
            "request_operation": message.operation,
            "status": status,
            "result": response,
        },
    )


def process_remote_envelope(
    db: Session,
    *,
    access: PatientCompanionAccess,
    keyset: PatientCompanionRemoteKeyset,
    compact_jwe: str,
    handlers: dict[str, RemoteDomainHandler] | None = None,
    unprotect=unprotect_os_bound,
) -> str:
    """Verify one patient command, execute exactly one allow-listed domain handler,
    commit its result with the replay ledger, then return a cabinet-signed encrypted ack.
    """

    if handlers is None:
        from backend.services.patient_companion_agenda import PC02_REMOTE_HANDLERS
        handlers = PC02_REMOTE_HANDLERS

    if access.revoked_at is not None:
        raise RemoteTransportRejected("Patient Companion access revoked")
    if keyset.access_id != access.id or keyset.status != "ACTIVE" or keyset.revoked_at is not None:
        raise RemoteTransportRejected("remote keyset is not active for this access")

    cabinet_encryption = _cabinet_key(
        db,
        employer_id=access.employer_id,
        kid=keyset.cabinet_encryption_kid,
        key_use="enc",
    )
    cabinet_signing = _cabinet_key(
        db,
        employer_id=access.employer_id,
        kid=keyset.cabinet_signing_kid,
        key_use="sig",
    )
    encryption_private = load_cabinet_private_jwk(cabinet_encryption, unprotect=unprotect)
    signing_private = load_cabinet_private_jwk(cabinet_signing, unprotect=unprotect)

    decoded = decrypt_and_verify(
        compact_jwe,
        recipient_encryption_private_jwk=encryption_private,
        sender_signing_public_jwk=_public_jwk(keyset.patient_signing_public_jwk_json),
        expected_sender_signing_kid=keyset.patient_signing_kid,
        expected_recipient_encryption_kid=keyset.cabinet_encryption_kid,
    )
    try:
        message = RelayInnerMessage.model_validate(decoded)
        message.assert_fresh()
    except Exception as exc:
        raise RemoteTransportRejected("remote application envelope invalid or expired") from exc

    try:
        claim = claim_remote_command(db, access=access, message=message)
    except (RemoteReplayDetected, RemoteCommandBusy):
        raise

    if claim.kind == "idempotent_result":
        stored = receipt_response(claim.receipt)
        ack = _ack_payload(
            message,
            status=stored["status"],
            response=stored["response"],
        )
    else:
        handler = handlers.get(message.operation)
        if handler is None:
            result = RemoteDomainResult(
                status="REJECTED",
                response={"code": "UNSUPPORTED_OPERATION"},
            )
        else:
            try:
                result = handler(db, access, message.payload)
            except Exception:
                db.rollback()
                raise
            if result.status not in {"ACCEPTED", "REJECTED"}:
                db.rollback()
                raise RemoteTransportRejected("domain handler returned invalid status")

        complete_remote_command(
            claim.receipt,
            status=result.status,
            response=result.response,
        )
        ack = _ack_payload(
            message,
            status=result.status,
            response=result.response,
        )
        # The claim, domain mutation and receipt completion are one transaction.
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    return sign_and_encrypt(
        ack.model_dump(mode="json"),
        sender_signing_private_jwk=signing_private,
        recipient_encryption_public_jwk=_public_jwk(keyset.patient_encryption_public_jwk_json),
        sender_signing_kid=keyset.cabinet_signing_kid,
        recipient_encryption_kid=keyset.patient_encryption_kid,
    )
