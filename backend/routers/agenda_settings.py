from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend import models
from backend.database import get_db
from backend.schemas.agenda import (
    CabinetSettingsOut, CabinetSettingsUpdate,
    AgendaExceptionOut, AgendaExceptionCreate
)
from backend.routers.auth import require_permission
from backend.services.holiday_engine import holiday_engine

router = APIRouter(prefix="/agenda", tags=["Agenda"])

@router.get("/settings", response_model=CabinetSettingsOut)
def get_cabinet_settings(db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("agenda"))):
    settings = db.query(models.CabinetSettings).first()
    if not settings:
        settings = models.CabinetSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.put("/settings", response_model=CabinetSettingsOut)
def update_cabinet_settings(settings_update: CabinetSettingsUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("agenda"))):
    settings = db.query(models.CabinetSettings).first()
    if not settings:
        settings = models.CabinetSettings()
        db.add(settings)
    
    for k, v in settings_update.model_dump().items():
        setattr(settings, k, v)
        
    db.commit()
    db.refresh(settings)
    return settings

@router.get("/exceptions", response_model=List[AgendaExceptionOut])
def list_exceptions(db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("agenda"))):
    return db.query(models.AgendaException).all()

@router.post("/exceptions", response_model=AgendaExceptionOut)
def create_exception(exc_in: AgendaExceptionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("agenda"))):
    exc = models.AgendaException(**exc_in.model_dump())
    db.add(exc)
    db.commit()
    db.refresh(exc)
    return exc

@router.delete("/exceptions/{exc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exception(exc_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("agenda"))):
    exc = db.query(models.AgendaException).filter(models.AgendaException.id == exc_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    db.delete(exc)
    db.commit()
    return None

@router.get("/upcoming-holidays")
def get_upcoming_holidays():
    return holiday_engine.get_upcoming_holidays(90)
