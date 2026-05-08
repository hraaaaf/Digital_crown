from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional, Dict
from datetime import date, datetime
import os
import pathlib
import time
import json
import logging

from backend import models, schemas, database
from backend.routers.auth import get_current_user
from backend.utils.access_control import assert_patient_access
from backend.services.document_factory import DocumentFactory
from backend.services.archive_service import get_archive_service
from backend.services.generators.report_gen import ReportGenerator
from backend.services.clinical_coherence import coherence_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Documents & Accounting"])

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DOCS_DIR = os.path.join(STATIC_DIR, "documents")
doc_factory = DocumentFactory(output_dir=DOCS_DIR, static_dir=STATIC_DIR)

def _extract_amount_from_clinical_data(clinical_data: dict) -> float:
    if not clinical_data: return 0.0
    if 'payments' in clinical_data:
        total = sum(float(p.get('montant', 0)) for p in clinical_data['payments'])
        if total > 0: return total
    if 'items' in clinical_data:
        total = sum(float(i.get('prix_unitaire', i.get('montant', 0))) for i in clinical_data['items'])
        if total > 0: return total
    return float(clinical_data.get('total', 0))

@router.post("/generate")
async def generate_document(req: schemas.DocumentRequest, archive: bool = False, preview: bool = False, force: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(req.patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == req.patient_id).first()
    
    user_id = current_user.id
    try:
        if req.type == "ordonnance":
            pdf_path = doc_factory.create_ordonnance(patient, schemas.OrdonnanceData(**req.data), db, user_id)
        elif req.type == "certificat":
            pdf_path = doc_factory.create_certificat(patient, schemas.CertificatData(**req.data), db, user_id)
        elif req.type == "devis":
            pdf_path = doc_factory.create_devis(patient, schemas.DevisData(**req.data), db, user_id)
        elif req.type in ["honoraires", "note"]:
            pdf_path = doc_factory.create_note_honoraires(patient, schemas.HonorairesData(**req.data), db, user_id)
        elif req.type == "libre":
            pdf_path = doc_factory.create_document_libre(patient, schemas.LibreData(**req.data), db, user_id)
        
        is_financial = req.type in ["honoraires", "note", "devis"]
        should_archive = (archive or is_financial) and not preview

        if should_archive:
            with open(pdf_path, "rb") as f: pdf_content = f.read()
            archive_service = get_archive_service(db)
            
            enum_map = {
                "ordonnance": models.DocumentType.ORDONNANCE, "certificat": models.DocumentType.CERTIFICAT,
                "devis": models.DocumentType.DEVIS, "honoraires": models.DocumentType.NOTE_HONORAIRES,
                "note": models.DocumentType.NOTE_HONORAIRES, "libre": models.DocumentType.DOCUMENT_LIBRE
            }
            
            doc, _ = archive_service.archive_document(
                patient_id=patient.id, file_content=pdf_content, filename=os.path.basename(pdf_path),
                doc_type=enum_map.get(req.type, models.DocumentType.AUTRE), uploaded_by_id=user_id, clinical_data=req.data
            )
            pdf_path = doc.file_path

        # Analyse de cohérence (Phase 1 & 2)
        warnings = await coherence_service.analyze_coherence(patient.id, req.type, req.data, db, doctor_id=user_id)

        # Nettoyage du chemin pour le frontend
        pdf_url = pdf_path.replace("\\", "/")
        if "static/" in pdf_url:
            pdf_url = pdf_url[pdf_url.find("static/"):]
        
        # Apprentissage des habitudes d'actes (Phase 5)
        if is_financial and not preview:
            from backend.services.accounting_service import accounting_service
            if req.type == "devis":
                for item in req.data.get('items', []):
                    accounting_service.record_act_usage(db, user_id, item.get('acte'), float(item.get('prix_unitaire', 0)))
            else: # honoraires/note
                for p in req.data.get('payments', []):
                    accounting_service.record_act_usage(db, user_id, p.get('acte'), float(p.get('montant', 0)))

        return {"status": "success", "pdf_url": pdf_url, "warnings": warnings}
    except Exception as e:
        logger.error(f"Erreur Génération : {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/archive", response_model=schemas.DocumentArchiveResponse)
async def archive_document(patient_id: int, doc_type: schemas.DocumentType, file: UploadFile = File(...), title: Optional[str] = None, on_conflict: schemas.ConflictResolution = schemas.ConflictResolution.CREATE_VERSION, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    content = await file.read()
    archive_service = get_archive_service(db)
    doc, is_new = archive_service.archive_document(patient_id=patient_id, file_content=content, filename=file.filename, doc_type=doc_type, uploaded_by_id=current_user.id, title=title, on_conflict=on_conflict)
    return {"success": True, "message": "Archivé", "document": doc}

@router.get("/", response_model=schemas.DocumentListResponse)
def list_documents(patient_id: Optional[int] = None, doc_type: Optional[schemas.DocumentType] = None, search: Optional[str] = None, page: int = 1, page_size: int = 20, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if patient_id:
        assert_patient_access(patient_id, current_user, db)
    
    archive_service = get_archive_service(db)
    docs, total = archive_service.search_documents(
        patient_id=patient_id, 
        doc_type=doc_type, 
        search_query=search, 
        page=page, 
        page_size=page_size,
        employer_id=current_user.get_employer_id()
    )
    return {"total": total, "page": page, "page_size": page_size, "documents": docs}

@router.get("/{document_id}/download")
def download_document(document_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if str(document_id).startswith("legacy:"):
        parts = str(document_id).split(":")
        patient_id = int(parts[1])
        assert_patient_access(patient_id, current_user, db)
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        folder = f"{patient.id}_{patient.nom.upper()}_{patient.prenom.capitalize()}"
        filename = os.path.basename(parts[2])
        safe_root = pathlib.Path(BASE_DIR, "static", "patients", folder, "Documents").resolve()
        file_path = (safe_root / filename).resolve()
        if not str(file_path).startswith(str(safe_root)):
            raise HTTPException(status_code=400, detail="Chemin de fichier invalide")
        return FileResponse(path=str(file_path), filename=filename)
    
    doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == int(document_id)).first()
    if not doc: raise HTTPException(status_code=404, detail="Introuvable")
    assert_patient_access(doc.patient_id, current_user, db)
    return FileResponse(path=doc.file_path, filename=doc.original_filename)

@router.post("/{document_id}/trash")
def move_to_trash(document_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    doc_id = int(document_id)
    doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
    if not doc: raise HTTPException(status_code=404, detail="Introuvable")
    assert_patient_access(doc.patient_id, current_user, db)
    
    archive_service = get_archive_service(db)
    doc = archive_service.move_to_trash(doc_id)
    return {"message": "Mis à la corbeille", "id": doc.id}

@router.post("/{document_id}/restore")
def restore_from_trash(document_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    doc_id = int(document_id)
    doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
    if not doc: raise HTTPException(status_code=404, detail="Introuvable")
    assert_patient_access(doc.patient_id, current_user, db)
    
    archive_service = get_archive_service(db)
    doc = archive_service.restore_from_trash(doc_id)
    return {"message": "Restauré", "id": doc.id}

@router.delete("/{document_id}")
def permanent_delete(document_id: str, confirm: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if not confirm: raise HTTPException(status_code=400, detail="Confirmation requise")
    doc_id = int(document_id)
    doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
    if not doc: raise HTTPException(status_code=404, detail="Introuvable")
    assert_patient_access(doc.patient_id, current_user, db)
    
    archive_service = get_archive_service(db)
    if archive_service.permanent_delete(doc_id): return {"status": "deleted"}
    raise HTTPException(status_code=500, detail="Erreur suppression")

@router.get("/accounting/honoraires", response_model=schemas.HonoraireListResponse)
def get_accounting_honoraires(patient_id: Optional[int] = None, assurance: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    user_employer_id = current_user.get_employer_id()
    query = db.query(models.DocumentArchive).join(models.Patient).filter(
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES, 
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        models.Patient.employer_id == user_employer_id
    )
    if patient_id: query = query.filter(models.DocumentArchive.patient_id == patient_id)
    if assurance: query = query.filter(models.Patient.assurance == assurance)
    if year: query = query.filter(func.extract('year', models.DocumentArchive.created_at) == year)
    if month: query = query.filter(func.extract('month', models.DocumentArchive.created_at) == month)
    docs = query.order_by(desc(models.DocumentArchive.created_at)).all()
    items = []
    total_amount = 0
    for doc in docs:
        amount = _extract_amount_from_clinical_data(doc.clinical_data)
        items.append({"id": doc.id, "patient_id": doc.patient_id, "patient_name": f"{doc.patient.nom} {doc.patient.prenom}", "assurance": doc.patient.assurance, "date": doc.created_at, "title": doc.title or "Note d'honoraires", "amount": amount, "file_url": f"api/documents/{doc.id}/download"})
        total_amount += amount
    return {"total": len(items), "total_amount": total_amount, "items": items}

@router.get("/accounting/export-pdf")
def export_accounting_pdf(patient_id: Optional[int] = None, assurance: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    data = get_accounting_honoraires(patient_id, assurance, year, month, db, current_user)
    report_gen = ReportGenerator()
    filepath = report_gen.generate_accounting_report(items=data["items"], total_amount=data["total_amount"], filters={"assurance": assurance, "month": month, "year": year})
    return FileResponse(path=os.path.join(os.getcwd(), filepath), filename=f"Compta_{year or 'Global'}.pdf")

@router.get("/stats/dashboard")
def get_document_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    user_employer_id = current_user.get_employer_id()
    total_docs = db.query(models.DocumentArchive).join(models.Patient).filter(models.Patient.employer_id == user_employer_id).count()
    total_size = db.query(func.sum(models.DocumentArchive.file_size)).join(models.Patient).filter(models.Patient.employer_id == user_employer_id).scalar() or 0
    by_type = db.query(models.DocumentArchive.document_type, func.count(models.DocumentArchive.id)).join(models.Patient).filter(models.Patient.employer_id == user_employer_id).group_by(models.DocumentArchive.document_type).all()
    return {"total_documents": total_docs, "total_size_mb": round(total_size / (1024*1024), 2), "by_type": {t.value: c for t, c in by_type}}

@router.post("/patients/{patient_id}/report")
def generate_patient_report(patient_id: int, req: schemas.CephaloPDFRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    last_analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).order_by(models.CephaloAnalysis.id.desc()).first()
    if not last_analysis: raise HTTPException(status_code=404, detail="Aucune analyse")
    
    analysis_data = {"id": last_analysis.id, "image_path": last_analysis.image_original_path, "results": last_analysis.angles_data or {}, "landmarks": last_analysis.landmarks_data}
    if req.ai_diagnostic: analysis_data["results"]["ai_diagnostic"] = req.ai_diagnostic
    if req.clinical_data: analysis_data["results"]["clinical_data"] = req.clinical_data.model_dump() if hasattr(req.clinical_data, 'model_dump') else req.clinical_data
    
    pdf_path = doc_factory.create_cephalo_report(patient, analysis_data, db=db, user_id=current_user.id)
    return FileResponse(path=pdf_path, filename=os.path.basename(pdf_path), media_type='application/pdf')
