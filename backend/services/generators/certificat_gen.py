# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY

from backend.services.base_template import BaseTemplate, NAVY_BLUE


class CertificatGenerator:
    def __init__(self, output_dir="static/documents"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()

    def _calculate_age(self, born):
        if not born:
            return 0
        today = date.today()
        birth = born.date() if hasattr(born, 'date') else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, data):
        now = datetime.now()
        date_str = now.strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join(self.output_dir, now.strftime('%Y'), now.strftime('%m'))
        os.makedirs(save_dir, exist_ok=True)
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        filename = f"CERTIFICAT_{safe_name}_{date_str}.pdf"
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

        font_name = "Helvetica"
        font_bold = "Helvetica-Bold"

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
        # Forçage Helvetica pour un contraste maximal Gras/Normal
        font_main = "Helvetica"
        font_bold = "Helvetica-Bold"

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
            Paragraph("<u>CERTIFICAT MEDICAL</u>", title_style),
            Spacer(1, 0.6 * cm),
            self._create_header(patient, data, p_color, config),
            Spacer(1, 1.2 * cm),
        ]

        age = self._calculate_age(patient.date_naissance)
        gender = getattr(patient, 'sexe', 'M')
        hon = "Mr" if gender in ["Homme", "Garçon", "M"] else "Madame"

        # Le champ `reason` porte le type de certificat choisi dans le formulaire
        reason = (getattr(data, 'reason', None) or "Repos médical").strip()
        is_work_stop = getattr(data, 'is_work_stop', False)

        if is_work_stop:
            type_repos = "un arrêt de travail"
        elif reason.lower().startswith("repos"):
            type_repos = "un repos médical"
        else:
            # Certificat à motif personnalisé (aptitude sportive, dispense…)
            type_repos = f"un repos / une dispense pour : {reason}"

        days = getattr(data, 'days', 1)
        start_date = getattr(data, 'start_date', date.today())
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except Exception:
                start_date = date.today()

        start_date_str = start_date.strftime('%d/%m/%Y')

        body_style = ParagraphStyle(
            name='CertifBody',
            parent=self.styles['Normal'],
            fontName=font_main,
            fontSize=11,
            textColor=p_color,
            alignment=TA_JUSTIFY,
            leading=18,
        )

        # Récupération sécurisée
        dr_name = config.nom_praticien if config and config.nom_praticien else "Docteur"
        
        # Enchaînement fluide et robuste
        nom_complet = f"{patient.nom.upper()} {patient.prenom.capitalize()}"
        
        certif_text = (
            f"Je, soussigné Dr. {dr_name}, certifie que l'état de santé de "
            f"{hon} <b>{nom_complet}</b>, âgé(e) de <b>{age} ans</b>, "
            f"nécessite {type_repos} d'une durée de <b>{days} jours</b>, à partir du <b>{start_date_str}</b>.<br/><br/>"
            f"Ce certificat est délivré à l'intéressé(e) pour servir et faire valoir ce que de droit."
        )
        
        elements.append(Paragraph(certif_text, body_style))

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
