import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request
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
from backend.routers.auth import get_current_user, has_permission, is_superadmin_user
from backend.utils.access_control import assert_patient_access
from backend.services.document_factory import DocumentFactory
from backend.services.archive_service import get_archive_service
from backend.services.generators.report_gen import ReportGenerator
from backend.services.clinical_coherence import coherence_service
from backend.utils.accounting_utils import extract_amount_from_clinical_data
from backend.services.audit_service import audit_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Documents & Accounting"])

# Configuration
import pathlib
from backend.core.media_paths import get_media_root
from backend.core.paths import AppPaths
BASE_DIR = pathlib.Path(__file__).parent.parent
MEDIA_DIR = get_media_root()
DOCS_DIR = str(MEDIA_DIR / "documents")
STATIC_DIR = str(AppPaths.get_static_dir())

os.makedirs(DOCS_DIR, exist_ok=True)
doc_factory = DocumentFactory(output_dir=DOCS_DIR, static_dir=STATIC_DIR)

# Logic moved to backend.utils.accounting_utils


DOCUMENT_TYPE_PERMISSIONS = {
    "ordonnance": "prescriptions",
    "rapport_cephalo": "cephalo",
    "certificat": "patients",
    "devis": "accounting",
    "note": "accounting",
    "note_honoraires": "accounting",
    "honoraires": "accounting",
    "libre": "patients",
    "lettre": "patients",
    "lettre_medicale": "patients",
    "document_libre": "patients",
    "photo_clinique": "patients",
    "radiographie": "patients",
    "moulage": "patients",
    "autre": "patients",
    "echeancier": "accounting",
}


def require_document_permission(doc_type: str, current_user: models.User) -> None:
    normalized_type = doc_type.lower()
    permission = DOCUMENT_TYPE_PERMISSIONS.get(normalized_type)
    if permission and not has_permission(current_user, permission):
        raise HTTPException(status_code=403, detail=f"Accès refusé. Permission requise : {permission}.")

@router.post("/generate",
    summary="Générer un document PDF",
    description="Génère une ordonnance, certificat, devis ou note d'honoraires. La génération ReportLab tourne dans un thread dédié pour ne pas bloquer l'event loop.")
async def generate_document(req: schemas.DocumentRequest, archive: bool = False, preview: bool = False, force: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    require_document_permission(req.type, current_user)
    assert_patient_access(req.patient_id, current_user, db)
    patient_id = req.patient_id
    user_id = current_user.id

    # Génération ReportLab dans un thread dédié (non-bloquant pour l'event loop FastAPI).
    # Chaque thread crée sa propre session SQLAlchemy (thread-safety SQLite/SQLCipher).
    def _generate_pdf_in_thread() -> str:
        with database.SessionLocal() as thread_db:
            thread_patient = thread_db.query(models.Patient).filter(models.Patient.id == patient_id).first()
            if req.type == "ordonnance":
                return doc_factory.create_ordonnance(thread_patient, schemas.OrdonnanceData(**req.data), thread_db, user_id)
            elif req.type == "certificat":
                return doc_factory.create_certificat(thread_patient, schemas.CertificatData(**req.data), thread_db, user_id)
            elif req.type == "devis":
                return doc_factory.create_devis(thread_patient, schemas.DevisData(**req.data), thread_db, user_id)
            elif req.type in ["honoraires", "note"]:
                return doc_factory.create_note_honoraires(thread_patient, schemas.HonorairesData(**req.data), thread_db, user_id)
            elif req.type in ["libre", "lettre"]:
                return doc_factory.create_document_libre(thread_patient, schemas.LibreData(**req.data), thread_db, user_id)
            elif req.type == "echeancier":
                if req.data.get("plan_id"):
                    return doc_factory.create_installment_plan(thread_db, req.data.get("plan_id"), user_id)
                else:
                    # Cas où on passe les données directement (depuis le frontend)
                    # Création du plan à la volée si ce n'est pas une preview, sinon mock ?
                    # Pour simplifier, on crée le plan si 'archive=true' ou on le fait en mémoire
                    # Comme la factory s'attend à un ID en base, on crée le plan temporairement puis on l'utilise.
                    plan_data = req.data
                    db_plan = models.InstallmentPlan(
                        patient_id=thread_patient.id,
                        title=plan_data.get("title", "Échéancier"),
                        total_amount=plan_data.get("totalAmount", 0)
                    )
                    thread_db.add(db_plan)
                    thread_db.commit()
                    thread_db.refresh(db_plan)
                    
                    for inst in plan_data.get("items", []):
                        db_inst = models.Installment(
                            plan_id=db_plan.id,
                            label=inst.get("label"),
                            amount=inst.get("amount"),
                            due_date=datetime.fromisoformat(inst.get("dueDate", datetime.now().isoformat()).split("T")[0])
                        )
                        thread_db.add(db_inst)
                    thread_db.commit()
                    
                    # On retourne le doc généré. Si ce n'est qu'une preview, on pourrait le supprimer ensuite,
                    # mais il est plus sûr de le conserver comme brouillon ou de laisser le backend faire le ménage.
                    return doc_factory.create_installment_plan(thread_db, db_plan.id, user_id)
            raise ValueError(f"Type de document non supporté : {req.type}")

    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()

    try:
        pdf_path = await asyncio.to_thread(_generate_pdf_in_thread)
        
        is_financial = req.type in ["honoraires", "note", "devis"]
        should_archive = (archive or is_financial) and not preview and not isinstance(pdf_path, dict)

        if should_archive:
            with open(pdf_path, "rb") as f: pdf_content = f.read()
            archive_service = get_archive_service(db)
            
            enum_map = {
                "ordonnance": models.DocumentType.ORDONNANCE, "certificat": models.DocumentType.CERTIFICAT,
                "devis": models.DocumentType.DEVIS, "honoraires": models.DocumentType.NOTE_HONORAIRES,
                "note": models.DocumentType.NOTE_HONORAIRES, "libre": models.DocumentType.DOCUMENT_LIBRE,
                "lettre": models.DocumentType.LETTRE_MEDICALE
            }
            
            # Logique de statut stricte respectant l'UI (Ghost Treasury v4.6)
            p_status = req.payment_status if req.payment_status else models.PaiementStatut.EN_ATTENTE
            p_collected = p_status == models.PaiementStatut.PAYE
            
            doc, _ = archive_service.archive_document(
                patient_id=patient.id, file_content=pdf_content, filename=os.path.basename(pdf_path),
                doc_type=enum_map.get(req.type, models.DocumentType.AUTRE), uploaded_by_id=user_id, clinical_data=req.data,
                is_accounted=req.is_accounted, 
                payment_status=p_status,
                is_collected=p_collected,
                on_conflict=(
                    schemas.ConflictResolution.OVERWRITE
                    if force and req.type in ["honoraires", "note"]
                    else schemas.ConflictResolution.CREATE_VERSION if force
                    else schemas.ConflictResolution.CANCEL
                )
            )
            pdf_path = doc.file_path

            # Étape 2 & 3 : Trésorerie Relationnelle (Ghost Treasury v4.6)
            if req.type in ["honoraires", "note"]:
                installments_data = req.data.get('installments', [])
                is_global = req.data.get('is_global_note', False)
                total_amount = sum(float(p.get('montant', 0)) for p in req.data.get('payments', []))

                # --- UNIFY-ACT-PERSISTENCE-1 : un Acte par ligne facturée -------------
                # La table Acte ne couvrait que ~13,6% des patients réels (jamais peuplée
                # par ce flux). Commun aux deux branches ci-dessous : la granularité par
                # ligne ne doit pas dépendre du mode de règlement (échéancier ou non).
                from backend.services.acte_classification import classify_acte_type
                acte_default_statut = (
                    models.PaiementStatut.EN_ATTENTE if (is_global and installments_data) else p_status
                )
                for item in req.data.get('payments', []):
                    libelle = item.get('acte') or 'Acte'
                    montant_item = float(item.get('montant', 0))
                    db.add(models.Acte(
                        patient_id=patient.id, praticien_id=user_id,
                        type_acte=classify_acte_type(libelle), libelle=libelle, montant=montant_item,
                        date_debut=doc.created_at, statut_paiement=acte_default_statut,
                        is_accounted=req.is_accounted,
                        is_collected=(acte_default_statut == models.PaiementStatut.PAYE),
                        document_archive_id=doc.id,
                    ))
                db.commit()
                # --- fin bloc Acte -----------------------------------------------------

                if is_global and installments_data:
                    # Création d'un plan de paiement
                    plan = models.InstallmentPlan(
                        patient_id=patient.id,
                        title=f"Plan de paiement - {datetime.now().strftime('%d/%m/%Y')}",
                        total_amount=total_amount
                    )
                    db.add(plan)
                    db.flush() # Pour avoir l'ID du plan
                    
                    for inst in installments_data:
                        # try parsing date or fallback
                        due_date_str = inst.get('date', datetime.now().strftime('%Y-%m-%d'))
                        try:
                            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                        except ValueError:
                            due_date = datetime.now()
                            
                        inst_amount = float(inst.get('amount', 0))
                        send_rem = inst.get('sendReminder', False)
                        db.add(models.Installment(
                            plan_id=plan.id,
                            label=inst.get('label', 'Échéance'),
                            amount=inst_amount,
                            due_date=due_date,
                            status="EN_ATTENTE",
                            notes='{"sendReminder": true}' if send_rem else None
                        ))
                    db.commit()
                else:
                    # Structure Unique (Pas de plan global)
                    if p_status in [models.PaiementStatut.PAYE, models.PaiementStatut.PARTIEL]:
                        # Création de l'encaissement (Payment)
                        # S'il y a des paiements avec mode de règlement, on les utilise, sinon on prend le premier
                        payments_arr = req.data.get('payments', [])
                        pm = "ESPECES"
                        if payments_arr:
                            pm_str = str(payments_arr[0].get('mode_reglement', 'Espèces')).upper()
                            if "VIREMENT" in pm_str: pm = "VIREMENT"
                            elif "CH" in pm_str: pm = "CHEQUE"
                            elif "TPE" in pm_str or "CARTE" in pm_str: pm = "CARTE"
                            
                        # Si partiel, idéalement on aurait le montant partiel, sinon on met 0 ou on attend une màj manuelle
                        paid_amount = total_amount if p_status == models.PaiementStatut.PAYE else total_amount / 2.0
                        
                        payment_obj = models.Payment(
                            patient_id=patient.id,
                            amount=paid_amount,
                            payment_method=pm,
                            payment_date=doc.created_at,
                            notes=f"Lien Doc ID: {doc.id}",
                            validated_by=f"{current_user.nom_complet or 'Utilisateur'} ({current_user.role})"
                        )
                        db.add(payment_obj)
                        db.commit()

        # Analyse de cohérence déterministe.
        warnings = await coherence_service.analyze_coherence(patient.id, req.type, req.data, db, doctor_id=user_id)

        # Nettoyage du chemin pour le frontend
        if isinstance(pdf_path, dict):
            pdf_url = pdf_path["url"]
        else:
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

        # D2: Suggestion RDV après acte ortho
        rdv_suggestion = None
        if is_financial and not preview:
            items = req.data.get('items', req.data.get('payments', []))
            for item in items:
                act_name = (item.get('acte') or item.get('description') or '').lower()
                if any(k in act_name for k in ['ortho', 'semestr', 'contention', 'bagues', 'appareil ortho']):
                    from datetime import timedelta as _td
                    rdv_suggestion = {
                        "message": "Planifier le prochain RDV dans 4 semaines",
                        "suggested_date": (datetime.now() + _td(weeks=4)).strftime('%Y-%m-%d'),
                    }
                    break

        # D3: Suggestion ordonnance radio post-prothèse
        suggest_radio = False
        _PROTHESE_KEYWORDS = ['couronne', 'prothèse', 'prothese', 'bridge', 'implant', 'facette', 'inlay', 'onlay']
        if req.type in ["honoraires", "note"] and not preview:
            items = req.data.get('payments', req.data.get('items', []))
            for item in items:
                act_name = (item.get('acte') or item.get('description') or '').lower()
                if any(k in act_name for k in _PROTHESE_KEYWORDS):
                    suggest_radio = True
                    break

        audit_service.log(db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(), action="GENERATE", resource_type="Document", resource_id=str(req.patient_id), details=f"Type: {req.type}, Preview: {preview}, Archive: {archive}")
        return {"status": "success", "pdf_url": pdf_url, "warnings": warnings, "rdv_suggestion": rdv_suggestion, "suggest_radio": suggest_radio}
    except ValueError as e:
        msg = str(e)
        if msg.startswith("DOUBLE_DETECTED:"):
            raise HTTPException(status_code=409, detail={"code": "DOUBLE_DETECTED", "message": msg[len("DOUBLE_DETECTED:"):].strip()})
        logger.error(f"Erreur Génération (ValueError) : {e}")
        raise HTTPException(status_code=422, detail=msg)
    except Exception as e:
        logger.error(f"Erreur Génération : {e}")
        raise HTTPException(status_code=500, detail=str(e))


from backend.schemas.branding import BrandingPreviewPayload

@router.post("/sample-preview")
async def generate_sample_preview(
    payload: Optional[BrandingPreviewPayload] = None,
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if not has_permission(current_user, "settings"):
        raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : settings.")
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
    require_document_permission(doc_type.value if hasattr(doc_type, "value") else str(doc_type), current_user)
    assert_patient_access(patient_id, current_user, db)
    content = await file.read()
    archive_service = get_archive_service(db)
    doc, is_new = archive_service.archive_document(patient_id=patient_id, file_content=content, filename=file.filename, doc_type=doc_type, uploaded_by_id=current_user.id, title=title, on_conflict=on_conflict)
    doc_dict = {c.key: getattr(doc, c.key) for c in doc.__table__.columns}
    doc_dict["file_exists"] = bool(doc.file_path and os.path.exists(os.path.join(BASE_DIR, doc.file_path)))
    doc_dict["download_url"] = f"/api/documents/{doc.id}/download"
    audit_service.log(
        db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(),
        action="DOCUMENT_UPLOADED", resource_type=str(doc_type), resource_id=str(doc.id),
        severity="INFO", details=f"Document {doc_type} archivé pour le patient {patient_id} : {file.filename}",
    )
    return {"success": True, "message": "Archivé", "document": doc_dict}

@router.get("/", response_model=schemas.DocumentListResponse)
def list_documents(patient_id: Optional[int] = None, doc_type: Optional[schemas.DocumentType] = None, search: Optional[str] = None, page: int = 1, page_size: int = 20, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : patients.")
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

    # Enrichir chaque doc avec file_exists pour que le frontend sache quoi afficher
    def _resolve_abs(file_path: str) -> str:
        if file_path.startswith("static/archives/") or file_path.startswith("static/documents/"):
            return str(MEDIA_DIR / file_path.replace("static/", "", 1))
        return os.path.join(BASE_DIR, file_path)

    docs_out = []
    for d in docs:
        d_dict = {c.key: getattr(d, c.key) for c in d.__table__.columns}
        d_dict["file_exists"] = bool(d.file_path and os.path.exists(_resolve_abs(d.file_path)))
        d_dict["download_url"] = f"/api/documents/{d.id}/download"
        docs_out.append(d_dict)

    return {"total": total, "page": page, "page_size": page_size, "documents": docs_out}

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
        # Fichier patient generique : permission "patients" requise (S6).
        if not has_permission(current_user, "patients"):
            raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : patients.")
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
    # Gate de permission selon le type de document (S6) : symetrique a generate/archive.
    # Ex : un PDF financier (devis/honoraires) exige la permission "accounting".
    require_document_permission(
        doc.document_type.value if hasattr(doc.document_type, "value") else str(doc.document_type),
        current_user,
    )
    assert_patient_access(doc.patient_id, current_user, db)

    # Résolution du chemin absolu
    if doc.file_path.startswith("static/archives/") or doc.file_path.startswith("static/documents/"):
        abs_path = str(MEDIA_DIR / doc.file_path.replace("static/", "", 1))
    else:
        abs_path = os.path.join(BASE_DIR, doc.file_path)

    if not os.path.exists(abs_path):
        raise HTTPException(
            status_code=404,
            detail="Fichier introuvable sur ce serveur. Le document existe en base mais le fichier physique est manquant (migration ou réinstallation)."
        )
    audit_service.log(
        db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(),
        action="MEDIA_ACCESS_GRANTED", resource_type=str(doc.document_type), resource_id=str(doc.id),
        severity="INFO", details=f"Téléchargement document {doc.id} (patient {doc.patient_id})",
    )
    return FileResponse(path=abs_path, filename=doc.original_filename)

@router.post("/{document_id}/trash")
def move_to_trash(document_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if document_id.startswith("legacy:"):
        if not has_permission(current_user, "patients"):
            raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : patients.")
        raise HTTPException(status_code=400, detail="Les documents legacy ne peuvent pas être mis à la corbeille via cette interface.")

    if document_id.startswith("acte_"):
        if not has_permission(current_user, ["patients", "accounting"]):
            raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : patients ou accounting.")
        try:
            acte_id = int(document_id.split("_", 1)[1])
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Identifiant d'acte invalide.")
        acte = db.query(models.Acte).filter(models.Acte.id == acte_id).first()
        if not acte:
            raise HTTPException(status_code=404, detail="Acte introuvable")
        assert_patient_access(acte.patient_id, current_user, db)
        acte.deleted_at = datetime.now()
        db.commit()
        return {"message": "Mis à la corbeille", "id": document_id}

    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : patients.")

    if document_id.startswith("doc_"):
        doc_id_int = int(document_id.replace("doc_", ""))
        doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id_int).first()
        if not doc: raise HTTPException(status_code=404, detail="Introuvable")
        doc_id = doc.id
    else:
        try:
            doc_id = int(document_id)
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
            if not doc: raise HTTPException(status_code=404, detail="Introuvable")
        except ValueError:
            raise HTTPException(status_code=400, detail="Identifiant de document invalide.")

    assert_patient_access(doc.patient_id, current_user, db)

    # Protection des Radios (seul le dentiste / proprio peut supprimer)
    if doc.document_type in [models.DocumentType.RADIOGRAPHIE, models.DocumentType.RAPPORT_CEPHALO]:
        if not is_superadmin_user(current_user) and (not current_user.role or current_user.role.value not in ["DENTISTE", "ADMIN"]):
            raise HTTPException(
                status_code=403, 
                detail="Seul le dentiste est autorisé à supprimer une radiographie du dossier patient."
            )

    archive_service = get_archive_service(db)
    doc = archive_service.move_to_trash(doc_id)
    return {"message": "Mis à la corbeille", "id": doc.id}

@router.post("/{document_id}/restore")
def restore_from_trash(document_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if document_id.startswith("acte_"):
        if not has_permission(current_user, ["patients", "accounting"]):
            raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : patients ou accounting.")
        try:
            acte_id = int(document_id.split("_", 1)[1])
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Identifiant d'acte invalide.")
        acte = db.query(models.Acte).filter(models.Acte.id == acte_id).first()
        if not acte or acte.deleted_at is None:
            raise HTTPException(status_code=404, detail="Acte introuvable dans la corbeille")
        assert_patient_access(acte.patient_id, current_user, db)
        acte.deleted_at = None
        db.commit()
        return {"message": "Restauré", "id": document_id}

    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : patients.")
    if document_id.startswith("doc_"):
        doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.public_id == document_id).first()
        if not doc: raise HTTPException(status_code=404, detail="Introuvable")
        doc_id = doc.id
    else:
        try:
            doc_id = int(document_id)
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
            if not doc: raise HTTPException(status_code=404, detail="Introuvable")
        except ValueError:
            raise HTTPException(status_code=400, detail="Identifiant de document invalide.")
            
    assert_patient_access(doc.patient_id, current_user, db)
    
    archive_service = get_archive_service(db)
    doc = archive_service.restore_from_trash(doc_id)
    return {"message": "Restauré", "id": doc.id}

@router.delete("/{document_id}")
def permanent_delete(document_id: str, confirm: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : patients.")
    if not confirm: raise HTTPException(status_code=400, detail="Confirmation requise")
    
    if document_id.startswith("doc_"):
        doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.public_id == document_id).first()
        if not doc: raise HTTPException(status_code=404, detail="Introuvable")
        doc_id = doc.id
    else:
        try:
            doc_id = int(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Identifiant de document invalide.")
    doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
    if not doc: raise HTTPException(status_code=404, detail="Introuvable")
    assert_patient_access(doc.patient_id, current_user, db)
    
    archive_service = get_archive_service(db)
    if archive_service.permanent_delete(doc_id): return {"status": "deleted"}
    raise HTTPException(status_code=500, detail="Erreur suppression")

@router.post("/patients/{patient_id}/report")
def generate_patient_report(patient_id: int, req: schemas.CephaloPDFRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if not has_permission(current_user, "cephalo"):
        raise HTTPException(status_code=403, detail="Accès refusé. Permission requise : cephalo.")
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    last_analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).order_by(models.CephaloAnalysis.id.desc()).first()
    if not last_analysis: raise HTTPException(status_code=404, detail="Aucune analyse")

    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    validation = cephalo_consistency_validator.validate(last_analysis.angles_data or {})
    if not validation.is_valid:
        audit_service.log(
            db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(),
            action="CEPHALO_PDF_BLOCKED", resource_type="CephaloAnalysis", resource_id=str(last_analysis.id),
            severity="WARNING",
            details=f"PDF céphalo refusé (patient {patient_id}) : {'; '.join(validation.fatals)}",
        )
        raise HTTPException(
            status_code=422,
            detail={
                "message": "PDF refusé : incohérences bloquantes dans les mesures céphalo.",
                "fatals": validation.fatals,
                "warnings": validation.warnings,
            },
        )

    analysis_data = {"id": last_analysis.id, "image_path": last_analysis.image_original_path, "results": last_analysis.angles_data or {}, "landmarks": last_analysis.landmarks_data}
    if req.ai_diagnostic: analysis_data["results"]["ai_diagnostic"] = req.ai_diagnostic
    if req.clinical_data: analysis_data["results"]["clinical_data"] = req.clinical_data.model_dump() if hasattr(req.clinical_data, 'model_dump') else req.clinical_data

    pdf_path = doc_factory.create_cephalo_report(patient, analysis_data, db=db, user_id=current_user.id)
    audit_service.log(
        db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(),
        action="CEPHALO_PDF_GENERATED", resource_type="CephaloAnalysis", resource_id=str(last_analysis.id),
        severity="INFO", details=f"PDF céphalo généré (patient {patient_id})",
    )
    return FileResponse(path=pdf_path, filename=os.path.basename(pdf_path), media_type='application/pdf')


@router.post("/patients/{patient_id}/rvg")
async def upload_rvg(
    patient_id: int,
    file: UploadFile = File(...),
    radio_type: str = Form("rvg"),
    tooth_number: Optional[str] = Form(None),
    sector: Optional[str] = Form(None),
    acquisition_date: Optional[date] = Form(None),
    note: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload une radio RVG/intra-orale pour un patient.
    Stocke dans DocumentArchive avec document_type=RADIOGRAPHIE et tags=["rvg", "intra_orale"].
    """
    # Sécurité : vérifier accès patient
    assert_patient_access(patient_id, current_user, db)
    employer_id = current_user.get_employer_id()

    # Permission check
    if not has_permission(current_user, DOCUMENT_TYPE_PERMISSIONS.get("radiographie")):
        raise HTTPException(status_code=403, detail="Permission refusée pour ajouter une radio.")

    # MIME type validation
    if file.content_type not in schemas.ALLOWED_MIMES:
        raise HTTPException(
            status_code=422,
            detail=f"Format non autorisé. Acceptés : {', '.join(schemas.ALLOWED_MIMES)}",
        )

    # File size validation
    file_data = await file.read()
    if len(file_data) > schemas.MAX_RVG_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (max {schemas.MAX_RVG_SIZE // (1024*1024)} MB).",
        )

    # Extension validation
    _, ext = os.path.splitext(file.filename or "file")
    if ext.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}:
        raise HTTPException(status_code=422, detail="Extension non autorisée.")

    # Get patient
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé.")

    # Prepare clinical data
    clinical_data = {
        "radio_type": radio_type,
        "tooth_number": tooth_number,
        "sector": sector,
        "acquisition_date": str(acquisition_date) if acquisition_date else None,
        "note": note,
    }

    # Archive the document using archive_service
    archive_service = get_archive_service(db)
    from uuid import uuid4
    unique_filename = f"{uuid4()}{ext}"

    doc, _ = archive_service.archive_document(
        patient_id=patient_id,
        file_content=file_data,
        filename=file.filename or unique_filename,
        doc_type=schemas.DocumentType.RADIOGRAPHIE,
        tags=["rvg", "intra_orale"],
        clinical_data=clinical_data,
        uploaded_by_id=current_user.id,
    )

    # Audit log
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="RVG_UPLOAD",
        resource_type="RADIOGRAPHIE",
        resource_id=str(patient_id),
        severity="INFO",
        details=f"RVG téléchargée pour le patient {patient_id} : {file.filename}",
    )

    db.commit()

    return {
        "id": doc.id,
        "patient_id": doc.patient_id,
        "download_url": f"/api/documents/{doc.id}/download",
        "document_type": doc.document_type.value,
        "original_filename": doc.original_filename,
        "tags": doc.tags,
        "clinical_data": doc.clinical_data,
        "created_at": doc.created_at.isoformat(),
    }


@router.get("/patients/{patient_id}/rvg")
async def list_patient_rvg(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Liste les radios RVG d'un patient.
    Filtre par document_type=RADIOGRAPHIE et tags contenant "rvg".
    """
    # Sécurité : vérifier accès patient
    assert_patient_access(patient_id, current_user, db)

    # Permission check
    if not has_permission(current_user, DOCUMENT_TYPE_PERMISSIONS.get("radiographie")):
        raise HTTPException(status_code=403, detail="Permission refusée.")

    # Query RVG documents (tenant isolation already enforced by assert_patient_access above)
    documents = (
        db.query(models.DocumentArchive)
        .filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.document_type == schemas.DocumentType.RADIOGRAPHIE,
            models.DocumentArchive.status == schemas.DocumentStatus.ACTIF,
        )
        .order_by(desc(models.DocumentArchive.created_at))
        .all()
    )

    # Filter by tags (only RVG/intra_orale)
    rvg_docs = [d for d in documents if d.tags and ("rvg" in d.tags or "intra_orale" in d.tags)]

    return [
        {
            "id": d.id,
            "patient_id": d.patient_id,
            "document_type": d.document_type.value,
            "original_filename": d.original_filename,
            "download_url": f"/api/documents/{d.id}/download",
            "tags": d.tags,
            "clinical_data": d.clinical_data,
            "created_at": d.created_at.isoformat(),
            "uploaded_by_id": d.uploaded_by_id,
        }
        for d in rvg_docs
    ]

