# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

from backend.services.base_template import BaseTemplate, NAVY_BLUE


class OrdonnanceGenerator:
    def __init__(self, output_dir="static/documents"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()

    def _calculate_age(self, born):
        if not born:
            return 0
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, data):
        now = datetime.now()
        date_str = now.strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join(self.output_dir, now.strftime('%Y'), now.strftime('%m'))
        os.makedirs(save_dir, exist_ok=True)
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        filename = f"ORDONNANCE_{safe_name}_{date_str}.pdf"
        return os.path.join(save_dir, filename)

    def _draw_canvas(self, canvas, doc, config=None, user=None):
        self.base_template.draw_static_elements(canvas, doc, config=config, draw_legal_ids=False, user=user)

    def _create_header(self, patient, data, p_color, config=None):
        doc_date = getattr(data, 'doc_date', date.today())
        if isinstance(doc_date, str):
            try:
                doc_date = datetime.strptime(doc_date, '%Y-%m-%d').date()
            except Exception:
                doc_date = date.today()

        current_date = doc_date.strftime('%d/%m/%Y')
        age = self._calculate_age(patient.date_naissance)

        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

        patient_style = ParagraphStyle(
            name='PatientInfo',
            parent=self.styles['Normal'],
            fontName=font_bold,
            fontSize=11,
            textColor=p_color,
            leading=14,
        )
        style_right = ParagraphStyle(
            'DocDate',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT,
            textColor=p_color,
            fontName=font_name,
            fontSize=11,
        )

        header_content = [[
            Paragraph(f"{patient.nom.upper()} {patient.prenom.capitalize()}, {age} ans", patient_style),
            Paragraph(f"Le : <u>{current_date}</u>", style_right),
        ]]

        header_table = Table(header_content, colWidths=[7.5 * cm, 4.3 * cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        return header_table

    def generate(self, patient, data, db=None, user_id=None):
        filepath = self._get_save_path(patient, data)

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
            fontSize=18,
            textColor=p_color,
            alignment=TA_CENTER,
            spaceAfter=20,
        )

        elements = [
            Spacer(1, 0.4 * cm),
            Paragraph("<u>ORDONNANCE</u>", title_style),
            Spacer(1, 0.6 * cm),
            self._create_header(patient, data, p_color, config),
            Spacer(1, 1.2 * cm),
        ]

        if hasattr(data, 'medications') and data.medications:
            # Forçage de la police Helvetica pour le corps médical (garantit le contraste Gras/Normal)
            med_font = "Helvetica"
            med_font_bold = "Helvetica-Bold"

            # Styles typographiques avec contraste optimal
            med_name_style = ParagraphStyle('MedName', parent=self.styles['Normal'], fontName=med_font_bold, fontSize=11, textColor=p_color)
            med_forme_style = ParagraphStyle('MedForme', parent=self.styles['Normal'], fontName=med_font, fontSize=10, textColor=p_color, alignment=TA_CENTER)
            med_dose_style = ParagraphStyle('MedDose', parent=self.styles['Normal'], fontName=med_font, fontSize=10, textColor=p_color, alignment=TA_RIGHT)
            
            poso_style = ParagraphStyle(
                'PosoElite', parent=self.styles['Normal'], fontName=med_font, fontSize=10,
                textColor=p_color, leftIndent=1.2*cm, spaceBefore=2, spaceAfter=12
            )

            for i, med in enumerate(data.medications, 1):
                forme = getattr(med, 'forme', '') or ""
                dose = getattr(med, 'dosage', '') or ""
                nom = getattr(med, 'nom', '') or ""
                posologie = getattr(med, 'posologie', '') or "Selon prescription."

                # Ligne 1 : Nom (Gauche) | Forme (Centre) | Dosage (Droite) dans un tableau invisible
                med_line_table = Table([
                    [
                        Paragraph(f"{i}- <b>{nom.upper()}</b>", med_name_style),
                        Paragraph(f"<i>{forme}</i>" if forme else "", med_forme_style),
                        Paragraph(f"{dose}", med_dose_style)
                    ]
                ], colWidths=[6.0*cm, 3.0*cm, 2.8*cm]) # Total: 11.8cm (Largeur utile A5)
                
                med_line_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 10), # Espacement entre chaque médicament
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ]))
                
                elements.append(med_line_table)
                
                # Ligne 2 : Posologie indentée en dessous
                elements.append(Paragraph(f"• {posologie}", poso_style))
        else:
            empty_style = ParagraphStyle(
                'Empty', parent=self.styles['Normal'],
                fontName=font_name, fontSize=10, textColor=p_color, alignment=TA_CENTER
            )
            elements.append(Paragraph("Aucun médicament prescrit.", empty_style))

        m_top = (config.margin_top if config else 3.6) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm

        doc = SimpleDocTemplate(
            filepath, pagesize=A5,
            rightMargin=1.5 * cm, leftMargin=1.5 * cm,
            topMargin=m_top, bottomMargin=m_bottom,
        )
        doc.cloture_text = None

        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user_obj)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)

        return filepath.replace("\\", "/")
