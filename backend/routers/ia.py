from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Response, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, date
from typing import List, Optional, Dict
import os
import uuid
import shutil
import logging

from backend import models, schemas, database
from backend.models_imaging_p4 import ImagingTrashRecord
from backend.routers.auth import get_current_user, require_permission, require_elite_license
from backend.utils.access_control import assert_patient_access
from backend.services.cephalo_service import CephaloService
from backend.services.prescription_service import prescription_service
from backend.services.panoramic_service import panoramic_engine

# Services
from backend.services.sota_vision_service import sota_vision_engine

# Configuration
from backend.config import settings
import os
import shutil

logger = logging.getLogger(__name__)
router = APIRouter(
    tags=["IA & Prescriptions"],
    dependencies=[Depends(require_elite_license)]
)

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RADIO_DIR = os.path.join(BASE_DIR, "static", "uploads", "radios")
os.makedirs(RADIO_DIR, exist_ok=True)


def _format_panoramic_visual_annotations(annotations: Optional[List[schemas.PanoramicVisualAnnotation]]) -> str:
    if not annotations:
        return ""

    lines = ["", "### ANNOTATIONS CLINIQUES LIBRES"]
    for ann in annotations:
        text = (ann.text or "").strip()
        if not text:
            continue
        lines.append(f"- {text} (repère visuel x={ann.x:.1f}%, y={ann.y:.1f}%).")
    return "\n".join(lines) if len(lines) > 2 else ""

@router.post("/upload-radio")
async def upload_radio(patient_id: int, background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    # Limite de taille : 10 Mo
    MAX_FILE_SIZE = 10 * 1024 * 1024
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 10 Mo)")
        
    RADIO_DIR = os.path.join(BASE_DIR, "static", "uploads", "radios")
    os.makedirs(RADIO_DIR, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_location = os.path.join(RADIO_DIR, unique_filename)
    db_path = f"api/static/uploads/radios/{unique_filename}"
    with open(file_location, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    try:
        service = CephaloService(db)
        result = service.process_new_radio(patient_id, file_location, db_path)
        result["file_url"] = f"{os.getenv('BACKEND_URL', 'http://localhost:8005')}/{db_path}"
        result["image_path"] = db_path

        # Ghost Brain Proactivity (background)
        def _background_tasks_radio(pid: int, user_id: int):
            try:
                with database.SessionLocal() as bg_db:
                    from backend.services.cmo_agent_service import cmo_agent
                    cmo_agent.generate_global_synthesis(bg_db, pid, user_id)
            except Exception as _e:
                logger.warning("Background tasks after radio upload failed: %s", _e)
        
        background_tasks.add_task(_background_tasks_radio, patient_id, current_user.id)

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

    out = schemas.CephaloAnalysisOut.model_validate(analysis)
    # Analyses legacy créées avant l'introduction de calibration_status : dérivé de
    # is_calibrated à la lecture, sans migration ni écriture (copie, jamais de mutation
    # de l'ORM/JSON persisté).
    if isinstance(out.angles_data, dict) and "calibration_status" not in out.angles_data:
        out.angles_data = {
            **out.angles_data,
            "calibration_status": "verified" if analysis.is_calibrated else "unverified",
        }
    return out

@router.put("/analyses/{analysis_id}")
def update_analysis(analysis_id: int, req: schemas.AnalysisUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
    analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if not analysis: raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    try:
        service = CephaloService(db)
        return service.refine_analysis(analysis_id=analysis_id, landmarks=req.landmarks, clinical_data=req.clinical_data, ai_diagnostic=req.ai_diagnostic, mm_per_pixel=req.mm_per_pixel, mcnamara_projections=req.mcnamara_projections.model_dump() if req.mcnamara_projections else None)
    except HTTPException as e:
        raise e
    except Exception as e: 
        logger.exception(f"Erreur critique lors de l'update analyse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-panoramic")
async def upload_panoramic(patient_id: int, background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("panoramic"))):
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
        # 1. Vision : nomination des dents UNIQUEMENT (aucune pathologie détectée par l'IA).
        #    La sémiologie est entièrement saisie manuellement par le praticien.
        vision_data = panoramic_engine.detect_teeth_only(file_location)

        # 2. Bilan déterministe initial (squelette de normalité, sans LLM)
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

        # FTS5 re-index & Ghost Brain Proactivity (background)
        def _background_tasks_pano(pid: int, user_id: int):
            try:
                with database.SessionLocal() as bg_db:
                    # 1. Re-index search
                    from backend.services.fts_indexer import index_patient
                    index_patient(pid, bg_db)
                    
                    # 2. Ghost Brain V2 : Déclencher le CMO Agent silencieusement pour qu'il mette à jour la mémoire
                    from backend.services.cmo_agent_service import cmo_agent
                    cmo_agent.generate_global_synthesis(bg_db, pid, user_id)
            except Exception as _e:
                logger.warning("Background tasks after panoramic upload failed: %s", _e)
        
        background_tasks.add_task(_background_tasks_pano, patient_id, current_user.id)

        result = {
            "id": db_analysis.id,
            "patient_id": patient_id,
            "file_url": f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/{db_path}",
            "image_path": db_path,
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
    trashed_ids = [
        row[0] for row in db.query(ImagingTrashRecord.analysis_id).filter(
            ImagingTrashRecord.modality == "panoramic",
            ImagingTrashRecord.patient_id == patient_id,
        ).all()
    ]
    query = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.patient_id == patient_id)
    if trashed_ids:
        query = query.filter(~models.PanoramicAnalysis.id.in_(trashed_ids))
    return query.order_by(models.PanoramicAnalysis.created_at.desc()).all()


@router.get("/patients/{patient_id}/panoramic-comparison")
def get_panoramic_comparison(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("panoramic")),
):
    """Compare the 2 most recent panoramic analyses to detect evolution."""
    assert_patient_access(patient_id, current_user, db)
    trashed_ids = [
        row[0] for row in db.query(ImagingTrashRecord.analysis_id).filter(
            ImagingTrashRecord.modality == "panoramic",
            ImagingTrashRecord.patient_id == patient_id,
        ).all()
    ]
    query = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.patient_id == patient_id)
    if trashed_ids:
        query = query.filter(~models.PanoramicAnalysis.id.in_(trashed_ids))
    analyses = query.order_by(desc(models.PanoramicAnalysis.created_at)).limit(2).all()
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
        all_detections = analysis.detections_data.get("detections", [])

        # Marquer les détections comme rejetées pour la persistance
        if req.rejected_detections:
            for idx in req.rejected_detections:
                if 0 <= idx < len(all_detections):
                    all_detections[idx]["rejected"] = True

        # On ne passe au générateur que les détections non rejetées
        active_detections = [d for d in all_detections if not d.get("rejected")]

        # Génération du bilan déterministe (annotations manuelles + constats généraux)
        report_markdown = panoramic_report_engine.generate_markdown(
            detections=active_detections,
            manual_anomalies=req.manual_anomalies,
            global_findings=req.global_findings,
        )
        annotation_block = _format_panoramic_visual_annotations(req.visual_annotations)
        synthesis_marker = "\n### SYNTHÈSE\n"
        if annotation_block and synthesis_marker in report_markdown:
            report_markdown = report_markdown.replace(
                synthesis_marker,
                f"{annotation_block}{synthesis_marker}",
                1,
            )
        else:
            report_markdown += annotation_block

        # Mise à jour persistante
        analysis.report_narrative = report_markdown
        # Forcer la mise à jour du JSON field dans SQLAlchemy
        analysis.detections_data = {
            **analysis.detections_data,
            "detections": all_detections,
            "manual_anomalies": req.manual_anomalies,
            "global_findings": req.global_findings,
            "visual_annotations": [ann.model_dump() for ann in (req.visual_annotations or [])],
        }

        db.commit()
        db.refresh(analysis)
        return {"id": analysis.id, "report_narrative": report_markdown}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Erreur lors de la génération du rapport panoramique: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/panoramic/{analysis_id}/report")
def edit_panoramic_report(analysis_id: int, req: schemas.PanoramicReportEdit, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("panoramic"))):
    """Sauvegarde l'édition manuelle du bilan (paragraphe / ligne) par le praticien."""
    analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    try:
        analysis.report_narrative = req.report_narrative
        db.commit()
        db.refresh(analysis)
        return {"id": analysis.id, "report_narrative": analysis.report_narrative}
    except Exception as e:
        db.rollback()
        logger.exception(f"Erreur lors de l'édition du bilan panoramique: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===============================================================================
# --- CEPHALO ANALYSES ENDPOINTS ---
# ===============================================================================

@router.get("/patients/{patient_id}/cephalo-analyses", response_model=List[schemas.CephaloAnalysisOut])
def get_patient_cephalo_analyses(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
    """Récupère l'historique des analyses céphalométriques d'un patient."""
    assert_patient_access(patient_id, current_user, db)
    trashed_ids = [
        row[0] for row in db.query(ImagingTrashRecord.analysis_id).filter(
            ImagingTrashRecord.modality == "cephalo",
            ImagingTrashRecord.patient_id == patient_id,
        ).all()
    ]
    query = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id)
    if trashed_ids:
        query = query.filter(~models.CephaloAnalysis.id.in_(trashed_ids))
    return query.order_by(models.CephaloAnalysis.created_at.desc()).all()

@router.get("/patients/{patient_id}/cephalo-trash", response_model=List[schemas.CephaloAnalysisOut])
def get_patient_cephalo_trash(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
    assert_patient_access(patient_id, current_user, db)
    trashed_ids = [
        row[0] for row in db.query(ImagingTrashRecord.analysis_id).filter(
            ImagingTrashRecord.modality == "cephalo",
            ImagingTrashRecord.patient_id == patient_id,
        ).order_by(ImagingTrashRecord.deleted_at.desc()).all()
    ]
    if not trashed_ids:
        return []
    analyses = db.query(models.CephaloAnalysis).filter(
        models.CephaloAnalysis.patient_id == patient_id,
        models.CephaloAnalysis.id.in_(trashed_ids),
    ).all()
    by_id = {analysis.id: analysis for analysis in analyses}
    return [by_id[analysis_id] for analysis_id in trashed_ids if analysis_id in by_id]


@router.delete("/cephalo/{analysis_id}")
def delete_cephalo_analysis(analysis_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
    """Place une analyse céphalométrique dans la corbeille récupérable."""
    analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    marker = db.query(ImagingTrashRecord).filter(
        ImagingTrashRecord.modality == "cephalo",
        ImagingTrashRecord.analysis_id == analysis_id,
    ).first()
    if marker is None:
        marker = ImagingTrashRecord(
            modality="cephalo",
            analysis_id=analysis_id,
            patient_id=analysis.patient_id,
            deleted_by=current_user.id,
        )
        db.add(marker)
        db.commit()
    return {"status": "trashed", "recoverable": True, "id": analysis_id}


@router.post("/cephalo/{analysis_id}/restore")
def restore_cephalo_analysis(analysis_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("cephalo"))):
    analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    marker = db.query(ImagingTrashRecord).filter(
        ImagingTrashRecord.modality == "cephalo",
        ImagingTrashRecord.analysis_id == analysis_id,
        ImagingTrashRecord.patient_id == analysis.patient_id,
    ).first()
    if marker is None:
        raise HTTPException(status_code=404, detail="Analyse absente de la corbeille")
    db.delete(marker)
    db.commit()
    return {"status": "restored", "id": analysis_id}


@router.get("/panoramic/{analysis_id}/pdf")
def download_panoramic_pdf(analysis_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("panoramic"))):
    """Génère et diffuse le PDF panoramique via un flux authentifié."""
    analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    try:
        from fastapi.responses import FileResponse
        from backend.services.generators.panoramic_elite_gen import panoramic_elite_generator
        pdf_rel = panoramic_elite_generator.generate(db=db, analysis_id=analysis_id, current_user=current_user)
        clean_rel = pdf_rel.removeprefix("api/")
        pdf_path = os.path.join(BASE_DIR, clean_rel)
        if not os.path.isfile(pdf_path):
            raise HTTPException(status_code=500, detail="PDF généré introuvable")
        return FileResponse(path=pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors de la génération du PDF panoramique Élite: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patients/{patient_id}/panoramic-trash", response_model=List[schemas.PanoramicAnalysisOut])
def get_patient_panoramic_trash(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("panoramic"))):
    assert_patient_access(patient_id, current_user, db)
    trashed_ids = [
        row[0] for row in db.query(ImagingTrashRecord.analysis_id).filter(
            ImagingTrashRecord.modality == "panoramic",
            ImagingTrashRecord.patient_id == patient_id,
        ).order_by(ImagingTrashRecord.deleted_at.desc()).all()
    ]
    if not trashed_ids:
        return []
    analyses = db.query(models.PanoramicAnalysis).filter(
        models.PanoramicAnalysis.patient_id == patient_id,
        models.PanoramicAnalysis.id.in_(trashed_ids),
    ).all()
    by_id = {analysis.id: analysis for analysis in analyses}
    return [by_id[analysis_id] for analysis_id in trashed_ids if analysis_id in by_id]


@router.delete("/panoramic/{analysis_id}")
def delete_panoramic_analysis(
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("panoramic")),
):
    """Place un examen panoramique dans la corbeille récupérable."""
    analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Bilan panoramique introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    marker = db.query(ImagingTrashRecord).filter(
        ImagingTrashRecord.modality == "panoramic",
        ImagingTrashRecord.analysis_id == analysis_id,
    ).first()
    if marker is None:
        marker = ImagingTrashRecord(
            modality="panoramic",
            analysis_id=analysis_id,
            patient_id=analysis.patient_id,
            deleted_by=current_user.id,
        )
        db.add(marker)
        db.commit()
    return {"status": "trashed", "recoverable": True, "id": analysis_id}


@router.post("/panoramic/{analysis_id}/restore")
def restore_panoramic_analysis(
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("panoramic")),
):
    analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Bilan panoramique introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    marker = db.query(ImagingTrashRecord).filter(
        ImagingTrashRecord.modality == "panoramic",
        ImagingTrashRecord.analysis_id == analysis_id,
        ImagingTrashRecord.patient_id == analysis.patient_id,
    ).first()
    if marker is None:
        raise HTTPException(status_code=404, detail="Examen absent de la corbeille")
    db.delete(marker)
    db.commit()
    return {"status": "restored", "id": analysis_id}