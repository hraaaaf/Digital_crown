from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
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
from backend.utils.accounting_utils import extract_amount_from_clinical_data

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Documents & Accounting"])

# Configuration
from backend.core.paths import AppPaths
MEDIA_DIR = AppPaths.get_user_data_dir() / "media"
DOCS_DIR = str(MEDIA_DIR / "documents")
STATIC_DIR = str(AppPaths.get_static_dir())

os.makedirs(DOCS_DIR, exist_ok=True)
doc_factory = DocumentFactory(output_dir=DOCS_DIR, static_dir=STATIC_DIR)

# Logic moved to backend.utils.accounting_utils

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
        elif req.type in ["libre", "lettre"]:
            pdf_path = doc_factory.create_document_libre(patient, schemas.LibreData(**req.data), db, user_id)
        
        is_financial = req.type in ["honoraires", "note", "devis"]
        should_archive = (archive or is_financial) and not preview

        if should_archive:
            with open(pdf_path, "rb") as f: pdf_content = f.read()
            archive_service = get_archive_service(db)
            
            enum_map = {
                "ordonnance": models.DocumentType.ORDONNANCE, "certificat": models.DocumentType.CERTIFICAT,
                "devis": models.DocumentType.DEVIS, "honoraires": models.DocumentType.NOTE_HONORAIRES,
                "note": models.DocumentType.NOTE_HONORAIRES, "libre": models.DocumentType.DOCUMENT_LIBRE,
                "lettre": models.DocumentType.LETTRE_MEDICALE
            }
            
            # Logique automatique de statut (Elite v4)
            p_status = models.PaiementStatut.EN_ATTENTE
            p_collected = False
            
            payments = req.data.get('payments', [])
            if payments:
                # Si au moins un paiement est en espèces ou TPE, on considère comme payé/encaissé pour simplifier
                # ou alors on regarde si TOUS sont encaissables
                all_instant = all(p.get('mode_reglement') in ['Espèces', 'TPE'] for p in payments)
                any_instant = any(p.get('mode_reglement') in ['Espèces', 'TPE'] for p in payments)
                
                if all_instant:
                    p_status = models.PaiementStatut.PAYE
                    p_collected = True
                elif any_instant:
                    p_status = models.PaiementStatut.PARTIEL
                    p_collected = False
                else:
                    p_status = models.PaiementStatut.A_ENCAISSER
                    p_collected = False
            
            doc, _ = archive_service.archive_document(
                patient_id=patient.id, file_content=pdf_content, filename=os.path.basename(pdf_path),
                doc_type=enum_map.get(req.type, models.DocumentType.AUTRE), uploaded_by_id=user_id, clinical_data=req.data,
                is_accounted=req.is_accounted, 
                payment_status=req.payment_status if req.payment_status != "EN_ATTENTE" else p_status,
                is_collected=p_collected
            )
            pdf_path = doc.file_path

        # Analyse de cohérence (Phase 1 & 2)
        warnings = await coherence_service.analyze_coherence(patient.id, req.type, req.data, db, doctor_id=user_id)

        # Nettoyage du chemin pour le frontend
        pdf_url = pdf_path.replace("\\", "/")
        
        # Si le chemin contient MEDIA_DIR, on le rend relatif à MEDIA_DIR et on préfixe par 'static/'
        media_path_str = str(MEDIA_DIR).replace("\\", "/")
        if media_path_str in pdf_url:
            pdf_url = "static" + pdf_url.split(media_path_str)[1]
        elif "static/" in pdf_url:
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


from pydantic import BaseModel

class BrandingPreviewPayload(BaseModel):
    selected_template: Optional[str] = None
    font_fr: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    margin_top: Optional[float] = None
    margin_bottom: Optional[float] = None
    header_scale: Optional[float] = None
    header_font_scale: Optional[float] = None
    header_logo_scale: Optional[float] = None
    header_line_height: Optional[float] = None
    footer_font_scale: Optional[float] = None
    footer_qr_scale: Optional[float] = None
    footer_line_height: Optional[float] = None
    qr_code_enabled: Optional[bool] = None
    qr_code_type: Optional[str] = None
    qr_code_style: Optional[str] = None
    qr_code_value: Optional[str] = None
    qr_code_label: Optional[str] = None

@router.post("/sample-preview")
async def generate_sample_preview(
    payload: Optional[BrandingPreviewPayload] = None,
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Patient fictif pour l'aperçu dynamique
    mock_patient = models.Patient(
        nom="EL ALAMI",
        prenom="Youssef",
        date_naissance=datetime(1990, 5, 12),
        sexe="M",
        telephone="06 61 23 45 67",
        email="youssef.elalami@email.ma",
        employer_id=current_user.id
    )
    
    # Ordonnance fictive représentative
    mock_data = schemas.OrdonnanceData(
        medications=[
            schemas.MedicationItem(nom="ZAMOC (Amoxicilline)", dosage="500 mg", forme="Sachets", posologie="1 sachet 3 fois par jour après les repas", type="MEDICAMENT"),
            schemas.MedicationItem(nom="DOLIPRANE", dosage="1000 mg", forme="Comprimés", posologie="1 comprimé toutes les 6 heures en cas de douleur", type="MEDICAMENT")
        ],
        doc_date=date.today()
    )
    
    custom_config = None
    if payload:
        dump_func = getattr(payload, "model_dump", getattr(payload, "dict", None))
        if dump_func:
            custom_config = {k: v for k, v in dump_func().items() if v is not None}
            
    try:
        pdf_path = doc_factory.create_ordonnance(mock_patient, mock_data, db, current_user.id, custom_config=custom_config)
        
        pdf_url = pdf_path.replace("\\", "/")
        media_path_str = str(MEDIA_DIR).replace("\\", "/")
        if media_path_str in pdf_url:
            pdf_url = "static" + pdf_url.split(media_path_str)[1]
        elif "static/" in pdf_url:
            pdf_url = pdf_url[pdf_url.find("static/"):]
            
        return {"pdf_url": pdf_url}
    except Exception as e:
        logger.error(f"Erreur Génération Aperçu Échantillon : {e}")
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
def download_document(
    document_id: str, 
    request: Request,
    db: Session = Depends(database.get_db)
):
    from backend.routers.auth import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError
    
    # 1. Extraction du token (Header ou Query)
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        token = request.query_params.get("token")
        
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")
        
    # 2. Validation du token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email or payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token invalide")
            
        current_user = db.query(models.User).filter(models.User.email == email).first()
        if not current_user or not current_user.is_active:
            raise HTTPException(status_code=401, detail="Utilisateur inactif")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token corrompu ou expiré")

    # 3. Logique de téléchargement
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
    
    # Résolution du chemin absolu (pour éviter FileNotFoundError si lancé hors du dossier backend)
    abs_path = os.path.join(BASE_DIR, doc.file_path)
    return FileResponse(path=abs_path, filename=doc.original_filename)

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
    
    # 1. Requête pour les documents (Notes d'honoraires)
    doc_query = db.query(models.DocumentArchive).join(models.Patient).filter(
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES, 
        or_(models.DocumentArchive.status == models.DocumentStatus.ACTIF, models.DocumentArchive.status == None),
        or_(models.DocumentArchive.is_latest_version == True, models.DocumentArchive.is_latest_version == None),
        or_(models.DocumentArchive.is_accounted == True, models.DocumentArchive.is_accounted == None),
        models.Patient.employer_id == user_employer_id
    )
    
    # 2. Requête pour les actes marqués pour la compta
    acte_query = db.query(models.Acte).join(models.Patient).filter(
        models.Acte.is_accounted == True,
        models.Patient.employer_id == user_employer_id
    )

    if patient_id: 
        doc_query = doc_query.filter(models.DocumentArchive.patient_id == patient_id)
        acte_query = acte_query.filter(models.Acte.patient_id == patient_id)
    if assurance: 
        doc_query = doc_query.filter(models.Patient.assurance == assurance)
        acte_query = acte_query.filter(models.Patient.assurance == assurance)
    if year: 
        doc_query = doc_query.filter(func.extract('year', models.DocumentArchive.created_at) == year)
        # Pour les actes on utilise date_debut
        acte_query = acte_query.filter(func.extract('year', models.Acte.date_debut) == year)
    if month: 
        doc_query = doc_query.filter(func.extract('month', models.DocumentArchive.created_at) == month)
        acte_query = acte_query.filter(func.extract('month', models.Acte.date_debut) == month)

    docs = doc_query.all()
    actes = acte_query.all()
    
    items = []
    total_amount = 0
    
    # Traitement des documents
    for doc in docs:
        amount = extract_amount_from_clinical_data(doc.clinical_data)
        items.append({
            "id": f"doc_{doc.id}", 
            "patient_id": doc.patient_id, 
            "patient_name": f"{doc.patient.nom} {doc.patient.prenom}", 
            "assurance": doc.patient.assurance or "AUCUNE", 
            "date": doc.created_at, 
            "title": doc.title or "Note d'honoraires", 
            "amount": amount, 
            "file_url": f"documents/{doc.id}/download",
            "payment_status": doc.payment_status or "EN_ATTENTE",
            "is_collected": doc.is_collected
        })
        total_amount += amount

    # Traitement des actes
    for acte in actes:
        items.append({
            "id": f"acte_{acte.id}",
            "patient_id": acte.patient_id,
            "patient_name": f"{acte.patient.nom} {acte.patient.prenom}",
            "assurance": acte.patient.assurance or "AUCUNE",
            "date": acte.date_debut,
            "title": f"Acte: {acte.libelle}",
            "amount": acte.montant,
            "file_url": "", # Pas de PDF pour un acte seul
            "payment_status": acte.statut_paiement or "EN_ATTENTE",
            "is_collected": acte.is_collected
        })
        total_amount += acte.montant

    # Tri par date décroissante
    items.sort(key=lambda x: x["date"], reverse=True)
    
    return {"total": len(items), "total_amount": total_amount, "items": items}

@router.get("/accounting/treasury-hub")
async def get_treasury_hub(
    db: Session = Depends(database.get_db),
    user: models.User = Depends(get_current_user)
):
    from backend.services.accounting_service import accounting_service
    return accounting_service.get_treasury_summary(db, user.get_employer_id())

@router.post("/accounting/encaisser/{item_id}")
async def mark_as_paid(
    item_id: str,
    db: Session = Depends(database.get_db),
    user: models.User = Depends(get_current_user)
):
    try:
        from backend.utils.access_control import assert_patient_access
        
        if item_id.startswith("doc_"):
            doc_id = int(item_id.split("_")[1])
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
            if not doc: raise HTTPException(status_code=404, detail="Document non trouvé")
            assert_patient_access(doc.patient_id, user, db)
            doc.payment_status = models.PaiementStatut.PAYE
            doc.is_collected = True
            doc.updated_at = datetime.now()
        elif item_id.startswith("acte_"):
            acte_id = int(item_id.split("_")[1])
            acte = db.query(models.Acte).filter(models.Acte.id == acte_id).first()
            if not acte: raise HTTPException(status_code=404, detail="Acte non trouvé")
            assert_patient_access(acte.patient_id, user, db)
            acte.statut_paiement = models.PaiementStatut.PAYE
            acte.is_collected = True
        else:
            doc_id = int(item_id)
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
            if not doc: raise HTTPException(status_code=404, detail="Élément non trouvé")
            assert_patient_access(doc.patient_id, user, db)
            doc.payment_status = models.PaiementStatut.PAYE
            doc.is_collected = True
            doc.updated_at = datetime.now()
            
        db.commit()
        return {"status": "success", "message": "Élément marqué comme encaissé"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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


def get_verification_html(title: str, subtitle: str, doc_type: str, patient_name: str, doc_date: str, primary_color: str = "#003380", status_text: str = "Authentique & Signé", status_color: str = "#10b981", is_valid: bool = True, warning_msg: str = "") -> str:
    icon_svg = '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zM9 11l2 2 4-4" stroke-linecap="round" stroke-linejoin="round"/></svg>' if is_valid else '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zM12 8v4M12 16h.01" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    gradient_color = "rgba(16, 185, 129, 0.05)" if is_valid else "rgba(239, 68, 68, 0.05)"
    shield_bg = "linear-gradient(135deg, #10b981 0%, #047857 100%)" if is_valid else "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)"
    shield_shadow = "rgba(16, 185, 129, 0.3)" if is_valid else "rgba(239, 68, 68, 0.3)"
    pulse_bg = "rgba(16, 185, 129, 0.15)" if is_valid else "rgba(239, 68, 68, 0.15)"
    
    warning_html = f'<div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 16px; padding: 12px; margin-top: 20px; font-size: 12px; color: #ef4444; font-weight: 600;">{warning_msg}</div>' if warning_msg else ''

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portail de Vérification de Document Clinique</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;900&family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: {primary_color};
            --accent: {status_color};
        }}
        body {{
            margin: 0;
            padding: 0;
            background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%);
            color: #f8fafc;
            font-family: 'Outfit', 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow-x: hidden;
        }}
        .container {{
            max-width: 500px;
            width: 90%;
            margin: 20px auto;
            text-align: center;
        }}
        .card {{
            background: rgba(15, 23, 42, 0.45);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 40px;
            padding: 40px;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
            animation: slideIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        .card::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, {gradient_color} 0%, transparent 60%);
            pointer-events: none;
        }}
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .shield-container {{
            width: 100px;
            height: 100px;
            margin: 0 auto 30px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .pulse-ring {{
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: {pulse_bg};
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(0.9); opacity: 1; }}
            100% {{ transform: scale(1.4); opacity: 0; }}
        }}
        .shield {{
            width: 70px;
            height: 70px;
            background: {shield_bg};
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 10px 25px {shield_shadow};
            position: relative;
            z-index: 10;
        }}
        .shield svg {{
            width: 32px;
            height: 32px;
            fill: none;
            stroke: white;
            stroke-width: 2.5;
        }}
        h1 {{
            font-size: 26px;
            font-weight: 900;
            margin: 0 0 8px;
            background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .subtitle {{
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            color: var(--primary);
            margin-bottom: 30px;
        }}
        .details-list {{
            text-align: left;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 24px;
            padding: 24px;
            margin-bottom: 30px;
        }}
        .detail-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 13px;
        }}
        .detail-item:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 0.1em;
        }}
        .detail-val {{
            color: #f1f5f9;
            font-weight: 600;
        }}
        .footer-brand {{
            margin-top: 40px;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.3em;
            color: #475569;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .footer-brand svg {{
            width: 14px;
            height: 14px;
            stroke: #475569;
            stroke-width: 2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="shield-container">
                <div class="pulse-ring"></div>
                <div class="shield">
                    {icon_svg}
                </div>
            </div>
            <h1>{title}</h1>
            <div class="subtitle">{subtitle}</div>
            
            <div class="details-list">
                <div class="detail-item">
                    <span class="detail-label">Type</span>
                    <span class="detail-val">{doc_type}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Patient</span>
                    <span class="detail-val">{patient_name}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Date d'Émission</span>
                    <span class="detail-val">{doc_date}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Statut</span>
                    <span class="detail-val" style="color: {status_color};">{status_text}</span>
                </div>
            </div>
            
            {warning_html}
            
            <div class="footer-brand">
                <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                Digital Crown Elite v4.6
            </div>
        </div>
    </div>
</body>
</html>"""


@router.get("/verify/{public_id}/{document_type}", response_class=HTMLResponse)
def verify_special_document(public_id: str, document_type: str, db: Session = Depends(database.get_db)):
    config = db.query(models.CabinetConfig).first()
    p_color = config.primary_color if config else "#003380"
    cabinet_name = config.nom_cabinet if config else "Cabinet Digital Crown"
    
    try:
        if document_type == "RADIO":
            # C'est un rapport radio ou une analyse
            analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == int(public_id)).first()
            if not analysis:
                analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == int(public_id)).first()
            
            if analysis:
                patient = db.query(models.Patient).filter(models.Patient.id == analysis.patient_id).first()
                p_name = f"{patient.nom.upper()} {patient.prenom[0]}." if patient else "PATIENT INCONNU"
                doc_date = analysis.created_at.strftime("%d/%m/%Y à %H:%M")
                return HTMLResponse(content=get_verification_html(
                    title="Rapport Radiographique Certifié",
                    subtitle=cabinet_name,
                    doc_type="IMAGERIE / RADIO DENTEX IA",
                    patient_name=p_name,
                    doc_date=doc_date,
                    primary_color=p_color
                ))
        
        elif document_type == "BILAN":
            patient = db.query(models.Patient).filter(models.Patient.id == int(public_id)).first()
            if patient:
                p_name = f"{patient.nom.upper()} {patient.prenom[0]}."
                doc_date = patient.created_at.strftime("%d/%m/%Y")
                return HTMLResponse(content=get_verification_html(
                    title="Bilan Orthodontique Certifié",
                    subtitle=cabinet_name,
                    doc_type="DOSSIER & BILAN CLINIQUE",
                    patient_name=p_name,
                    doc_date=doc_date,
                    primary_color=p_color
                ))
    except Exception as e:
        logger.error(f"Error verifying special document: {str(e)}")
        
    return HTMLResponse(content=get_verification_html(
        title="Document Introuvable",
        subtitle="Erreur de Sécurité",
        doc_type="INCONNU",
        patient_name="NON DISPONIBLE",
        doc_date="NON SPÉCIFIÉE",
        primary_color="#ef4444",
        status_text="Non Certifié / Invalide",
        status_color="#ef4444",
        is_valid=False,
        warning_msg="Ce document n'a pas été authentifié par notre plateforme. Il s'agit potentiellement d'un document falsifié ou expiré."
    ))

@router.get("/verify/{doc_id}", response_class=HTMLResponse)
def verify_document(doc_id: str, db: Session = Depends(database.get_db)):
    config = db.query(models.CabinetConfig).first()
    p_color = config.primary_color if config else "#003380"
    cabinet_name = config.nom_cabinet if config else "Cabinet Digital Crown"
    
    try:
        # Recherche par ID ou nom de fichier
        doc = None
        if doc_id.isdigit():
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == int(doc_id)).first()
        if not doc:
            doc = db.query(models.DocumentArchive).filter(
                or_(
                    models.DocumentArchive.filename.contains(doc_id),
                    models.DocumentArchive.original_filename.contains(doc_id)
                )
            ).first()
            
        if doc:
            patient = db.query(models.Patient).filter(models.Patient.id == doc.patient_id).first()
            p_name = f"{patient.nom.upper()} {patient.prenom[0]}." if patient else "PATIENT INCONNU"
            doc_date = doc.created_at.strftime("%d/%m/%Y à %H:%M")
            return HTMLResponse(content=get_verification_html(
                title="Document Médical Certifié",
                subtitle=cabinet_name,
                doc_type=doc.document_type.value,
                patient_name=p_name,
                doc_date=doc_date,
                primary_color=p_color
            ))
    except Exception as e:
        logger.error(f"Error verifying document: {str(e)}")
        
    return HTMLResponse(content=get_verification_html(
        title="Document Introuvable",
        subtitle="Erreur de Sécurité",
        doc_type="INCONNU",
        patient_name="NON DISPONIBLE",
        doc_date="NON SPÉCIFIÉE",
        primary_color="#ef4444",
        status_text="Non Certifié / Invalide",
        status_color="#ef4444",
        is_valid=False,
        warning_msg="Ce document n'a pas été authentifié par notre plateforme. Il s'agit potentiellement d'un document falsifié ou expiré."
    ))

@router.get("/track/{doc_id}", response_class=HTMLResponse)
def track_document(doc_id: str, db: Session = Depends(database.get_db)):
    config = db.query(models.CabinetConfig).first()
    p_color = config.primary_color if config else "#003380"
    cabinet_name = config.nom_cabinet if config else "Cabinet Digital Crown"
    
    try:
        doc = None
        if doc_id.isdigit():
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == int(doc_id)).first()
        if not doc:
            doc = db.query(models.DocumentArchive).filter(
                or_(
                    models.DocumentArchive.filename.contains(doc_id),
                    models.DocumentArchive.original_filename.contains(doc_id)
                )
            ).first()
            
        if doc:
            patient = db.query(models.Patient).filter(models.Patient.id == doc.patient_id).first()
            p_name = f"{patient.nom.upper()} {patient.prenom[0]}." if patient else "PATIENT INCONNU"
            doc_date = doc.created_at.strftime("%d/%m/%Y à %H:%M")
            
            p_status = doc.payment_status.value if doc.payment_status else "NON DÉFINI"
            p_color_map = {
                "PAYE": "#10b981",
                "PARTIEL": "#f59e0b",
                "EN_ATTENTE": "#94a3b8",
                "A_ENCAISSER": "#3b82f6"
            }
            status_color = p_color_map.get(doc.payment_status.name if hasattr(doc.payment_status, 'name') else doc.payment_status, "#10b981")
            
            return HTMLResponse(content=get_verification_html(
                title="Suivi de Dossier Trésorerie",
                subtitle=cabinet_name,
                doc_type=f"HONORAIRES / {doc.document_type.value}",
                patient_name=p_name,
                doc_date=doc_date,
                primary_color=p_color,
                status_text=f"Statut Réglement : {p_status}",
                status_color=status_color
            ))
    except Exception as e:
        logger.error(f"Error tracking document: {str(e)}")
        
    return HTMLResponse(content=get_verification_html(
        title="Dossier Introuvable",
        subtitle="Erreur de Sécurité",
        doc_type="INCONNU",
        patient_name="NON DISPONIBLE",
        doc_date="NON SPÉCIFIÉE",
        primary_color="#ef4444",
        status_text="Non Référencé / Invalide",
        status_color="#ef4444",
        is_valid=False,
        warning_msg="Ce dossier de suivi de trésorerie n'a pas été authentifié par notre plateforme. Il s'agit potentiellement d'un dossier inexistant ou archivé."
    ))
