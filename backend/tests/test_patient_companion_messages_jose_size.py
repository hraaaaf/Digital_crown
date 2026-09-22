from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from backend.services.patient_companion_remote_crypto import sign_and_encrypt
from relay.contract import RELAY_MAX_BLOB_BYTES, RelayInnerMessage


def test_pc08_twenty_max_messages_fit_real_jose_relay_ceiling(remote_key_material):
    now = datetime.now(timezone.utc)
    items = [
        {
            "message_id": str(uuid.uuid4()),
            "client_message_id": str(uuid.uuid4()),
            "sender_kind": "STAFF",
            "body": "x" * 4096,
            "created_at": now.isoformat(),
            "staff_read_at": None,
            "patient_received_at": None,
            "patient_read_at": None,
        }
        for _ in range(20)
    ]
    inner = RelayInnerMessage(
        message_id=uuid.uuid4(),
        access_id=uuid.uuid4(),
        sent_at=now,
        expires_at=now + timedelta(minutes=15),
        idempotency_key=uuid.uuid4(),
        operation="command.result",
        payload={
            "request_message_id": str(uuid.uuid4()),
            "request_operation": "message.sync",
            "status": "ACCEPTED",
            "result": {
                "code": "MESSAGE_SYNC",
                "items": items,
                "before_cursor": items[0]["message_id"],
                "has_more": True,
                "limit": 20,
            },
        },
    )
    blob = sign_and_encrypt(
        inner.model_dump(mode="json"),
        sender_signing_private_jwk=remote_key_material["cabinet_signing_private"],
        recipient_encryption_public_jwk=remote_key_material["patient_encryption_public"],
        sender_signing_kid=remote_key_material["cabinet_signing_kid"],
        recipient_encryption_kid=remote_key_material["patient_encryption_kid"],
    )
    assert len(blob.encode("utf-8")) < RELAY_MAX_BLOB_BYTES
