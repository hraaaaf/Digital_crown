"""
Router API pour la gestion des cabinets (Setup Wizard & Configuration).
"""
import os
import uuid
import shutil
from typing import Optional, List
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request, Form
from sqlalchemy.orm import Session
from PIL import Image

from backend import models, schemas, database
from backend.config import settings
from backend.database import get_db
from backend.routers.auth import get_current_user, is_superadmin_user
from backend.services.logo_processor import LogoProcessor
from backend.services.license_service import LicenseService

router = APIRouter()


def _has_settings_write_access(current_user: models.User) -> bool:
    if is_superadmin_user(current_user):
        return True
    if current_user.role == models.UserRole.ADMIN:
        return True
    if current_user.role == models.UserRole.DENTISTE and current_user.employer_id is None:
        return True
    permissions = current_user.permissions or {}
    return permissions.get("settings") is True


def _require_settings_write(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not _has_settings_write_access(current_user):
        raise HTTPException(status_code=403, detail="Permission Réglages requise.")
    return current_user


def _require_setup_owner(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if is_superadmin_user(current_user):
        return current_user
    if current_user.role not in (models.UserRole.ADMIN, models.UserRole.DENTISTE) or current_user.employer_id is not None:
        raise HTTPException(status_code=403, detail="Initialisation réservée au compte principal.")
    return current_user


def _normalize_hex(color) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color[:3])


def _is_neutral(color) -> bool:
    r, g, b = color[:3]
    spread = max(color[:3]) - min(color[:3])
    brightness = (r + g + b) / 3
    return spread < 18 or brightness < 28 or brightness > 240


def _extract_brand_colors(content: bytes) -> Optional[dict]:
    try:
        with Image.open(BytesIO(content)) as img:
            img = img.convert("RGB")
            img.thumbnail((240, 240))
            palette = img.convert("P", palette=Image.ADAPTIVE, colors=8)
            raw_colors = palette.getcolors() or []
            palette_values = palette.getpalette() or []
            ranked = []
            for count, idx in sorted(raw_colors, reverse=True):
                base = idx * 3
                rgb = tuple(palette_values[base:base + 3])
                if len(rgb) != 3 or _is_neutral(rgb):
                    continue
                if rgb not in ranked:
                    ranked.append(rgb)
            if not ranked:
                return None
            primary = ranked[0]
            secondary = ranked[1] if len(ranked) > 1 else primary
            accent = ranked[2] if len(ranked) > 2 else secondary
            return {
                "primary_color": _normalize_hex(primary),
                "secondary_color": _normalize_hex(secondary),
                "accent_color": _normalize_hex(accent),
            }
    except Exception:
        return None


def _normalize_clinic_update_dict(update_dict: dict, config: Optional[models.CabinetConfig] = None) -> dict:
    """Normalise les champs wizard/settings vers les colonnes CabinetConfig."""
    normalized = dict(update_dict)

    if "selected_font" in normalized and "font_fr" not in normalized:
        normalized["font_fr"] = normalized.pop("selected_font")
    elif "selected_font" in normalized:
        normalized.pop("selected_font")

    if "adresse" in normalized:
        if "footer_address" not in normalized:
            normalized["footer_address"] = normalized.pop("adresse")
        else:
            normalized.pop("adresse")

    if "telephone" in normalized:
        if "footer_phones" not in normalized:
            normalized["footer_phones"] = normalized.pop("telephone")
        else:
            normalized.pop("telephone")

    if "nom" in normalized:
        nom_val = normalized.pop("nom")
        normalized["nom_praticien"] = nom_val
        if "nom_cabinet" not in normalized:
            normalized["nom_cabinet"] = nom_val

        dr_prefixes = ("Dr.", "Dr ", "Pr.", "Pr ", "Docteur", "Professeur")
        display_name = nom_val if any(nom_val.startswith(p) for p in dr_prefixes) else f"Dr. {nom_val}"
        current_headers = list(config.header_lines_fr) if config and config.header_lines_fr else []
        if current_headers:
            current_headers[0] = display_name
        else:
            current_headers = [display_name]
        normalized["header_lines_fr"] = current_headers

    return normalized


@router.post("/recheck-license")
async def recheck_license(request: Request, current_user: models.User = Depends(get_current_user)):
    """Re-vérifie la licence (Admin only)."""
    if current_user.role != models.UserRole.ADMIN and not is_superadmin_user(current_user):
        raise HTTPException(status_code=403, detail="Non autorisé.")

    clinic_id = os.getenv("CLINIC_ID", "default_clinic")
    license_ok = await LicenseService().validate_license(clinic_id)
    request.app.state.license_ok = license_ok

    if not license_ok:
        raise HTTPException(status_code=402, detail="La licence est toujours invalide.")

    return {"message": "Licence validée avec succès. Application déverrouillée."}


@router.get("/init-status")
def check_init_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Retourne uniquement l'état d'initialisation du cabinet authentifié.

    Cette lecture est fail-closed : elle ne choisit jamais un utilisateur/config global,
    ne crée aucune configuration et ne modifie aucun état d'initialisation.
    """
    employer_id = current_user.get_employer_id()
    config = db.query(models.CabinetConfig).filter(
        models.CabinetConfig.owner_id == employer_id
    ).first()

    if not config:
        return {
            "is_initialized": False,
            "needs_setup": True,
        }

    is_initialized = bool(config.is_initialized)
    return {
        "is_initialized": is_initialized,
        "needs_setup": not is_initialized,
    }


@router.post("/")
def create_clinic(
    config: schemas.CabinetConfigCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(_require_setup_owner),
):
    """Créer la configuration d'un nouveau cabinet (Wizard étape 1)."""
    admin_user = current_user

    existing_cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == admin_user.id).first()

    create_dict = _normalize_clinic_update_dict(config.model_dump(exclude_unset=True))
    create_dict["owner_id"] = admin_user.id
    create_dict["is_initialized"] = True
    if "cabinet_type" in create_dict:
        create_dict["cabinet_type"] = models.CabinetType(create_dict["cabinet_type"])

    if existing_cabinet:
        if existing_cabinet.is_initialized:
            raise HTTPException(status_code=400, detail="Un cabinet existe déjà. Contactez l'administrateur.")
        for key, value in create_dict.items():
            if hasattr(existing_cabinet, key):
                setattr(existing_cabinet, key, value)
        db.commit()
        db.refresh(existing_cabinet)
        return existing_cabinet

    db_config = models.CabinetConfig(**create_dict)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/me")
def get_my_clinic(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Récupérer la configuration du cabinet."""
    employer_id = current_user.get_employer_id()
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non configuré")

    return config


@router.put("/me")
def update_my_clinic(
    config_update: schemas.CabinetConfigUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(_require_settings_write)
):
    """Mettre à jour la configuration du cabinet."""
    employer_id = current_user.get_employer_id()
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non configuré")

    update_dict = _normalize_clinic_update_dict(
        config_update.model_dump(exclude_unset=True),
        config=config,
    )

    for key, value in update_dict.items():
        if hasattr(config, key):
            setattr(config, key, value)

    db.commit()
    db.refresh(config)
    return config


@router.post("/me/logo")
async def upload_clinic_logo(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(_require_settings_write)
):
    """Uploader le logo du cabinet."""
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez PNG, JPG ou SVG")

    employer_id = current_user.get_employer_id()
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non configuré")

    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    clinic_dir = os.path.join(static_dir, "uploads", "clinics", config.public_id)
    os.makedirs(clinic_dir, exist_ok=True)

    file_ext = file.filename.split(".")[-1].lower()
    file_bytes = await file.read()

    if file.content_type == "image/svg+xml":
        final_bytes = file_bytes
        file_ext = "svg"
    else:
        png_bytes = LogoProcessor.process_logo(file_bytes)
        final_bytes = png_bytes
        file_ext = "png"

    unique_name = f"logo_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = os.path.join(clinic_dir, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(final_bytes)

    relative_path = f"clinics/{config.public_id}/{unique_name}"
    config.logo_path = relative_path
    db.commit()

    return {"logo_url": f"/static/uploads/{relative_path}"}


def _process_letterhead_file(content: bytes, content_type: str,
                             strip_body: bool, header_pct: float, footer_pct: float) -> tuple[bytes, bool]:
    """Prépare le fichier letterhead et retourne (octets finaux, was_processed)."""
    was_processed = False

    if content_type == "application/pdf":
        try:
            import fitz
            pdf = fitz.open(stream=content, filetype="pdf")
            if pdf.page_count == 0:
                pdf.close()
                raise HTTPException(status_code=400, detail="PDF vide — aucune page à utiliser comme modèle")
            pix = pdf[0].get_pixmap(dpi=150)
            content = pix.tobytes("png")
            pdf.close()
            was_processed = True
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="PDF illisible — impossible de le convertir en image")

    if strip_body:
        try:
            import io as _io
            from PIL import Image, ImageDraw
            img = Image.open(_io.BytesIO(content)).convert("RGB")
            w, h = img.size
            header_px = int(h * max(5.0, min(header_pct, 45.0)) / 100.0)
            footer_px = int(h * max(5.0, min(footer_pct, 45.0)) / 100.0)
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, header_px, w, h - footer_px], fill="white")
            buf = _io.BytesIO()
            img.save(buf, format="PNG")
            content = buf.getvalue()
            was_processed = True
        except Exception:
            raise HTTPException(status_code=400, detail="Image illisible — impossible de nettoyer le corps du document")

    return content, was_processed


@router.post("/me/letterhead")
async def upload_clinic_letterhead(
    file: UploadFile = File(...),
    hide_header: bool = Form(True),
    hide_footer: bool = Form(True),
    margins_top: float = Form(3.6),
    margins_bottom: float = Form(3.2),
    strip_body: bool = Form(False),
    header_pct: float = Form(25.0),
    footer_pct: float = Form(18.0),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(_require_settings_write)
):
    """Uploader le papier en-tête (Letterhead) du cabinet."""
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez PNG, JPG ou PDF")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 5Mo)")

    employer_id = current_user.get_employer_id()
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Cabinet non configuré")

    content, was_processed = _process_letterhead_file(
        content, file.content_type, strip_body, header_pct, footer_pct,
    )

    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    clinic_dir = os.path.join(static_dir, "uploads", "clinics", config.public_id)
    os.makedirs(clinic_dir, exist_ok=True)

    file_ext = "png" if was_processed else file.filename.split(".")[-1].lower()
    unique_name = f"letterhead_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = os.path.join(clinic_dir, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    relative_path = f"clinics/{config.public_id}/{unique_name}"
    config.letterhead_path = relative_path
    config.use_letterhead = True
    config.margin_top = margins_top
    config.margin_bottom = margins_bottom
    config.hide_header = hide_header
    config.hide_footer = hide_footer
    detected_colors = _extract_brand_colors(content)
    if detected_colors:
        config.primary_color = detected_colors["primary_color"]
        config.secondary_color = detected_colors["secondary_color"]
        config.accent_color = detected_colors["accent_color"]
    db.commit()

    return {
        "letterhead_url": f"/static/uploads/{relative_path}",
        "use_letterhead": True,
        "hide_default_header": hide_header,
        "hide_default_footer": hide_footer,
        "detected_colors": detected_colors,
        "message": "Letterhead uploadé avec succès.",
    }
