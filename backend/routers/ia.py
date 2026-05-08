from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, date
from typing import List, Optional, Dict
import os
import uuid
import shutil
import logging

from backend import models, schemas, database
from backend.routers.auth import get_current_user
from backend.utils.access_control import assert_patient_access
from backend.services.cephalo_engine import cephalo_engine
from backend.services.ai_advisor import ai_advisor
from backend.services.cephalo_service import CephaloService
from backend.services.prescription_service import prescription_service
from backend.services.panoramic_service import panoramic_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["IA & Prescriptions"])

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RADIO_DIR = os.path.join(BASE_DIR, "static", "uploads", "radios")
os.makedirs(RADIO_DIR, exist_ok=True)

@router.post("/upload-radio")
async def upload_radio(patient_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    # Limite de taille : 10 Mo
    MAX_FILE_SIZE = 10 * 1024 * 1024
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 10 Mo)")
        
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_location = os.path.join(RADIO_DIR, unique_filename)
    db_path = f"api/static/uploads/radios/{unique_filename}"
    with open(file_location, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    try:
        service = CephaloService(db)
        result = service.process_new_radio(patient_id, file_location, db_path)
        result["file_url"] = f"{os.getenv("BACKEND_URL", "http://localhost:8000")}/{db_path}"
        return result
    except Exception as e:
        if os.path.exists(file_location): os.remove(file_location)
        logger.exception(f"Erreur critique lors de l'upload radio: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analyses/{analysis_id}", response_model=schemas.CephaloAnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    return analysis

@router.put("/analyses/{analysis_id}")
def update_analysis(analysis_id: int, req: schemas.AnalysisUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if not analysis: raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    try:
        service = CephaloService(db)
        return service.refine_analysis(analysis_id=analysis_id, landmarks=req.landmarks, clinical_data=req.clinical_data, ai_diagnostic=req.ai_diagnostic, mm_per_pixel=req.mm_per_pixel, mcnamara_projections=req.mcnmara_projections.model_dump() if req.mcnmara_projections else None)
    except HTTPException as e:
        raise e
    except Exception as e: 
        logger.exception(f"Erreur critique lors de l'update analyse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-panoramic")
async def upload_panoramic(patient_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    # Limite de taille : 10 Mo
    MAX_FILE_SIZE = 10 * 1024 * 1024
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 10 Mo)")
        
    PANORAMIC_DIR = os.path.join(BASE_DIR, "static", "uploads", "panoramic")
    os.makedirs(PANORAMIC_DIR, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_location = os.path.join(PANORAMIC_DIR, unique_filename)
    db_path = f"api/static/uploads/panoramic/{unique_filename}"
    
    with open(file_location, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    
    try:
        # 1. Vision Inference (Loki-Silvres Model via PanoramicEngine)
        vision_data = panoramic_engine.predict(file_location)
        
        # 2. Deterministic Report Generation (Zéro-Hallucination)
        from backend.services.panoramic_report_engine import panoramic_report_engine
        detections_data = vision_data.get("detections_data", {})
        report_markdown = panoramic_report_engine.generate_markdown(detections_data)
        
        # 3. Save to DB (Persistence)
        db_analysis = models.PanoramicAnalysis(
            patient_id=patient_id,
            image_path=db_path,
            detections_data=detections_data, # Schéma validé FullAnalysis
            report_narrative=report_markdown
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        
        # Merge results
        result = {
            "id": db_analysis.id,
            "patient_id": patient_id,
            "file_url": f"{os.getenv("BACKEND_URL", "http://localhost:8000")}/{db_path}",
            "vision": vision_data,
            "report_narrative": report_markdown,
            "created_at": db_analysis.created_at
        }
        
        return result
        
    except Exception as e:
        if os.path.exists(file_location): os.remove(file_location)
        logger.exception(f"Erreur critique lors de l'upload panoramique: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/patients/{patient_id}/panoramic-analyses", response_model=List[schemas.PanoramicAnalysisOut])
def get_patient_panoramic_analyses(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Récupère l'historique des analyses panoramiques d'un patient."""
    assert_patient_access(patient_id, current_user, db)
    analyses = db.query(models.PanoramicAnalysis).filter(
        models.PanoramicAnalysis.patient_id == patient_id
    ).order_by(models.PanoramicAnalysis.created_at.desc()).all()
    return analyses

@router.post("/analyses/{analysis_id}/calibrate")
def calibrate_analysis(analysis_id: int, req: schemas.CalibrationRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Calibrage manuel mm/pixel."""
    analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if not analysis: raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    try:
        service = CephaloService(db)
        
        import math
        dist_px = math.sqrt((req.p2.x - req.p1.x)**2 + (req.p2.y - req.p1.y)**2)
        if dist_px < 5: # On demande au moins 5 pixels de distance pour la précision
            raise HTTPException(status_code=400, detail="Les points de calibration sont trop proches (min 5px)")
        
        mm_per_pixel = req.distance_mm / dist_px
        
        # Validation "Métier" : Un ratio réaliste pour une radio dentaire
        # Typiquement entre 0.05 et 0.5 mm/pixel. On est large avec [0.01, 2.0].
        if mm_per_pixel < 0.01 or mm_per_pixel > 2.0:
            raise HTTPException(status_code=400, detail=f"Ratio mm/pixel aberrant ({mm_per_pixel:.4f}). Verifiez vos points.")
        
        # Mise à jour de l'analyse avec le nouveau ratio
        analysis.mm_per_pixel = mm_per_pixel
        analysis.is_calibrated = True
        db.commit()
        
        return {
            "status": "success",
            "mm_per_pixel": mm_per_pixel,
            "is_calibrated": True
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Erreur critique lors du calibrage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
