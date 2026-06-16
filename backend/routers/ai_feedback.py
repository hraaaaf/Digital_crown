from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import asyncio

from backend import database, models
from backend.routers.auth import get_current_user, require_permission, require_elite_license
from backend.security import SECRET_KEY, ALGORITHM, token_blacklist

router = APIRouter(
    tags=["Ghost Hub Feedback"]
)


class AIFeedbackCreate(BaseModel):
    patient_id: int
    insight_type: str
    insight_content: str
    action: str  # accept | reject | edit | resolved
    corrected_text: Optional[str] = None


def _get_websocket_user(websocket: WebSocket, db: Session) -> Optional[models.User]:
    token = websocket.cookies.get("access_token") or websocket.query_params.get("token")
    if token and token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")

        if token_type not in ("access", "mobile"):
            return None
        if jti and token_blacklist.is_revoked(jti, db):
            return None

        if token_type == "mobile":
            user_id = int(payload["sub"])
            user = db.query(models.User).filter(models.User.id == user_id).first()
        else:
            email: str = payload.get("sub")
            if email is None:
                return None
            user = db.query(models.User).filter(models.User.email == email).first()
    except (JWTError, ValueError, KeyError):
        return None

    if user is None or not user.is_active:
        return None
    return user


@router.post("/feedback", dependencies=[Depends(require_elite_license)])
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


@router.get("/feedback/stats", dependencies=[Depends(require_elite_license)])
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

# --- GHOST BRAIN V2 - MEMORY ENDPOINTS ---
from backend.services.ghost_memory_service import ghost_memory

@router.get("/ghost-insights", dependencies=[Depends(require_elite_license)])
def get_ghost_insights(
    limit: int = 10,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """
    Récupère les déductions proactives récentes générées par le Ghost Brain V2.
    Affiche une bulle de notification dans l'UI.
    """
    emp_id = current_user.employer_id or current_user.id
    logs = db.query(models.GhostMemoryLog).filter(
        models.GhostMemoryLog.employer_id == emp_id,
        models.GhostMemoryLog.is_read == False
    ).order_by(models.GhostMemoryLog.created_at.desc()).limit(limit).all()
    
    return {
        "unread_count": ghost_memory.get_unread_count(db, emp_id),
        "insights": [
            {
                "id": log.id,
                "patient_id": log.patient_id,
                "insight_type": log.insight_type,
                "content": log.content,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }

@router.post("/ghost-insights/{log_id}/read", dependencies=[Depends(require_elite_license)])
def mark_ghost_insight_read(
    log_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """Marque un insight comme lu par le praticien."""
    emp_id = current_user.employer_id or current_user.id
    log = db.query(models.GhostMemoryLog).filter(
        models.GhostMemoryLog.id == log_id,
        models.GhostMemoryLog.employer_id == emp_id,
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Insight introuvable")
    log.is_read = True
    db.commit()
    return {"status": "read"}


@router.websocket("/ws/ghost-insights/{employer_id}")
async def websocket_ghost_insights(websocket: WebSocket, employer_id: int, db: Session = Depends(database.get_db)):
    """
    Flux WebSocket Temps Réel pour les insights du Ghost Brain.
    Remplace le polling HTTP par un push Server-Side.
    """
    current_user = _get_websocket_user(websocket, db)
    if current_user is None or (current_user.employer_id or current_user.id) != employer_id:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    last_count = -1
    try:
        while True:
            # Server-side micro-polling (ultra léger sur SQLite, évite l'overhead HTTP)
            unread_count = ghost_memory.get_unread_count(db, employer_id)
            if unread_count != last_count:
                logs = db.query(models.GhostMemoryLog).filter(
                    models.GhostMemoryLog.employer_id == employer_id,
                    models.GhostMemoryLog.is_read == False
                ).order_by(models.GhostMemoryLog.created_at.desc()).limit(10).all()
                
                await websocket.send_json({
                    "unread_count": unread_count,
                    "insights": [
                        {
                            "id": log.id,
                            "patient_id": log.patient_id,
                            "insight_type": log.insight_type,
                            "content": log.content,
                            "created_at": log.created_at.isoformat()
                        } for log in logs
                    ]
                })
                last_count = unread_count
            await asyncio.sleep(2)  # Latence max: 2 secondes
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
