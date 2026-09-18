from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend import database, models
from backend.models import AgendaResource
from backend.routers.auth import require_permission
from backend.schemas.agenda_resources import AgendaResourceCreate, AgendaResourceOut, AgendaResourceUpdate

router = APIRouter(prefix="/resources", tags=["Agenda Resources"])


def _tenant_id(user: models.User) -> int:
    return user.get_employer_id()


@router.get("", response_model=list[AgendaResourceOut])
def list_resources(include_inactive: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("agenda"))):
    q = db.query(AgendaResource).filter(AgendaResource.employer_id == _tenant_id(current_user))
    if not include_inactive:
        q = q.filter(AgendaResource.is_active.is_(True))
    return q.order_by(AgendaResource.resource_type.asc(), AgendaResource.name.asc()).all()


@router.post("", response_model=AgendaResourceOut, status_code=201)
def create_resource(payload: AgendaResourceCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("agenda"))):
    resource = AgendaResource(employer_id=_tenant_id(current_user), name=payload.name.strip(), resource_type=payload.resource_type)
    db.add(resource)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Une ressource avec ce nom existe déjà dans ce cabinet")
    db.refresh(resource)
    return resource


@router.patch("/{resource_id}", response_model=AgendaResourceOut)
def update_resource(resource_id: int, payload: AgendaResourceUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("agenda"))):
    resource = db.query(AgendaResource).filter(AgendaResource.id == resource_id, AgendaResource.employer_id == _tenant_id(current_user)).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Ressource agenda introuvable")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    for key, value in data.items():
        setattr(resource, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Une ressource avec ce nom existe déjà dans ce cabinet")
    db.refresh(resource)
    return resource
