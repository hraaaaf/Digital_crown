# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

from backend.services.base_template import BaseTemplate, NAVY_BLUE, PinnedCloture


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

        font_name = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

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

        patient_text = f"<b>{patient.nom.upper()} {patient.prenom.capitalize()}, {age} ans</b>"
        patient_w = 7.5 * cm
        adaptive_patient_style = self.base_template.get_adaptive_style(patient_style, patient_text, patient_w - 0.2*cm)
        
        header_content = [[
            Paragraph(patient_text, adaptive_patient_style),
            Paragraph(f"Le : <u>{current_date}</u>", style_right),
        ]]

        header_table = Table(header_content, colWidths=[7.5 * cm, 4.3 * cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1,-1), 12),
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
        font_name = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

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
            Paragraph("<u><b>ORDONNANCE</b></u>", title_style),
            Spacer(1, 0.6 * cm),
            self._create_header(patient, data, p_color, config),
            Spacer(1, 1.2 * cm),
        ]

        if hasattr(data, 'medications') and data.medications:
            # Utilisation de la police premium Montserrat (v6.0)
            med_font = self.base_template.premium_font
            med_font_bold = self.base_template.premium_bold

            # Détermination du facteur de compression si trop de médicaments (Single Page Force)
            num_meds = len(data.medications)
            compression_factor = 1.0
            if num_meds > 7:
                compression_factor = 0.9
            elif num_meds > 10:
                compression_factor = 0.8
            
            # Styles typographiques avec contraste optimal et adaptabilité
            base_med_fs = 13 * compression_factor
            base_form_fs = 11 * compression_factor
            base_poso_fs = 12 * compression_factor
            
            med_name_style = ParagraphStyle('MedName', parent=self.styles['Normal'], fontName=med_font_bold, fontSize=base_med_fs, textColor=p_color)
            med_forme_style = ParagraphStyle('MedForme', parent=self.styles['Normal'], fontName=med_font, fontSize=base_form_fs, textColor=p_color, alignment=TA_CENTER)
            med_dose_style = ParagraphStyle('MedDose', parent=self.styles['Normal'], fontName=med_font, fontSize=base_form_fs, textColor=p_color, alignment=TA_RIGHT)
            
            poso_style = ParagraphStyle(
                'PosoElite', parent=self.styles['Normal'], fontName=med_font, fontSize=base_poso_fs,
                textColor=p_color, leftIndent=1.5*cm, spaceBefore=2, spaceAfter=8 if num_meds > 6 else 14,
                leading=base_poso_fs * 1.2
            )
            
            warning_style = ParagraphStyle(
                'RadioWarning', parent=self.styles['Normal'], fontName=med_font, fontSize=10 * compression_factor,
                textColor=colors.HexColor("#7F1D1D"), leftIndent=1.5*cm, spaceBefore=2, spaceAfter=8 if num_meds > 6 else 14,
                italic=True
            )

            for i, med in enumerate(data.medications, 1):
                forme = getattr(med, 'forme', '') or ""
                dose = getattr(med, 'dosage', '') or ""
                nom = getattr(med, 'nom', '') or ""
                posologie = getattr(med, 'posologie', '') or ""
                m_type = getattr(med, 'type', 'MEDICAMENT')

                # Détermination du mode Radio
                is_radio = m_type == "EXAMEN" or "RADIO" in nom.upper() or "X-RAY" in nom.upper()
                
                # Nettoyage de la forme si personnalisée
                display_forme = forme.replace('AUTRE: ', '').replace('Autre: ', '') if forme else ""
                
                # Ligne 1 : Construction dynamique des colonnes
                cols = []
                col_widths = []

                # Nom (toujours présent) - Application de la police adaptative
                name_text = f"{i}- <b>{nom.upper()}</b>"
                name_w = 7.0*cm
                adaptive_name_style = self.base_template.get_adaptive_style(med_name_style, name_text, name_w - 0.5*cm)
                cols.append(Paragraph(name_text, adaptive_name_style))
                col_widths.append(name_w)
                
                # On n'affiche Forme/Dose que si c'est un médicament ET que les champs sont remplis
                if not is_radio:
                    if display_forme:
                        # Application de la police adaptative pour la forme (Bain de bouche, etc.)
                        form_w = 3.0*cm
                        adaptive_form_style = self.base_template.get_adaptive_style(med_forme_style, display_forme, form_w - 0.2*cm)
                        cols.append(Paragraph(f"<i>{display_forme}</i>", adaptive_form_style))
                        col_widths.append(form_w)
                    else:
                        col_widths[0] += 1.0*cm
                        
                    if dose:
                        dose_w = 1.8*cm
                        adaptive_dose_style = self.base_template.get_adaptive_style(med_dose_style, dose, dose_w - 0.1*cm)
                        cols.append(Paragraph(f"{dose}", adaptive_dose_style))
                        col_widths.append(dose_w)
                    else:
                        col_widths[0] += 0.8*cm

                # Recalcul des largeurs si colonnes manquantes (Total A5 utile = ~11.8cm)
                total_w = sum(col_widths)
                if total_w < 11.8*cm:
                    col_widths[0] += (11.8*cm - total_w)

                med_line_table = Table([cols], colWidths=col_widths)
                # Ajustement du padding pour gagner de l'espace si num_meds est élevé
                top_pad = 12 if num_meds < 7 else 8
                med_line_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), top_pad),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ]))
                
                elements.append(med_line_table)
                
                # Ligne 2 : Posologie ou Avertissement Radio (Suppression du point devant)
                if is_radio:
                    warning_msg = "⚠️ Radioprotection : À réaliser selon les normes de sécurité en vigueur."
                    if posologie:
                        warning_msg += f" {posologie}"
                    elements.append(Paragraph(warning_msg, warning_style))
                elif posologie:
                    elements.append(Paragraph(f"{posologie}", poso_style)) # Pas de point ici
                else:
                    elements.append(Spacer(1, 0.5*cm))
        else:
            empty_style = ParagraphStyle(
                'Empty', parent=self.styles['Normal'],
                fontName=font_name, fontSize=10, textColor=p_color, alignment=TA_CENTER
            )
            elements.append(Paragraph("Aucun médicament prescrit.", empty_style))

        # Clôture ancrée en bas (Signature)
        cloture_style = ParagraphStyle(
            name='OrdoCloture', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=10, 
            textColor=p_color, 
            alignment=TA_CENTER
        )
        elements.append(PinnedCloture("Signature et Cachet", cloture_style))

        # Utilisation des marges configurées avec un seuil minimal de sécurité (v5.0)
        m_top = (max(config.margin_top, 4.8) if config and config.margin_top is not None else 4.8) * cm
        m_bottom = (max(config.margin_bottom, 4.5) if config and config.margin_bottom is not None else 4.5) * cm

        doc = SimpleDocTemplate(
            filepath, pagesize=A5,
            rightMargin=1.5 * cm, leftMargin=1.5 * cm,
            topMargin=m_top, bottomMargin=m_bottom,
        )
        doc.qr_type = 'VALIDATION'
        doc.doc_id = getattr(data, 'id', 'ORD-TEMP')
        doc.cloture_text = None

        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user_obj)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)

        return filepath.replace("\\", "/")
