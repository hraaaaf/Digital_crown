import os
from datetime import datetime, date
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
        self._init_styles()

    def _init_styles(self):
        self.styles.add(ParagraphStyle(
            name='HeaderInfo', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=NAVY_BLUE, leading=14
        ))
        self.styles.add(ParagraphStyle(
            name='HeaderDate', parent=self.styles['Normal'], fontName='Helvetica', fontSize=10, textColor=NAVY_BLUE, alignment=TA_RIGHT
        ))
        self.styles.add(ParagraphStyle(
            name='LibreTitle', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=NAVY_BLUE, alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='LibreBody', parent=self.styles['Normal'], fontName='Helvetica', fontSize=11, textColor=NAVY_BLUE, alignment=TA_JUSTIFY, leading=16
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
        filename = f"LIBRE_{safe_name}_{doc_id}.pdf"
        return os.path.join(save_dir, filename)

    def _draw_canvas(self, canvas, doc):
        """Dessine BaseTemplate et conserve la signature positionnée."""
        self.base_template.draw_static_elements(canvas, doc)
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 11)
        canvas.setFillColor(NAVY_BLUE)
        canvas.drawRightString(14.8*cm - 1.5*cm, 4*cm, "Signature et Cachet :")
        canvas.restoreState()

    def _create_header(self, patient, data):
        doc_date = getattr(data, 'doc_date', date.today())
        current_date = doc_date.strftime('%d/%m/%Y')
        age = getattr(data, 'age', self._calculate_age(patient.date_naissance))
        
        info_text = f"Nom : {patient.nom.upper()} {patient.prenom.capitalize()}<br/>Âge : {age} ans"
        header_table = Table([
            [Paragraph(info_text, self.styles['HeaderInfo']), Paragraph(f"Le : ....{current_date}....", self.styles['HeaderDate'])]
        ], colWidths=[6.0*cm, 5.8*cm])
        header_table.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
        return header_table

    def generate(self, patient, data):
        filepath = self._get_save_path(patient, data)
        titre = getattr(data, 'titre', 'DOCUMENT MÉDICAL')
        
        # Smart Scaling : ajustement en fonction de la longueur du texte
        contenu_html = getattr(data, 'texte', '')
        t_gap = 0.8 if len(contenu_html) < 400 else 0.4
        
        elements = [
            Spacer(1, 0.5*cm),
            self._create_header(patient, data),
            Spacer(1, t_gap*cm),
            Paragraph(f"<u><b>{titre.upper()}</b></u>", self.styles['LibreTitle']),
            Spacer(1, t_gap*cm)
        ]

        elements.append(Paragraph(contenu_html, self.styles['LibreBody']))
        
        doc = SimpleDocTemplate(filepath, pagesize=A5, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=3.6*cm, bottomMargin=5.5*cm)
        doc.build(elements, onFirstPage=self._draw_canvas, onLaterPages=self._draw_canvas)
        
        relative_path = filepath[filepath.find("static"):] if "static" in filepath else filepath
        return relative_path.replace("\\", "/")