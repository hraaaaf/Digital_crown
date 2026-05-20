"""
Routes publiques PWA Mobile — Appairage ZKA.
Aucune authentification JWT requise : le token éphémère est la seule preuve d'identité.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend import models, database

router = APIRouter(tags=["Mobile ZKA"])


class ClaimTokenRequest(BaseModel):
    token: str


@router.post(
    "/claim-token",
    summary="Échanger un token éphémère contre les credentials ZKA",
    description=(
        "Token à usage unique (UUID, TTL 5 min) généré côté desktop. "
        "La masterKey ne transite jamais dans une URL."
    ),
)
def claim_pairing_token(
    body: ClaimTokenRequest,
    db: Session = Depends(database.get_db),
):
    record = (
        db.query(models.ZKAPairingToken)
        .filter(
            models.ZKAPairingToken.token == body.token,
            models.ZKAPairingToken.used_at == None,  # noqa: E711
            models.ZKAPairingToken.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Token invalide, expiré ou déjà utilisé.")

    record.used_at = datetime.utcnow()
    db.commit()

    return {"publicId": record.public_id, "masterKey": record.master_key}
