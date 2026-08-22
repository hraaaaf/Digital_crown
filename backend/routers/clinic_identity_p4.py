"""P4B practitioner identity routes mounted under the canonical clinics router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.database import get_db
from backend.models_identity_p4 import migrate_identity_columns
from backend.routers.auth import get_current_user, is_superadmin_user
from backend.schemas.clinic_identity_p4 import PractitionerIdentityOut, PractitionerIdentityUpdate

# Existing installations must gain the additive columns before any normal auth query
# attempts to materialize User/CabinetConfig with the expanded mapper. Fresh databases
# do not have the tables yet and are handled later by Base.metadata.create_all.
migrate_identity_columns(database.engine)

router = APIRouter()


def _require_principal_practitioner(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if is_superadmin_user(current_user):
        return current_user
    if current_user.employer_id is not None:
        raise HTTPException(status_code=403, detail="Profil praticien réservé au compte principal.")
    if current_user.role not in (models.UserRole.ADMIN, models.UserRole.DENTISTE):
        raise HTTPException(status_code=403, detail="Profil praticien réservé au compte principal.")
    return current_user


@router.get("/me/practitioner", response_model=PractitionerIdentityOut)
def get_practitioner_identity(
    current_user: models.User = Depends(_require_principal_practitioner),
):
    """Read the canonical practitioner identity owned by the principal User."""
    return current_user


@router.patch("/me/practitioner", response_model=PractitionerIdentityOut)
def update_practitioner_identity(
    update: PractitionerIdentityUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_principal_practitioner),
):
    """Update practitioner-owned fields only; never write CabinetConfig aliases."""
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user
