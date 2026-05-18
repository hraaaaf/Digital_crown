from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime
import os

from backend import models, schemas, database
from backend.routers.auth import get_current_user
from backend.utils.access_control import assert_patient_access

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

def generate_next_dossier_number(db: Session, employer_id: int) -> str:
    last_patient = db.query(models.Patient).filter(models.Patient.employer_id == employer_id).order_by(models.Patient.id.desc()).first()
    if last_patient and last_patient.numero_dossier:
        try:
            last_num = int(last_patient.numero_dossier.split('-')[1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = db.query(models.Patient).filter(models.Patient.employer_id == employer_id).count() + 1
    else:
        next_num = 1
    return f"P-{next_num:06d}"


# --- ROUTES CRUD ---

@router.get("/next-dossier-number")
def get_next_dossier_number(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return {"next_number": generate_next_dossier_number(db, current_user.get_employer_id())}

@router.get("/check-dossier/{numero}")
def check_dossier_availability(numero: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    exists = db.query(models.Patient).filter(models.Patient.numero_dossier == numero).first()
    return {
        "exists": bool(exists),
        "patient_id": exists.id if exists else None,
        "patient_name": f"{exists.nom.upper()} {exists.prenom.capitalize()}" if exists else None
    }

@router.get("/", response_model=List[schemas.PatientOut])
def read_patients(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    user_employer_id = current_user.get_employer_id()
    query = db.query(models.Patient).options(
        joinedload(models.Patient.dossier)
    ).filter(models.Patient.employer_id == user_employer_id)
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Patient.nom.ilike(search_term),
                models.Patient.prenom.ilike(search_term),
                models.Patient.numero_dossier.ilike(search_term)
            )
        )
    return query.offset(skip).limit(limit).all()

from backend.services.audit_service import audit_service

@router.post("/", response_model=schemas.PatientOut)
def create_patient(patient: schemas.PatientBase, force_create: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    existing = check_duplicate_patient(db, patient.nom, patient.prenom, patient.date_naissance)
    if existing and not force_create:
        raise HTTPException(status_code=409, detail={"message": "Doublon détecté", "existing_patient": {"id": existing.id}})
    
    patient_data = patient.model_dump() if hasattr(patient, 'model_dump') else patient.dict()
    patient_data['nom'] = patient_data['nom'].upper().strip()
    patient_data['prenom'] = patient_data['prenom'].capitalize().strip()
    
    employer_id = current_user.get_employer_id()
    patient_data['employer_id'] = employer_id
    
    if not patient_data.get('numero_dossier'):
        patient_data['numero_dossier'] = generate_next_dossier_number(db, employer_id)
    
    db_patient = models.Patient(**patient_data)
    db.add(db_patient); db.flush()
    db.add(models.DossierClinique(patient_id=db_patient.id, is_ortho_active=False))
    
    # Audit log
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="CREATE",
        resource_type="Patient",
        resource_id=str(db_patient.id),
        details=f"Creation du patient {db_patient.nom} {db_patient.prenom} (Dossier: {db_patient.numero_dossier})"
    )
    
    db.commit(); db.refresh(db_patient)
    return db_patient

@router.get("/{patient_id}", response_model=schemas.PatientOut)
def read_patient(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    return patient

@router.get("/{patient_id}/score")
def get_patient_score(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    
    # 1. Calcul Assiduité (Rendez-vous)
    rdvs = db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).all()
    honores = sum(1 for r in rdvs if r.status == models.AppointmentStatus.TERMINE)
    annules = sum(1 for r in rdvs if r.status == models.AppointmentStatus.ANNULE)
    
    total_rdv = honores + annules
    assiduite_score = 100
    if total_rdv > 0:
        assiduite_score = int((honores / total_rdv) * 100)
        
    # 2. Calcul Solvabilité (Actes / Paiements)
    actes = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).all()
    total_facture = sum(a.montant for a in actes)
    
    total_encaisse = 0
    for a in actes:
        if a.statut_paiement == models.PaiementStatut.PAYE:
            total_encaisse += a.montant
        elif a.statut_paiement == models.PaiementStatut.PARTIEL:
            total_encaisse += a.montant * 0.5  # Heuristique basique si on n'a pas les reçus exacts

    solvabilite_score = 100
    if total_facture > 0:
        solvabilite_score = int((total_encaisse / total_facture) * 100)
        
    # 3. Score Global (60% Assiduité, 40% Solvabilité)
    score_global = int((assiduite_score * 0.6) + (solvabilite_score * 0.4))
    
    # 4. Détermination du Grade (Priorité au Manuel)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    grade = patient.manual_grade if patient and patient.manual_grade else "BRONZE"
    
    if not (patient and patient.manual_grade):
        if score_global >= 90:
            grade = "PLATINUM"
        elif score_global >= 75:
            grade = "GOLD"
        elif score_global >= 50:
            grade = "SILVER"
        
    return {
        "score": score_global,
        "grade": grade,
        "is_manual": bool(patient and patient.manual_grade),
        "comment": patient.grade_comment if patient else None,
        "details": {
            "assiduite_score": assiduite_score,
            "solvabilite_score": solvabilite_score,
            "rdv_honores": honores,
            "rdv_annules": annules,
            "total_facture": total_facture,
            "total_encaisse": total_encaisse
        }
    }

@router.patch("/{patient_id}/grade")
def update_patient_grade(patient_id: int, data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")
        
    if "grade" in data:
        # None signifie retour au mode automatique
        patient.manual_grade = data["grade"]
    if "comment" in data:
        patient.grade_comment = data["comment"]
        
    db.commit()
    return {"status": "success"}

# --- CLINICAL INTELLIGENCE ---

@router.get("/{patient_id}/documents")
def get_patient_documents(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()

    # 1. BDD
    docs = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        or_(models.DocumentArchive.status == models.DocumentStatus.ACTIF, models.DocumentArchive.status == None),
        or_(models.DocumentArchive.is_latest_version == True, models.DocumentArchive.is_latest_version == None)
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
    assert_patient_access(patient_id, current_user, db)
    # Logique originale restaurée
    devis = db.query(models.DocumentArchive).filter(models.DocumentArchive.patient_id == patient_id, models.DocumentArchive.document_type == models.DocumentType.DEVIS).all()
    return {
        "suggestion": "Suite de traitement" if devis else "Consultation",
        "duration": 45 if devis else 30,
        "has_active_plan": bool(devis)
    }

@router.get("/{patient_id}/analyses", response_model=List[schemas.CephaloAnalysisOut])
def get_patient_analyses(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    return db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).all()

# --- CLINICAL INTELLIGENCE V2.0 ---

@router.get("/{patient_id}/ai-summary")
def get_patient_ai_summary(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Module 2 — Résumé Flash Patient (P0)."""
    assert_patient_access(patient_id, current_user, db)
    from backend.services.clinical_intelligence import clinical_intel
    return clinical_intel.get_patient_summary(db, patient_id)

@router.get("/{patient_id}/ai-diagnostic")
def get_patient_ai_diagnostic(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Module 3 — Panneau Conseil Clinique (P2)."""
    assert_patient_access(patient_id, current_user, db)
    from backend.services.clinical_intelligence import clinical_intel
    return clinical_intel.get_full_diagnostic(db, patient_id)

@router.put("/{patient_id}", response_model=schemas.PatientOut)
def update_patient(patient_id: int, patient_update: schemas.PatientUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    update_data = patient_update.model_dump(exclude_unset=True) if hasattr(patient_update, 'model_dump') else patient_update.dict(exclude_unset=True)
    
    # Check duplicates if name/date changed
    new_nom = update_data.get('nom', db_patient.nom).upper().strip()
    new_prenom = update_data.get('prenom', db_patient.prenom).capitalize().strip()
    new_date = update_data.get('date_naissance', db_patient.date_naissance)
    
    if (new_nom != db_patient.nom or 
        new_prenom != db_patient.prenom or 
        new_date != db_patient.date_naissance):
        existing = check_duplicate_patient(db, new_nom, new_prenom, new_date, exclude_id=patient_id)
        if existing:
            raise HTTPException(status_code=409, detail="Un autre patient avec le même nom et date de naissance existe déjà")

    # Update normalization
    if 'nom' in update_data: update_data['nom'] = update_data['nom'].upper().strip()
    if 'prenom' in update_data: update_data['prenom'] = update_data['prenom'].capitalize().strip()
    
    for key, value in update_data.items():
        setattr(db_patient, key, value)
    
    # Audit log
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="UPDATE",
        resource_type="Patient",
        resource_id=str(patient_id),
        details=f"Mise a jour des donnees du patient {patient_id}. Champs modifies: {list(update_data.keys())}"
    )
    
    db.commit()
    db.refresh(db_patient)
    return db_patient

# --- GÉNÉRATION RAPPORTS (COMPATIBILITÉ) ---

@router.post("/{patient_id}/pdf")
def generate_cephalo_pdf(
    patient_id: int, 
    req: schemas.CephaloPDFRequest, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Génération du rapport céphalo PDF (Route de compatibilité Ghost Elite)."""
    from backend.routers.documents import doc_factory
    from fastapi.responses import FileResponse
    
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    last_analysis = db.query(models.CephaloAnalysis).filter(
        models.CephaloAnalysis.patient_id == patient_id
    ).order_by(models.CephaloAnalysis.id.desc()).first()
    
    if not last_analysis: 
        raise HTTPException(status_code=404, detail="Aucune analyse céphalométrique trouvée pour ce patient")
    
    analysis_data = {
        "id": last_analysis.id,
        "image_path": last_analysis.image_original_path,
        "results": last_analysis.angles_data or {},
        "landmarks": last_analysis.landmarks_data
    }
    
    if req.ai_diagnostic: 
        analysis_data["results"]["ai_diagnostic"] = req.ai_diagnostic
    if req.clinical_data: 
        analysis_data["results"]["clinical_data"] = req.clinical_data.model_dump() if hasattr(req.clinical_data, 'model_dump') else req.clinical_data
    
    pdf_path = doc_factory.create_cephalo_report(patient, analysis_data, db=db, user_id=current_user.id)
    return FileResponse(path=pdf_path, filename=os.path.basename(pdf_path), media_type='application/pdf')
