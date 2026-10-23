"""CB-02 source-only guided French preview API.

Opt-in twice, authenticated, tenant-bound, read-only and never executable.
No legacy bot action dispatcher or pending action is called. No durable draft
state or patient data can be supplied as 'verified' by a browser.
"""
from dataclasses import asdict
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.routers.auth import get_current_user, has_permission
from backend.services.bot.guided_nlu_cb02 import parse_guided_french
from backend.services.bot.patient_selector import lookup_patient_candidates
from backend.routers.bot_workflows import cabinet_day_context

router = APIRouter(tags=["bot-cb02-guided-experimental"])

INTENT_PERMISSION = {
    "AGENDA_READ": ("agenda",),
    "PATIENT_LOOKUP": ("patients",),
    "RDV_PREPARE": ("agenda", "patients"),
}


class CB02GuidedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    utterance: str = Field(..., min_length=1, max_length=160)
    # A choice is not trusted: it is matched again against the original name
    # and tenant-filtered live candidates inside THIS request.
    chosen_patient_id: Optional[int] = Field(None, gt=0)


def _candidate(patient):
    return {
        "id": patient.id, "nom": patient.nom, "prenom": patient.prenom,
        "numero_dossier": patient.numero_dossier,
    }


@router.post("/guided/preview")
def guided_nlu_preview(
    req: CB02GuidedRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # 404 even for an authenticated user when the experiment is disabled.
    if not (
        settings.CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED
        and settings.CROWN_BOT_GUIDED_NLU_ENABLED
    ):
        raise HTTPException(status_code=404, detail="Not found")

    owner = user.get_employer_id()
    if not isinstance(owner, int) or owner <= 0:
        raise HTTPException(status_code=403, detail="Accès refusé.")
    if not isinstance(user.id, int) or user.id <= 0:
        raise HTTPException(status_code=403, detail="Accès refusé.")

    # Server, not client, owns the clinic-local day and binding.
    day = date.fromisoformat(cabinet_day_context()["day"])
    result = parse_guided_french(
        req.utterance, cabinet_today=day,
        principal_scope=f"{owner}:{user.id}",
    )
    if req.chosen_patient_id is not None and (
        result.intent not in ("PATIENT_LOOKUP", "RDV_PREPARE")
        or "patient" not in result.fields or result.status == "refused"
    ):
        raise HTTPException(status_code=422, detail="Sélection invalide.")

    permissions = INTENT_PERMISSION.get(result.intent)
    if permissions is None:
        # No interpretations, patient lookup or clinical information given.
        return {"status": "refused", "intent": None, "fields": {},
                "message": result.reason or "Demande non reconnue.",
                "proposal": None, "executable": False}

    if not all(has_permission(user, permission) for permission in permissions):
        raise HTTPException(status_code=403, detail="Accès refusé.")

    if result.status == "refused":
        return {"status": "refused", "intent": result.intent, "fields": {},
                "message": result.reason or "Demande refusée.",
                "proposal": None, "executable": False}

    payload = {
        "status": result.status,
        "intent": result.intent,
        # Do not leak employer/user IDs or the raw utterance.
        "fields": dict(result.fields),
        "message": (result.question or (
            "Syntaxe comprise ; contrôles serveur obligatoires."
            if result.status == "requires_server_authorization"
            else "Aperçu uniquement : aucun rendez-vous enregistré."
        )),
        "proposal": None, "executable": False,
    }
    patient_slot = result.fields.get("patient")
    if patient_slot is None:
        if req.chosen_patient_id is not None:
            raise HTTPException(status_code=422, detail="Sélection invalide.")
        return payload

    # No client-provided patient entity is trusted. All candidates are scoped
    # to the current authenticated principal's employer and non-deleted rows.
    selector = patient_slot["value"]
    if selector.startswith("name:"):
        selector = selector[5:]
    elif selector.startswith("dossier:"):
        selector = selector
    elif selector.startswith("id:"):
        selector = selector
    else:
        raise HTTPException(status_code=422, detail="Sélecteur invalide.")

    matches, truncated = lookup_patient_candidates(
        db, employer_id=owner, selector=selector
    )
    if not matches:
        # Foreign, unknown or soft-deleted ID have the SAME denial.
        raise HTTPException(status_code=404, detail="Patient introuvable.")
    if truncated:
        payload["status"] = "clarification"
        payload["message"] = "Plusieurs correspondances. Précisez le numéro de dossier."
        payload["fields"].pop("patient", None)
        return payload

    if req.chosen_patient_id is not None:
        matched = [p for p in matches if p.id == req.chosen_patient_id]
        if not matched:
            raise HTTPException(status_code=409, detail="Sélection obsolète.")
        patient = matched[0]
    elif len(matches) > 1:
        payload["status"] = "disambiguation"
        payload["message"] = "Choisissez un dossier du cabinet."
        payload["candidates"] = [_candidate(p) for p in matches]
        # Mark this identity as unverified until fresh explicit choice.
        return payload
    else:
        patient = matches[0]

    payload["patient"] = _candidate(patient)
    payload["fields"]["patient"] = {
        "value": f"id:{patient.id}",
        "source": "server_verified",
        "rule": "LIVE_EMPLOYER_AND_DELETION_FILTER",
    }
    if result.intent == "PATIENT_LOOKUP":
        payload["status"] = "read"
        payload["message"] = "Dossier du cabinet identifié par le serveur."
    # RDV_PREPARE stays only a draft / clarification; never an action.
    # A persisted draft, execution UUID or cabinet booking is impossible here.
    return payload
