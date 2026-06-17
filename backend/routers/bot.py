from fastapi import APIRouter, Depends, HTTPException, Body, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import json
import logging
from backend.services.security.data_sanitizer import data_sanitizer

from backend.database import get_db
from backend import models
from backend.routers.auth import get_current_user, has_permission
from backend.services.audit_service import audit_service
from backend.services.bot.intent_parser import intent_parser as regex_parser, ParsedIntent
from backend.services.bot.llm_parser import llm_parser
from backend.services.bot.action_dispatcher import (
    ActionDispatcher, CONVERSATIONAL_FALLBACK, CONVERSATIONAL_SUGGESTIONS,
)

router = APIRouter(tags=["bot"])
logger = logging.getLogger(__name__)

# On utilise le SLM Parser par défaut, qui bascule (fallback) 
# sur le regex_parser en cas d'erreur ou timeout.
parser = llm_parser
dispatcher = ActionDispatcher()

# En-dessous de ce seuil de confiance (ou si l'intent est UNKNOWN), on demande
# au LLM de désambiguïser. 0.80 = le regex a matché quelque chose mais sans
# certitude → vaut le coup de vérifier. Au-dessus, on fait confiance au regex.
LLM_CONFIDENCE_THRESHOLD = 0.80

INTENT_PERMISSIONS = {
    "QUERY_PATIENT": "patients",
    "SEARCH_PATIENT": "patients",
    "QUERY_AGENDA": "agenda",
    "CREATE_APPOINTMENT": "agenda",
    "QUERY_FINANCE": "accounting",
    "QUERY_STATS": "accounting",
    "QUERY_LAB": "patients",
    "QUERY_ALERTS": "patients",
    "CREATE_PRESCRIPTION": "prescriptions",
    "CREATE_DEVIS": "accounting",
    "CHANGE_STATUS": "agenda",
}

ACTION_PERMISSIONS = {
    "CREATE_APPOINTMENT": "agenda",
    "OPEN_PRESCRIPTION_EDITOR": "prescriptions",
    "OPEN_DEVIS_EDITOR": "accounting",
    "CHANGE_STATUS": "agenda",
}


def require_bot_permission(current_user: models.User, permission: str | None) -> None:
    if permission and not has_permission(current_user, permission):
        raise HTTPException(status_code=403, detail=f"Accès refusé. Permission requise : {permission}.")


# ── Helpers partagés entre /chat et /chat/stream ─────────────────────────────

def _resolve_session(payload: Dict[str, Any], db: Session, current_user: models.User) -> Tuple[str, str, Optional[int]]:
    """
    Résout/crée la session, sauvegarde le message utilisateur, rattache le
    contexte patient (`patient_id` envoyé par le front depuis un dossier patient).
    Retourne (session_id, message, session_patient_id).
    """
    message = payload.get("message", "").strip()
    session_id = payload.get("session_id")
    patient_id = payload.get("patient_id")
    if not message:
        raise HTTPException(status_code=400, detail="Message vide")

    employer_id = current_user.get_employer_id()
    if not session_id:
        title_words = message.split()[:5]
        title = " ".join(title_words) + ("..." if len(message.split()) > 5 else "")
        bot_session = models.BotSession(
            employer_id=employer_id, user_id=current_user.id, title=title, patient_id=patient_id,
        )
        db.add(bot_session)
        db.commit()
        db.refresh(bot_session)
        session_id = bot_session.id
    else:
        bot_session = db.query(models.BotSession).filter(
            models.BotSession.id == session_id,
            models.BotSession.employer_id == employer_id,
            models.BotSession.user_id == current_user.id,
        ).first()
        if not bot_session:
            raise HTTPException(status_code=404, detail="Session introuvable")
        bot_session.updated_at = datetime.now()
        # Rattache le patient si la session n'en avait pas encore
        if patient_id and not bot_session.patient_id:
            bot_session.patient_id = patient_id

    db.add(models.BotMessage(session_id=session_id, sender="user", text=message))
    db.commit()
    return session_id, message, bot_session.patient_id


def _build_context(session_id: str, db: Session) -> List[Dict[str, str]]:
    """Fenêtre de contexte des 4 derniers messages (réponses bot sanitizées)."""
    recent_msgs = (
        db.query(models.BotMessage)
        .filter(models.BotMessage.session_id == session_id)
        .order_by(desc(models.BotMessage.created_at))
        .limit(4)
        .all()
    )
    return [
        {
            "role": m.sender,
            "content": data_sanitizer.sanitize_bot_response(m.text) if m.sender == "bot" else m.text,
        }
        for m in reversed(recent_msgs)
    ]


# Intents pour lesquels un patient de session sert de défaut si aucun n'est cité.
PATIENT_CENTRIC_INTENTS = {"QUERY_PATIENT", "CREATE_PRESCRIPTION", "CREATE_DEVIS", "CHANGE_STATUS"}


def _parse_and_authorize(
    message: str, context_window: List[Dict[str, str]], current_user: models.User,
    session_patient_id: Optional[int] = None,
) -> Tuple[ParsedIntent, bool]:
    """Regex-first puis fallback LLM si peu confiant. Vérifie la permission. Retourne (intent, llm_used)."""
    parsed_intent = regex_parser.parse(message, context=context_window)
    llm_used = False
    if parsed_intent.intent == "UNKNOWN" or parsed_intent.confidence < LLM_CONFIDENCE_THRESHOLD:
        logger.info(
            "Regex peu confiant (intent=%s, conf=%.2f), appel au LLM avec contexte...",
            parsed_intent.intent, parsed_intent.confidence,
        )
        parsed_intent = parser.parse(message, context=context_window)
        llm_used = True

    # Injection du patient de session : si la conversation est ouverte depuis un
    # dossier patient et qu'aucun patient n'est cité, on l'utilise par défaut puis
    # on réévalue la complétude (évite de redemander "quel patient ?").
    if (
        session_patient_id
        and parsed_intent.intent in PATIENT_CENTRIC_INTENTS
        and "patient_id" not in parsed_intent.entities
        and "patient_name" not in parsed_intent.entities
    ):
        parsed_intent.entities["patient_id"] = session_patient_id
        needs, prompt = regex_parser._check_completeness(parsed_intent.intent, parsed_intent.entities)
        parsed_intent.needs_clarification = needs
        parsed_intent.clarification_prompt = prompt

    require_bot_permission(current_user, INTENT_PERMISSIONS.get(parsed_intent.intent))
    return parsed_intent, llm_used


def _store_pending_action(
    session_id: str, pending_action: Dict[str, Any], db: Session, current_user: models.User
) -> str:
    """Stocke une pending_action en DB et retourne son ID (UUID). TTL = 30 min."""
    record = models.BotPendingAction(
        session_id=session_id,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action_type=pending_action.get("type", ""),
        params_json=pending_action.get("params", {}),
        status="pending",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.add(record)
    db.flush()  # genere l'ID sans commit (le commit suit dans _persist_bot_message)
    return record.id


def _persist_bot_message(
    session_id: str, response_dict: Dict[str, Any], llm_used: bool,
    db: Session, current_user: models.User
) -> None:
    pending_action = response_dict.get("pending_action")
    pending_action_id = None

    if pending_action:
        pending_action_id = _store_pending_action(session_id, pending_action, db, current_user)
        # Remplacer l'objet complet par l'ID dans la reponse — le client ne voit que l'ID.
        response_dict["pending_action_id"] = pending_action_id
        # Garder l'objet pour l'affichage du message de confirmation (readonly).
        # Il n'est plus executable directement : seul l'ID est accepte par /execute.

    db.add(models.BotMessage(
        session_id=session_id,
        sender="bot",
        text=response_dict.get("message", ""),
        raw_data={
            "action_type": response_dict.get("action_type"),
            "pending_action": pending_action,       # description display uniquement
            "pending_action_id": pending_action_id, # ID executable
            "suggestions": response_dict.get("suggestions", []),
            "used_llm": llm_used,
        },
    ))
    db.commit()


def _apply_upsell(session_id: str, llm_used: bool, db: Session, response_dict: Dict[str, Any]) -> None:
    """Compte les échanges LLM de la session et active l'upsell au-delà de 3."""
    if not llm_used:
        response_dict["show_upsell"] = False
        return
    all_bot_msgs = db.query(models.BotMessage).filter(
        models.BotMessage.session_id == session_id,
        models.BotMessage.sender == "bot",
    ).all()
    count = sum(1 for m in all_bot_msgs if m.raw_data and m.raw_data.get("used_llm"))
    response_dict["llm_exchange_count"] = count
    response_dict["show_upsell"] = count >= 3

@router.get("/sessions")
async def get_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Récupère la liste des sessions actives (non archivées) de l'utilisateur.
    """
    employer_id = current_user.get_employer_id()
    sessions = db.query(models.BotSession).filter(
        models.BotSession.employer_id == employer_id,
        models.BotSession.user_id == current_user.id,
        models.BotSession.is_archived == False
    ).order_by(desc(models.BotSession.updated_at)).all()
    
    return [
        {
            "id": s.id,
            "title": s.title,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None
        }
        for s in sessions
    ]

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Récupère l'historique complet des messages d'une session.
    """
    employer_id = current_user.get_employer_id()
    session = db.query(models.BotSession).filter(
        models.BotSession.id == session_id,
        models.BotSession.employer_id == employer_id,
        models.BotSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    messages = db.query(models.BotMessage).filter(
        models.BotMessage.session_id == session_id
    ).order_by(models.BotMessage.created_at).all()
    
    return [
        {
            "id": m.id,
            "sender": m.sender,
            "text": m.text,
            "actionType": m.raw_data.get("action_type") if m.raw_data else None,
            "pendingAction": m.raw_data.get("pending_action") if m.raw_data else None,
            "pendingActionId": m.raw_data.get("pending_action_id") if m.raw_data else None,
            "suggestions": m.raw_data.get("suggestions", []) if m.raw_data else [],
            "createdAt": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]

@router.delete("/sessions/{session_id}")
async def archive_session(
    session_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Archive (soft delete) une session.
    """
    employer_id = current_user.get_employer_id()
    session = db.query(models.BotSession).filter(
        models.BotSession.id == session_id,
        models.BotSession.employer_id == employer_id,
        models.BotSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    session.is_archived = True
    db.commit()
    
    return {"status": "success", "message": "Session archivée"}

@router.post("/chat")
async def bot_chat(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Point d'entrée non-streaming de l'assistant Crown Bot (rétrocompat).
    Le frontend utilise désormais /chat/stream.
    """
    session_id, message, session_patient_id = _resolve_session(payload, db, current_user)
    context_window = _build_context(session_id, db)
    parsed_intent, llm_used = _parse_and_authorize(message, context_window, current_user, session_patient_id)

    response_dict = dispatcher.dispatch(parsed_intent, db, current_user).to_dict()

    _persist_bot_message(session_id, response_dict, llm_used, db, current_user)
    _apply_upsell(session_id, llm_used, db, response_dict)
    response_dict["session_id"] = session_id
    return response_dict


def _sse(obj: Dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def bot_chat_stream(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Variante streaming (SSE). Émet :
      - {type:"session", session_id}        une fois, au début
      - {type:"token", content}             0..N (texte conversationnel au fil de l'eau)
      - {type:"final", ...response_dict}     une fois, à la fin (message, suggestions,
                                             pending_action, show_upsell, session_id)
    Les réponses "read"/"write" (DB, instantanées) sont émises en un seul token.
    Seuls GREETING/UNKNOWN sont réellement streamés depuis le LLM.
    """
    # Tout ce qui peut lever une HTTPException (session, permission) se fait AVANT
    # le StreamingResponse — une fois le statut 200 envoyé, on ne peut plus l'annuler.
    session_id, message, session_patient_id = _resolve_session(payload, db, current_user)
    context_window = _build_context(session_id, db)
    parsed_intent, llm_used = _parse_and_authorize(message, context_window, current_user, session_patient_id)

    is_conversational = (
        parsed_intent.intent in ("GREETING", "UNKNOWN")
        and not parsed_intent.needs_clarification
    )

    def event_stream():
        yield _sse({"type": "session", "session_id": session_id})
        nonlocal llm_used

        if is_conversational:
            kind = parsed_intent.intent
            messages_llm, mapping = dispatcher.build_conversational(kind, message)
            collected: List[str] = []
            for piece in data_sanitizer.restore_stream(parser.stream_completion(messages_llm), mapping):
                collected.append(piece)
                yield _sse({"type": "token", "content": piece})

            text = "".join(collected).strip()
            if not text:
                # LLM indisponible → texte de repli, émis en un bloc
                text = CONVERSATIONAL_FALLBACK[kind]
                yield _sse({"type": "token", "content": text})
            # UNKNOWN = vrai raisonnement LLM → compte dans le quota upsell.
            # GREETING reste gratuit (ne pénalise pas un simple "bonjour").
            if kind == "UNKNOWN":
                llm_used = True
            response_dict = {
                "message": text,
                "action_type": "info",
                "pending_action": None,
                "suggestions": CONVERSATIONAL_SUGGESTIONS[kind],
            }
        else:
            response_dict = dispatcher.dispatch(parsed_intent, db, current_user).to_dict()
            yield _sse({"type": "token", "content": response_dict.get("message", "")})

        _persist_bot_message(session_id, response_dict, llm_used, db, current_user)
        _apply_upsell(session_id, llm_used, db, response_dict)
        response_dict["session_id"] = session_id
        yield _sse({"type": "final", **response_dict})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@router.post("/execute")
async def bot_execute(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Execute une action confirmee par l'utilisateur.
    Accepte UNIQUEMENT pending_action_id (UUID stocke cote serveur).
    Le payload complet n'est jamais accepte depuis le client — l'action
    ne peut pas etre forgee, seulement confirmee par ID.
    """
    action_id = payload.get("pending_action_id")
    if not action_id:
        raise HTTPException(status_code=400, detail="pending_action_id manquant.")

    # Recuperation + verification tenant
    employer_id = current_user.get_employer_id()
    record = db.query(models.BotPendingAction).filter(
        models.BotPendingAction.id == action_id,
        models.BotPendingAction.user_id == current_user.id,
        models.BotPendingAction.employer_id == employer_id,
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Action introuvable ou acces refuse.")

    if record.status == "executed":
        raise HTTPException(status_code=409, detail="Cette action a deja ete executee.")

    if record.status == "expired" or record.expires_at < datetime.utcnow():
        record.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="Cette action a expire (> 30 min). Redemandez au Crown Bot.")

    if record.status == "cancelled":
        raise HTTPException(status_code=409, detail="Cette action a ete annulee.")

    action_type = record.action_type

    # Fail-closed : type inconnu ou non autorise -> 403
    permission = ACTION_PERMISSIONS.get(action_type)
    if permission is None:
        raise HTTPException(status_code=403, detail=f"Action non autorisee : {action_type}")
    require_bot_permission(current_user, permission)

    # Audit (S8) — point d'etranglement, toute ecriture LLM est tracee ici.
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="BOT_EXECUTE",
        resource_type=str(action_type),
        resource_id=str(record.params_json.get("patient_id")) if record.params_json.get("patient_id") else None,
        severity="WARNING",
        details=f"Action confirmee via Crown Bot (id={action_id}) : {action_type}",
    )

    # Reconstituer le format attendu par ActionDispatcher.execute()
    pending_action = {"type": action_type, "params": record.params_json}
    response = dispatcher.execute(pending_action, db, current_user)

    # Marquer comme execute
    record.status = "executed"
    record.executed_at = datetime.utcnow()
    db.commit()

    return response.to_dict()


@router.post("/execute/{action_id}/cancel")
async def bot_cancel_action(
    action_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Annule une pending_action non encore executee."""
    record = db.query(models.BotPendingAction).filter(
        models.BotPendingAction.id == action_id,
        models.BotPendingAction.user_id == current_user.id,
        models.BotPendingAction.employer_id == current_user.get_employer_id(),
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Action introuvable.")
    if record.status not in ("pending",):
        raise HTTPException(status_code=409, detail=f"Impossible d'annuler : statut = {record.status}.")
    record.status = "cancelled"
    db.commit()
    return {"status": "cancelled"}
