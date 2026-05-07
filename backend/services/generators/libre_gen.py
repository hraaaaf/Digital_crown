# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5, A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
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
        """En-tête flexible : Supporte les surcharges utilisateur."""
        # 1. Gestion de la Date (Priorité à custom_date)
        custom_date = getattr(data, 'custom_date', None)
        if custom_date:
            current_date = custom_date
        else:
            doc_date = getattr(data, 'doc_date', date.today())
            current_date = doc_date.strftime('%d/%m/%Y') if hasattr(doc_date, 'strftime') else str(doc_date)
        
        # 2. Gestion du Destinataire (PrioritÃ© Ã  custom_patient)
        custom_patient = getattr(data, 'custom_patient', None)
        hide_patient = getattr(data, 'hide_patient_header', False)
        
        if hide_patient:
            return Spacer(1, 0.1*cm)

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
        
        if custom_patient:
            # Mode personnalisé : On affiche juste le texte saisi par l'utilisateur
            left_content = Paragraph(f"<b>Destinataire :</b> {custom_patient}", patient_style)
        else:
            # Mode standard : Nom, Âge, Dossier
            age = self._calculate_age(patient.date_naissance)
            left_content = Paragraph(f"Nom : {patient.nom.upper()} {patient.prenom.capitalize()}<br/>Âge : {age} ans", patient_style)

        header_content = [
            [
                left_content, 
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
        # CTO Fix: Preserve newlines for ReportLab Paragraph
        contenu_html = contenu_html.replace('\n', '<br/>')
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
        
        # 3. Style du corps (Flexible)
        alignment_map = {
            'left': TA_LEFT,
            'center': TA_CENTER,
            'right': TA_RIGHT,
            'justify': TA_JUSTIFY
        }
        user_align = getattr(data, 'alignment', 'justify')
        final_align = alignment_map.get(user_align, TA_JUSTIFY)
        
        body_style = ParagraphStyle(
            name='LibreBody', 
            parent=self.styles['Normal'], 
            fontName=font_name, 
            fontSize=11, 
            textColor=p_color, # Respect du Branding Forcing
            alignment=final_align, 
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

        # Gestion du format de page (A4 vs A5)
        page_format = getattr(data, 'page_size', 'A5').upper()
        page_size = A4 if page_format == 'A4' else A5

        m_top = (config.margin_top if config else 3.6) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm
        
        doc = SimpleDocTemplate(filepath, pagesize=page_size, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=m_top, bottomMargin=m_bottom)
        doc.qr_type = 'WEBSITE'
        doc.doc_id = f"LIBRE-{datetime.now().strftime('%m%H%M')}"
        doc.cloture_text = "Signature et Cachet"
        
        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user_obj)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
        
        return filepath.replace("\\", "/")
