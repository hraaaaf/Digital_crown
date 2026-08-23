from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import get_current_user, is_superadmin_user
from backend.services.license_service import LicenseService

router = APIRouter()


def _canonical_cabinet(db: Session, current_user: models.User) -> tuple[models.CabinetConfig, models.User, str]:
    employer_id = current_user.get_employer_id()
    config = (
        db.query(models.CabinetConfig)
        .filter(models.CabinetConfig.owner_id == employer_id)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non configuré.")

    owner = db.query(models.User).filter(models.User.id == config.owner_id).first()
    if not owner:
        raise HTTPException(status_code=409, detail="Propriétaire du cabinet introuvable.")

    clinic_id = str(config.clinic_id or config.public_id or "").strip()
    if not clinic_id:
        raise HTTPException(status_code=409, detail="Identité de licence du cabinet introuvable.")

    return config, owner, clinic_id


@router.post("/recheck-license")
async def recheck_license(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Revalide la licence du cabinet authentifié sans identifiant d'environnement."""
    if current_user.role != models.UserRole.ADMIN and not is_superadmin_user(current_user):
        raise HTTPException(status_code=403, detail="Non autorisé.")

    _, owner, clinic_id = _canonical_cabinet(db, current_user)
    result = await LicenseService().validate_license_with_expiry(clinic_id)
    if result.get("active") is None:
        raise HTTPException(
            status_code=503,
            detail="Service de licence indisponible. État local conservé.",
        )

    license_ok = bool(result.get("active"))
    owner.is_licensed = license_ok
    owner.license_expires_at = result.get("expiration_date") if license_ok else None
    db.commit()

    # The middleware cache lives in backend.main. This import is deliberately
    # runtime-only: the endpoint can only execute after main finished importing.
    try:
        from backend.main import invalidate_license_cache
        invalidate_license_cache(owner.email)
    except Exception:
        # SQLite is already the source of truth; cache TTL is only 60s. Do not
        # turn a successful server validation into an error because cache
        # invalidation itself failed.
        pass

    request.app.state.license_ok = license_ok
    if not license_ok:
        raise HTTPException(status_code=402, detail="La licence est toujours invalide.")

    return {
        "message": "Licence validée avec succès. Application déverrouillée.",
        "clinic_id": clinic_id,
        "source": result.get("source"),
    }
