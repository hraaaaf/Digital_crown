from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import os

from backend import models, schemas, database
from backend.routers.auth import get_current_user

router = APIRouter(tags=["Patients"])

# --- HELPERS ---

def check_duplicate_patient(db: Session, nom: str, prenom: str, date_naissance: datetime, exclude_id: int = None) -> models.Patient:
    query = db.query(models.Patient).filter(
        func.lower(models.Patient.nom) == nom.lower().strip(),
        func.lower(models.Patient.prenom) == prenom.lower().strip(),
        models.Patient.date_naissance == date_naissance
    )
    if exclude_id:
        query = query.filter(models.Patient.id != exclude_id)
    return query.first()

def generate_next_dossier_number(db: Session) -> str:
    last_patient = db.query(models.Patient).order_by(models.Patient.id.desc()).first()
    if last_patient and last_patient.numero_dossier:
        try:
            last_num = int(last_patient.numero_dossier.split('-')[1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = db.query(models.Patient).count() + 1
    else:
        next_num = 1
    return f"P-{next_num:06d}"

# --- ROUTES CRUD ---

@router.get("/next-dossier-number")
def get_next_dossier_number(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return {"next_number": generate_next_dossier_number(db)}

@router.get("/", response_model=List[schemas.PatientOut])
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Patient).offset(skip).limit(limit).all()

@router.post("/", response_model=schemas.PatientOut)
def create_patient(patient: schemas.PatientBase, force_create: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    existing = check_duplicate_patient(db, patient.nom, patient.prenom, patient.date_naissance)
    if existing and not force_create:
        raise HTTPException(status_code=409, detail={"message": "Doublon détecté", "existing_patient": {"id": existing.id}})
    
    patient_data = patient.model_dump() if hasattr(patient, 'model_dump') else patient.dict()
    patient_data['nom'] = patient_data['nom'].upper().strip()
    patient_data['prenom'] = patient_data['prenom'].capitalize().strip()
    if not patient_data.get('numero_dossier'):
        patient_data['numero_dossier'] = generate_next_dossier_number(db)
    
    db_patient = models.Patient(**patient_data)
    db.add(db_patient); db.flush()
    db.add(models.DossierClinique(patient_id=db_patient.id, is_ortho_active=False))
    db.commit(); db.refresh(db_patient)
    return db_patient

@router.get("/{patient_id}", response_model=schemas.PatientOut)
def read_patient(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable")
    return patient

# --- CLINICAL INTELLIGENCE ---

@router.get("/{patient_id}/documents")
def get_patient_documents(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable")

    # 1. BDD
    docs = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        models.DocumentArchive.is_latest_version == True
    ).order_by(models.DocumentArchive.created_at.desc()).all()
    
    results = []
    for doc in docs:
        results.append({
            "id": str(doc.id), "name": doc.original_filename, "type": doc.document_type.value,
            "date": doc.created_at.strftime("%d/%m/%Y"), "url": f"static/{doc.file_path.split('static/')[-1]}",
            "clinical_data": doc.clinical_data, "timestamp": doc.created_at.timestamp()
        })
        
    # 2. Legacy
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    p_folder = f"{patient.id}_{patient.nom.upper()}_{patient.prenom.capitalize()}"
    legacy_dir = os.path.join(static_dir, "patients", p_folder, "Documents")
    
    if os.path.exists(legacy_dir):
        for f in os.listdir(legacy_dir):
            if f.endswith(".pdf"):
                results.append({
                    "id": f"legacy:{patient_id}:{f}", "name": f, "type": "LEGACY",
                    "date": "Ancien", "url": f"static/patients/{p_folder}/Documents/{f}",
                    "timestamp": os.path.getmtime(os.path.join(legacy_dir, f))
                })
    results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return results

@router.get("/{patient_id}/appointment-intel")
def get_patient_intel(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Logique originale restaurée
    devis = db.query(models.DocumentArchive).filter(models.DocumentArchive.patient_id == patient_id, models.DocumentArchive.document_type == models.DocumentType.DEVIS).all()
    return {
        "suggestion": "Suite de traitement" if devis else "Consultation",
        "duration": 45 if devis else 30,
        "has_active_plan": bool(devis)
    }

@router.get("/{patient_id}/analyses", response_model=List[schemas.CephaloAnalysisOut])
def get_patient_analyses(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).all()

# --- CLINICAL INTELLIGENCE V2.0 ---

@router.get("/{patient_id}/ai-summary")
def get_patient_ai_summary(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Module 2 — Résumé Flash Patient (P0)."""
    from backend.services.clinical_intelligence import clinical_intel
    return clinical_intel.get_patient_summary(db, patient_id)

@router.get("/{patient_id}/ai-diagnostic")
def get_patient_ai_diagnostic(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Module 3 — Panneau Conseil Clinique (P2)."""
    from backend.services.clinical_intelligence import clinical_intel
    return clinical_intel.get_full_diagnostic(db, patient_id)
