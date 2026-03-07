# ==============================================================================
# SCRIPT DE SEEDING - TEMPLATES SYSTÈME (Phase SaaS)
# ==============================================================================
import logging
from sqlalchemy.orm import Session
from backend import models
from backend.schemas import DesignConfig, StyleKey

logger = logging.getLogger(__name__)


# Template HTML commun (verrouillé, sécurisé)
# Même structure pour tous les styles, seul le CSS (design_config) change
ORDONNANCE_TEMPLATE_HTML = """
<div class="document">
    <h1 class="doc-title">{{ titre }}</h1>
    
    <div class="doc-meta">
        <p>Fait à {{ cabinet.ville }}, le {{ date }}</p>
    </div>
    
    <div class="patient-info">
        <p><strong>Patient:</strong> {{ patient.nom }} {{ patient.prenom }}</p>
        <p><strong>Âge:</strong> {{ patient.age }} ans</p>
    </div>
    
    <div class="doc-content">
        {{ content }}
    </div>
    
    <div class="signature-section">
        <p class="signature-label">Signature et cachet:</p>
    </div>
</div>
""".strip()


# ==============================================================================
# CONFIGURATIONS DESIGN (6 styles)
# ==============================================================================

def get_classic_design() -> dict:
    """Style Classique - Times New Roman, noir, bordures fines."""
    return DesignConfig(
        fonts={
            "fr": "Times New Roman",
            "ar": "Amiri",
            "fallback": "Georgia"
        },
        colors={
            "primary": "#000000",
            "secondary": "#333333",
            "background": "#FFFFFF",
            "accent": "#666666"
        },
        layout={
            "page_size": "A5",
            "margins": {"top": 3.6, "right": 1.5, "bottom": 3.2, "left": 1.5},
            "header_height": 4.0,
            "footer_height": 2.5
        },
        watermark={
            "enabled": False,
            "size_cm": 5.0,
            "opacity": 0.0,
            "position": "center"
        },
        header={
            "bilingual": True,
            "logo_in_header": True,
            "logo_header_size_cm": 2.0,
            "show_lines": True
        },
        borders={
            "header_line": True,
            "header_line_style": "single",
            "header_line_color": "#000000",
            "content_border": True,
            "content_border_radius": 0
        },
        typography={
            "title_size": 20,
            "title_bold": True,
            "title_underline": True,
            "title_align": "center",
            "body_size": 11,
            "body_line_height": 1.6
        },
        spacing={
            "paragraph_gap_cm": 1.0,
            "section_gap_cm": 0.8
        }
    ).model_dump()


def get_modern_design() -> dict:
    """Style Moderne - Helvetica, bleu #003380, épuré."""
    return DesignConfig(
        fonts={
            "fr": "Helvetica",
            "ar": "Helvetica",
            "fallback": "Arial"
        },
        colors={
            "primary": "#003380",
            "secondary": "#4A6FA5",
            "background": "#FFFFFF",
            "accent": "#0055AA"
        },
        layout={
            "page_size": "A5",
            "margins": {"top": 3.6, "right": 1.5, "bottom": 3.2, "left": 1.5},
            "header_height": 4.0,
            "footer_height": 2.5
        },
        watermark={
            "enabled": True,
            "size_cm": 6.0,
            "opacity": 0.08,
            "position": "center"
        },
        header={
            "bilingual": True,
            "logo_in_header": True,
            "logo_header_size_cm": 2.5,
            "show_lines": True
        },
        borders={
            "header_line": True,
            "header_line_style": "single",
            "header_line_color": "#003380",
            "content_border": False,
            "content_border_radius": 0
        },
        typography={
            "title_size": 18,
            "title_bold": True,
            "title_underline": True,
            "title_align": "center",
            "body_size": 10,
            "body_line_height": 1.5
        },
        spacing={
            "paragraph_gap_cm": 0.8,
            "section_gap_cm": 0.6
        }
    ).model_dump()


def get_minimalist_design() -> dict:
    """Style Minimaliste - Inter, gris, espacé."""
    return DesignConfig(
        fonts={
            "fr": "Inter",
            "ar": "Arial",
            "fallback": "sans-serif"
        },
        colors={
            "primary": "#333333",
            "secondary": "#666666",
            "background": "#FFFFFF",
            "accent": "#999999"
        },
        layout={
            "page_size": "A5",
            "margins": {"top": 4.0, "right": 2.0, "bottom": 4.0, "left": 2.0},
            "header_height": 4.0,
            "footer_height": 2.5
        },
        watermark={
            "enabled": False,
            "size_cm": 5.0,
            "opacity": 0.0,
            "position": "center"
        },
        header={
            "bilingual": False,
            "logo_in_header": False,
            "logo_header_size_cm": 1.0,
            "show_lines": False
        },
        borders={
            "header_line": False,
            "header_line_style": "none",
            "header_line_color": "#CCCCCC",
            "content_border": False,
            "content_border_radius": 0
        },
        typography={
            "title_size": 16,
            "title_bold": False,
            "title_underline": False,
            "title_align": "left",
            "body_size": 10,
            "body_line_height": 1.8
        },
        spacing={
            "paragraph_gap_cm": 1.5,
            "section_gap_cm": 1.2
        }
    ).model_dump()


def get_medical_design() -> dict:
    """Style Médical - Georgia, vert #2E7D32, rassurant."""
    return DesignConfig(
        fonts={
            "fr": "Georgia",
            "ar": "Amiri",
            "fallback": "serif"
        },
        colors={
            "primary": "#2E7D32",
            "secondary": "#4CAF50",
            "background": "#F1F8E9",
            "accent": "#81C784"
        },
        layout={
            "page_size": "A5",
            "margins": {"top": 3.6, "right": 1.5, "bottom": 3.2, "left": 1.5},
            "header_height": 4.0,
            "footer_height": 2.5
        },
        watermark={
            "enabled": True,
            "size_cm": 5.0,
            "opacity": 0.05,
            "position": "center"
        },
        header={
            "bilingual": True,
            "logo_in_header": True,
            "logo_header_size_cm": 2.0,
            "show_lines": True
        },
        borders={
            "header_line": True,
            "header_line_style": "double",
            "header_line_color": "#2E7D32",
            "content_border": False,
            "content_border_radius": 0
        },
        typography={
            "title_size": 19,
            "title_bold": True,
            "title_underline": False,
            "title_align": "center",
            "body_size": 11,
            "body_line_height": 1.6
        },
        spacing={
            "paragraph_gap_cm": 1.0,
            "section_gap_cm": 0.8
        }
    ).model_dump()


def get_premium_design() -> dict:
    """Style Premium - Playfair Display, or #C9A227, élégant."""
    return DesignConfig(
        fonts={
            "fr": "Playfair Display",
            "ar": "Amiri",
            "fallback": "Georgia"
        },
        colors={
            "primary": "#C9A227",
            "secondary": "#D4AF37",
            "background": "#FFFBF0",
            "accent": "#E5C100"
        },
        layout={
            "page_size": "A5",
            "margins": {"top": 3.8, "right": 1.8, "bottom": 3.5, "left": 1.8},
            "header_height": 4.2,
            "footer_height": 2.5
        },
        watermark={
            "enabled": True,
            "size_cm": 4.0,
            "opacity": 0.15,
            "position": "top-right"
        },
        header={
            "bilingual": True,
            "logo_in_header": True,
            "logo_header_size_cm": 2.2,
            "show_lines": True
        },
        borders={
            "header_line": True,
            "header_line_style": "double",
            "header_line_color": "#C9A227",
            "content_border": True,
            "content_border_radius": 5
        },
        typography={
            "title_size": 22,
            "title_bold": True,
            "title_underline": True,
            "title_align": "center",
            "body_size": 11,
            "body_line_height": 1.7
        },
        spacing={
            "paragraph_gap_cm": 1.2,
            "section_gap_cm": 1.0
        }
    ).model_dump()


def get_saninova_design() -> dict:
    """Style Saninova (Signature) - Helvetica, bleu #003380, watermark 7cm."""
    return DesignConfig(
        fonts={
            "fr": "Helvetica-Bold",
            "ar": "Amiri",
            "fallback": "Helvetica"
        },
        colors={
            "primary": "#003380",
            "secondary": "#003380",
            "background": "#FFFFFF",
            "accent": "#0055AA"
        },
        layout={
            "page_size": "A5",
            "margins": {"top": 3.6, "right": 1.5, "bottom": 3.2, "left": 1.5},
            "header_height": 4.0,
            "footer_height": 2.5
        },
        watermark={
            "enabled": True,
            "size_cm": 7.0,
            "opacity": 0.10,
            "position": "center"
        },
        header={
            "bilingual": True,
            "logo_in_header": True,
            "logo_header_size_cm": 2.5,
            "show_lines": True
        },
        borders={
            "header_line": True,
            "header_line_style": "single",
            "header_line_color": "#003380",
            "content_border": False,
            "content_border_radius": 0
        },
        typography={
            "title_size": 18,
            "title_bold": True,
            "title_underline": True,
            "title_align": "center",
            "body_size": 11,
            "body_line_height": 1.6
        },
        spacing={
            "paragraph_gap_cm": 1.0,
            "section_gap_cm": 0.8
        }
    ).model_dump()


# ==============================================================================
# CONFIGURATION DES 6 TEMPLATES
# ==============================================================================

SYSTEM_TEMPLATES_CONFIG = [
    {
        "style_key": StyleKey.CLASSIQUE,
        "name": "Classique Élégant",
        "description": "Style médical traditionnel avec Times New Roman et bordures fines",
        "is_default": False,
        "design_config": get_classic_design
    },
    {
        "style_key": StyleKey.MODERNE,
        "name": "Moderne Épuré",
        "description": "Style contemporain avec Helvetica et lignes aériennes",
        "is_default": False,
        "design_config": get_modern_design
    },
    {
        "style_key": StyleKey.MINIMALISTE,
        "name": "Minimaliste",
        "description": "Style épuré sans bordures avec espacement généreux",
        "is_default": False,
        "design_config": get_minimalist_design
    },
    {
        "style_key": StyleKey.MEDICAL,
        "name": "Médical Hospitalier",
        "description": "Style rassurant vert avec double bordure",
        "is_default": False,
        "design_config": get_medical_design
    },
    {
        "style_key": StyleKey.PREMIUM,
        "name": "Premium Luxe",
        "description": "Style élégant doré pour cabinet haut de gamme",
        "is_default": False,
        "design_config": get_premium_design
    },
    {
        "style_key": StyleKey.SANINOVA,
        "name": "SANINOVA (Signature)",
        "description": "Style signature Digital Crown avec filigrane logo centré",
        "is_default": True,  # Celui par défaut
        "design_config": get_saninova_design
    },
]


# ==============================================================================
# FONCTION PRINCIPALE DE SEEDING
# ==============================================================================

def seed_system_templates(db: Session) -> None:
    """
    Injection des templates système au démarrage.
    Vérifie l'existence avant insertion pour éviter les doublons.
    """
    logger.info("Vérification des templates système...")
    
    templates_created = 0
    templates_skipped = 0
    
    for config in SYSTEM_TEMPLATES_CONFIG:
        # Vérifier si le template existe déjà
        existing = db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == models.DocumentType.ORDONNANCE,
            models.DocumentTemplate.style_key == config["style_key"],
            models.DocumentTemplate.is_system == True
        ).first()
        
        if existing:
            logger.debug(f"Template '{config['name']}' déjà existant, ignoré.")
            templates_skipped += 1
            continue
        
        # Créer le template
        template = models.DocumentTemplate(
            type=models.DocumentType.ORDONNANCE,
            style_key=config["style_key"],
            name=config["name"],
            description=config["description"],
            user_id=None,  # Système = pas de propriétaire
            is_system=True,
            is_default=config["is_default"],
            body_html=ORDONNANCE_TEMPLATE_HTML,
            design_config=config["design_config"]()
        )
        
        db.add(template)
        templates_created += 1
        logger.info(f"Template créé: {config['name']}")
    
    db.commit()
    
    if templates_created > 0:
        logger.info(f"✅ {templates_created} templates système créés avec succès")
    if templates_skipped > 0:
        logger.info(f"⏭️  {templates_skipped} templates déjà existants (ignorés)")
    
    if templates_created == 0 and templates_skipped == 0:
        logger.warning("Aucun template traité")


def seed_certificat_templates(db: Session) -> None:
    """
    Injection des templates pour certificats médicaux.
    """
    certificat_templates = [
        {
            "style_key": StyleKey.SANINOVA,
            "name": "Certificat Médical Standard",
            "description": "Certificat médical avec style signature",
            "is_default": True
        }
    ]
    
    CERTIFICAT_TEMPLATE_HTML = """
<div class="document">
    <h1 class="doc-title">CERTIFICAT MÉDICAL</h1>
    
    <div class="doc-meta">
        <p>Fait à {{ cabinet.ville }}, le {{ date }}</p>
    </div>
    
    <div class="patient-info">
        <p><strong>Patient:</strong> {{ patient.nom }} {{ patient.prenom }}</p>
        <p><strong>Âge:</strong> {{ patient.age }} ans</p>
    </div>
    
    <div class="doc-content">
        {{ content }}
    </div>
    
    <div class="certification-text">
        <p>Ce certificat est délivré à l'intéressé(e) pour servir et faire valoir ce que de droit.</p>
    </div>
    
    <div class="signature-section">
        <p class="signature-label">Signature et cachet:</p>
    </div>
</div>
""".strip()
    
    for config in certificat_templates:
        existing = db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == models.DocumentType.CERTIFICAT,
            models.DocumentTemplate.style_key == config["style_key"],
            models.DocumentTemplate.is_system == True
        ).first()
        
        if existing:
            continue
        
        template = models.DocumentTemplate(
            type=models.DocumentType.CERTIFICAT,
            style_key=config["style_key"],
            name=config["name"],
            description=config["description"],
            user_id=None,
            is_system=True,
            is_default=config["is_default"],
            body_html=CERTIFICAT_TEMPLATE_HTML,
            design_config=get_saninova_design()  # Même style que l'ordonnance
        )
        
        db.add(template)
        logger.info(f"Template certificat créé: {config['name']}")
    
    db.commit()


def run_full_seed(db: Session) -> None:
    """
    Exécute le seeding complet de tous les templates système.
    Appelé au démarrage de l'application.
    """
    try:
        seed_system_templates(db)
        seed_certificat_templates(db)
        logger.info("🎨 Seeding des templates terminé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors du seeding des templates: {e}")
        db.rollback()
        raise
