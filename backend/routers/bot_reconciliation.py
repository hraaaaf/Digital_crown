"""Read-only reconciliation inventory for pre-upgrade durable executing actions.

A durable 'executing' from old builds does not prove whether the business
write committed. NEVER convert it to pending, replay it, or auto-mark success.
This endpoint reveals no payload or patient PII and is scoped to action owner.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db
from backend.routers.auth import get_current_user

router = APIRouter(tags=["bot"])


@router.get("/execute/reconciliation")
def list_bot_actions_requiring_reconciliation(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Only this authenticated user's actions from their active cabinet."""
    actions = (
        db.query(models.BotPendingAction)
        .filter(
            models.BotPendingAction.user_id == current_user.id,
            models.BotPendingAction.employer_id == current_user.get_employer_id(),
            models.BotPendingAction.status == "executing",
        )
        .order_by(models.BotPendingAction.created_at.asc())
        .limit(limit)
        .all()
    )
    return {
        "status": "manual_reconciliation_required" if actions else "clear",
        "safe_to_retry": False,
        "automatic_reset": False,
        "actions": [
            {
                "action_id": action.id,
                "action_type": action.action_type,
                "created_at": action.created_at,
                "expired_at": action.expires_at,
                "status": "executing",
                "required_action": "verify_business_state_before_any_manual_resolution",
            }
            for action in actions
        ],
    }
