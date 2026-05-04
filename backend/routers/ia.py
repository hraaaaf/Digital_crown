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
from backend.services.cephalo_engine import cephalo_engine
from backend.services.ai_advisor import ai_advisor
from backend.services.cephalo_service import CephaloService
from backend.services.prescription_service import prescription_service
from backend.services.panoramic_service import panoramic_engine
from backend.services.panoramic_ai_advisor import panoramic_ai_advisor

logger = logging.getLogger(__name__)
router = APIRouter(tags=["IA & Prescriptions"])

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RADIO_DIR = os.path.join(BASE_DIR, "static", "uploads", "radios")
os.makedirs(RADIO_DIR, exist_ok=True)

@router.post("/upload-radio")
async def upload_radio(patient_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable")
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_location = os.path.join(RADIO_DIR, unique_filename)
    db_path = f"api/static/uploads/radios/{unique_filename}"
    with open(file_location, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    try:
        service = CephaloService(db)
        result = service.process_new_radio(patient_id, file_location, db_path)
        result["file_url"] = f"http://localhost:8000/{db_path}"
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
    return analysis

@router.put("/analyses/{analysis_id}")
def update_analysis(analysis_id: int, req: schemas.AnalysisUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    try:
        service = CephaloService(db)
        return service.refine_analysis(analysis_id=analysis_id, landmarks=req.landmarks, clinical_data=req.clinical_data, ai_diagnostic=req.ai_diagnostic, mm_per_pixel=req.mm_per_pixel, mcnamara_projections=req.mcnmara_projections.model_dump() if req.mcnmara_projections else None)
    except Exception as e: 
        logger.exception(f"Erreur critique lors de l'update analyse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-panoramic")
async def upload_panoramic(patient_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable")
    
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
        
        # 2. AI Advisor / State Machine (Report Generation)
        report_data = await panoramic_ai_advisor.generate_report(vision_data)
        
        # 3. Save to DB (Persistence)
        db_analysis = models.PanoramicAnalysis(
            patient_id=patient_id,
            image_path=db_path,
            detections_data=vision_data,
            report_narrative=report_data.get("narrative_report", "")
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        
        # Merge results
        result = {
            "id": db_analysis.id,
            "patient_id": patient_id,
            "file_url": f"http://localhost:8000/{db_path}",
            "vision": vision_data,
            "report": report_data,
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
    analyses = db.query(models.PanoramicAnalysis).filter(
        models.PanoramicAnalysis.patient_id == patient_id
    ).order_by(models.PanoramicAnalysis.created_at.desc()).all()
    return analyses

@router.post("/analyses/{analysis_id}/calibrate")
def calibrate_analysis(analysis_id: int, req: Dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Calibrage manuel mm/pixel."""
    try:
        service = CephaloService(db)
        # Extraction des données du corps de la requête
        p1 = req.get("p1")
        p2 = req.get("p2")
        dist_mm = req.get("distance_mm", 10.0)
        
        if not p1 or not p2:
            raise HTTPException(status_code=400, detail="Points de calibration manquants")
            
        import math
        dist_px = math.sqrt((p2['x'] - p1['x'])**2 + (p2['y'] - p1['y'])**2)
        if dist_px == 0: raise HTTPException(status_code=400, detail="Distance nulle entre les points")
        
        mm_per_pixel = dist_mm / dist_px
        
        # Mise à jour de l'analyse avec le nouveau ratio
        analysis = service.repo.get_by_id(analysis_id)
        if not analysis: raise HTTPException(status_code=404, detail="Analyse introuvable")
        
        analysis.mm_per_pixel = mm_per_pixel
        analysis.is_calibrated = True
        db.commit()
        
        return {
            "status": "success",
            "mm_per_pixel": mm_per_pixel,
            "is_calibrated": True
        }
    except Exception as e:
        logger.exception(f"Erreur critique lors du calibrage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
