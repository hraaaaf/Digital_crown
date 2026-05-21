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
from backend.routers.auth import get_current_user, require_permission
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
async def upload_radio(patient_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
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
def get_analysis(analysis_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
    analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    return analysis

@router.put("/analyses/{analysis_id}")
def update_analysis(analysis_id: int, req: schemas.AnalysisUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
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
async def upload_panoramic(patient_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("panoramic"))):
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

        # FTS5 re-index for this patient (background)
        import threading
        def _reindex():
            try:
                from backend.services.fts_indexer import index_patient
                with database.SessionLocal() as idx_db:
                    index_patient(patient_id, idx_db)
            except Exception as _e:
                logger.warning("FTS re-index after panoramic upload failed: %s", _e)
        threading.Thread(target=_reindex, daemon=True).start()

        result = {
            "id": db_analysis.id,
            "patient_id": patient_id,
            "file_url": f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/{db_path}",
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
def get_patient_panoramic_analyses(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("panoramic"))):
    """Récupère l'historique des analyses panoramiques d'un patient."""
    assert_patient_access(patient_id, current_user, db)
    analyses = db.query(models.PanoramicAnalysis).filter(
        models.PanoramicAnalysis.patient_id == patient_id
    ).order_by(models.PanoramicAnalysis.created_at.desc()).all()
    return analyses


@router.get("/patients/{patient_id}/panoramic-comparison")
def get_panoramic_comparison(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("panoramic")),
):
    """Compare the 2 most recent panoramic analyses to detect evolution."""
    assert_patient_access(patient_id, current_user, db)
    analyses = (
        db.query(models.PanoramicAnalysis)
        .filter(models.PanoramicAnalysis.patient_id == patient_id)
        .order_by(desc(models.PanoramicAnalysis.created_at))
        .limit(2)
        .all()
    )
    if len(analyses) < 2:
        return {"available": False, "reason": "Moins de 2 bilans panoramiques disponibles."}
    from backend.services.temporal_comparator import compare_panoramic_analyses
    diff = compare_panoramic_analyses(older=analyses[1], newer=analyses[0])
    return {"available": True, **diff}

@router.post("/analyses/{analysis_id}/calibrate")
def calibrate_analysis(analysis_id: int, req: schemas.CalibrationRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
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

@router.post("/generate-panoramic-report")
async def generate_panoramic_report(req: schemas.PanoramicReportRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("panoramic"))):
    """Génère un bilan professionnel basé sur les détections IA et les annotations manuelles."""
    analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == req.analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    
    assert_patient_access(analysis.patient_id, current_user, db)
    
    try:
        from backend.services.panoramic_report_engine import panoramic_report_engine
        
        # Récupération des détections IA stockées
        detections = analysis.detections_data.get("detections", [])
        
        # Génération du nouveau rapport hybride (IA + Manuel)
        report_markdown = panoramic_report_engine.generate_markdown(
            detections=detections, 
            manual_anomalies=req.manual_anomalies
        )
        
        # Mise à jour persistante
        analysis.report_narrative = report_markdown
        db.commit()
        db.refresh(analysis)
        
        return {
            "id": analysis.id,
            "report_narrative": report_markdown
        }
    except Exception as e:
        logger.exception(f"Erreur lors de la génération du rapport panoramique: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/panoramic/{analysis_id}/pdf")
def download_panoramic_pdf(analysis_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("panoramic"))):
    """Génère et retourne l'URL du bilan PDF professionnel Élite."""
    try:
        from backend.services.generators.panoramic_elite_gen import panoramic_elite_generator
        pdf_url = panoramic_elite_generator.generate(
            db=db,
            analysis_id=analysis_id,
            current_user=current_user
        )
        return {"pdf_url": f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/{pdf_url}"}
    except Exception as e:
        logger.exception(f"Erreur lors de la génération du PDF panoramique Élite: {e}")
        raise HTTPException(status_code=500, detail=str(e))
