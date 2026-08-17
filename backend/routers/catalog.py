from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List

from backend import models
from backend.database import get_db
from backend.schemas.catalog import (
    SpecialtyCreate, SpecialtyUpdate, SpecialtyOut,
    PathologyCreate, PathologyUpdate, PathologyOut,
    CatalogActCreate, CatalogActUpdate, CatalogActOut,
)
from backend.routers.auth import get_current_user
from backend.services import cabinet_catalog_store as store

router = APIRouter(tags=["Catalog (Specialties, Acts, Pathologies)"])


def _tenant_id(user: models.User) -> int:
    return user.get_employer_id()


def _conflict(db: Session, label: str, exc: IntegrityError):
    db.rollback()
    raise HTTPException(status_code=409, detail=f"{label} already exists for this cabinet") from exc


@router.get("/specialties", response_model=List[SpecialtyOut])
def get_specialties(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return store.list_catalog(db, _tenant_id(current_user))


@router.post("/specialties", response_model=SpecialtyOut, status_code=status.HTTP_201_CREATED)
def create_specialty(
    payload: SpecialtyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        row = store.create_specialty(db, _tenant_id(current_user), payload.model_dump())
    except IntegrityError as exc:
        _conflict(db, "Specialty", exc)
    return {**row, "pathologies": [], "acts": []}


@router.put("/specialties/{specialty_id}", response_model=SpecialtyOut)
def update_specialty(
    specialty_id: int,
    payload: SpecialtyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tenant = _tenant_id(current_user)
    try:
        row = store.update_owned(db, store.specialties, specialty_id, tenant, payload.model_dump(exclude_unset=True))
    except IntegrityError as exc:
        _conflict(db, "Specialty", exc)
    if not row:
        raise HTTPException(status_code=404, detail="Specialty not found")
    current = next((item for item in store.list_catalog(db, tenant) if item["id"] == specialty_id), None)
    return current or {**row, "pathologies": [], "acts": []}


@router.post("/specialties/{specialty_id}/pathologies", response_model=PathologyOut, status_code=status.HTTP_201_CREATED)
def create_pathology(
    specialty_id: int,
    payload: PathologyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        row = store.create_pathology(db, _tenant_id(current_user), specialty_id, payload.model_dump())
    except IntegrityError as exc:
        _conflict(db, "Pathology", exc)
    if not row:
        raise HTTPException(status_code=404, detail="Specialty not found")
    return row


@router.put("/pathologies/{pathology_id}", response_model=PathologyOut)
def update_pathology(
    pathology_id: int,
    payload: PathologyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        row = store.update_owned(
            db, store.pathologies, pathology_id, _tenant_id(current_user), payload.model_dump(exclude_unset=True)
        )
    except IntegrityError as exc:
        _conflict(db, "Pathology", exc)
    if not row:
        raise HTTPException(status_code=404, detail="Pathology not found")
    return row


@router.post("/specialties/{specialty_id}/acts", response_model=CatalogActOut, status_code=status.HTTP_201_CREATED)
def create_act(
    specialty_id: int,
    payload: CatalogActCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        row = store.create_act(db, _tenant_id(current_user), specialty_id, payload.model_dump())
    except IntegrityError as exc:
        _conflict(db, "Act", exc)
    if not row:
        raise HTTPException(status_code=404, detail="Specialty not found")
    return row


@router.put("/acts/{act_id}", response_model=CatalogActOut)
def update_act(
    act_id: int,
    payload: CatalogActUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        row = store.update_owned(db, store.acts, act_id, _tenant_id(current_user), payload.model_dump(exclude_unset=True))
    except IntegrityError as exc:
        _conflict(db, "Act", exc)
    if not row:
        raise HTTPException(status_code=404, detail="Act not found")
    return row
