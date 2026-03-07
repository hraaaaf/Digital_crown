import os
from datetime import datetime, date
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE

class CertificatGenerator:
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
            name='CertificatTitleA5', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=18, textColor=NAVY_BLUE, alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='CertifBody', parent=self.styles['Normal'], fontName='Helvetica', fontSize=12, textColor=NAVY_BLUE, alignment=TA_JUSTIFY, leading=18
        ))
        self.styles.add(ParagraphStyle(
            name='SignatureStyle', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=NAVY_BLUE, alignment=TA_RIGHT
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
        filename = f"CERTIFICAT_{safe_name}_{doc_id}.pdf"
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
        doc = SimpleDocTemplate(filepath, pagesize=A5, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=3.6*cm, bottomMargin=3*cm)
        doc.build(elements, onFirstPage=self._draw_canvas, onLaterPages=self._draw_canvas)
        relative_path = filepath[filepath.find("static"):] if "static" in filepath else filepath
        return relative_path.replace("\\", "/")

    def generate(self, patient, data):
        filepath = self._get_save_path(patient, data)
        doc_date = getattr(data, 'doc_date', date.today())

        elements = [
            Spacer(1, 0.5*cm),
            self._create_header(patient, data),
            Spacer(1, 1.2*cm),
            Paragraph("<u><b>CERTIFICAT MÉDICAL</b></u>", self.styles['CertificatTitleA5']),
            Spacer(1, 0.8*cm)
        ]

        # Utilisation stricte de l'objet patient pour l'âge et le sexe
        age = self._calculate_age(patient.date_naissance)
        gender = patient.sexe
        hon = "Mr" if gender in ["Homme", "Garçon", "M"] else "Madame"
        
        type_repos = "Arrêt de travail" if getattr(data, 'is_work_stop', False) else "Repos médical"
        start_date_str = getattr(data, 'start_date', doc_date).strftime('%d/%m/%Y')
        
        # Ajustement Smart Scaling pour texte très long
        text_len = len(getattr(data, 'reason', ''))
        spacing_bottom = 2.0 if text_len < 100 else 1.0

        certif_text = (
            f"Je, sousigné Dr Benmoussa Achraf, certifie que l'état de santé de "
            f"{hon} <b>{patient.nom.upper()} {patient.prenom}</b>, âgé(e) de {age} ans, "
            f"nécessite un <b>{type_repos}</b> de <b>{data.days} jours</b>, à partir du {start_date_str}.<br/><br/>"
            f"Ce certificat est délivré à l'intéressé(e) pour servir et faire valoir ce que de droit."
        )
        
        content_block = [Paragraph(certif_text, self.styles['CertifBody']), Spacer(1, spacing_bottom*cm), Paragraph("Signature et Cachet :", self.styles['SignatureStyle'])]
        elements.append(KeepTogether(content_block))

        return self._build_pdf(filepath, elements)