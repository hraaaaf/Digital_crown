"""
Router API pour la gestion des cabinets (Setup Wizard & Configuration).
"""
import os
import uuid
import shutil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend import models, schemas, database
from backend.services.card_extractor import card_extractor

router = APIRouter()


def get_db():
    """Dépendance pour obtenir une session DB."""
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/init-status")
def check_init_status(db: Session = Depends(get_db)):
    """
    Vérifie si le cabinet est initialisé. 
    Règle absolue : S'il y a un Dentiste/Admin en DB, on considère le cabinet initialisé et on bypass le Wizard.
    """
    admin_user = db.query(models.User).filter(
        models.User.role.in_([models.UserRole.ADMIN, models.UserRole.DENTISTE])
    ).first()

    if admin_user:
        any_config = db.query(models.CabinetConfig).first()
        if not any_config:
            new_config = models.CabinetConfig(
                owner_id=admin_user.id,
                nom_cabinet=admin_user.nom_complet or "Mon Cabinet",
                nom_praticien=admin_user.nom_complet or "Docteur",
                is_initialized=True
            )
            db.add(new_config)
            db.commit()
        elif not any_config.is_initialized:
            any_config.is_initialized = True
            db.commit()
            
        return {
            "is_initialized": True,
            "needs_setup": False
        }
    
    # Mode "Nouveau Client" (pas de dentiste créé / base de donnée vide)
    return {
        "is_initialized": False,
        "needs_setup": True
    }


@router.post("/")
def create_clinic(
    config: schemas.CabinetConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Créer la configuration d'un nouveau cabinet (Wizard étape 1).
    """
    existing_cabinet = db.query(models.CabinetConfig).first()
    if existing_cabinet:
        raise HTTPException(status_code=400, detail="Un cabinet existe déjà. Contactez l'administrateur.")
    
    admin_user = db.query(models.User).filter(
        models.User.role == models.UserRole.ADMIN
    ).first()
    
    if not admin_user:
        from backend.database import pwd_context
        admin_user = models.User(
            email="admin@digitalcrown.local",
            hashed_password=pwd_context.hash("admin123"),
            role=models.UserRole.ADMIN,
            nom_complet=config.header_lines_fr[0] if config.header_lines_fr else "Administrateur"
        )
        db.add(admin_user)
        db.flush()
    
    db_config = models.CabinetConfig(
        owner_id=admin_user.id,
        nom_cabinet=config.nom_cabinet,
        header_lines_fr=config.header_lines_fr,
        header_lines_ar=config.header_lines_ar,
        footer_address=config.footer_address,
        footer_phones=config.footer_phones,
        primary_color=config.primary_color,
        font_fr=config.font_fr,
        font_ar=config.font_ar,
        watermark_enabled=config.watermark_enabled,
        watermark_opacity=config.watermark_opacity,
        selected_theme=config.selected_theme,
        cabinet_type=models.CabinetType(config.cabinet_type),
        is_initialized=True
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config


@router.get("/me")
def get_my_clinic(db: Session = Depends(get_db)):
    """Récupérer la configuration du cabinet."""
    config = db.query(models.CabinetConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non configuré")
    
    return config


@router.put("/me")
def update_my_clinic(
    config_update: schemas.CabinetConfigUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour la configuration du cabinet."""
    config = db.query(models.CabinetConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non trouvé")
    
    update_dict = config_update.model_dump(exclude_unset=True)
    
    # Mapping intelligent des alias vers les colonnes physiques
    if "adresse" in update_dict:
        if "footer_address" not in update_dict:
            update_dict["footer_address"] = update_dict.pop("adresse")
        else:
            update_dict.pop("adresse")
            
    if "telephone" in update_dict:
        if "footer_phones" not in update_dict:
            update_dict["footer_phones"] = update_dict.pop("telephone")
        else:
            update_dict.pop("telephone")
            
    if "nom" in update_dict:
        nom_val = update_dict.pop("nom")
        update_dict["nom_praticien"] = nom_val
        if "nom_cabinet" not in update_dict:
            update_dict["nom_cabinet"] = nom_val
            
        current_headers = list(config.header_lines_fr) if config.header_lines_fr else []
        if current_headers:
            current_headers[0] = nom_val
        else:
            current_headers = [nom_val]
        update_dict["header_lines_fr"] = current_headers
        
    for key, value in update_dict.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.post("/me/logo")
async def upload_clinic_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Uploader le logo du cabinet."""
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez PNG, JPG ou SVG")
    
    config = db.query(models.CabinetConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non configuré")
    
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    clinic_dir = os.path.join(static_dir, "uploads", "clinics", config.public_id)
    os.makedirs(clinic_dir, exist_ok=True)
    
    file_ext = file.filename.split(".")[-1]
    unique_name = f"logo_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = os.path.join(clinic_dir, unique_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    relative_path = f"clinics/{config.public_id}/{unique_name}"
    config.logo_path = relative_path
    db.commit()
    
    return {"logo_url": f"/static/uploads/{relative_path}"}


@router.post("/me/letterhead")
async def upload_clinic_letterhead(
    file: UploadFile = File(...),
    hide_header: bool = True,
    hide_footer: bool = True,
    margins_top: float = 3.6,
    margins_bottom: float = 3.2,
    db: Session = Depends(get_db)
):
    """Uploader le papier en-tête (Letterhead) du cabinet."""
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Format non supporté. Utilisez PNG, JPG ou PDF"
        )
    
    file_size = 0
    chunk_size = 1024 * 1024
    chunks = []
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        chunks.append(chunk)
        if file_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 5Mo)")
    
    file_content = b"".join(chunks)
    
    config = db.query(models.CabinetConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non configuré")
    
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    clinic_dir = os.path.join(static_dir, "uploads", "clinics", config.public_id)
    os.makedirs(clinic_dir, exist_ok=True)
    
    file_ext = file.filename.split(".")[-1]
    if file_ext.lower() == "pdf":
        file_ext = "png"
    unique_name = f"letterhead_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = os.path.join(clinic_dir, unique_name)
    
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    relative_path = f"clinics/{config.public_id}/{unique_name}"
    config.letterhead_path = relative_path
    config.margin_top = margins_top
    config.margin_bottom = margins_bottom
    db.commit()
    
    return {
        "letterhead_url": f"/static/uploads/{relative_path}",
        "hide_default_header": hide_header,
        "hide_default_footer": hide_footer,
        "message": "Letterhead uploadé avec succès."
    }

@router.post("/extract-card")
async def extract_business_card(file: UploadFile = File(...)):
    """Extraction IA d'une carte de visite pour remplissage auto."""
    # Sauvegarde temporaire
    temp_path = f"temp_card_{uuid.uuid4().hex}.jpg"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        data = await card_extractor.extract(temp_path)
        return data
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
