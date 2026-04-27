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
    db_path = f"static/uploads/radios/{unique_filename}"
    with open(file_location, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    try:
        service = CephaloService(db)
        result = service.process_new_radio(patient_id, file_location, db_path)
        result["file_url"] = f"http://localhost:8000/{db_path}"
        return result
    except Exception as e:
        if os.path.exists(file_location): os.remove(file_location)
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/analyses/{analysis_id}")
def update_analysis(analysis_id: int, req: schemas.AnalysisUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    try:
        service = CephaloService(db)
        return service.refine_analysis(analysis_id=analysis_id, landmarks=req.landmarks, clinical_data=req.clinical_data, ai_diagnostic=req.ai_diagnostic, mm_per_pixel=req.mm_per_pixel, mcnamara_projections=req.mcnmara_projections.model_dump() if req.mcnmara_projections else None)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
