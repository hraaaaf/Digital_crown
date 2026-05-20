# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE, PinnedCloture


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
        """Rendu Elite avec signature et QR Code alignés."""
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

        self.base_template.update_active_fonts(config)
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        font_main = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

        title_style = ParagraphStyle(
            name='TitleA5',
            parent=self.styles['Normal'],
            fontName=font_bold,
            fontSize=18,
            textColor=p_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            leading=22
        )

        elements = [
            # Offset initial réduit pour un meilleur équilibre vertical (v4.0)
            Spacer(1, 0.4 * cm),
            Paragraph("<u><b>CERTIFICAT MEDICAL</b></u>", title_style),
            Spacer(1, 1.0 * cm),
            self._create_header(patient, data, p_color, config),
            Spacer(1, 1.8 * cm),
        ]

        age = self._calculate_age(patient.date_naissance)
        is_minor = age < 16
        gender = getattr(patient, 'sexe', getattr(patient, 'genre', 'M'))
        is_male = gender in ["Homme", "Garçon", "M", "m", "Male", "male"]
        
        # Honorifiques Pédiatriques vs Adultes
        if is_minor:
            hon = "l'enfant"
            pres = "présent" if is_male else "présente"
            int_ = "l'intéressé" if is_male else "l'intéressée"
            eviction_term = "une éviction scolaire"
            reprise_term = "une reprise des cours"
        else:
            hon = "Monsieur" if is_male else "Madame"
            pres = "présent" if is_male else "présente"
            int_ = "l'intéressé" if is_male else "l'intéressée"
            eviction_term = "un arrêt de travail"
            reprise_term = "une reprise du travail"
        
        # Déterminer la spécialité (Ortho vs Dentaire)
        is_ortho = False
        if hasattr(patient, 'dossier') and patient.dossier:
            is_ortho = patient.dossier.is_ortho_active

        # Phrasage Elite dynamique selon le choix du praticien
        reason = (getattr(data, 'reason', "Repos médical") or "Repos médical").strip()
        days = getattr(data, 'days', 1)
        observations = getattr(data, 'observations', '').strip()
        reason_lower = reason.lower()
        dr_name = config.nom_praticien if config and config.nom_praticien else "BENMOUSSA Achraf"
        nom_complet = f"{patient.nom.upper()} {patient.prenom.capitalize()}"
        
        # Initialisation par défaut
        certif_text = ""
        
        # Calcul précis des dates d'arrêt/éviction
        from datetime import timedelta
        doc_date_obj = getattr(data, 'doc_date', date.today())
        if isinstance(doc_date_obj, str):
            try:
                doc_date_obj = datetime.strptime(doc_date_obj, '%Y-%m-%d').date()
            except Exception:
                doc_date_obj = date.today()
        
        days_int = int(days)
        if days_int > 0:
            end_date = doc_date_obj + timedelta(days=days_int - 1)
            date_phrase = f"allant du <b>{doc_date_obj.strftime('%d/%m/%Y')}</b> au <b>{end_date.strftime('%d/%m/%Y')} inclus</b>"
        else:
            date_phrase = f"le <b>{doc_date_obj.strftime('%d/%m/%Y')}</b>"

        if "post-opératoire" in reason_lower:
            certif_text = (
                f"Je, soussigné Dr. <b>{dr_name}</b>, certifie après examen clinique que l'état de santé de "
                f"{hon} <b>{nom_complet}</b> nécessite <b>{eviction_term} de {days} jours</b>, {date_phrase}, "
                f"suite à une intervention chirurgicale buccale.<br/><br/>"
            )
        elif "intervention" in reason_lower:
            spec = "orthodontique" if is_ortho else "dentaire"
            certif_text = (
                f"Je, soussigné Dr. <b>{dr_name}</b>, certifie après examen clinique que l'état de santé de "
                f"{hon} <b>{nom_complet}</b> nécessite des <b>soins de suite d'intervention</b> "
                f"{spec} pour une période de <b>{days} jours</b>, {date_phrase}.<br/><br/>"
            )
        elif "présence" in reason_lower:
            spec = "orthodontiques" if is_ortho else "dentaires"
            certif_text = (
                f"Je, soussigné Dr. <b>{dr_name}</b>, certifie que {hon} <b>{nom_complet}</b> a été "
                f"<b>{pres} au cabinet</b> {date_phrase} pour y recevoir des soins {spec} professionnels.<br/><br/>"
            )
        elif "aptitude" in reason_lower or "sport" in reason_lower:
            spec = "à la pratique de l'éducation physique et sportive" if is_minor else "à la pratique du sport en compétition"
            certif_text = (
                f"Je, soussigné Dr. <b>{dr_name}</b>, certifie après examen clinique que {hon} <b>{nom_complet}</b> "
                f"<b>ne présente à ce jour aucune contre-indication clinique apparente</b> {spec}.<br/><br/>"
            )
        elif "reprise" in reason_lower:
            certif_text = (
                f"Je, soussigné Dr. <b>{dr_name}</b>, certifie que {hon} <b>{nom_complet}</b> est en état "
                f"d'assurer <b>{reprise_term}</b> à compter du {doc_date_obj.strftime('%d/%m/%Y')}.<br/><br/>"
            )
        elif "contre-indication" in reason_lower:
            certif_text = (
                f"Je, soussigné Dr. <b>{dr_name}</b>, certifie après examen clinique que l'état de santé de "
                f"{hon} <b>{nom_complet}</b> présente une <b>contre-indication médicale temporaire</b> "
                f"à la pratique ou à l'acte mentionné, pour une durée de <b>{days} jours</b>, {date_phrase}.<br/><br/>"
            )
        else:
            phrase_motif = f"<b>{reason}</b>" if reason else f"<b>{eviction_term}</b>"
            certif_text = (
                f"Je, soussigné Dr. <b>{dr_name}</b>, certifie après examen clinique que l'état de santé de "
                f"{hon} <b>{nom_complet}</b> nécessite {phrase_motif} "
                f"de <b>{days} jours</b>, {date_phrase}.<br/><br/>"
            )

        body_style = ParagraphStyle(
            name='CertifBody',
            parent=self.styles['Normal'],
            fontName=font_main,
            fontSize=11,
            textColor=p_color,
            alignment=TA_JUSTIFY,
            leading=18,
        )

        if observations:
            certif_text += f"<b>Observations :</b> {observations}<br/><br/>"
            
        certif_text += f"Ce certificat est délivré à {int_} pour servir et faire valoir ce que de droit."
        
        elements.append(Paragraph(certif_text, body_style))

        # Clôture ancrée en bas
        cloture_style = ParagraphStyle(
            name='CertifCloture', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=10, 
            textColor=p_color, 
            alignment=TA_CENTER
        )
        elements.append(PinnedCloture("Signature et Cachet", cloture_style))

        # Forçage d'une marge supérieure minimale de sécurité (v5.0)
        m_top = (max(config.margin_top, 4.8) if config and config.margin_top else 4.8) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm

        doc = SimpleDocTemplate(
            filepath, pagesize=A5,
            rightMargin=1.8 * cm, leftMargin=1.8 * cm,
            topMargin=m_top, bottomMargin=m_bottom,
        )
        doc.qr_type = 'VALIDATION'
        doc.doc_id = getattr(data, 'id', 'CERT-TEMP')
        doc.cloture_text = None

        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user_obj)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)

        return filepath.replace("\\", "/")
