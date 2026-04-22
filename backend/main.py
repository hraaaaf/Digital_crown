# ==============================================================================
# FICHIER 3 : backend/main.py
# ==============================================================================
import os
import shutil
import uuid
import time
import subprocess
import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from pydantic import BaseModel

# --- IMPORTS SERVICES IA (INSTANCE SINGLETON DYNAMIQUE) ---
from backend.services.cephalo_engine import cephalo_engine
from backend.services.vision_service import vision_engine
from backend.services.ai_advisor import ai_advisor
from backend.services.prescription_service import prescription_service

# --- IMPORTS SERVICES DOCUMENTS ---
from backend.services.pdf_generator import PDFReportGenerator
from backend.services.document_factory import DocumentFactory
from backend.services.archive_service import ArchiveService, get_archive_service
from backend.services.generators.report_gen import ReportGenerator

# --- IMPORTS SÉCURITÉ ---
from backend.services.file_validator import (
    validate_uploaded_image, 
    sanitize_filename,
    ALLOWED_EXTENSIONS
)

from backend import models, schemas, database
from backend.seed_templates import run_full_seed
import contextlib

logger = logging.getLogger(__name__)

# --- MAPPING POUR L'ARCHIVE COMPTABLE ---
MONTHS_FR = {
    1: "Janvier", 2: "Fevrier", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Aout", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Decembre"
}

# --- CONFIGURATION CHEMINS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
RADIO_DIR = os.path.join(STATIC_DIR, "uploads", "radios")
REPORTS_DIR = os.path.join(STATIC_DIR, "reports")
DOCS_DIR = os.path.join(STATIC_DIR, "documents")
BACKUP_DIR = os.path.join(STATIC_DIR, "backups")

os.makedirs(RADIO_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Instanciation des Moteurs
pdf_engine = PDFReportGenerator(output_dir=REPORTS_DIR)
doc_factory = DocumentFactory(output_dir=DOCS_DIR)

# --- LIFESPAN (Démarrage & Arrêt) ---
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    logger.info("Démarrage du système Digital Crown...")
    
    # 1. Initialisation BDD
    try:
        models.Base.metadata.create_all(bind=database.engine)
        # Migration manuelle pour les nouvelles colonnes si create_all ne les a pas ajoutées 
        # (create_all n'ajoute pas de colonnes aux tables existantes)
        from sqlalchemy import text
        with database.engine.connect() as connection:
            for col_name, col_def in [
                ("contacts_json", "JSON DEFAULT '{}'"),
                ("cloture_note_template", "TEXT DEFAULT 'Arrêtée la présente note à la somme de {total_words} TTC.'"),
                ("cloture_devis_template", "TEXT DEFAULT 'Arrêté le présent devis à la somme de {total_words} TTC.'")
            ]:
                res = connection.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name='cabinet_configs' AND column_name='{col_name}'"))
                if not res.fetchone():
                    logger.info(f"Migration: Ajout de la colonne {col_name}...")
                    connection.execute(text(f"ALTER TABLE cabinet_configs ADD COLUMN {col_name} {col_def}"))
                    connection.commit()
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation/migration BDD: {e}")
    
    # 2. Seeding des templates système
    try:
        with database.SessionLocal() as db:
            run_full_seed(db)
    except Exception as e:
        logger.warning(f"Seeding initial reporté: {e}")
        
    yield
    
    # Arrêt
    logger.info("Arrêt du système...")

app = FastAPI(
    title="Digital Crown API - SANINOVA Edition",
    lifespan=lifespan
)

# --- MIDDLEWARES ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Logue les détails des erreurs 422 pour le débugging."""
    logger.error(f"422 Validation Error: {request.method} {request.url}")
    logger.error(f"Détails: {exc.errors()}")
    # Pour le body, c'est asynchrone, on peut le logger si besoin mais attention aux gros payloads
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# --- CORS CONFIGURATION ---
# En production, définir ALLOWED_ORIGINS dans le .env
# Ex: ALLOWED_ORIGINS=http://localhost:5173,https://moncabinet.com
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes
    allow_headers=["*"],  # Autorise tous les headers
    expose_headers=["X-Total-Count"],
    max_age=600,  # Cache preflight 10 minutes
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Import et inclusion du routeur clinics (APRÈS app = FastAPI())
from backend.routers.clinics import router as clinics_router
app.include_router(clinics_router, prefix="/api/clinics", tags=["Clinics"])

# DEBUG: Afficher les routes enregistrées au démarrage
logger.info("=== ROUTES ENREGISTREES ===")
for route in app.routes:
    if hasattr(route, "methods") and hasattr(route, "path"):
        logger.info(f"  {route.methods} {route.path}")
logger.info("===========================")

# Suppression de l'initialisation BDD et seeding obsolètes hors lifespan


# ==============================================================================
# --- SPRINT : ADMIN & DASHBOARD TEMPS RÉEL ---
# ==============================================================================

class CabinetUpdate(BaseModel):
    """Schéma de mise à jour injecté localement pour garantir la stabilité"""
    nom_complet: Optional[str] = None
    nom: Optional[str] = None  # Alias pour le frontend
    specialites: Optional[str] = None
    adresse_complete: Optional[str] = None
    adresse: Optional[str] = None  # Alias pour le frontend
    telephone_fixe: Optional[str] = None
    telephone: Optional[str] = None  # Alias pour le frontend
    telephone_mobile: Optional[str] = None
    identifiants_legaux: Optional[Dict[str, str]] = None
    inpe: Optional[str] = None  # Alias pour le frontend

@app.get("/debug/normalize-docs")
def normalize_docs(db: Session = Depends(database.get_db)):
    """Normalise la casse des types de documents (Enum PostgreSQL)."""
    try:
        from sqlalchemy import text
        # On passe par le type TEXT pour la normalisation
        # Note: On cast vers DocumentType (Enum) si possible, sinon on laisse en VARCHAR pour l'update
        # 1. Normaliser les notes d'honoraires (Pluriel)
        db.execute(text("UPDATE document_archives SET document_type = 'NOTE_HONORAIRES' WHERE document_type::text IN ('note_honoraires', 'note_honoraire', 'NOTE_HONORAIRE', 'note_honoraires');"))
        # 2. Normaliser les autres types standards
        db.execute(text("UPDATE document_archives SET document_type = 'ORDONNANCE' WHERE document_type::text IN ('ordonnance', 'ORDONNANCE');"))
        db.execute(text("UPDATE document_archives SET document_type = 'DEVIS' WHERE document_type::text IN ('devis', 'DEVIS');"))
        db.execute(text("UPDATE document_archives SET document_type = 'CERTIFICAT' WHERE document_type::text IN ('certificat', 'CERTIFICAT');"))
        # 3. Gérer le cas BILAN -> RAPPORT_CEPHALO
        db.execute(text("UPDATE document_archives SET document_type = 'RAPPORT_CEPHALO' WHERE document_type::text IN ('bilan', 'BILAN', 'rapport_cephalo');"))
        # 4. LIBRE
        db.execute(text("UPDATE document_archives SET document_type = 'DOCUMENT_LIBRE' WHERE document_type::text IN ('libre', 'LIBRE', 'document_libre');"))
        
        db.commit()
        return {"status": "success", "message": "Types de documents normalisés avec succès."}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@app.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(database.get_db)):
    """Remonte les métriques temps réel conformes à l'interface DashboardStats."""
    total_p = db.query(models.Patient).count()
    total_a = db.query(models.CephaloAnalysis).count()
    
    # Récupération des 5 derniers patients avec sécurité anti-null
    db_recent = db.query(models.Patient).order_by(models.Patient.created_at.desc()).limit(5).all()
    
    recent_list = []
    now = datetime.now()
    
    for p in db_recent:
        # Extraction sécurisée du dernier acte
        last_acte = p.actes[-1] if p.actes else None
        
        # Calcul du temps relatif (ex: "2h")
        delta = now - p.created_at
        time_str = f"{delta.seconds // 3600}h" if delta.days == 0 else f"{delta.days}j"

        recent_list.append({
            "id": p.id,
            "nom": (p.nom or "").upper(),
            "prenom": (p.prenom or "").capitalize(),
            "acte": last_acte.libelle if last_acte else "Consultation",
            "time": time_str,
            "type": last_acte.type_acte.value if last_acte else "Ortho"
        })
    
    return {
        "total_patients": total_p,
        "total_analyses": total_a,
        "in_waiting": 4, 
        "weekly_activity": [20, 45, 30, 85, 60, 90, 40],
        "recent_patients": recent_list
    }

@app.put("/cabinet/me", response_model=schemas.PraticienProfileOut)
def update_cabinet_info(settings: CabinetUpdate, db: Session = Depends(database.get_db)):
    """Met à jour les informations globales du praticien/cabinet."""
    praticien = db.query(models.User).filter(models.User.role.in_([models.UserRole.DENTISTE, models.UserRole.ADMIN])).first()
    if not praticien: 
        raise HTTPException(status_code=404, detail="Cabinet introuvable")
    
    update_data = settings.model_dump(exclude_unset=True) if hasattr(settings, 'model_dump') else settings.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "nom":
            praticien.nom_complet = value
        elif key == "adresse":
            praticien.adresse_complete = value
        elif key == "telephone":
            praticien.telephone_fixe = value
        elif key == "inpe":
            legaux = dict(praticien.identifiants_legaux or {})
            legaux["INPE"] = value
            praticien.identifiants_legaux = legaux
        elif hasattr(praticien, key):
            setattr(praticien, key, value)
        
    db.commit()
    db.refresh(praticien)
    return praticien

@app.get("/admin/export-db")
def export_database():
    """Système de Backup intelligent."""
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_url = str(database.engine.url)
    
    if "sqlite" in db_url:
        db_path = db_url.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Fichier de base de données SQLite introuvable.")
        return FileResponse(path=db_path, filename=f"backup_clinique_{now_str}.db", media_type='application/octet-stream')
        
    elif "postgresql" in db_url:
        dump_filename = f"backup_clinique_{now_str}.sql"
        dump_path = os.path.join(BACKUP_DIR, dump_filename)
        try:
            url = database.engine.url
            env = os.environ.copy()
            if url.password:
                env['PGPASSWORD'] = url.password
            
            subprocess.run([
                "pg_dump", "-h", url.host or "localhost", "-U", url.username or "postgres", "-f", dump_path, url.database
            ], env=env, check=True)
            
            return FileResponse(path=dump_path, filename=dump_filename, media_type='application/octet-stream')
        except Exception as e:
            logger.error(f"Erreur lors du dump PostgreSQL: {e}")
            raise HTTPException(status_code=500, detail="Échec de la sauvegarde PostgreSQL.")
            
    else:
        raise HTTPException(status_code=400, detail="Moteur de base de données non supporté pour l'export direct.")

# ==============================================================================
# --- ROUTES DE BASE : CABINET & PATIENTS ---
# ==============================================================================

@app.get("/cabinet/me", response_model=schemas.PraticienProfileOut)
def get_cabinet_info(db: Session = Depends(database.get_db)):
    """Récupère les informations du praticien ( identity )."""
    praticien = db.query(models.User).filter(models.User.role.in_([models.UserRole.DENTISTE, models.UserRole.ADMIN])).first()
    if not praticien: raise HTTPException(status_code=404, detail="Cabinet introuvable")
    
    # Injection des alias pour compatibilité frontend (Settings.tsx)
    praticien.nom = praticien.nom_complet
    praticien.adresse = praticien.adresse_complete
    praticien.telephone = praticien.telephone_fixe
    praticien.inpe = (praticien.identifiants_legaux or {}).get("INPE", "")
    
    return praticien

def check_duplicate_patient(db: Session, nom: str, prenom: str, date_naissance: datetime, exclude_id: int = None) -> models.Patient:
    """
    Vérifie si un patient avec le même nom/prénom/date existe déjà (insensible à la casse).
    Retourne le patient existant ou None.
    """
    from sqlalchemy import func
    
    query = db.query(models.Patient).filter(
        func.lower(models.Patient.nom) == nom.lower().strip(),
        func.lower(models.Patient.prenom) == prenom.lower().strip(),
        models.Patient.date_naissance == date_naissance
    )
    
    if exclude_id:
        query = query.filter(models.Patient.id != exclude_id)
    
    return query.first()


def generate_next_dossier_number(db: Session) -> str:
    """
    Génère le prochain numéro de dossier disponible.
    Format: P-XXXXXX (ex: P-000001, P-000002, etc.)
    """
    from sqlalchemy import func
    
    # Récupérer le dernier patient créé
    last_patient = db.query(models.Patient).order_by(models.Patient.id.desc()).first()
    
    if last_patient and last_patient.numero_dossier:
        # Essayer d'extraire le numéro du dernier dossier
        try:
            # Format attendu: P-XXXXXX
            last_num = int(last_patient.numero_dossier.split('-')[1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            # Si le format est différent, compter le nombre total de patients
            count = db.query(models.Patient).count()
            next_num = count + 1
    else:
        # Premier patient
        next_num = 1
    
    return f"P-{next_num:06d}"


@app.get("/patients/next-dossier-number")
def get_next_dossier_number(db: Session = Depends(database.get_db)):
    """
    Retourne le prochain numéro de dossier disponible.
    Utile pour le frontend lors de la création d'un nouveau patient.
    """
    next_number = generate_next_dossier_number(db)
    return {"next_number": next_number}


@app.get("/patients/", response_model=List[schemas.PatientOut])
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Patient).offset(skip).limit(limit).all()


@app.post("/patients/", response_model=schemas.PatientOut)
def create_patient(
    patient: schemas.PatientBase, 
    force_create: bool = False,  # Paramètre pour forcer la création malgré le doublon
    db: Session = Depends(database.get_db)
):
    """
    Crée un nouveau patient avec vérification des doublons.
    Si force_create=False et doublon détecté -> retourne une erreur 409 avec le patient existant.
    Si numero_dossier n'est pas fourni, il sera généré automatiquement.
    """
    try:
        # Vérifier les doublons (insensible à la casse)
        existing = check_duplicate_patient(
            db, 
            patient.nom, 
            patient.prenom, 
            patient.date_naissance
        )
        
        if existing and not force_create:
            raise HTTPException(
                status_code=409,  # Conflict
                detail={
                    "message": "Un patient avec le même nom, prénom et date de naissance existe déjà.",
                    "existing_patient": {
                        "id": existing.id,
                        "nom": existing.nom,
                        "prenom": existing.prenom,
                        "date_naissance": existing.date_naissance.isoformat() if existing.date_naissance else None,
                        "created_at": existing.created_at.isoformat() if existing.created_at else None
                    },
                    "suggestion": "Utilisez force_create=true pour créer malgré le doublon, ou ouvrez le dossier existant."
                }
            )
        
        patient_data = patient.model_dump() if hasattr(patient, 'model_dump') else patient.dict()
        # Normaliser le nom/prénom (première lettre majuscule)
        patient_data['nom'] = patient_data['nom'].upper().strip()
        patient_data['prenom'] = patient_data['prenom'].capitalize().strip()
        
        # Générer automatiquement le numéro de dossier si non fourni ou vide
        if not patient_data.get('numero_dossier'):
            patient_data['numero_dossier'] = generate_next_dossier_number(db)
        else:
            # Vérifier que le numéro de dossier n'existe pas déjà
            existing_numero = db.query(models.Patient).filter(
                models.Patient.numero_dossier == patient_data['numero_dossier']
            ).first()
            if existing_numero:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": f"Le numéro de dossier '{patient_data['numero_dossier']}' existe déjà.",
                        "existing_patient": {
                            "id": existing_numero.id,
                            "numero_dossier": existing_numero.numero_dossier,
                            "nom": existing_numero.nom,
                            "prenom": existing_numero.prenom,
                        },
                        "suggestion": "Utilisez un autre numéro ou laissez vide pour générer automatiquement."
                    }
                )
        
        # Le sexe est déjà une string valide (M/F) grâce à Pydantic
        
        db_patient = models.Patient(**patient_data)
        db.add(db_patient); db.flush()
        
        # Extraire les antécédents médicaux s'ils sont fournis
        antecedents = patient_data.pop('antecedents_medicaux', None)
        db.add(models.DossierClinique(
            patient_id=db_patient.id, 
            is_ortho_active=False,
            antecedents_medicaux=antecedents
        ))
        db.commit(); db.refresh(db_patient)
        return db_patient
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patients/check-duplicate")
def check_patient_duplicate(
    patient: schemas.PatientBase,
    db: Session = Depends(database.get_db)
):
    """
    Endpoint de pré-vérification pour le frontend.
    Retourne les doublons potentiels sans créer le patient.
    """
    existing = check_duplicate_patient(
        db, 
        patient.nom, 
        patient.prenom, 
        patient.date_naissance
    )
    
    if existing:
        return {
            "has_duplicate": True,
            "existing_patient": {
                "id": existing.id,
                "nom": existing.nom,
                "prenom": existing.prenom,
                "date_naissance": existing.date_naissance.isoformat() if existing.date_naissance else None,
                "created_at": existing.created_at.isoformat() if existing.created_at else None
            },
            "similarity": "exact"  # Pourrait être "fuzzy" dans le futur
        }
    
    return {"has_duplicate": False}

@app.get("/patients/{patient_id}", response_model=schemas.PatientOut)
def read_patient(patient_id: int, db: Session = Depends(database.get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable")
    return patient

@app.put("/patients/{patient_id}", response_model=schemas.PatientOut)
def update_patient(
    patient_id: int, 
    patient_update: schemas.PatientBase, 
    force_update: bool = False,
    db: Session = Depends(database.get_db)
):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient: raise HTTPException(status_code=404, detail="Patient introuvable")
    
    # Vérifier si la mise à jour créerait un doublon
    existing = check_duplicate_patient(
        db,
        patient_update.nom,
        patient_update.prenom,
        patient_update.date_naissance,
        exclude_id=patient_id
    )
    
    if existing and not force_update:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Ces modifications créeraient un doublon avec un patient existant.",
                "existing_patient": {
                    "id": existing.id,
                    "nom": existing.nom,
                    "prenom": existing.prenom,
                    "date_naissance": existing.date_naissance.isoformat() if existing.date_naissance else None,
                },
                "suggestion": "Utilisez force_update=true pour forcer la modification."
            }
        )
    
    update_data = patient_update.model_dump() if hasattr(patient_update, 'model_dump') else patient_update.dict()
    # Normaliser
    update_data['nom'] = update_data['nom'].upper().strip()
    update_data['prenom'] = update_data['prenom'].capitalize().strip()
    
    # Vérifier l'unicité du numéro de dossier si modifié
    if update_data.get('numero_dossier') and update_data['numero_dossier'] != db_patient.numero_dossier:
        existing_numero = db.query(models.Patient).filter(
            models.Patient.numero_dossier == update_data['numero_dossier'],
            models.Patient.id != patient_id
        ).first()
        if existing_numero:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": f"Le numéro de dossier '{update_data['numero_dossier']}' est déjà utilisé par un autre patient.",
                    "existing_patient": {
                        "id": existing_numero.id,
                        "numero_dossier": existing_numero.numero_dossier,
                        "nom": existing_numero.nom,
                        "prenom": existing_numero.prenom,
                    }
                }
            )
    
    for key, value in update_data.items():
        setattr(db_patient, key, value)

    db.commit(); db.refresh(db_patient)
    return db_patient

@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(database.get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient: raise HTTPException(status_code=404, detail="Patient introuvable")
    db.delete(db_patient); db.commit()
    return {"status": "success", "message": f"Dossier du patient {patient_id} supprimé avec succès"}

@app.get("/patients/{patient_id}/analyses", response_model=List[schemas.CephaloAnalysisOut])
def get_patient_analyses(patient_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).all()

# --- LECTURE DES ARCHIVES PATIENT ---

@app.get("/patients/{patient_id}/documents")
def get_patient_documents(patient_id: int, db: Session = Depends(database.get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable")

    # 1. Lecture desde documents modernes (Base de données)
    docs = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        models.DocumentArchive.is_latest_version == True
    ).order_by(models.DocumentArchive.created_at.desc()).all()
    
    documents = []
    for doc in docs:
        doc_type_mapping = {
            "ORDONNANCE": "ORDONNANCE",
            "CERTIFICAT": "CERTIFICAT",
            "DEVIS": "DEVIS",
            "NOTE_HONORAIRES": "NOTE",
            "DOCUMENT_LIBRE": "LIBRE"
        }
        display_type = doc_type_mapping.get(doc.document_type.value, doc.document_type.value)
        
        pdf_path = doc.file_path.replace("\\", "/")
        if "static/" in pdf_path:
            pdf_path = pdf_path[pdf_path.find("static/"):]
            
        documents.append({
            "id": str(doc.id),
            "name": doc.original_filename,
            "type": display_type,
            "date": doc.created_at.strftime("%d/%m/%Y"),
            "url": pdf_path,
            "clinical_data": doc.clinical_data,
            "timestamp": doc.created_at.timestamp()
        })
        
    # 2. Rétrocompatibilité : Lecture des anciens fichiers (Legacy)
    # On ne les ajoute QUE s'ils ne sont pas déjà présents en base de données (doublons)
    import uuid
    p_folder = f"{patient.id}_{patient.nom.upper()}_{patient.prenom.capitalize()}"
    patient_docs_dir = os.path.join(STATIC_DIR, "patients", p_folder, "Documents")
    
    existing_filenames = {doc["name"] for doc in documents}
    
    if os.path.exists(patient_docs_dir):
        for filename in os.listdir(patient_docs_dir):
            if filename.endswith(".pdf") and filename not in existing_filenames:
                file_path = os.path.join(patient_docs_dir, filename)
                parts = filename.split('_')
                doc_type = parts[0] if len(parts) > 0 else "DOCUMENT"
                
                display_date = "N/A"
                if len(parts) > 1 and len(parts[1]) == 8:
                    d = parts[1]
                    display_date = f"{d[:2]}/{d[2:4]}/{d[4:]}"
                
                documents.append({
                    "id": f"legacy:{patient_id}:{filename}", 
                    "name": filename,
                    "type": doc_type,
                    "date": display_date,
                    "url": f"static/patients/{p_folder}/Documents/{filename}",
                    "clinical_data": None,
                    "timestamp": os.path.getmtime(file_path)
                })

    # Trier par date descendante
    documents.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return documents

# ==============================================================================
# --- ROUTES ANALYSES : ORCHESTRATION IA, DDM & BILAN COMPLET ---
# ==============================================================================

@app.post("/patients/{patient_id}/upload-radio")
def upload_radio(patient_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: 
        raise HTTPException(status_code=404, detail="Patient introuvable")

    # --- SAUVEGARDE DU FICHIER (validation simplifiée) ---
    content_type = file.content_type or ""
    if "jpeg" in content_type or "jpg" in content_type:
        ext = ".jpg"
    else:
        ext = ".png"
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_location = os.path.join(RADIO_DIR, unique_filename)
    db_path = f"static/uploads/radios/{unique_filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Vérifier que le fichier existe et a une taille > 0
    if not os.path.exists(file_location) or os.path.getsize(file_location) == 0:
        raise HTTPException(status_code=400, detail="Erreur lors de la sauvegarde du fichier")
    
    logger.info(f"Fichier sauvegardé: {file_location}, taille: {os.path.getsize(file_location)} bytes")

    # 1. Inférence Vision
    try:
        vision_result = vision_engine.predict_landmarks(file_location)
        pts = vision_result["landmarks"]
        points_dict = {p['id']: (p['x'], p['y']) for p in pts}
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de l'image: {e}")
        # Supprimer le fichier en cas d'erreur
        if os.path.exists(file_location):
            os.remove(file_location)
        raise HTTPException(status_code=400, detail=f"Impossible d'analyser l'image: {str(e)}")
    
    # 2. Calcul des métriques & Orchestration IA
    final_payload = cephalo_engine.calculate_metrics(points_dict)
    
    # 3. Initialisation structurelle V4 du conteneur Bilan
    final_payload["clinical_data"] = {
        "ddm_maxillaire": None, 
        "ddm_mandibulaire": None, 
        "ddm_reelle": None, 
        "plan_traitement": ""
    }
    
    # 4. Injection des métadonnées de vision
    final_payload["vision_metadata"] = {
        "mode_inference": vision_result["mode_inference"],
        "warning": vision_result["warning"],
        "processing_time_ms": vision_result["processing_time_ms"]
    }

    db_analysis = models.CephaloAnalysis(
        patient_id=patient_id,
        image_original_path=db_path,
        angles_data=final_payload,
        landmarks_data=pts
    )
    db.add(db_analysis); db.commit(); db.refresh(db_analysis)

    return {
        "status": "success",
        "analysis_id": db_analysis.id,
        "file_url": f"http://localhost:8000/{db_path}",
        "results": final_payload,
        "ai_diagnostic": final_payload.get("ai_narrative", {}),
        "landmarks": pts,
        "is_calibrated": db_analysis.is_calibrated,
        "mm_per_pixel": db_analysis.mm_per_pixel
    }

@app.put("/analyses/{analysis_id}")
def update_analysis(analysis_id: int, req: schemas.AnalysisUpdate, db: Session = Depends(database.get_db)):
    """Sauvegarde unifiée V4 : Points, Diagnostic IA et Données de Moulages (DDM)."""
    db_analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if not db_analysis: raise HTTPException(status_code=404, detail="Analyse introuvable")

    # 1. Recalcul Géométrique (avec projections McNamara si fournies)
    points_dict = {p.id: (p.x, p.y) for p in req.landmarks}
    mcnamara_proj = req.mcnmara_projections.model_dump() if req.mcnmara_projections else None
    final_payload = cephalo_engine.calculate_metrics(points_dict, custom_mm_ratio=req.mm_per_pixel, mcnamara_projections=mcnamara_proj)

    # 2. Persistance du Diagnostic IA (Master Logic)
    if req.ai_diagnostic:
        # On conserve le texte corrigé manuellement par le médecin
        final_payload["ai_diagnostic"] = req.ai_diagnostic
    else:
        # On régénère via l'IA
        final_payload["ai_diagnostic"] = ai_advisor.generate_diagnostic(final_payload)
    
    # 3. Persistance du Bilan Clinique (Moulages & Plan de Traitement)
    if req.clinical_data is not None:
        # Conversion du modèle Pydantic en Dict pour stockage JSON
        cd = req.clinical_data.model_dump() if hasattr(req.clinical_data, 'model_dump') else req.clinical_data
        
        # Calcul automatique de la DDM Réelle si l'IMPA et les DDM Cliniques sont présents
        impa = final_payload["metrics"]["analyse_dentaire"]["IMPA"]["value"]
        
        # DDM Céphalo = (IMPA − 90°) / 2.5  →  s'applique aux DEUX arcades
        ddm_cephalo = (impa - 90) / 2.5 if impa else 0
        
        # DDM Réelle Maxillaire = DDM Clinique Max + DDM Céphalo
        if cd.get("ddm_maxillaire"):
            ddm_max_clinique = cd["ddm_maxillaire"].get("calcul_ddm", 0)
            ddm_max_reelle = ddm_max_clinique + ddm_cephalo
            cd["ddm_maxillaire"]["calcul_ddm_reelle"] = round(ddm_max_reelle, 2)
        else:
            ddm_max_reelle = 0
        
        # DDM Réelle Mandibulaire = DDM Clinique Mand + DDM Céphalo
        if cd.get("ddm_mandibulaire"):
            ddm_mand_clinique = cd["ddm_mandibulaire"].get("calcul_ddm", 0)
            ddm_mand_reelle = ddm_mand_clinique + ddm_cephalo
            cd["ddm_mandibulaire"]["calcul_ddm_reelle"] = round(ddm_mand_reelle, 2)
        else:
            ddm_mand_reelle = 0
        
        # DDM Réelle Totale = Max + Mand
        cd["ddm_reelle"] = round(ddm_max_reelle + ddm_mand_reelle, 2)
            
        final_payload["clinical_data"] = cd
    else:
        # Conservation des données existantes si non fournies dans l'update
        final_payload["clinical_data"] = db_analysis.angles_data.get("clinical_data", {})

    if req.mm_per_pixel is not None:
        final_payload["mm_per_pixel"] = req.mm_per_pixel
    
    # 4. Stockage des projections McNamara (A', B', N') si fournies par le frontend
    if req.mcnmara_projections:
        final_payload["mcnamara_projections"] = req.mcnmara_projections.model_dump() if hasattr(req.mcnmara_projections, 'model_dump') else req.mcnmara_projections.dict()
        logger.info(f"[McNamara] Projections reçues - A': {final_payload['mcnamara_projections'].get('A_prime')}, B': {final_payload['mcnamara_projections'].get('B_prime')}")

    # 5. Mise à jour Base de données
    db_analysis.landmarks_data = [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in req.landmarks]
    db_analysis.angles_data = final_payload
    db.commit()
    db.refresh(db_analysis)

    # LOG: Compare landmarks reçus et renvoyés
    import logging
    logging.warning("[PUT /analyses/%s] Landmarks reçus: %s", analysis_id, req.landmarks)
    logging.warning("[PUT /analyses/%s] Landmarks renvoyés: %s", analysis_id, db_analysis.landmarks_data)

    return {
        "status": "success",
        "analysis_id": db_analysis.id,
        "results": final_payload,
        "ai_diagnostic": final_payload["ai_diagnostic"],
        "landmarks": db_analysis.landmarks_data,
        "is_calibrated": db_analysis.is_calibrated,
        "mm_per_pixel": db_analysis.mm_per_pixel
    }


@app.post("/analyses/{analysis_id}/calibrate", response_model=schemas.CalibrationResponse)
def calibrate_analysis(
    analysis_id: int, 
    req: schemas.CalibrationRequest, 
    db: Session = Depends(database.get_db)
):
    """
    Calibration de l'échelle mm/pixel pour une analyse céphalométrique.
    
    Le praticien définit deux points sur la radio et indique la distance réelle en mm.
    Le système calcule automatiquement le ratio mm/pixel.
    """
    db_analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    
    # Calcul de la distance en pixels entre les deux points
    dx = req.p2.x - req.p1.x
    dy = req.p2.y - req.p1.y
    distance_pixels = (dx**2 + dy**2)**0.5
    
    if distance_pixels < 10:
        raise HTTPException(
            status_code=400, 
            detail="Distance trop faible entre les points (min 10 pixels)"
        )
    
    # Calcul du ratio mm/pixel
    mm_per_pixel = req.distance_mm / distance_pixels
    
    # Stockage dans la base de données
    db_analysis.is_calibrated = True
    db_analysis.mm_per_pixel = mm_per_pixel
    db_analysis.calibration_data = {
        "p1": {"x": req.p1.x, "y": req.p1.y},
        "p2": {"x": req.p2.x, "y": req.p2.y},
        "distance_mm": req.distance_mm,
        "distance_pixels": round(distance_pixels, 2)
    }
    
    # Recalcul des métriques avec le nouveau ratio
    if db_analysis.landmarks_data:
        points_dict = {p['id']: (p['x'], p['y']) for p in db_analysis.landmarks_data}
        new_angles = cephalo_engine.calculate_metrics(points_dict, custom_mm_ratio=mm_per_pixel)
        db_analysis.angles_data = new_angles
    
    db.commit()
    db.refresh(db_analysis)
    
    logger.info(
        f"Calibration effectuée pour analyse {analysis_id}: "
        f"{mm_per_pixel:.4f} mm/pixel ({req.distance_mm}mm / {distance_pixels:.1f}px)"
    )
    
    return schemas.CalibrationResponse(
        success=True,
        mm_per_pixel=round(mm_per_pixel, 6),
        message=f"Calibration effectuée: {mm_per_pixel:.4f} mm/pixel"
    )


@app.post("/patients/{patient_id}/pdf")
def generate_patient_pdf(patient_id: int, req: schemas.CephaloPDFRequest, db: Session = Depends(database.get_db)):
    """Nouvelle Usine PDF Bilan Complet : Intègre les corrections textuelles et les moulages."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable")

    last_analysis = db.query(models.CephaloAnalysis)\
        .filter(models.CephaloAnalysis.patient_id == patient_id)\
        .order_by(models.CephaloAnalysis.id.desc())\
        .first()

    if not last_analysis: raise HTTPException(status_code=404, detail="Aucune analyse disponible")

    analysis_data = {
        "id": last_analysis.id,
        "image_path": last_analysis.image_original_path,
        "results": last_analysis.angles_data or {},
        "landmarks": last_analysis.landmarks_data
    }

    # 🛡️ Injection Prioritaire : Ecrasement du JSON par les modifications en temps réel du Frontend (Live Preview)
    if req.ai_diagnostic:
        analysis_data["results"]["ai_diagnostic"] = req.ai_diagnostic
    
    if req.clinical_data:
        analysis_data["results"]["clinical_data"] = req.clinical_data.model_dump() if hasattr(req.clinical_data, 'model_dump') else req.clinical_data

    try:
        # Orchestration vers le nouveau moteur de Bilan Complet Multi-pages
        # Transmission de db et owner_id pour thémisation
        pdf_path = doc_factory.create_bilan_report(patient, analysis_data, db=db, user_id=patient.owner_id)
    except Exception as e:
        import traceback
        logger.error(f"Échec de la génération du Bilan Complet PDF : {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error(f"Analysis data: {analysis_data}")
        raise HTTPException(status_code=500, detail=f"Erreur PDF : {str(e)}")

    return FileResponse(path=pdf_path, filename=os.path.basename(pdf_path), media_type='application/pdf')

# ==============================================================================
# --- SPRINT 3 : AI ADVISOR ENDPOINT ---
# ==============================================================================

@app.get("/patients/{patient_id}/ai-diagnostic")
def get_ai_diagnostic(patient_id: int, db: Session = Depends(database.get_db)):
    """Route de secours pour regénérer un diagnostic IA à la demande"""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable.")

    last_analysis = db.query(models.CephaloAnalysis)\
        .filter(models.CephaloAnalysis.patient_id == patient_id)\
        .order_by(models.CephaloAnalysis.id.desc())\
        .first()

    if not last_analysis: raise HTTPException(status_code=404, detail="Aucune analyse trouvée.")

    try:
        report = ai_advisor.generate_diagnostic(last_analysis.angles_data)
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du moteur IA : {str(e)}")

# ==============================================================================
# --- PHASE 2 : SMART ORDONNANCE ENDPOINTS ---
# ==============================================================================

@app.get("/prescriptions/categories/search", response_model=List[schemas.ClinicalCategoryOut])
def search_categories(q: str, db: Session = Depends(database.get_db)):
    return db.query(models.ClinicalCategory).filter(models.ClinicalCategory.label.ilike(f"%{q}%")).limit(10).all()

@app.get("/prescriptions/search", response_model=List[schemas.MedicationOut])
def search_medications(q: str, db: Session = Depends(database.get_db)):
    return db.query(models.Medication).filter(models.Medication.nom.ilike(f"%{q}%")).order_by(models.Medication.usage_count.desc()).limit(20).all()

@app.get("/prescriptions/suggest", response_model=List[schemas.ClinicalProtocolOut])
def suggest_protocols(category_id: int, db: Session = Depends(database.get_db)):
    protocols = db.query(models.ClinicalProtocol).filter(models.ClinicalProtocol.category_id == category_id).all()
    if not protocols: raise HTTPException(status_code=404, detail="Aucun protocole")
    return protocols

@app.post("/prescriptions/learn")
def learn_prescription(req: schemas.PrescriptionLearnRequest, db: Session = Depends(database.get_db)):
    for med_data in req.medications:
        if not med_data.nom or not med_data.nom.strip(): continue
            
        norm_name = med_data.nom.strip().lower()
        db_med = db.query(models.Medication).filter(func.lower(models.Medication.nom) == norm_name).first()
        if db_med: db_med.usage_count += 1
        else: db.add(models.Medication(nom=med_data.nom.strip(), dosage=med_data.dosage, forme=med_data.forme, usage_count=1))
    db.commit()
    return {"status": "success", "message": "Base de connaissance mise à jour"}

# ==============================================================================
# --- SPRINT 1 : SMART BILLING / CATALOGUE DES ACTES ENDPOINTS ---
# ==============================================================================

@app.get("/actes/catalog/search", response_model=List[schemas.ClinicalActCatalogOut])
def search_clinical_acts(q: str, db: Session = Depends(database.get_db)):
    normalized_q = q.strip().lower()
    return db.query(models.ClinicalActCatalog)\
             .filter(func.lower(models.ClinicalActCatalog.name).ilike(f"%{normalized_q}%"))\
             .order_by(models.ClinicalActCatalog.usage_count.desc())\
             .limit(20)\
             .all()

@app.post("/actes/catalog/learn")
def learn_clinical_acts(req: schemas.ActLearnRequest, db: Session = Depends(database.get_db)):
    for act in req.acts:
        if not act.name or not act.name.strip(): continue
            
        norm_name = act.name.strip().lower()
        db_act = db.query(models.ClinicalActCatalog).filter(func.lower(models.ClinicalActCatalog.name) == norm_name).first()
        
        if db_act:
            db.query(models.ClinicalActCatalog).filter(models.ClinicalActCatalog.id == db_act.id).update({"usage_count": models.ClinicalActCatalog.usage_count + 1})
        else:
            db.add(models.ClinicalActCatalog(name=act.name.strip(), base_price=act.price_applied, usage_count=1))
            
    db.commit()
    return {"status": "success", "message": "Catalogue des actes synchronisé"}

# ==============================================================================
# --- DOCUMENT FACTORY ROUTE (AVEC ARCHIVAGE PAR PARAMÈTRE D'URL) ---
# ==============================================================================

@app.post("/documents/generate")
def generate_document(req: schemas.DocumentRequest, archive: bool = False, preview: bool = False, force: bool = False, db: Session = Depends(database.get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == req.patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable")

    # --- AJOUT: Récupération de l'identité du médecin ---
    user = db.query(models.User).first()
    user_id = user.id if user else 1

    pdf_path = ""
    try:
        if req.type == "ordonnance":
            data = schemas.OrdonnanceData(**req.data)
            has_valid_meds = any(m.nom and m.nom.strip() for m in data.medications)
            if archive and not has_valid_meds:
                raise ValueError("Interdiction du système : Impossible d'archiver une ordonnance sans médicament.")
            
            # --- CORRECTION: On passe db et user_id ---
            pdf_path = doc_factory.create_ordonnance(patient, data, db, user_id)
            
        elif req.type == "certificat":
            pdf_path = doc_factory.create_certificat(patient, schemas.CertificatData(**req.data), db, user_id)
        elif req.type == "devis":
            pdf_path = doc_factory.create_devis(patient, schemas.DevisData(**req.data), db, user_id)
        elif req.type in ["honoraires", "note"]: 
            pdf_path = doc_factory.create_note_honoraires(patient, schemas.HonorairesData(**req.data), db, user_id)
        elif req.type == "libre":
            pdf_path = doc_factory.create_document_libre(patient, schemas.LibreData(**req.data), db, user_id)
        else:
            raise HTTPException(status_code=400, detail="Type inconnu")

        # Documents financiers : archivage SYSTÉMATIQUE sauf en mode aperçu live
        # Le live preview (preview=True) ne déclenche JAMAIS l'archivage
        is_financial = req.type in ["honoraires", "note", "devis"]
        should_archive = (archive or is_financial) and not preview

        if should_archive:
            today = date.today()
            date_str = today.strftime('%d%m%Y')
            ts = str(int(time.time()))[-4:]
            final_filename = f"{req.type.upper() if req.type != 'honoraires' else 'NOTE'}_{date_str}_{ts}_{patient.nom.upper()}.pdf"
            
            source_path = os.path.join(BASE_DIR, pdf_path) if not os.path.isabs(pdf_path) else pdf_path
            if os.path.exists(source_path):
                with open(source_path, "rb") as f:
                    pdf_content = f.read()
                
                enum_map = {
                    "ordonnance": models.DocumentType.ORDONNANCE,
                    "certificat": models.DocumentType.CERTIFICAT,
                    "devis": models.DocumentType.DEVIS,
                    "honoraires": models.DocumentType.NOTE_HONORAIRES,
                    "note": models.DocumentType.NOTE_HONORAIRES,
                    "libre": models.DocumentType.DOCUMENT_LIBRE
                }
                mapped_type = enum_map.get(req.type, models.DocumentType.AUTRE)
                
                title_map = {
                    "ordonnance": "Ordonnance",
                    "certificat": "Certificat médical",
                    "devis": "Devis estimatif",
                    "honoraires": "Note d'honoraires",
                    "note": "Note d'honoraires",
                    "libre": "Document libre"
                }

                # Gestion du mode 'force' pour les doublons
                on_conflict = schemas.ConflictResolution.CREATE_VERSION if force else schemas.ConflictResolution.CANCEL

                archive_service = get_archive_service(db)
                logger.info(f"Archivage en cours pour {patient.nom} - Type: {mapped_type}")
                doc, _ = archive_service.archive_document(
                    patient_id=patient.id,
                    file_content=pdf_content,
                    filename=final_filename,
                    doc_type=mapped_type,
                    uploaded_by_id=user_id,
                    clinical_data=req.data,
                    title=title_map.get(req.type, req.type.capitalize()),
                    on_conflict=on_conflict
                )
                logger.info(f"Archivage réussi : ID {doc.id}")
                pdf_path = doc.file_path.replace("\\", "/")

    except Exception as e:
        logger.error(f"Erreur lors de la génération/archivage : {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    # Nettoyage et normalisation du chemin pour le frontend
    # On garantit que l'URL retournée commence par static/
    clean_path = pdf_path.replace("\\", "/")
    if "static/" in clean_path:
        idx = clean_path.find("static/")
        clean_path = clean_path[idx:]
    
    return {
        "status": "success", 
        "pdf_url": clean_path,
        "filename": final_filename if should_archive else os.path.basename(pdf_path)
    }
# ==============================================================================
# --- SPRINT 5 : ARCHIVAGE DOCUMENTAIRE VERSIONNE ---
# ==============================================================================

# TEMP: Authentification simplifiée (à remplacer par JWT)
def get_current_user(db: Session = Depends(database.get_db)) -> Optional[models.User]:
    """Récupère l'utilisateur courant (mock pour le développement)."""
    # En production, utiliser OAuth2/JWT
    return db.query(models.User).first()

@app.post("/documents/check-conflicts", response_model=schemas.DocumentConflictCheck)
def check_document_conflicts(
    patient_id: int,
    doc_type: schemas.DocumentType,
    filename: str,
    db: Session = Depends(database.get_db)
):
    """Vérifie les conflits potentiels avant archivage (sans uploader le fichier)."""
    # Note: le hash complet nécessite le fichier, ici on fait une pré-vérification
    archive_service = get_archive_service(db)
    
    # Simuler un hash vide pour la pré-vérification
    conflict = archive_service.check_conflicts(patient_id, "", filename, doc_type)
    
    return schemas.DocumentConflictCheck(
        has_conflict=conflict.get("has_conflict", False),
        conflict_reason=conflict.get("conflict_reason"),
        suggested_action=conflict.get("suggested_action"),
        message=conflict.get("message")
    )

@app.post("/documents/archive", response_model=schemas.DocumentArchiveResponse)
async def archive_document(
    patient_id: int,
    doc_type: schemas.DocumentType,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: str = "",  # JSON string list
    on_conflict: schemas.ConflictResolution = schemas.ConflictResolution.CREATE_VERSION,
    check_conflicts: bool = True,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)  # À implémenter
):
    """Archive un document avec gestion intelligente des conflits."""
    try:
        # Lire le contenu
        content = await file.read()
        
        # Parser les tags
        import json
        tag_list = json.loads(tags) if tags else []
        
        # Service d'archivage
        archive_service = get_archive_service(db)
        
        # Vérifier les conflits
        if check_conflicts:
            file_hash = archive_service._calculate_file_hash(content)
            conflict = archive_service.check_conflicts(
                patient_id, file_hash, file.filename, doc_type
            )
            
            if conflict["has_conflict"] and on_conflict == schemas.ConflictResolution.CANCEL:
                return schemas.DocumentArchiveResponse(
                    success=False,
                    message=conflict["message"],
                    conflict_info=schemas.DocumentConflictCheck(
                        has_conflict=True,
                        conflict_reason=conflict["conflict_reason"],
                        suggested_action=conflict["suggested_action"],
                        message=conflict["message"]
                    ),
                    requires_action=True
                )
        
        # Archiver le document
        doc, is_new_version = archive_service.archive_document(
            patient_id=patient_id,
            file_content=content,
            filename=file.filename,
            doc_type=doc_type,
            uploaded_by_id=current_user.id if current_user else None,
            title=title,
            description=description,
            tags=tag_list,
            on_conflict=on_conflict
        )
        
        message = "Document archivé avec succès"
        if is_new_version:
            message = f"Nouvelle version créée (v{doc.version_number})"
        
        return schemas.DocumentArchiveResponse(
            success=True,
            message=message,
            document=doc
        )
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur archivage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=schemas.DocumentListResponse)
def list_documents(
    patient_id: Optional[int] = None,
    doc_type: Optional[schemas.DocumentType] = None,
    status: schemas.DocumentStatus = schemas.DocumentStatus.ACTIF,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(database.get_db)
):
    """Liste les documents avec filtres et recherche."""
    archive_service = get_archive_service(db)
    
    docs, total = archive_service.search_documents(
        patient_id=patient_id,
        doc_type=doc_type,
        status=status,
        search_query=search,
        page=page,
        page_size=page_size
    )
    
    return schemas.DocumentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        documents=docs
    )

@app.get("/documents/{document_id}", response_model=schemas.DocumentArchiveOut)
def get_document(
    document_id: str,
    include_versions: bool = False,
    db: Session = Depends(database.get_db)
):
    """Récupère les détails d'un document et ses versions."""
    if str(document_id).startswith("legacy:"):
        return {
            "id": document_id,
            "filename": str(document_id).split(":")[-1],
            "original_filename": str(document_id).split(":")[-1],
            "document_type": "AUTRE",
            "is_latest_version": True,
            "version_number": 1,
            "status": "ACTIF",
            "created_at": datetime.now(),
            "download_url": f"static/documents/{document_id}/download"
        }

    doc = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == int(document_id)
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    if include_versions:
        archive_service = get_archive_service(db)
        versions = archive_service.get_document_versions(doc.document_group_id)
        doc.all_versions = [
            schemas.DocumentVersionInfo(
                version_number=v.version_number,
                created_at=v.created_at,
                file_size=v.file_size,
                is_latest=v.is_latest_version
            ) for v in versions
        ]
    
    return doc

@app.get("/documents/{document_id}/download")
def download_document(
    document_id: str,
    version: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    """Télécharge un document (ou une version spécifique)."""
    if str(document_id).startswith("legacy:"):
        try:
            parts = str(document_id).split(":")
            patient_id = parts[1]
            filename = parts[2]
            patient = db.query(models.Patient).filter(models.Patient.id == int(patient_id)).first()
            if not patient: raise HTTPException(status_code=404, detail="Patient legacy introuvable")
            folder = f"{patient.id}_{patient.nom.upper()}_{patient.prenom.capitalize()}"
            file_path = os.path.join(STATIC_DIR, "patients", folder, "Documents", filename)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Fichier legacy non trouvé")
            return FileResponse(path=file_path, filename=filename, media_type="application/pdf")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    query = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == int(document_id)
    )
    
    doc = query.first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Si une version spécifique est demandée
    if version and version != doc.version_number:
        doc = db.query(models.DocumentArchive).filter(
            and_(
                models.DocumentArchive.document_group_id == doc.document_group_id,
                models.DocumentArchive.version_number == version
            )
        ).first()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Version non trouvée")
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Fichier non trouvé sur le disque")
    
    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,
        media_type="application/pdf"
    )

@app.post("/documents/{document_id}/trash", response_model=schemas.DocumentTrashResponse)
def move_to_trash(
    document_id: str,
    db: Session = Depends(database.get_db)
):
    """Déplace un document dans la corbeille (ou suppression physique si legacy)."""
    if str(document_id).startswith("legacy:"):
        # Logique de suppression physique pour les fichiers hors-BDD
        try:
            parts = str(document_id).split(":")
            if len(parts) < 3:
                 raise HTTPException(status_code=400, detail="ID legacy malformé")
            
            patient_id = parts[1]
            filename = parts[2]
            
            patient = db.query(models.Patient).filter(models.Patient.id == int(patient_id)).first()
            if not patient: raise HTTPException(status_code=404, detail="Patient legacy introuvable")
            
            folder = f"{patient.id}_{patient.nom.upper()}_{patient.prenom.capitalize()}"
            file_path = os.path.join(STATIC_DIR, "patients", folder, "Documents", filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return schemas.DocumentTrashResponse(
                message="Document legacy supprimé définitivement (pas de corbeille)",
                document_id=document_id,
                deleted_at=datetime.now(),
                permanent_delete_at=datetime.now()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur suppression legacy: {str(e)}")

    archive_service = get_archive_service(db)
    
    try:
        doc = archive_service.move_to_trash(int(document_id))
        return schemas.DocumentTrashResponse(
            message="Document déplacé dans la corbeille",
            document_id=doc.id,
            deleted_at=doc.deleted_at,
            permanent_delete_at=doc.permanent_delete_at
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/documents/{document_id}/restore", response_model=schemas.DocumentRestoreResponse)
def restore_from_trash(
    document_id: str,
    db: Session = Depends(database.get_db)
):
    """Restaure un document depuis la corbeille."""
    if str(document_id).startswith("legacy:"):
        raise HTTPException(status_code=400, detail="Les documents legacy ne supportent pas la corbeille")

    archive_service = get_archive_service(db)
    
    try:
        doc = archive_service.restore_from_trash(int(document_id))
        return schemas.DocumentRestoreResponse(
            message="Document restauré avec succès",
            document_id=doc.id,
            restored_at=datetime.now()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/documents/{document_id}")
def permanent_delete_document(
    document_id: str,
    confirm: bool = False,
    db: Session = Depends(database.get_db)
):
    """Supprime définitivement un document (admin uniquement ou depuis corbeille)."""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Vous devez confirmer la suppression définitive avec ?confirm=true"
        )
    
    archive_service = get_archive_service(db)
    
    # Vérifier que le doc est bien dans la corbeille
    try:
        doc = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == int(document_id)
        ).first()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="ID de document invalide")
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    if doc.status != models.DocumentStatus.SUPPRIME:
        raise HTTPException(
            status_code=400, 
            detail="Le document doit être dans la corbeille avant suppression définitive"
        )
    
    if archive_service.permanent_delete(document_id):
        return {"message": "Document supprimé définitivement"}
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression")

@app.get("/documents/trash/list", response_model=schemas.DocumentListResponse)
def list_trash(
    patient_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(database.get_db)
):
    """Liste les documents dans la corbeille."""
    archive_service = get_archive_service(db)
    
    docs, total = archive_service.search_documents(
        patient_id=patient_id,
        status=schemas.DocumentStatus.SUPPRIME,
        page=page,
        page_size=page_size
    )
    
    return schemas.DocumentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        documents=docs
    )

@app.post("/admin/cleanup-trash")
def cleanup_trash_cron(
    secret_key: str,  # Sécurité basique pour le cron
    db: Session = Depends(database.get_db)
):
    """
    Endpoint pour le nettoyage automatique de la corbeille (à appeler via cron).
    Ex: 0 2 * * * curl -X POST https://api/cleanup-trash?secret_key=XXX
    """
    expected_key = os.getenv("CRON_SECRET_KEY", "change-me-in-production")
    if secret_key != expected_key:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    archive_service = get_archive_service(db)
    deleted_count = archive_service.cleanup_expired_trash()
    
    return {
        "message": f"Nettoyage effectué",
        "documents_deleted": deleted_count,
        "timestamp": datetime.now()
    }

# --- Utilitaire DRY pour extraction robuste des montants ---
def _extract_amount_from_clinical_data(clinical_data: dict) -> float:
    """
    Extraction robuste du montant depuis clinical_data avec fallbacks :
      1. payments[].montant (notes d'honoraires classiques)
      2. items[].prix_unitaire (devis transformés)
      3. clé 'total' directe
    """
    if not clinical_data:
        return 0.0
    
    # Stratégie 1 : payments (notes d'honoraires)
    if 'payments' in clinical_data:
        total = sum(float(p.get('montant', 0)) for p in clinical_data['payments'])
        if total > 0:
            return total
    
    # Stratégie 2 : items (devis)
    if 'items' in clinical_data:
        total = sum(float(i.get('prix_unitaire', i.get('montant', 0))) for i in clinical_data['items'])
        if total > 0:
            return total
    
    # Stratégie 3 : clé 'total' directe
    return float(clinical_data.get('total', 0))

# Route 1463 supprimée car redondante avec la route 1286 unifiée.

@app.get("/accounting/honoraires", response_model=schemas.HonoraireListResponse)
def get_accounting_honoraires(
    patient_id: Optional[int] = None,
    assurance: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    """Liste globale des notes d'honoraires avec filtres (patient, assurance, date)."""
    query = db.query(models.DocumentArchive).join(models.Patient).filter(
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF
    )
    
    if patient_id:
        query = query.filter(models.DocumentArchive.patient_id == patient_id)
    if assurance:
        query = query.filter(models.Patient.assurance == assurance)
    if year:
        query = query.filter(func.extract('year', models.DocumentArchive.created_at) == year)
    if month:
        query = query.filter(func.extract('month', models.DocumentArchive.created_at) == month)
        
    docs = query.order_by(desc(models.DocumentArchive.created_at)).all()
    
    items = []
    total_amount = 0
    
    for doc in docs:
        # Extraction robuste du montant avec fallbacks multiples
        amount = _extract_amount_from_clinical_data(doc.clinical_data)
        
        items.append(schemas.HonoraireItem(
            id=doc.id,
            patient_id=doc.patient_id,
            patient_name=f"{doc.patient.nom} {doc.patient.prenom}",
            assurance=doc.patient.assurance,
            date=doc.created_at,
            title=doc.title or doc.original_filename or "Note d'honoraires",
            amount=amount,
            file_url=f"documents/{doc.id}/download"
        ))
        total_amount += amount
        
    return schemas.HonoraireListResponse(
        total=len(items),
        total_amount=total_amount,
        items=items
    )

@app.get("/accounting/export-pdf")
def export_accounting_pdf(
    patient_id: Optional[int] = None,
    assurance: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    """Génère et télécharge un rapport PDF récapitulatif."""
    # Rigueur CTO : On réutilise la même logique de filtrage que la liste
    query = db.query(models.DocumentArchive).join(models.Patient).filter(
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF
    )
    
    if patient_id:
        query = query.filter(models.DocumentArchive.patient_id == patient_id)
    if assurance:
        query = query.filter(models.Patient.assurance == assurance)
    if year:
        query = query.filter(func.extract('year', models.DocumentArchive.created_at) == year)
    if month:
        query = query.filter(func.extract('month', models.DocumentArchive.created_at) == month)
        
    docs = query.order_by(desc(models.DocumentArchive.created_at)).all()
    
    items = []
    total_amount = 0
    for doc in docs:
        amount = _extract_amount_from_clinical_data(doc.clinical_data)
        
        items.append(schemas.HonoraireItem(
            id=doc.id,
            patient_id=doc.patient_id,
            patient_name=f"{doc.patient.nom} {doc.patient.prenom}",
            assurance=doc.patient.assurance,
            date=doc.created_at,
            title=doc.title or doc.original_filename or "Note d'honoraires",
            amount=amount,
            file_url=f"documents/{doc.id}/download"
        ))
        total_amount += amount
        
    # Génération via le nouveau service
    report_gen = ReportGenerator()
    pdf_url = report_gen.generate_accounting_report(
        items=items,
        total_amount=total_amount,
        filters={"assurance": assurance, "month": month, "year": year}
    )
    
    return {"pdf_url": pdf_url}

@app.get("/patients/{patient_id}/appointment-intel")
def get_patient_appointment_intel(patient_id: int, db: Session = Depends(database.get_db)):
    """Analyse le dossier pour suggérer le prochain RDV."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient introuvable")

    # 1. Analyse des devis pour trouver le "Reste à faire"
    devis_docs = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.document_type == models.DocumentType.DEVIS,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF
    ).all()

    suggestion = "Consultation Standard"
    suggested_duration = 30
    has_active_plan = False

    if devis_docs:
        # On prend le plus récent
        latest_devis = sorted(devis_docs, key=lambda x: x.created_at, reverse=True)[0]
        suggestion = f"Suite Devis : {latest_devis.title or 'Traitement'}"
        has_active_plan = True
        suggested_duration = 45 # Standard pour un acte de devis

    # 2. Analyse financière (Impayés)
    notes = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF
    ).all()
    
    total_due = sum((_extract_amount_from_clinical_data(doc.clinical_data)) for doc in devis_docs)
    total_paid = sum((_extract_amount_from_clinical_data(doc.clinical_data)) for doc in notes)
    solde = total_due - total_paid

    return {
        "suggestion": suggestion,
        "duration": suggested_duration,
        "has_active_plan": has_active_plan,
        "solde_attente": solde if solde > 0 else 0,
        "alert_message": f"Patient a un solde de {solde:.0f} MAD en attente" if solde > 100 else None
    }


@app.get("/documents/stats/dashboard")
def get_document_stats(
    db: Session = Depends(database.get_db)
):
    """Statistiques pour le dashboard d'archivage."""
    total_docs = db.query(models.DocumentArchive).count()
    total_size = db.query(func.sum(models.DocumentArchive.file_size)).scalar() or 0
    trash_count = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.status == models.DocumentStatus.SUPPRIME
    ).count()
    
    # Par type
    by_type = db.query(
        models.DocumentArchive.document_type,
        func.count(models.DocumentArchive.id)
    ).group_by(models.DocumentArchive.document_type).all()
    
    return {
        "total_documents": total_docs,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "in_trash": trash_count,
        "by_type": {t.value: c for t, c in by_type}
    }



# ==============================================================================
# ROUTES API MULTI-TENANT (Phase SaaS) - TEMPLATES UNIQUEMENT
# Les routes /api/clinics sont dans backend/routers/clinics.py
# ==============================================================================

# --- Dépendances d'authentification (simplifiées pour l'instant) ---
async def get_current_user(db: Session = Depends(database.get_db)) -> models.User:
    """Récupère l'utilisateur courant (à remplacer par JWT dans production)."""
    # Pour l'instant, on prend le premier dentiste trouvé
    # TODO: Implémenter véritable auth JWT
    user = db.query(models.User).filter(
        models.User.role.in_([models.UserRole.DENTISTE, models.UserRole.ADMIN])
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Non authentifié")
    return user


# --- 2. GESTION DES TEMPLATES ---

@app.get("/api/templates")
def list_system_templates(
    type: Optional[str] = None,
    is_system: Optional[bool] = True,
    db: Session = Depends(database.get_db)
):
    """Liste les templates (système par défaut)."""
    query = db.query(models.DocumentTemplate)
    
    if is_system:
        query = query.filter(models.DocumentTemplate.is_system == True)
    
    if type:
        query = query.filter(models.DocumentTemplate.type == type)
    
    templates = query.all()
    
    # Retourner sous forme de liste simplifiée
    return [
        {
            "id": t.id,
            "type": t.type.value if hasattr(t.type, 'value') else t.type,
            "style_key": t.style_key,
            "name": t.name,
            "is_default": t.is_default,
            "description": t.description
        }
        for t in templates
    ]


@app.post("/api/templates/", response_model=schemas.DocumentTemplateOut)
def create_template(
    template: schemas.DocumentTemplateCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Créer un nouveau template personnalisé."""
    # Vérifier si c'est un admin qui crée un template système
    if template.is_system and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Seuls les admins peuvent créer des templates système")
    
    # Créer le template
    db_template = models.DocumentTemplate(
        type=template.type,
        style_key=template.style_key,
        name=template.name,
        description=template.description,
        user_id=current_user.id if not template.is_system else None,
        is_system=template.is_system,
        is_default=template.is_default,
        body_html=template.body_html,
        design_config=template.design_config.model_dump()
    )
    
    # Si c'est le template par défaut, retirer le flag des autres templates du même type
    if template.is_default:
        db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == template.type,
            models.DocumentTemplate.user_id == (current_user.id if not template.is_system else None)
        ).update({"is_default": False})
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template


@app.get("/api/clinics/{clinic_id}/templates/", response_model=List[schemas.DocumentTemplateList])
def get_clinic_templates(
    clinic_id: str,
    type: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Récupérer tous les templates actifs pour un cabinet spécifique."""
    # Vérifier que l'utilisateur a accès à ce cabinet
    config = db.query(models.CabinetConfig).filter(
        models.CabinetConfig.public_id == clinic_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non trouvé")
    
    # Vérifier les droits d'accès (propriétaire ou admin)
    if config.owner_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Accès non autorisé à ce cabinet")
    
    # Construire la requête
    query = db.query(models.DocumentTemplate).filter(
        # Templates système OU templates personnels du propriétaire
        ((models.DocumentTemplate.is_system == True) & (models.DocumentTemplate.user_id.is_(None))) |
        (models.DocumentTemplate.user_id == config.owner_id)
    )
    
    # Filtrer par type si spécifié
    if type:
        query = query.filter(models.DocumentTemplate.type == type)
    
    templates = query.all()
    
    return templates


@app.get("/api/templates/{template_id}", response_model=schemas.DocumentTemplateOut)
def get_template(
    template_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Récupérer un template spécifique."""
    template = db.query(models.DocumentTemplate).filter(
        models.DocumentTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Vérifier les droits d'accès
    if template.is_system:
        # Templates système : visibles par tous, mais body_html caché dans la réponse (géré par le schéma)
        pass
    elif template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return template


@app.put("/api/templates/{template_id}", response_model=schemas.DocumentTemplateOut)
def update_template(
    template_id: str,
    updates: schemas.DocumentTemplateUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mettre à jour un template (nom, design_config uniquement - sécurité SSTI)."""
    template = db.query(models.DocumentTemplate).filter(
        models.DocumentTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Vérifier les droits
    if template.is_system:
        raise HTTPException(status_code=403, detail="Templates système en lecture seule")
    
    if template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Mise à jour des champs autorisés
    update_data = updates.model_dump(exclude_unset=True)
    
    if "design_config" in update_data:
        template.design_config = update_data["design_config"].model_dump()
    
    if "name" in update_data:
        template.name = update_data["name"]
    
    if "is_default" in update_data and update_data["is_default"]:
        # Retirer le flag des autres templates du même type
        db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == template.type,
            models.DocumentTemplate.user_id == current_user.id,
            models.DocumentTemplate.id != template_id
        ).update({"is_default": False})
        template.is_default = True
    
    db.commit()
    db.refresh(template)
    return template


@app.delete("/api/templates/{template_id}")
def delete_template(
    template_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Supprimer un template personnalisé."""
    template = db.query(models.DocumentTemplate).filter(
        models.DocumentTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    if template.is_system:
        raise HTTPException(status_code=403, detail="Impossible de supprimer un template système")
    
    if template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    db.delete(template)
    db.commit()
    
    return {"message": "Template supprimé avec succès"}


@app.post("/api/templates/{template_id}/set-default")
def set_default_template(
    template_id: str,
    db: Session = Depends(database.get_db)
):
    """Définir un template comme défaut pour son type."""
    template = db.query(models.DocumentTemplate).filter(
        models.DocumentTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Pour le MVP, on permet l'accès sans vérification stricte
    # Retirer le flag des autres templates du même type
    target_user_id = template.user_id if not template.is_system else None
    query = db.query(models.DocumentTemplate).filter(
        models.DocumentTemplate.type == template.type,
        models.DocumentTemplate.id != template_id
    )
    
    if template.is_system:
        query = query.filter(models.DocumentTemplate.is_system == True)
    else:
        query = query.filter(models.DocumentTemplate.user_id == target_user_id)
    
    query.update({"is_default": False})
    
    template.is_default = True
    db.commit()
    
    return {"message": "Template défini comme défaut"}



@app.get("/prescriptions/smart-suggest/{patient_id}")
async def get_smart_suggestion(
    patient_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Analyse le contexte clinique et propose une ordonnance (version personnalisée).
    """
    today = datetime.now()
    start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
    
    rdvs = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id,
        models.Appointment.datetime_start >= start_of_day
    ).all()
    
    act_names = [r.motif for r in rdvs if r.motif]
    
    if not act_names:
        last_rdv = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_id
        ).order_by(desc(models.Appointment.datetime_start)).first()
        if last_rdv and last_rdv.motif:
            act_names = [last_rdv.motif]

    return prescription_service.resolve_smart_prescription(
        db, patient_id, act_names, doctor_id=current_user.id
    )

@app.post("/api/prescriptions/preferences/")
async def save_prescription_preference(
    payload: Dict, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Enregistre une surcharge de protocole pour le médecin connecté.
    """
    act_code = payload.get("act_code")
    drugs = payload.get("drugs")
    
    if not act_code or not drugs:
        raise HTTPException(status_code=400, detail="Données incomplètes")

    # Chercher si une pref existe déjà
    pref = db.query(models.DoctorPrescriptionPreference).filter(
        models.DoctorPrescriptionPreference.doctor_id == current_user.id,
        models.DoctorPrescriptionPreference.act_code == act_code
    ).first()
    
    if pref:
        pref.drugs_json = drugs
    else:
        pref = models.DoctorPrescriptionPreference(
            doctor_id=current_user.id,
            act_code=act_code,
            drugs_json=drugs
        )
        db.add(pref)
    
    db.commit()
    return {"status": "success", "message": f"Protocole personnalisé enregistré pour {act_code}"}


# ==============================================================================
# --- ROUTES AGENDA CLINIQUE ---
# ==============================================================================

@app.get("/appointments/", response_model=List[schemas.AppointmentOut])
def get_appointments(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Appointment)
    if start_date:
        query = query.filter(models.Appointment.datetime_start >= datetime.fromisoformat(start_date.replace("Z", "+00:00")))
    if end_date:
        query = query.filter(models.Appointment.datetime_start <= datetime.fromisoformat(end_date.replace("Z", "+00:00")))
    return query.order_by(models.Appointment.datetime_start.asc()).all()

@app.post("/appointments/", response_model=schemas.AppointmentOut)
def create_appointment(
    appt: schemas.AppointmentCreate,
    db: Session = Depends(database.get_db)
):
    db_appt = models.Appointment(**appt.model_dump())
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    return db_appt

@app.put("/appointments/{id}", response_model=schemas.AppointmentOut)
def update_appointment(
    id: int,
    appt_update: schemas.AppointmentUpdate,
    db: Session = Depends(database.get_db)
):
    db_appt = db.query(models.Appointment).filter(models.Appointment.id == id).first()
    if not db_appt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    
    update_data = appt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_appt, key, value)
        
    db.commit()
    db.refresh(db_appt)
    return db_appt

@app.delete("/appointments/{id}")
def delete_appointment(id: int, db: Session = Depends(database.get_db)):
    db_appt = db.query(models.Appointment).filter(models.Appointment.id == id).first()
    if not db_appt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    db.delete(db_appt)
    db.commit()
    return {"status": "success"}
