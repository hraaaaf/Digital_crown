"""
Routes publiques (sans authentification) — landing page, demandes de démo.
"""
import json
import os
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Public"])

_DEMO_REQUESTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "demo_requests.json"
)


def _load_requests() -> list:
    if not os.path.exists(_DEMO_REQUESTS_FILE):
        return []
    try:
        with open(_DEMO_REQUESTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_requests(requests: list) -> None:
    os.makedirs(os.path.dirname(_DEMO_REQUESTS_FILE), exist_ok=True)
    with open(_DEMO_REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)


class DemoRequestIn(BaseModel):
    nom: str
    email: EmailStr
    cabinet: str
    telephone: str = ""
    message: str = ""


@router.post("/demo-request", summary="Soumettre une demande de démo")
def submit_demo_request(payload: DemoRequestIn):
    requests = _load_requests()
    entry = {
        "id": len(requests) + 1,
        "nom": payload.nom.strip(),
        "email": payload.email,
        "cabinet": payload.cabinet.strip(),
        "telephone": payload.telephone.strip(),
        "message": payload.message.strip(),
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "NEW",
    }
    requests.append(entry)
    _save_requests(requests)

    # Notification email non-bloquante
    try:
        from backend.services.email_service import email_service
        body = (
            f"Nouvelle demande de démo DigitalCrown\n\n"
            f"Nom : {entry['nom']}\n"
            f"Email : {entry['email']}\n"
            f"Cabinet : {entry['cabinet']}\n"
            f"Téléphone : {entry['telephone']}\n"
            f"Message : {entry['message']}\n"
            f"Date : {entry['submitted_at']}"
        )
        email_service.send_email(
            to_email="contact@digitalcrown.dz",
            subject=f"[DÉMO] {entry['nom']} — {entry['cabinet']}",
            body=body,
        )
    except Exception:
        pass  # Email optionnel — on ne bloque pas si non configuré

    return {"success": True, "message": "Votre demande a bien été reçue. Nous vous contacterons sous 24h."}


@router.get("/demo-requests", summary="Lister les demandes (super-admin)")
def list_demo_requests(secret: str = ""):
    """Protégé par un simple secret en query param pour le super-admin."""
    expected = os.getenv("SUPERADMIN_SECRET", "")
    if not expected or secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    return _load_requests()
