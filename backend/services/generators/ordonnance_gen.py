import os
import re
from datetime import datetime, date
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from backend.services.base_template import BaseTemplate, NAVY_BLUE

class OrdonnanceGenerator:
    def __init__(self, output_dir="static/documents"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        self.styles.add(ParagraphStyle(
            name='HeaderInfo', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=NAVY_BLUE, leading=14
        ))
        self.styles.add(ParagraphStyle(
            name='HeaderDate', parent=self.styles['Normal'], fontName='Helvetica', fontSize=10, textColor=NAVY_BLUE, alignment=TA_RIGHT
        ))
        self.styles.add(ParagraphStyle(
            name='TitlePremium', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=18, textColor=NAVY_BLUE, alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='MedName', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=NAVY_BLUE, alignment=TA_LEFT
        ))
        self.styles.add(ParagraphStyle(
            name='PosoStyle', parent=self.styles['Normal'], fontName='Helvetica', fontSize=9.5, textColor=NAVY_BLUE, leftIndent=1.0*cm, leading=12
        ))

    def _calculate_age(self, born):
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, data):
        doc_date = getattr(data, 'doc_date', date.today())
        year_str, month_str = doc_date.strftime('%Y'), doc_date.strftime('%m')
        save_dir = os.path.join(self.output_dir, year_str, month_str)
        os.makedirs(save_dir, exist_ok=True)
        
        doc_id = getattr(data, 'id', doc_date.strftime('%Y%m%d'))
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        filename = f"ORDONNANCE_{safe_name}_{doc_id}.pdf"
        return os.path.join(save_dir, filename)

    def _draw_canvas(self, canvas, doc):
        self.base_template.draw_static_elements(canvas, doc)

    def _create_header(self, patient, data):
        doc_date = getattr(data, 'doc_date', date.today())
        current_date = doc_date.strftime('%d/%m/%Y')
        # Calcul strict basé sur l'objet patient
        age = self._calculate_age(patient.date_naissance)
        
        info_text = f"Nom : {patient.nom.upper()} {patient.prenom.capitalize()}<br/>Âge : {age} ans"
        
        header_table = Table([
            [Paragraph(info_text, self.styles['HeaderInfo']), Paragraph(f"Le : ....{current_date}....", self.styles['HeaderDate'])]
        ], colWidths=[6.0*cm, 5.8*cm])
        header_table.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
        return header_table

    def _build_pdf(self, filepath, elements):
        doc = SimpleDocTemplate(filepath, pagesize=A5, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=3.6*cm, bottomMargin=3.2*cm)
        doc.build(elements, onFirstPage=self._draw_canvas, onLaterPages=self._draw_canvas)
        relative_path = filepath[filepath.find("static"):] if "static" in filepath else filepath
        return relative_path.replace("\\", "/")

    def generate(self, patient, data):
        filepath = self._get_save_path(patient, data)
        
        # Smart Scaling
        num_meds = len(data.medications)
        spacing = 0.6 if num_meds <= 4 else 0.3
        
        elements = [
            Spacer(1, 0.5*cm),
            self._create_header(patient, data),
            Spacer(1, 0.8*cm),
            Paragraph("<u><b>ORDONNANCE</b></u>", self.styles['TitlePremium']),
            Spacer(1, 1.6*cm)
        ]

        for i, med in enumerate(data.medications, 1):
            forme = getattr(med, 'forme', 'Sachets')
            dosage = med.dosage
            
            if forme.lower() in dosage.lower():
                dosage = re.sub(re.escape(forme), '', dosage, flags=re.IGNORECASE).strip()
            
            row = [
                Paragraph(f"<b>{i}-</b>", self.styles['MedName']),
                Paragraph(f"<u><b>{med.nom.upper()}</b></u>", self.styles['MedName']),
                Paragraph(dosage, self.styles['MedName']),
                Paragraph(forme, self.styles['MedName'])
            ]
            
            # Colonnes réajustées : plus d'espace pour le nom du médicament
            t = Table([row], colWidths=[0.6*cm, 6.5*cm, 2.8*cm, 1.9*cm])
            t.setStyle(TableStyle([
                ('TEXTCOLOR', (0,0), (-1,-1), NAVY_BLUE), 
                ('VALIGN', (0,0), (-1,-1), 'BOTTOM'), 
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 3),  # Petit padding droit pour éviter collage
            ]))
            elements.append(t)
            elements.append(Paragraph(med.posologie, self.styles['PosoStyle']))
            elements.append(Spacer(1, spacing*cm))

        return self._build_pdf(filepath, elements)