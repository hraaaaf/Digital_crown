# ==============================================================================
# MOTEUR DE TEMPLATES PDF MULTI-TENANT
# ==============================================================================
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Environment, BaseLoader, StrictUndefined, TemplateError
import importlib.util
# Détection dynamique pour supprimer les avertissements de l'IDE sur les modules manquants
WEASYPRINT_AVAILABLE = importlib.util.find_spec("weasyprint") is not None
if not WEASYPRINT_AVAILABLE:
    logging.warning("WeasyPrint non installé. Fallback ReportLab uniquement.")

from backend import models
from backend.schemas import DesignConfig

logger = logging.getLogger(__name__)


class SecureTemplateRenderer:
    """
    Rendu Jinja2 sécurisé contre SSTI (Server-Side Template Injection).
    """
    
    # Variables autorisées uniquement
    ALLOWED_VARIABLES = {
        'patient', 'praticien', 'cabinet', 'date', 
        'content', 'titre', 'medications', 'actes', 'custom'
    }
    
    def __init__(self):
        # Environnement Jinja2 sécurisé
        self.env = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined,  # Lève une erreur si variable non définie
            autoescape=True  # Échappement HTML automatique
        )
    
    def render(self, template_html: str, context: Dict[str, Any]) -> str:
        """
        Rendu sécurisé du template.
        
        Args:
            template_html: Le HTML avec variables Jinja2
            context: Dictionnaire de variables (patient, cabinet, etc.)
        
        Returns:
            HTML rendu
        """
        # Vérification de sécurité basique
        self._security_check(template_html)
        
        # Filtrer le contexte pour ne garder que les variables autorisées
        safe_context = {
            k: v for k, v in context.items() 
            if k in self.ALLOWED_VARIABLES
        }
        
        try:
            template = self.env.from_string(template_html)
            return template.render(**safe_context)
        except TemplateError as e:
            logger.error(f"Erreur de rendu template: {e}")
            raise ValueError(f"Template invalide: {e}")
    
    def _security_check(self, html: str):
        """
        Détecte les tentatives d'injection de code Python.
        """
        dangerous_patterns = [
            '__import__', 'eval(', 'exec(', 'os.', 'sys.',
            'subprocess', 'import ', 'from ', '.read()', '.write()',
            '{{ config', '{{ self', '{% raw %}', '{% endraw %}'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in html.lower():
                logger.warning(f"Tentative d'injection détectée: {pattern}")
                raise ValueError(f"Contenu non autorisé détecté: {pattern}")


class CSSGenerator:
    """
    Convertit un DesignConfig (JSON) en CSS WeasyPrint.
    """
    
    @staticmethod
    def generate(design: DesignConfig, base_url: str = "") -> str:
        """
        Génère le CSS complet à partir de la configuration design.
        """
        fonts = design.fonts
        colors = design.colors
        layout = design.layout
        watermark = design.watermark
        header = design.header
        borders = design.borders
        typography = design.typography
        spacing = design.spacing
        
        # Gestion du letterhead (papier en-tête)
        letterhead = design.letterhead
        letterhead_css = ""
        hide_header_css = ""
        hide_footer_css = ""
        
        if letterhead.enabled and letterhead.image_url:
            # Ajouter le background-image sur la page
            letterhead_css = f"""
            background-image: url('{letterhead.image_url}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            """
            
            # Masquer le header/footer par défaut si demandé
            if letterhead.hide_default_header:
                hide_header_css = """
                .header, .doc-header { display: none !important; }
                """
            if letterhead.hide_default_footer:
                hide_footer_css = """
                .footer, .doc-footer { display: none !important; }
                """
        
        css = f"""
        @page {{
            size: {layout.page_size};
            margin: {layout.margins.top}cm {layout.margins.right}cm {layout.margins.bottom}cm {layout.margins.left}cm;
            {letterhead_css}
            
            @top-center {{
                content: "";
                height: {layout.header_height}cm;
            }}
            
            @bottom-center {{
                content: "";
                height: {layout.footer_height}cm;
            }}
        }}
        
        /* Masquage header/footer pour mode letterhead */
        {hide_header_css}
        {hide_footer_css}
        
        /* Fonts */
        body {{
            font-family: '{fonts.fr}', '{fonts.fallback}', sans-serif;
            font-size: {typography.body_size}pt;
            line-height: {typography.body_line_height};
            color: {colors.primary};
        }}
        
        .arabic {{
            font-family: '{fonts.ar}', '{fonts.fallback}', sans-serif;
            direction: rtl;
        }}
        
        /* Titre principal */
        .doc-title {{
            font-size: {typography.title_size}pt;
            font-weight: {'bold' if typography.title_bold else 'normal'};
            text-align: {typography.title_align};
            color: {colors.primary};
            margin-bottom: {spacing.section_gap_cm}cm;
            {'text-decoration: underline;' if typography.title_underline else ''}
        }}
        
        /* En-tête */
        .header {{
            {'border-bottom: 1px solid ' + borders.header_line_color + ';' if borders.header_line else ''}
            padding-bottom: 0.5cm;
            margin-bottom: {spacing.section_gap_cm}cm;
        }}
        
        .header-left {{
            float: left;
            width: 45%;
        }}
        
        .header-right {{
            float: right;
            width: 45%;
            text-align: right;
        }}
        
        .logo {{
            width: {header.logo_header_size_cm}cm;
            height: auto;
            margin: 0 auto;
            display: block;
        }}
        
        /* Informations patient */
        .patient-info {{
            margin-bottom: {spacing.section_gap_cm}cm;
            {'border-left: 3px solid ' + colors.primary + '; padding-left: 0.5cm;' if borders.content_border else ''}
        }}
        
        .patient-name {{
            font-weight: bold;
            font-size: {typography.body_size + 1}pt;
        }}
        
        /* Contenu */
        .content {{
            margin-top: {spacing.paragraph_gap_cm}cm;
        }}
        
        .content p {{
            margin-bottom: {spacing.paragraph_gap_cm}cm;
        }}
        
        /* Pied de page */
        .footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 9pt;
            color: {colors.secondary};
            {'border-top: 1px solid ' + colors.primary + '; padding-top: 0.3cm;' if borders.header_line else ''}
        }}
        
        /* Watermark */
        .watermark {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            opacity: {watermark.opacity};
            width: {watermark.size_cm}cm;
            height: auto;
            z-index: -1;
        }}
        
        /* Tableaux (ordonnances, devis) */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: {spacing.section_gap_cm}cm 0;
        }}
        
        th, td {{
            padding: 0.3cm;
            text-align: left;
            border-bottom: 1px solid {colors.secondary};
        }}
        
        th {{
            font-weight: bold;
            color: {colors.primary};
        }}
        """
        
        return css


class TemplateEngine:
    """
    Moteur unifié de génération PDF.
    """
    
    def __init__(self, static_dir: str = "static"):
        self.static_dir = static_dir
        self.renderer = SecureTemplateRenderer()
        self.css_generator = CSSGenerator()
        self._check_weasyprint()
    
    def _check_weasyprint(self):
        """Vérifie si WeasyPrint est fonctionnel."""
        if not WEASYPRINT_AVAILABLE:
            self.weasyprint_available = False
            return
        try:
            # Test simple
            weasy = importlib.import_module("weasyprint")
            weasy.HTML(string="<html><body>Test</body></html>").write_pdf()
            self.weasyprint_available = True
        except Exception as e:
            logger.warning(f"WeasyPrint non disponible: {e}. Fallback vers ReportLab.")
            self.weasyprint_available = False
    
    def generate_pdf(
        self,
        template: models.DocumentTemplate,
        cabinet: models.CabinetConfig,
        context: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Génère un PDF à partir d'un template.
        
        Args:
            template: Le DocumentTemplate à utiliser
            cabinet: La configuration du cabinet (logo, adresse...)
            context: Variables de rendu (patient, date...)
            output_path: Chemin de sortie du PDF
        
        Returns:
            Chemin du PDF généré
        """
        if not self.weasyprint_available:
            return self._fallback_reportlab(template, cabinet, context, output_path)
        
        try:
            return self._generate_weasyprint(template, cabinet, context, output_path)
        except Exception as e:
            logger.error(f"Erreur WeasyPrint: {e}. Fallback ReportLab.")
            return self._fallback_reportlab(template, cabinet, context, output_path)
    
    def _generate_weasyprint(
        self,
        template: models.DocumentTemplate,
        cabinet: models.CabinetConfig,
        context: Dict[str, Any],
        output_path: str
    ) -> str:
        """Génération via WeasyPrint (haute qualité)."""
        
        # 1. Préparer le contexte
        render_context = {
            'patient': context.get('patient', {}),
            'praticien': context.get('praticien', {}),
            'cabinet': {
                'nom': cabinet.owner.nom_complet if cabinet.owner else '',
                'adresse': cabinet.footer_address,
                'telephones': cabinet.footer_phones,
                'ville': cabinet.footer_address.split(',')[-1].strip() if ',' in cabinet.footer_address else '',
                'header_fr': cabinet.header_lines_fr,
                'header_ar': cabinet.header_lines_ar,
                'logo_url': f"file://{os.path.abspath(os.path.join(self.static_dir, 'uploads', cabinet.logo_path))}" if cabinet.logo_path else None
            },
            'date': context.get('date', datetime.now().strftime('%d/%m/%Y')),
            'titre': context.get('titre', template.name),
            'content': context.get('content', ''),
            'medications': context.get('medications', []),
            'actes': context.get('actes', []),
            'custom': context.get('custom', {})
        }
        
        # 2. Rendre le HTML
        body_html = self.renderer.render(template.body_html, render_context)
        
        # 3. Construire le HTML complet
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body>
            {f'<img src="file://{os.path.abspath(os.path.join(self.static_dir, "uploads", cabinet.logo_path))}" class="watermark" />' if cabinet.watermark_enabled and cabinet.logo_path else ''}
            
            {f'''
            <div class="header">
                <div class="header-left">
                    {'<br>'.join(cabinet.header_lines_fr)}
                </div>
                <div class="header-right arabic">
                    {'<br>'.join(cabinet.header_lines_ar)}
                </div>
                {f'<img src="file://{os.path.abspath(os.path.join(self.static_dir, "uploads", cabinet.logo_path))}" class="logo" />' if cabinet.logo_path else ''}
            </div>
            ''' if not cabinet.letterhead_path else ''}
            
            <div class="content">
                {body_html}
            </div>
            
            {f'''
            <div class="footer">
                {cabinet.footer_address}<br>
                {cabinet.footer_phones}
            </div>
            ''' if not cabinet.letterhead_path else ''}
        </body>
        </html>
        """
        
        # 4. Générer le CSS
        design_config = DesignConfig(**template.design_config)
        
        # Synchronisation des marges si un papier en-tête est actif
        if cabinet.letterhead_path:
            design_config.layout.margins.top = cabinet.margin_top
            design_config.layout.margins.bottom = cabinet.margin_bottom
            # En mode letterhead, on active aussi l'option letterhead du design si pas déjà fait
            design_config.letterhead.enabled = True
            design_config.letterhead.image_url = f"file://{os.path.abspath(os.path.join(self.static_dir, 'uploads', cabinet.letterhead_path))}"
        
        css = self.css_generator.generate(design_config)
        
        # 5. Rendu PDF
        weasy = importlib.import_module("weasyprint")
        weasy_fonts = importlib.import_module("weasyprint.text.fonts")
        
        font_config = weasy_fonts.FontConfiguration()
        weasy.HTML(string=full_html, base_url=self.static_dir).write_pdf(
            output_path,
            stylesheets=[weasy.CSS(string=css, font_config=font_config)]
        )
        
        return output_path
    
    def _fallback_reportlab(
        self,
        template: models.DocumentTemplate,
        cabinet: models.CabinetConfig,
        context: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Fallback ReportLab AMÉLIORÉ avec branding du cabinet.
        """
        from reportlab.lib.pagesizes import A5
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from backend.services.base_template import BaseTemplate
        
        logger.warning("WeasyPrint indisponible : Utilisation du fallback ReportLab avec branding.")
        
        # Marges dynamiques
        m_top = (cabinet.margin_top if cabinet else 3.6) * cm
        m_bottom = (cabinet.margin_bottom if cabinet else 3.2) * cm
        
        doc = SimpleDocTemplate(
            output_path, 
            pagesize=A5,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=m_top,
            bottomMargin=m_bottom
        )
        
        styles = getSampleStyleSheet()
        p_color = colors.HexColor(cabinet.primary_color) if cabinet else colors.HexColor('#003380')
        
        title_style = ParagraphStyle(
            'TitleBranded', 
            parent=styles['Heading1'], 
            textColor=p_color, 
            alignment=1, # TA_CENTER
            fontSize=16
        )
        
        story = []
        story.append(Spacer(1, 0.5*cm))
        # Le titre est optionnel et doit être géré dans le contenu du template
        # story.append(Paragraph(f"<u><b>{template.name.upper()}</b></u>", title_style))
        story.append(Spacer(1, 1.2*cm))
        
        # Contenu HTML simplifié pour ReportLab
        content = context.get('content', '')
        if isinstance(content, str):
            # Nettoyage minimal pour éviter les erreurs ReportLab
            content = content.replace('\n', '<br/>')
        
        story.append(Paragraph(content, styles['Normal']))
        
        # Dessin du branding
        bt = BaseTemplate()
        draw_method = lambda canv, d: bt.draw_static_elements(canv, d, config=cabinet)
        
        doc.build(story, onFirstPage=draw_method, onLaterPages=draw_method)
        return output_path
    
    def preview_template(
        self,
        template: models.DocumentTemplate,
        cabinet: models.CabinetConfig
    ) -> bytes:
        """
        Génère un PDF de prévisualisation avec des données fictives.
        """
        sample_context = {
            'patient': {'nom': 'DUPONT', 'prenom': 'Marie', 'age': 35},
            'praticien': {'nom': 'Dr. Benmoussa Achraf'},
            'date': datetime.now().strftime('%d/%m/%Y'),
            'titre': template.name.upper(),
            'content': '<p>Ceci est un texte d\'exemple pour la prévisualisation.</p>',
            'medications': [
                {'nom': 'PARACETAMOL', 'dosage': '500mg', 'posologie': '3x/jour'}
            ]
        }
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            self.generate_pdf(template, cabinet, sample_context, tmp.name)
            with open(tmp.name, 'rb') as f:
                return f.read()
