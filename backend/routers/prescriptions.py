from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend import models, schemas, database
from backend.routers.auth import get_current_user, require_permission
from backend.utils.access_control import assert_patient_access
from backend.services.prescription_service import prescription_service

prescription_router = APIRouter(tags=["Prescriptions"])
actes_router = APIRouter(tags=["Actes Cliniques"])

@prescription_router.get("/search", response_model=List[schemas.MedicationOut])
def search_medications(q: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    return db.query(models.Medication).filter(models.Medication.nom.ilike(f"%{q}%")).order_by(models.Medication.usage_count.desc()).limit(20).all()

@prescription_router.get("/suggest", response_model=List[schemas.ClinicalProtocolOut])
def suggest_protocols(category_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    return db.query(models.ClinicalProtocol).filter(models.ClinicalProtocol.category_id == category_id).all()

@prescription_router.get("/habits/suggest")
def get_medication_habits(q: str = "", db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    return prescription_service.get_personalized_suggestions(db, current_user.id, q)

@prescription_router.get("/habits/details")
def get_medication_habit_details(med_name: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    return prescription_service.get_medication_details(db, current_user.id, med_name)

@prescription_router.get("/habits/presets")
def get_prescription_presets(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    return prescription_service.get_doctor_presets(db, current_user.id)

@prescription_router.post("/habits/record")
def record_medication_habit(req: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    med_name = req.get("medication_name")
    dosage = req.get("dosage")
    posologie = req.get("posologie")
    if not med_name:
        raise HTTPException(status_code=400, detail="Nom du médicament manquant")
    prescription_service.record_medication_usage(db, current_user.id, med_name, dosage, posologie)
    return {"status": "success"}

@prescription_router.post("/habits/record-batch")
def record_medication_habits_batch(req: List[dict], db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    for item in req:
        med_name = item.get("medication_name")
        dosage = item.get("dosage")
        posologie = item.get("posologie")
        if med_name:
            prescription_service.record_medication_usage(db, current_user.id, med_name, dosage, posologie)
    return {"status": "success"}

@prescription_router.post("/safety/check")
def check_prescription_safety(req: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    """
    Vérifie la sécurité d'une ordonnance pour un patient donné.
    """
    patient_id = req.get("patient_id")
    drug_names = req.get("drug_names", [])
    if not patient_id:
        raise HTTPException(status_code=400, detail="ID Patient manquant")
    return prescription_service.check_safety(db, patient_id, drug_names)

@prescription_router.get("/smart-suggest/{patient_id}")
async def get_smart_suggestion(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    assert_patient_access(patient_id, current_user, db)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    rdvs = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id, 
        models.Appointment.datetime_start >= today
    ).all()
    act_names = [r.motif for r in rdvs if r.motif]
    return prescription_service.resolve_smart_prescription(db, patient_id, act_names, doctor_id=current_user.id)

@actes_router.get("/catalog/search", response_model=List[dict])
def search_clinical_acts(q: str = "", db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    from backend.services.accounting_service import accounting_service
    
    if not q.strip():
        # Renvoyer les actes fréquents du médecin fusionnés avec le catalogue par défaut
        frequent = accounting_service.get_frequent_acts(db, current_user.id, limit=20)
        frequent_names = {f["name"].lower() for f in frequent} if frequent else set()
            
        fallback_names = [
            ("Consultation dentaire", 200, "Diagnostic"),
            ("Détartrage et polissage", 400, "Prévention"),
            ("Extraction simple", 300, "Chirurgie"),
            ("Extraction molaire", 450, "Chirurgie"),
            ("Traitement canalaire (Monoradiculaire)", 500, "Endodontie"),
            ("Traitement canalaire (Pluriradiculaire)", 800, "Endodontie"),
            ("Composite 2 faces", 350, "Conservatrice"),
            ("Composite 3 faces", 500, "Conservatrice"),
            ("Couronne céramo-métallique", 2500, "Prothèse"),
            ("Implant dentaire", 6000, "Implantologie"),
        ]
        
        results = frequent if frequent else []
        for i, (name, price, cat) in enumerate(fallback_names):
            if name.lower() not in frequent_names:
                results.append({
                    "id": f"default_{i}",
                    "name": name,
                    "base_price": price,
                    "category": cat,
                    "is_habit": False
                })
        
        return results
        
    return accounting_service.search_acts(db, current_user.id, q)

@actes_router.get("/duration")
def get_act_recommended_duration(q: str = "", current_user: models.User = Depends(get_current_user)):
    from backend.services.habits_engine import habits_engine
    duration = habits_engine.get_recommended_duration(q)
    return {"duration": duration}

@actes_router.post("/catalog/bundles")
def get_act_bundles(req: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """
    Retourne les bundles d'actes recommandés pour une liste d'actes donnés.
    """
    from backend.services.accounting_service import accounting_service
    act_names = req.get("act_names", [])
    return accounting_service.get_smart_bundles(act_names)

@actes_router.get("/brain/summary")
def get_brain_summary(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """
    Retourne une synthèse de tout ce que le système a appris sur le praticien.
    """
    from backend.services.accounting_service import accounting_service
    from backend.services.prescription_service import prescription_service
    
    return {
        "frequent_acts": accounting_service.get_frequent_acts(db, current_user.id, limit=5),
        "frequent_drugs": prescription_service.get_doctor_habits_summary(db, current_user.id),
        "total_knowledge_points": db.query(models.DoctorActHabit).filter(models.DoctorActHabit.doctor_id == current_user.id).count() + 
                                  db.query(models.DoctorMedicationHabit).filter(models.DoctorMedicationHabit.doctor_id == current_user.id).count()
    }

from backend.services.prescription_agentic_service import prescription_agentic

# --- AGENTIC PRESCRIPTION (V2.0) ---

@prescription_router.get("/agentic/assessment/{patient_id}")
async def get_clinical_assessment(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    """
    Étape 1 : Agent Chercheur.
    Analyse le dossier et les actes prévus pour générer un bilan scientifique.
    """
    assert_patient_access(patient_id, current_user, db)
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
async def design_agentic_plan(req: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
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
async def save_prescription_preference(req: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    """
    Enregistre une habitude de prescription pour le médecin actuel.
    """
    act_code = req.get("act_code")
    drugs = req.get("drugs")
    if not act_code or not drugs:
        raise HTTPException(status_code=400, detail="Données de préférence incomplètes")
        
    prescription_service.learn_habit(db, current_user.id, act_code, drugs)
    return {"status": "success", "message": "Habitude enregistrée avec succès"}

@prescription_router.delete("/preferences/{act_code}")
async def delete_prescription_preference(act_code: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    """
    Supprime un preset (habitude de prescription par acte) pour le médecin actuel.
    """
    prescription_service.delete_doctor_preset(db, current_user.id, act_code)
    return {"status": "success", "message": "Preset supprimé avec succès"}

@prescription_router.get("/certif-suggest/{patient_id}")
async def suggest_certificate(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):
    """
    Analyse les actes récents pour suggérer un type de certificat.
    """
    assert_patient_access(patient_id, current_user, db)
    
    # Récupérer l'acte ou le RDV le plus récent (aujourd'hui)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Chercher un acte réalisé aujourd'hui
    last_act = db.query(models.Acte).filter(
        models.Acte.patient_id == patient_id,
        models.Acte.date_debut >= today
    ).order_by(models.Acte.date_debut.desc()).first()
    
    # 2. Chercher un RDV aujourd'hui
    last_rdv = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id,
        models.Appointment.datetime_start >= today
    ).order_by(models.Appointment.datetime_start.desc()).first()
    
    motif_text = (last_act.libelle if last_act else (last_rdv.motif if last_rdv else "")).lower()
    
    suggestion = {
        "type": "Certificat de Présence",
        "days": 1,
        "confidence": "low",
        "reason": "Pas d'acte chirurgical récent détecté."
    }
    
    if any(k in motif_text for k in ["extraction", "chirurgie", "implant", "lambeau", "resection"]):
        suggestion = {
            "type": "Repos Post-Opératoire",
            "days": 3,
            "confidence": "high",
            "reason": f"Suite à l'acte : {motif_text.title()}"
        }
    elif any(k in motif_text for k in ["ortho", "bagues", "appareil", "ajustement"]):
        suggestion = {
            "type": "Suite d'Intervention",
            "days": 1,
            "confidence": "medium",
            "reason": "Suite à un réglage orthodontique."
        }
    elif any(k in motif_text for k in ["examen", "aptitude", "sport"]):
        suggestion = {
            "type": "Certificat d'aptitude",
            "days": 1,
            "confidence": "medium",
            "reason": "Examen clinique réalisé."
        }
        
    return suggestion
