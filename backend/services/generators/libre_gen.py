import os
import io
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE


class SignatureManager:
    """Gère l'affichage intelligent de la signature sur la dernière page uniquement."""
    
    def __init__(self, base_template):
        self.base_template = base_template
        self.total_pages = 0
        self.current_page = 0
    
    def draw_with_signature(self, canvas, doc, config=None, user=None):
        """Dessine le template et gère la signature selon la page."""
        self.base_template.draw_static_elements(canvas, doc, config=config, user=user)
        self.current_page += 1
        
        is_last_page = (self.current_page == self.total_pages)
        
        if is_last_page:
            p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
            # Police dynamique
            font_name = self.base_template.arabic_font
            font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name
            
            canvas.saveState()
            canvas.setFont(font_bold, 11)
            canvas.setFillColor(p_color)
            canvas.drawRightString(14.8*cm - 1.5*cm, 4*cm, "Signature et Cachet :")
            canvas.restoreState()


class LibreGenerator:
    def __init__(self, output_dir="static/documents"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()

    def _calculate_age(self, born):
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, data):
        """Nommage conforme : LIBRE_NOM_PRENOM_YYYYMMDD_HHMMSS.pdf"""
        now = datetime.now()
        date_str = now.strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join(self.output_dir, now.strftime('%Y'), now.strftime('%m'))
        os.makedirs(save_dir, exist_ok=True)
        
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        filename = f"LIBRE_{safe_name}_{date_str}.pdf"
        return os.path.join(save_dir, filename)

    def _create_header(self, patient, data, p_color):
        doc_date = getattr(data, 'doc_date', date.today())
        current_date = doc_date.strftime('%d/%m/%Y')
        age = getattr(data, 'age', self._calculate_age(patient.date_naissance))
        
        # Police dynamique
        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

        info_style = ParagraphStyle(
            name='HeaderInfo', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=10, 
            textColor=p_color, 
            leading=14
        )
        date_style = ParagraphStyle(
            name='HeaderDate', 
            parent=self.styles['Normal'], 
            fontName=font_name, 
            fontSize=10, 
            textColor=p_color, 
            alignment=TA_RIGHT
        )
        
        info_text = f"Nom : {patient.nom.upper()} {patient.prenom.capitalize()}<br/>Âge : {age} ans"
        header_table = Table([
            [Paragraph(info_text, info_style), Paragraph(f"Le : ....{current_date}....", date_style)]
        ], colWidths=[6.0*cm, 5.8*cm])
        header_table.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
        return header_table

    def _build_elements(self, patient, data, config=None):
        """Construit la liste des éléments du document."""
        titre = getattr(data, 'titre', None) or getattr(data, 'title', 'DOCUMENT MÉDICAL')
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        
        contenu_brut = getattr(data, 'texte', None) or getattr(data, 'content', None) or getattr(data, 'text', '')
        
        import html
        contenu_escape = html.escape(contenu_brut)
        contenu_html = contenu_escape.replace('\n', '<br/>')
        
        t_gap = 0.8 if len(contenu_brut) < 400 else 0.4
        
        # Police dynamique
        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

        title_style = ParagraphStyle(
            name='LibreTitle', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=16, 
            textColor=p_color, 
            alignment=TA_CENTER
        )
        
        body_style = ParagraphStyle(
            name='LibreBody', 
            parent=self.styles['Normal'], 
            fontName=font_name, 
            fontSize=11, 
            textColor=colors.HexColor('#000000'), 
            alignment=TA_JUSTIFY, 
            leading=16
        )
        
        elements = [
            Spacer(1, 0.5*cm),
            # self._create_header(patient, data, p_color),
            Spacer(1, t_gap*cm),
            # Paragraph(f"<u><b>{titre.upper()}</b></u>", title_style),
            Spacer(1, 0.6*cm)
        ]

        elements.append(Paragraph(contenu_html, body_style))
        
        return elements

    def generate(self, patient, data, db=None, user_id=None):
        filepath = self._get_save_path(patient, data)
        
        config = None
        user_obj = None
        if db and user_id:
            from backend.models import CabinetConfig, User
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
            user_obj = db.query(User).filter(User.id == user_id).first()
            
        elements = self._build_elements(patient, data, config=config)
        
        # === PASS 1: Compter le nombre de pages ===
        buffer = io.BytesIO()
        m_top = (config.margin_top if config else 3.6) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm + 1.5*cm
        
        temp_doc = SimpleDocTemplate(
            buffer, 
            pagesize=A5, 
            rightMargin=1.5*cm, 
            leftMargin=1.5*cm, 
            topMargin=m_top, 
            bottomMargin=m_bottom
        )
        
        page_count = [0]
        def count_pages(canvas, doc):
            page_count[0] += 1
            self.base_template.draw_static_elements(canvas, doc, config=config, user=user_obj)
        
        temp_doc.build(elements, onFirstPage=count_pages, onLaterPages=count_pages)
        total_pages = page_count[0]
        
        # === PASS 2: Générer le vrai PDF avec signature sur la dernière page ===
        sig_manager = SignatureManager(self.base_template)
        sig_manager.total_pages = total_pages
        
        m_top = (config.margin_top if config else 3.6) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm + 1.5*cm # On ajoute de l'espace pour la signature
        
        final_doc = SimpleDocTemplate(
            filepath, 
            pagesize=A5, 
            rightMargin=1.5*cm, 
            leftMargin=1.5*cm, 
            topMargin=m_top, 
            bottomMargin=m_bottom
        )
        # On injecte la config dans SignatureManager
        draw_method = lambda canv, d: sig_manager.draw_with_signature(canv, d, config=config, user=user_obj)
        final_doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
        
        relative_path = filepath[filepath.find("static"):] if "static" in filepath else filepath
        return relative_path.replace("\\", "/")
