"""Atomic claim / pending transitions for a stored bot action.

The /bot/execute caller MUST keep the claim uncommitted until its business
write and final executed status can be committed in the SAME transaction.
PostgreSQL holds the affected row lock until then. A crash before commit
rolls both operations back to pending; a committed executed action is final.
Older durable 'executing' rows from pre-upgrade runs still need reconciliation.
"""

from datetime import datetime


def claim_pending_action(db, action_model, action_id: str, user_id: int,
                         employer_id: int, now: datetime) -> bool:
    """One conditional SQL UPDATE. PostgreSQL serializes concurrent claims."""
    updated = db.query(action_model).filter(
        action_model.id == action_id,
        action_model.user_id == user_id,
        action_model.employer_id == employer_id,
        action_model.status == "pending",
        action_model.expires_at > now,
    ).update({"status": "executing"}, synchronize_session=False)
    return updated == 1


def transition_pending_action(
    db, action_model, action_id: str, user_id: int, employer_id: int,
    *, new_status: str, now: datetime, expired: bool = False,
) -> bool:
    """Atomic pending-only cancel/expiry, sharing the claim's tenant/owner fence.

    A stale caller must never overwrite `executing` (or a final status).
    Cancel requires an unexpired pending row. Expiry requires expired pending.
    The caller commits a successful transition; on failure it rolls back.
    """
    if new_status not in {"cancelled", "expired"} or (new_status == "expired") != expired:
        raise ValueError("Unsupported pending-action transition")
    query = db.query(action_model).filter(
        action_model.id == action_id,
        action_model.user_id == user_id,
        action_model.employer_id == employer_id,
        action_model.status == "pending",
    )
    if expired:
        query = query.filter(action_model.expires_at <= now)
    else:
        query = query.filter(action_model.expires_at > now)
    return query.update({"status": new_status}, synchronize_session=False) == 1
