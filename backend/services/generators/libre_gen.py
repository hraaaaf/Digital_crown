import os
import re
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE

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

    def _get_save_path(self, patient, titre):
        now = datetime.now()
        date_str = now.strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join(self.output_dir, now.strftime('%Y'), now.strftime('%m'))
        os.makedirs(save_dir, exist_ok=True)
        
        safe_titre = re.sub(r'[^\w\s-]', '', titre).strip().replace(' ', '_')[:30]
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        filename = f"LIBRE_{date_str}_{safe_titre}_{safe_name}.pdf"
        return os.path.join(save_dir, filename)

    def _draw_canvas(self, canvas, doc, config=None, user=None):
        """Rendu Elite avec identifiants légaux et clôture épinglée - IDENTIQUE À ACCOUNTING."""
        self.base_template.draw_static_elements(canvas, doc, config=config, draw_legal_ids=True, user=user)
        
        p_width, p_height = doc.pagesize
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        font_name = self.base_template.arabic_font
        
        if hasattr(doc, 'cloture_text') and doc.cloture_text:
            canvas.saveState()
            canvas.setFont(font_name, 10)
            canvas.setFillColor(p_color)
            canvas.drawCentredString(p_width/2, 3.2*cm, "Signature et Cachet")
            canvas.restoreState()

    def _create_header(self, patient, data, p_color, config=None):
        """En-tête Patient - COPIE CONFORME DE ACCOUNTING."""
        # Correction : Utiliser la date choisie par l'utilisateur
        doc_date = getattr(data, 'doc_date', date.today())
        current_date = doc_date.strftime('%d/%m/%Y') if hasattr(doc_date, 'strftime') else str(doc_date)
        age = self._calculate_age(patient.date_naissance)
        
        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

        patient_style = ParagraphStyle(
            name='PatientInfo', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=11, 
            textColor=p_color, 
            leading=14
        )
        style_right = ParagraphStyle(
            'DocDate', 
            parent=self.styles['Normal'], 
            alignment=TA_RIGHT, 
            textColor=p_color,
            fontName=font_name,
            fontSize=11
        )
        
        header_content = [
            [
                Paragraph(f"Nom : {patient.nom.upper()} {patient.prenom.capitalize()}<br/>Âge : {age} ans<br/>Dossier N° : {patient.numero_dossier or 'N/A'}", patient_style), 
                Paragraph(f"Le : {current_date}", style_right)
            ]
        ]
        
        header_table = Table(header_content, colWidths=[7.0*cm, 4.8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        return header_table

    def generate(self, patient, data, db=None, user_id=None):
        titre = getattr(data, 'titre', 'Document Libre')
        contenu_html = getattr(data, 'contenu', '')
        filepath = self._get_save_path(patient, titre)
        
        config = None
        user_obj = None
        if db and user_id:
            from backend.models import CabinetConfig, User
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
            user_obj = db.query(User).filter(User.id == user_id).first()
        
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

        title_style = ParagraphStyle(
            name='TitleA5', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=17, 
            textColor=p_color, 
            alignment=TA_CENTER,
            leading=22,
            spaceAfter=12
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
            Spacer(1, 0.4*cm),
            Paragraph(f"<u><b>{titre.upper()}</b></u>", title_style),
            Spacer(1, 0.8*cm),
            self._create_header(patient, data, p_color, config),
            Spacer(1, 1.2*cm),
            Paragraph(contenu_html, body_style)
        ]

        m_top = (config.margin_top if config else 3.6) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm
        
        doc = SimpleDocTemplate(filepath, pagesize=A5, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=m_top, bottomMargin=m_bottom)
        doc.cloture_text = "Signature et Cachet"
        
        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user_obj)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
        
        relative_path = filepath[filepath.find("static"):] if "static" in filepath else filepath
        return relative_path.replace("\\", "/")
