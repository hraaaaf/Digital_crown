from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from backend.database import get_db
from backend import models
from backend.routers.auth import get_current_active_user
from backend.services.bot.intent_parser import CrownIntentParser
from backend.services.bot.action_dispatcher import ActionDispatcher

router = APIRouter(prefix="/api/bot", tags=["bot"])
logger = logging.getLogger(__name__)

parser = CrownIntentParser()
dispatcher = ActionDispatcher()

@router.post("/chat")
async def bot_chat(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Point d'entrée de l'assistant Crown Bot.
    Accepte un message texte, l'analyse de façon déterministe, exécute l'action de lecture,
    ou prépare une action d'écriture pour confirmation.
    Optionnellement (Phase SLM), on pourrait reformuler la réponse ici.
    """
    message = payload.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message vide")

    # 1. Parse Intent (100% Deterministic)
    parsed_intent = parser.parse(message)

    # 2. Dispatch Action
    response = dispatcher.dispatch(parsed_intent, db, current_user)

    # 3. (Optional) Reformulation SLM
    # if response.action_type == "read" or response.action_type == "info":
    #    response.message = llm_service.reformulate(response.message)

    return response.to_dict()

@router.post("/execute")
async def bot_execute(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Exécute une action en attente (pending_action) après confirmation utilisateur.
    """
    # En pratique, le frontend peut appeler directement les API classiques 
    # (ex: POST /api/prescriptions) au lieu de passer par ce endpoint.
    # On laisse ce stub au cas où on voudrait centraliser.
    return {"status": "success", "message": "Action exécutée via endpoint métier."}
