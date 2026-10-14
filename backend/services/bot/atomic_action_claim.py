"""Atomic claim of a stored action, independent of the action's business logic.

The caller MUST commit the successful claim before invoking a side-effecting
dispatcher, and must not blindly retry an 'executing' action after a crash.
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
