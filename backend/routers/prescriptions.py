from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend import models, schemas, database
from backend.routers.auth import get_current_user
from backend.services.prescription_service import prescription_service

prescription_router = APIRouter(tags=["Prescriptions"])
actes_router = APIRouter(tags=["Actes Cliniques"])

@prescription_router.get("/search", response_model=List[schemas.MedicationOut])
def search_medications(q: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Medication).filter(models.Medication.nom.ilike(f"%{q}%")).order_by(models.Medication.usage_count.desc()).limit(20).all()

@prescription_router.get("/suggest", response_model=List[schemas.ClinicalProtocolOut])
def suggest_protocols(category_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.ClinicalProtocol).filter(models.ClinicalProtocol.category_id == category_id).all()

@prescription_router.get("/smart-suggest/{patient_id}")
async def get_smart_suggestion(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    rdvs = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id, 
        models.Appointment.datetime_start >= today
    ).all()
    act_names = [r.motif for r in rdvs if r.motif]
    return prescription_service.resolve_smart_prescription(db, patient_id, act_names, doctor_id=current_user.id)

@actes_router.get("/catalog/search", response_model=List[schemas.ClinicalActCatalogOut])
def search_clinical_acts(q: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.ClinicalActCatalog).filter(models.ClinicalActCatalog.name.ilike(f"%{q.strip()}%")).order_by(models.ClinicalActCatalog.usage_count.desc()).limit(20).all()

@prescription_router.post("/preferences")
async def save_prescription_preference(req: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return {"status": "success", "message": "Préférence enregistrée"}
