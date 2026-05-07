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

@prescription_router.get("/habits/suggest")
def get_medication_habits(q: str = "", db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return prescription_service.get_personalized_suggestions(db, current_user.id, q)

@prescription_router.get("/habits/details")
def get_medication_habit_details(med_name: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return prescription_service.get_medication_details(db, current_user.id, med_name)

@prescription_router.get("/habits/presets")
def get_prescription_presets(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return prescription_service.get_doctor_presets(db, current_user.id)

@prescription_router.post("/habits/record")
def record_medication_habit(req: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    med_name = req.get("medication_name")
    dosage = req.get("dosage")
    posologie = req.get("posologie")
    if not med_name:
        raise HTTPException(status_code=400, detail="Nom du médicament manquant")
    prescription_service.record_medication_usage(db, current_user.id, med_name, dosage, posologie)
    return {"status": "success"}

@prescription_router.post("/habits/record-batch")
def record_medication_habits_batch(req: List[dict], db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    for item in req:
        med_name = item.get("medication_name")
        dosage = item.get("dosage")
        posologie = item.get("posologie")
        if med_name:
            prescription_service.record_medication_usage(db, current_user.id, med_name, dosage, posologie)
    return {"status": "success"}

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

from backend.services.prescription_agentic_service import prescription_agentic

# --- AGENTIC PRESCRIPTION (V2.0) ---

@prescription_router.get("/agentic/assessment/{patient_id}")
async def get_clinical_assessment(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """
    Étape 1 : Agent Chercheur.
    Analyse le dossier et les actes prévus pour générer un bilan scientifique.
    """
    # Récupérer les actes récents ou prévus
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    rdvs = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id, 
        models.Appointment.datetime_start >= today
    ).all()
    act_names = [r.motif for r in rdvs if r.motif]
    if not act_names:
        # Fallback sur les derniers actes réalisés si pas de RDV aujourd'hui
        last_actes = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).order_by(models.Acte.date_debut.desc()).limit(3).all()
        act_names = [a.libelle for a in last_actes]

    return prescription_agentic.generate_clinical_assessment(db, patient_id, act_names, doctor_id=current_user.id)

@prescription_router.post("/agentic/design")
async def design_agentic_plan(req: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """
    Étape 2 : Agent Architecte.
    Transforme le bilan en plan de traitement concret (Noms commerciaux Maroc).
    """
    assessment = req.get("assessment")
    patient_context = req.get("patient_context")
    if not assessment or not patient_context:
        raise HTTPException(status_code=400, detail="Bilan ou contexte patient manquant")
        
    return prescription_agentic.design_treatment_plan(assessment, patient_context)

@prescription_router.post("/preferences")
async def save_prescription_preference(req: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """
    Enregistre une habitude de prescription pour le médecin actuel.
    """
    act_code = req.get("act_code")
    drugs = req.get("drugs")
    if not act_code or not drugs:
        raise HTTPException(status_code=400, detail="Données de préférence incomplètes")
        
    prescription_service.learn_habit(db, current_user.id, act_code, drugs)
    return {"status": "success", "message": "Habitude enregistrée avec succès"}
