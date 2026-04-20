import os
import re
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from backend.services.base_template import BaseTemplate, NAVY_BLUE

class OrdonnanceGenerator:
    def __init__(self, output_dir="static/documents"):
        self.output_dir = output_dir
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()

    def _calculate_age(self, born):
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, data):
        """Nommage conforme : ORDONNANCE_NOM_PRENOM_YYYYMMDD_HHMMSS.pdf"""
        now = datetime.now()
        date_str = now.strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join(self.output_dir, now.strftime('%Y'), now.strftime('%m'))
        os.makedirs(save_dir, exist_ok=True)
        
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        filename = f"ORDONNANCE_{safe_name}_{date_str}.pdf"
        return os.path.join(save_dir, filename)

    def _draw_canvas(self, canvas, doc, config=None):
        self.base_template.draw_static_elements(canvas, doc, config=config)

    def generate(self, patient, data, db=None, user_id=None):
        filepath = self._get_save_path(patient, data)
        
        # --- RÉCUPÉRATION CONFIGURATION ---
        config = None
        if db and user_id:
            from backend.models import CabinetConfig
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
        
        primary_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        
        # Smart Scaling
        num_meds = len(data.medications)
        spacing = 0.6 if num_meds <= 4 else 0.3
        
        # Police dynamique
        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

        # Custom Style for this Doctor
        title_style = ParagraphStyle(
            name='TitlePremium', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=16, 
            textColor=primary_color, 
            alignment=TA_CENTER,
            underlineWidth=1.5
        )
        
        # TOUJOURS dessiner le Titre et le bloc Patient (même avec un papier en-tête !)
        elements = [
            Spacer(1, 0.5*cm),
            Paragraph("ORDONNANCE", title_style),
            Spacer(1, 1.0*cm),
            self._create_header(patient, data, primary_color),
            Spacer(1, 1.5*cm)
        ]

        for i, med in enumerate(data.medications, 1):
            forme = getattr(med, 'forme', 'Sachets')
            dosage = med.dosage
            
            if forme.lower() in dosage.lower():
                dosage = re.sub(re.escape(forme), '', dosage, flags=re.IGNORECASE).strip()
            
            med_name_style = ParagraphStyle(
                name='MedName', 
                parent=self.styles['Normal'], 
                fontName=font_bold, 
                fontSize=10, 
                textColor=primary_color, 
                alignment=TA_LEFT
            )
            
            row = [
                Paragraph(f"<b>{i}-</b>", med_name_style),
                Paragraph(f"<u><b>{med.nom.upper()}</b></u>", med_name_style),
                Paragraph(dosage, med_name_style),
                Paragraph(forme, med_name_style)
            ]
            
            t = Table([row], colWidths=[0.6*cm, 6.5*cm, 2.8*cm, 1.9*cm])
            t.setStyle(TableStyle([
                ('TEXTCOLOR', (0,0), (-1,-1), primary_color), 
                ('VALIGN', (0,0), (-1,-1), 'BOTTOM'), 
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ]))
            elements.append(t)
            
            poso_style = ParagraphStyle(
                name='PosoStyle', 
                parent=self.styles['Normal'], 
                fontName=font_name, 
                fontSize=9.5, 
                textColor=colors.HexColor('#333333'), 
                leftIndent=1.0*cm, 
                leading=12
            )
            elements.append(Paragraph(med.posologie, poso_style))
            elements.append(Spacer(1, spacing*cm))

        # Build dynamique avec marges de la config
        m_top = (config.margin_top if config else 3.6) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm
        
        doc = SimpleDocTemplate(
            filepath, 
            pagesize=A5, 
            rightMargin=1.5*cm, 
            leftMargin=1.5*cm, 
            topMargin=m_top, 
            bottomMargin=m_bottom
        )
        
        # On passe la config au draw_canvas via une lambda
        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config)
        
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
        
        relative_path = filepath[filepath.find("static"):] if "static" in filepath else filepath
        return relative_path.replace("\\", "/")

    def _create_header(self, patient, data, p_color):
        doc_date = getattr(data, 'doc_date', date.today())
        current_date = doc_date.strftime('%d/%m/%Y')
        age = self._calculate_age(patient.date_naissance)
        
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