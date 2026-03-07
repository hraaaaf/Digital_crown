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
    Vérifier si le cabinet est initialisé (pour le wizard).
    """
    any_config = db.query(models.CabinetConfig).first()
    
    if any_config:
        return {
            "is_initialized": any_config.is_initialized,
            "needs_setup": not any_config.is_initialized
        }
    
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
        header_lines_fr=config.header_lines_fr,
        header_lines_ar=config.header_lines_ar,
        footer_address=config.footer_address,
        footer_phones=config.footer_phones,
        primary_color=config.primary_color,
        font_fr=config.font_fr,
        font_ar=config.font_ar,
        watermark_enabled=config.watermark_enabled,
        watermark_opacity=config.watermark_opacity,
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
    
    for key, value in config_update.model_dump(exclude_unset=True).items():
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
    db.commit()
    
    return {
        "letterhead_url": f"/static/uploads/{relative_path}",
        "hide_default_header": hide_header,
        "hide_default_footer": hide_footer,
        "message": "Letterhead uploadé avec succès."
    }
