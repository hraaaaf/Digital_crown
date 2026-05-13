from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional, Dict
from datetime import datetime
import os
import subprocess
import logging

from backend import models, schemas, database
from backend.routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Admin & Dashboard"])

@router.get("/normalize-docs")
def normalize_docs(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Normalise les types de documents en DB."""
    try:
        db.execute(text("UPDATE document_archives SET document_type = 'NOTE_HONORAIRES' WHERE document_type::text IN ('note_honoraires', 'note_honoraire', 'NOTE_HONORAIRE');"))
        db.execute(text("UPDATE document_archives SET document_type = 'RAPPORT_CEPHALO' WHERE document_type::text IN ('bilan', 'BILAN', 'rapport_cephalo');"))
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    emp_id = current_user.get_employer_id()
    
    total_p = db.query(models.Patient).filter(models.Patient.employer_id == emp_id).count()
    total_a = db.query(models.CephaloAnalysis).join(models.Patient).filter(models.Patient.employer_id == emp_id).count()
    db_recent = db.query(models.Patient).filter(models.Patient.employer_id == emp_id).order_by(models.Patient.created_at.desc()).limit(5).all()
    
    # Calcul de l'activité sur les 7 derniers jours
    weekly_activity = []
    from datetime import timedelta
    for i in range(6, -1, -1):
        day = datetime.now().date() - timedelta(days=i)
        count = db.query(models.Patient).filter(
            models.Patient.employer_id == emp_id,
            func.date(models.Patient.created_at) == day
        ).count()
        # On normalise en pourcentage pour le mini-graphique (max 100%)
        # Si on a 0 patient, on met 5% pour le style "Ghost"
        weekly_activity.append(max(5, min(100, count * 10))) 

    recent_list = []
    for p in db_recent:
        last_acte = p.actes[-1] if p.actes else None
        recent_list.append({
            "id": p.id, "nom": (p.nom or "").upper(), "prenom": (p.prenom or "").capitalize(),
            "acte": last_acte.libelle if last_acte else "Consultation",
            "time": "Récent", "type": last_acte.type_acte.value if last_acte else "Ortho"
        })
    return {
        "total_patients": total_p, 
        "total_analyses": total_a, 
        "recent_patients": recent_list,
        "weekly_activity": weekly_activity,
        "in_waiting": 0
    }


@router.get("/cabinet/me", response_model=schemas.PraticienProfileOut)
def get_cabinet_info(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    emp_id = current_user.get_employer_id()
    praticien = db.query(models.User).filter(models.User.id == emp_id).first()
    
    if not praticien: raise HTTPException(status_code=404, detail="Cabinet introuvable")
    
    # Injection des alias et données de config pour le frontend
    praticien.nom = praticien.nom_complet
    praticien.adresse = praticien.adresse_complete
    praticien.telephone = praticien.telephone_fixe
    praticien.inpe = (praticien.identifiants_legaux or {}).get("INPE", "")
    
    if praticien.cabinet_config:
        praticien.header_lines_fr = praticien.cabinet_config.header_lines_fr
        praticien.header_lines_ar = praticien.cabinet_config.header_lines_ar
        praticien.specialty_ids = praticien.cabinet_config.specialty_ids
        
    return praticien

@router.put("/cabinet/me", response_model=schemas.PraticienProfileOut)
def update_cabinet_info(settings: Dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    emp_id = current_user.get_employer_id()
    praticien = db.query(models.User).filter(models.User.id == emp_id).first()
    
    if not praticien: raise HTTPException(status_code=404, detail="Cabinet introuvable")
    
    config = praticien.cabinet_config
    
    for key, value in settings.items():
        if key == "nom": praticien.nom_complet = value
        elif key == "adresse": praticien.adresse_complete = value
        elif key == "telephone": praticien.telephone_fixe = value
        elif key == "inpe":
            legaux = dict(praticien.identifiants_legaux or {})
            legaux["INPE"] = value
            praticien.identifiants_legaux = legaux
        elif hasattr(praticien, key): 
            setattr(praticien, key, value)
        
        # Sync with CabinetConfig if exists
        if config and hasattr(config, key):
            setattr(config, key, value)
            
    db.commit(); db.refresh(praticien)
    
    # Re-inject for response
    praticien.nom = praticien.nom_complet
    praticien.adresse = praticien.adresse_complete
    praticien.telephone = praticien.telephone_fixe
    if config:
        praticien.header_lines_fr = config.header_lines_fr
        praticien.header_lines_ar = config.header_lines_ar
        praticien.specialty_ids = config.specialty_ids
        
    return praticien



@router.get("/export-db")
def export_database(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_url = str(database.engine.url)
    if "sqlite" in db_url:
        db_path = db_url.replace("sqlite:///", "")
        return FileResponse(path=db_path, filename=f"backup_{now_str}.db")
    elif "postgresql" in db_url:
        dump_path = os.path.join(os.getcwd(), "static", "backups", f"backup_{now_str}.sql")
        os.makedirs(os.path.dirname(dump_path), exist_ok=True)
        url = database.engine.url
        env = os.environ.copy()
        if url.password: env['PGPASSWORD'] = url.password
        subprocess.run(["pg_dump", "-h", url.host or "localhost", "-U", url.username or "postgres", "-f", dump_path, url.database], env=env, check=True)
        return FileResponse(path=dump_path, filename=f"backup_{now_str}.sql")
    raise HTTPException(status_code=400, detail="Moteur non supporté")
