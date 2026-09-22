from datetime import datetime, timedelta, timezone
import uuid

import pytest

from relay.contract import RelayInnerMessage


def _message(sent_at, expires_at):
    return RelayInnerMessage(
        message_id=uuid.uuid4(),
        access_id=uuid.uuid4(),
        sent_at=sent_at,
        expires_at=expires_at,
        idempotency_key=uuid.uuid4(),
        operation="appointment.request",
        payload={},
    )


def test_remote_command_ttl_is_bounded_to_fifteen_minutes():
    now = datetime.now(timezone.utc)
    msg = _message(now, now + timedelta(minutes=16))
    with pytest.raises(ValueError, match="TTL"):
        msg.assert_fresh(now=now)


def test_remote_command_rejects_excessive_future_clock_skew():
    now = datetime.now(timezone.utc)
    msg = _message(now + timedelta(minutes=6), now + timedelta(minutes=10))
    with pytest.raises(ValueError, match="future"):
        msg.assert_fresh(now=now)
