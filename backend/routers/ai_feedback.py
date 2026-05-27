from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend import database, models
from backend.routers.auth import get_current_user, require_permission

router = APIRouter(tags=["Ghost Hub Feedback"])


class AIFeedbackCreate(BaseModel):
    patient_id: int
    insight_type: str
    insight_content: str
    action: str  # accept | reject | edit | resolved
    corrected_text: Optional[str] = None


@router.post("/feedback")
def submit_feedback(
    payload: AIFeedbackCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """Record a practitioner's reaction to an AI insight."""
    if payload.action not in ("accept", "reject", "edit", "resolved"):
        raise HTTPException(status_code=422, detail="action must be accept, reject, edit, or resolved")

    fb = models.AIFeedback(
        patient_id=payload.patient_id,
        insight_type=payload.insight_type,
        insight_content=payload.insight_content,
        action=payload.action,
        corrected_text=payload.corrected_text,
        employer_id=current_user.employer_id or current_user.id,
    )
    db.add(fb)
    db.commit()
    return {"status": "recorded", "id": fb.id}


@router.get("/feedback/stats")
def get_feedback_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """Return accept/reject rates per insight type for the current employer."""
    emp_id = current_user.employer_id or current_user.id
    rows = (
        db.query(
            models.AIFeedback.insight_type,
            models.AIFeedback.action,
            func.count(models.AIFeedback.id).label("count"),
        )
        .filter(models.AIFeedback.employer_id == emp_id)
        .group_by(models.AIFeedback.insight_type, models.AIFeedback.action)
        .all()
    )

    stats: dict = {}
    for insight_type, action, count in rows:
        if insight_type not in stats:
            stats[insight_type] = {}
        stats[insight_type][action] = count

    return {"stats": stats}
