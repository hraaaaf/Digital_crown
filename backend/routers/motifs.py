from __future__ import annotations

from uuid import uuid4
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import get_current_user, require_permission

router = APIRouter()

Urgency = Literal["urgence", "normal", "planifié"]
ALLOWED_CATEGORY_IDS = {
    "DOULEUR", "URGENCE", "PARODONTAL", "ESTHETIQUE", "CONSERVATRICE",
    "PROTHESE", "ORTHODONTIE", "IMPLANTOLOGIE", "PREVENTION", "CABINET",
}


class CabinetMotifCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    category_id: str = Field(default="CABINET", min_length=1, max_length=64)
    urgency: Urgency = "normal"

    def normalized_category(self) -> str:
        category = self.category_id.strip().upper() or "CABINET"
        if category not in ALLOWED_CATEGORY_IDS:
            raise HTTPException(status_code=422, detail="Catégorie de motif invalide.")
        return category


class CabinetMotifUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    category_id: str | None = Field(default=None, min_length=1, max_length=64)
    urgency: Urgency | None = None


def _payload(row: models.CabinetMotif) -> dict:
    return {
        "id": row.public_id,
        "label": row.label,
        "category_id": row.category_id,
        "urgency": row.urgency,
        "is_active": row.is_active,
        "source": "cabinet",
    }


def _tenant_id(user: models.User) -> int:
    return user.get_employer_id()


def _find_owned(db: Session, public_id: str, tenant_id: int) -> models.CabinetMotif | None:
    return (
        db.query(models.CabinetMotif)
        .filter(
            models.CabinetMotif.public_id == public_id,
            models.CabinetMotif.employer_id == tenant_id,
        )
        .first()
    )


def _assert_unique_label(db: Session, tenant_id: int, label: str, *, exclude_id: int | None = None) -> None:
    clean = label.strip()
    query = db.query(models.CabinetMotif).filter(
        models.CabinetMotif.employer_id == tenant_id,
        func.lower(models.CabinetMotif.label) == clean.lower(),
        models.CabinetMotif.is_active.is_(True),
    )
    if exclude_id is not None:
        query = query.filter(models.CabinetMotif.id != exclude_id)
    if query.first() is not None:
        raise HTTPException(status_code=409, detail="Ce motif existe déjà dans le cabinet.")


@router.get("")
@router.get("/")
def list_cabinet_motifs(
    include_inactive: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.CabinetMotif).filter(
        models.CabinetMotif.employer_id == _tenant_id(current_user),
    )
    if not include_inactive:
        query = query.filter(models.CabinetMotif.is_active.is_(True))
    rows = query.order_by(models.CabinetMotif.label.asc()).all()
    return [_payload(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_cabinet_motif(
    body: CabinetMotifCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("settings")),
):
    tenant_id = _tenant_id(current_user)
    label = body.label.strip()
    _assert_unique_label(db, tenant_id, label)
    row = models.CabinetMotif(
        public_id=f"cm_{uuid4().hex}",
        employer_id=tenant_id,
        label=label,
        category_id=body.normalized_category(),
        urgency=body.urgency,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _payload(row)


@router.put("/{public_id}")
def update_cabinet_motif(
    public_id: str,
    body: CabinetMotifUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("settings")),
):
    tenant_id = _tenant_id(current_user)
    row = _find_owned(db, public_id, tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Motif introuvable.")

    if body.label is not None:
        label = body.label.strip()
        _assert_unique_label(db, tenant_id, label, exclude_id=row.id)
        row.label = label
    if body.category_id is not None:
        category = body.category_id.strip().upper() or "CABINET"
        if category not in ALLOWED_CATEGORY_IDS:
            raise HTTPException(status_code=422, detail="Catégorie de motif invalide.")
        row.category_id = category
    if body.urgency is not None:
        row.urgency = body.urgency

    db.commit()
    db.refresh(row)
    return _payload(row)


@router.post("/{public_id}/deactivate")
def deactivate_cabinet_motif(
    public_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("settings")),
):
    row = _find_owned(db, public_id, _tenant_id(current_user))
    if row is None:
        raise HTTPException(status_code=404, detail="Motif introuvable.")
    row.is_active = False
    db.commit()
    db.refresh(row)
    return _payload(row)
