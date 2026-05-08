# ==============================================================================
# MOTEUR DE TEMPLATES PDF MULTI-TENANT
# ==============================================================================
import logging
import os
from typing import Dict, Any
from datetime import datetime
from jinja2 import Environment, StrictUndefined, TemplateError
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
        'patient', 'patient_nom', 'patient_prenom', 'patient_age',
        'praticien', 'cabinet', 'config', 'date', 'date_generation',
        'content', 'titre', 'medications', 'actes', 'custom',
        'qr_code_url', 'logo_url', 'draw_legal_ids'
    }
    
    def __init__(self, template_dir: str = "backend/templates"):
        # Environnement Jinja2 avec FileSystemLoader pour supporter les extends
        from jinja2 import FileSystemLoader
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            undefined=StrictUndefined,
            autoescape=True
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
            if template_html.endswith('.html'):
                template = self.env.get_template(template_html)
            else:
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
            letterhead_css = (
                f"background-image: url('{letterhead.image_url}');\n"
                "background-size: cover;\n"
                "background-position: center;\n"
                "background-repeat: no-repeat;"
            )
            
            if letterhead.hide_default_header:
                hide_header_css = ".header, .doc-header { display: none !important; }"
            if letterhead.hide_default_footer:
                hide_footer_css = ".footer, .doc-footer { display: none !important; }"
        
        css_lines = []
        css_lines.append("@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@400;600&display=swap');")
        
        css_lines.append("@page {")
        css_lines.append(f"    size: {layout.page_size};")
        css_lines.append(f"    margin: {layout.margins.top}cm {layout.margins.right}cm {layout.margins.bottom}cm {layout.margins.left}cm;")
        if letterhead_css:
            css_lines.append(f"    {letterhead_css}")
        
        css_lines.append(".doc-content { font-size: 11pt; line-height: 1.6; }")
        css_lines.append(f"    @top-center {{ content: ''; height: {layout.header_height}cm; }}")
        css_lines.append(f"    @bottom-center {{ content: ''; height: {layout.footer_height}cm; }}")
        css_lines.append("}}")
        
        css_lines.append("/* Masquage header/footer */")
        if hide_header_css: css_lines.append(hide_header_css)
        if hide_footer_css: css_lines.append(hide_footer_css)
        
        css_lines.append("/* Fonts - Médical Premium */")
        css_lines.append("body {")
        css_lines.append("    font-family: 'Outfit', 'Inter', 'Helvetica', sans-serif;")
        css_lines.append(f"    font-size: {typography.body_size}pt;")
        css_lines.append(f"    line-height: {typography.body_line_height};")
        css_lines.append(f"    color: {colors.primary};")
        css_lines.append("    font-weight: 400;")
        css_lines.append("}")
        
        css_lines.append("/* Force Branding */")
        css_lines.append(f"body, body *, p, div, span, b, i, strong, em {{ color: {colors.primary} !important; }}")
        
        css_lines.append(".arabic {")
        css_lines.append(f"    font-family: '{fonts.ar}', 'Amiri', serif;")
        css_lines.append("    direction: rtl;")
        css_lines.append("}}")
        
        css_lines.append(".doc-title {")
        css_lines.append(f"    font-size: {typography.title_size}pt;")
        css_lines.append(f"    font-weight: {'bold' if typography.title_bold else 'normal'};")
        css_lines.append(f"    text-align: {typography.title_align};")
        css_lines.append(f"    color: {colors.primary};")
        css_lines.append(f"    margin-bottom: {spacing.section_gap_cm}cm;")
        if typography.title_underline:
            css_lines.append("    text-decoration: underline;")
        css_lines.append("}}")
        
        css_lines.append(".header {")
        if borders.header_line:
            css_lines.append(f"    border-bottom: 1px solid {borders.header_line_color};")
        css_lines.append("    padding-bottom: 0.5cm;")
        css_lines.append(f"    margin-bottom: {spacing.section_gap_cm}cm;")
        css_lines.append("}}")
        
        css_lines.append(".header-left { float: left; width: 45%; color: " + colors.primary + "; }")
        css_lines.append(".header-right { float: right; width: 45%; text-align: right; color: " + colors.secondary + "; }")
        
        css_lines.append(".logo {")
        css_lines.append(f"    width: {header.logo_header_size_cm}cm;")
        css_lines.append("    height: auto; margin: 0 auto; display: block;")
        css_lines.append("}")
        
        css_lines.append(".doc-date { text-align: right; margin-bottom: 1cm; }")
        css_lines.append(f".patient-info {{ margin-bottom: {spacing.section_gap_cm}cm; }}")
        css_lines.append(".doc-patient-info { font-weight: bold; }")
        css_lines.append(f".patient-name {{ font-weight: bold; font-size: {typography.body_size + 1}pt; }}")
        
        css_lines.append(f".content {{ margin-top: {spacing.paragraph_gap_cm}cm; }}")
        css_lines.append(".doc-header { margin-bottom: 2cm; }")
        css_lines.append(f".content p {{ margin-bottom: {spacing.paragraph_gap_cm}cm; }}")
        
        css_lines.append(f".doc-footer-signature {{ margin-top: {spacing.paragraph_gap_cm}cm; color: {colors.primary}; font-weight: bold; }}")
        
        css_lines.append(".qr-signature {")
        css_lines.append("    position: absolute; bottom: 0.5cm; right: 0.5cm;")
        css_lines.append("    width: 2.2cm; height: 2.2cm; opacity: 0.9;")
        css_lines.append("}")
        
        css_lines.append(".footer {")
        css_lines.append("    position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 9pt;")
        css_lines.append(f"    color: {colors.secondary};")
        if borders.header_line:
            css_lines.append(f"    border-top: 1px solid {colors.primary}; padding-top: 0.3cm;")
        css_lines.append("}")
        
        css_lines.append(".watermark {")
        css_lines.append("    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);")
        css_lines.append(f"    opacity: {watermark.opacity}; width: {watermark.size_cm}cm; height: auto; z-index: -1;")
        css_lines.append("}}")
        
        css_lines.append("table { width: 100%; border-collapse: collapse; margin: " + str(spacing.section_gap_cm) + "cm 0; }")
        css_lines.append(f"th, td {{ padding: 0.3cm; text-align: left; border-bottom: 1px solid {colors.secondary}; }}")
        css_lines.append(f"th {{ font-weight: bold; color: {colors.primary}; }}")
        
        return "\n".join(css_lines)


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
            'patient_nom': context.get('patient', {}).get('nom', ''),
            'patient_prenom': context.get('patient', {}).get('prenom', ''),
            'patient_age': context.get('patient', {}).get('age', ''),
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
            'config': cabinet, # Pour base_elite.html
            'date': context.get('date', datetime.now().strftime('%d/%m/%Y')),
            'date_generation': context.get('date', datetime.now().strftime('%d/%m/%Y')),
            'titre': context.get('titre', template.name),
            'content': context.get('content', ''),
            'medications': context.get('medications', []),
            'actes': context.get('actes', []),
            'qr_code_url': context.get('custom', {}).get('qr_code_url', ''), # Pour base_elite.html
            'logo_url': f"file://{os.path.abspath(os.path.join(self.static_dir, 'uploads', cabinet.logo_path))}" if cabinet.logo_path else None,
            'custom': context.get('custom', {}),
            'draw_legal_ids': context.get('draw_legal_ids', False)
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

            {f'<img src="{render_context["custom"]["qr_code_url"]}" class="qr-signature" />' if "custom" in render_context and "qr_code_url" in render_context["custom"] else ''}
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
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_RIGHT
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
        
        # Styles personnalisés branchés sur la couleur primaire
        p_color = colors.HexColor(cabinet.primary_color) if cabinet else colors.HexColor('#003380')
        
        styles = getSampleStyleSheet()
        # On force la couleur de marque sur ABSOLUMENT TOUS les styles ReportLab
        for name in styles.byName:
            styles[name].textColor = p_color
            styles[name].fontName = 'Helvetica'
            
        styles['Normal'].fontSize = 11
        styles['Normal'].leading = 16 # Plus d'interligne pour le look premium
        
        title_style = ParagraphStyle(
            'TitleBranded', 
            parent=styles['Heading1'], 
            textColor=p_color, 
            alignment=1, # TA_CENTER
            fontSize=18,
            leading=22,
            fontName='Helvetica-Bold'
        )
        
        story = []
        story.append(Spacer(1, 0.5*cm))
        
        # 1. En-tête Patient Épuré (Style Elite)
        patient = context.get('patient', {})
        date_doc = context.get('date', datetime.now().strftime('%d/%m/%Y'))
        age = patient.get('age', '??')
        
        info_text = f"<b>{patient.get('nom', 'PATIENT').upper()} {patient.get('prenom', '').capitalize()}</b>, {age} ans"
        date_text = f"Le : <u>{date_doc}</u>"
        
        header_table = Table([
            [Paragraph(info_text, styles['Normal']), Paragraph(date_text, ParagraphStyle(name='RightDate', parent=styles['Normal'], alignment=TA_RIGHT, textColor=p_color))]
        ], colWidths=[7.5*cm, 4.3*cm])
        header_table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 0), 
            ('RIGHTPADDING', (0,0), (-1,-1), 0), 
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TEXTCOLOR', (0,0), (-1,-1), p_color),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15)
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 0.8*cm))

        # 2. Rendu du Titre
        story.append(Paragraph("<u><b>CERTIFICAT MEDICAL</b></u>", title_style))
        story.append(Spacer(1, 1.5*cm))
        
        # 3. Contenu
        content = context.get('content', '')
        praticien = context.get('praticien', {})
        dr_name = praticien.get('nom_complet', 'Docteur')
        
        # Nettoyage Dr
        import re
        dr_name = re.sub(r'^(Dr\.?\s*)+', '', dr_name, flags=re.IGNORECASE).strip()
        
        if isinstance(content, str):
            # Nettoyage minimal
            content = content.replace('\n', '<br/>')
            
            # Si c'est un certificat et que le contenu est court, on l'étoffe comme le legacy
            titre = context.get('titre', '')
            if 'CERTIFICAT' in titre.upper() and len(content) < 200:
                 hon = context.get('hon', 'Mr/Mme')
                 start_date = context.get('start_date', date_doc)
                 days = context.get('certif_days', 3)
                 type_repos = context.get('type_repos', 'un repos médical')
                 
                 content = (
                    f"Je, soussigné Dr. {dr_name}, certifie que l'état de santé de "
                    f"{hon} <b>{patient.get('nom', 'PATIENT').upper()} {patient.get('prenom', '').capitalize()}</b>, "
                    f"âgé(e) de <b>{age} ans</b>, nécessite {type_repos} d'une durée de <b>{days} jours</b>, à partir du <b>{start_date}</b>.<br/><br/>"
                    f"Ce certificat est délivré à l'intéressé(e) pour servir et faire valoir ce que de droit."
                )
            
            # Si le contenu est une liste de médicaments (Ordonnance)
            elif 'medications' in context and context['medications']:
                content = ""
                for i, med in enumerate(context['medications'], 1):
                    content += f"<b>{i}. {med.get('nom', '')}</b> - {med.get('dosage', '')}<br/>"
                    content += f"<i>{med.get('posologie', '')}</i><br/><br/>"
        
        story.append(Paragraph(content, styles['Normal']))
        
        # Dessin du branding
        bt = BaseTemplate()
        draw_legal_ids = context.get('draw_legal_ids', False)
        draw_method = lambda canv, d: bt.draw_static_elements(canv, d, config=cabinet, draw_legal_ids=draw_legal_ids)
        
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
