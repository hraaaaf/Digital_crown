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

# Nombres en toutes lettres jusqu'à 31 (plage cliniquement pertinente)
_DAYS_WORDS = {
    1: 'un', 2: 'deux', 3: 'trois', 4: 'quatre', 5: 'cinq',
    6: 'six', 7: 'sept', 8: 'huit', 9: 'neuf', 10: 'dix',
    11: 'onze', 12: 'douze', 13: 'treize', 14: 'quatorze', 15: 'quinze',
    16: 'seize', 17: 'dix-sept', 18: 'dix-huit', 19: 'dix-neuf', 20: 'vingt',
    21: 'vingt-et-un', 22: 'vingt-deux', 23: 'vingt-trois', 24: 'vingt-quatre',
    25: 'vingt-cinq', 26: 'vingt-six', 27: 'vingt-sept', 28: 'vingt-huit',
    29: 'vingt-neuf', 30: 'trente', 31: 'trente-et-un',
}


def _days_in_words(n: int) -> str:
    return _DAYS_WORDS.get(n, str(n))


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

        # Date de naissance formatée pour identification obligatoire
        dob_str = ""
        if patient.date_naissance:
            dob = patient.date_naissance.date() if hasattr(patient.date_naissance, 'date') else patient.date_naissance
            dob_str = dob.strftime('%d/%m/%Y')

        font_name = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

        patient_style = ParagraphStyle(
            name='PatientInfo',
            parent=self.styles['Normal'],
            fontName=font_bold,
            fontSize=11,
            textColor=p_color,
            leading=16,
        )
        style_right = ParagraphStyle(
            'DocDate',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT,
            textColor=p_color,
            fontName=font_name,
            fontSize=11,
        )

        patient_line = f"<b>{patient.nom.upper()} {patient.prenom.capitalize()}</b>"
        if dob_str:
            patient_line += f", né(e) le {dob_str}"
        patient_line += f", {age} ans"

        patient_w = 7.5 * cm
        adaptive_patient_style = self.base_template.get_adaptive_style(patient_style, patient_line, patient_w - 0.2*cm)

        header_content = [[
            Paragraph(patient_line, adaptive_patient_style),
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

        # Accord grammatical selon âge et genre
        if is_minor:
            hon = "l'enfant"
            pres = "présent" if is_male else "présente"
            int_ = "l'intéressé" if is_male else "l'intéressée"
            eviction_term = "une éviction scolaire"
            reprise_term = "la reprise des cours"
            ne_e = "né" if is_male else "née"
        else:
            hon = "Monsieur" if is_male else "Madame"
            pres = "présent" if is_male else "présente"
            int_ = "l'intéressé" if is_male else "l'intéressée"
            # "arrêt de travail" est réservé aux médecins ; le chirurgien-dentiste
            # délivre un "certificat de repos médical" (incapacité temporaire)
            eviction_term = "un repos médical"
            reprise_term = "la reprise de son activité professionnelle"
            ne_e = "né" if is_male else "née"

        # Déterminer la spécialité (Ortho vs Dentaire)
        is_ortho = False
        if hasattr(patient, 'dossier') and patient.dossier:
            is_ortho = patient.dossier.is_ortho_active

        reason = (getattr(data, 'reason', "Repos médical") or "Repos médical").strip()
        days = getattr(data, 'days', 1)
        observations = getattr(data, 'observations', '').strip()
        reason_lower = reason.lower()
        dr_name = config.nom_praticien if config and config.nom_praticien else "BENMOUSSA Achraf"
        nom_complet = f"{patient.nom.upper()} {patient.prenom.capitalize()}"

        certif_text = ""

        from datetime import timedelta
        doc_date_obj = getattr(data, 'doc_date', date.today())
        if isinstance(doc_date_obj, str):
            try:
                doc_date_obj = datetime.strptime(doc_date_obj, '%Y-%m-%d').date()
            except Exception:
                doc_date_obj = date.today()

        days_int = int(days)
        days_words = _days_in_words(days_int)
        days_label = f"<b>{days_int} ({days_words}) jours</b>"

        if days_int > 0:
            end_date = doc_date_obj + timedelta(days=days_int - 1)
            date_phrase = (
                f"allant du <b>{doc_date_obj.strftime('%d/%m/%Y')}</b> "
                f"au <b>{end_date.strftime('%d/%m/%Y')} inclus</b>"
            )
        else:
            date_phrase = f"le <b>{doc_date_obj.strftime('%d/%m/%Y')}</b>"

        if "post-opératoire" in reason_lower:
            certif_text = (
                f"Je soussigné Dr. <b>{dr_name}</b>, chirurgien-dentiste, certifie avoir examiné ce jour "
                f"{hon} <b>{nom_complet}</b>, {ne_e}(e) le "
                + (patient.date_naissance.strftime('%d/%m/%Y') if patient.date_naissance else "—")
                + f", et que son état de santé nécessite <b>{eviction_term}</b> "
                f"de {days_label}, {date_phrase}, "
                f"suite à une intervention chirurgicale bucco-dentaire. "
                f"<b>Sauf complications.</b><br/><br/>"
            )
        elif "intervention" in reason_lower:
            spec = "orthodontiques" if is_ortho else "bucco-dentaires"
            certif_text = (
                f"Je soussigné Dr. <b>{dr_name}</b>, chirurgien-dentiste, certifie avoir examiné ce jour "
                f"{hon} <b>{nom_complet}</b>, et que son état de santé nécessite des "
                f"<b>soins de suite consécutifs à une intervention {spec}</b> "
                f"pour une durée de {days_label}, {date_phrase}.<br/><br/>"
            )
        elif "présence" in reason_lower:
            spec = "orthodontiques" if is_ortho else "bucco-dentaires"
            certif_text = (
                f"Je soussigné Dr. <b>{dr_name}</b>, chirurgien-dentiste, certifie que "
                f"{hon} <b>{nom_complet}</b> a été <b>{pres} à ce cabinet</b> "
                f"le <b>{doc_date_obj.strftime('%d/%m/%Y')}</b> pour y recevoir des soins {spec}.<br/><br/>"
            )
        elif "aptitude" in reason_lower or "sport" in reason_lower:
            spec = "à la pratique de l'éducation physique et sportive" if is_minor else "à la pratique du sport"
            certif_text = (
                f"Je soussigné Dr. <b>{dr_name}</b>, chirurgien-dentiste, certifie avoir examiné ce jour "
                f"{hon} <b>{nom_complet}</b> et qu'il/elle "
                f"<b>ne présente à ce jour aucune contre-indication bucco-dentaire clinique apparente</b> "
                f"{spec}.<br/><br/>"
            )
        elif "reprise" in reason_lower:
            certif_text = (
                f"Je soussigné Dr. <b>{dr_name}</b>, chirurgien-dentiste, certifie avoir examiné ce jour "
                f"{hon} <b>{nom_complet}</b> et que son état de santé lui permet "
                f"d'assurer <b>{reprise_term}</b> à compter du <b>{doc_date_obj.strftime('%d/%m/%Y')}</b>.<br/><br/>"
            )
        elif "contre-indication" in reason_lower:
            certif_text = (
                f"Je soussigné Dr. <b>{dr_name}</b>, chirurgien-dentiste, certifie avoir examiné ce jour "
                f"{hon} <b>{nom_complet}</b> et que son état de santé présente une "
                f"<b>contre-indication médicale temporaire bucco-dentaire</b> "
                f"à l'acte ou à l'activité mentionné(e), pour une durée de {days_label}, "
                f"{date_phrase}.<br/><br/>"
            )
        else:
            phrase_motif = f"<b>{reason}</b>" if reason else f"<b>{eviction_term}</b>"
            certif_text = (
                f"Je soussigné Dr. <b>{dr_name}</b>, chirurgien-dentiste, certifie avoir examiné ce jour "
                f"{hon} <b>{nom_complet}</b> et que son état de santé nécessite {phrase_motif} "
                f"de {days_label}, {date_phrase}.<br/><br/>"
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

        certif_text += (
            f"Ce certificat est délivré à {int_}, remis en main propre à sa demande, "
            f"pour servir et valoir ce que de droit."
        )

        elements.append(Paragraph(certif_text, body_style))

        cloture_style = ParagraphStyle(
            name='CertifCloture',
            parent=self.styles['Normal'],
            fontName=font_bold,
            fontSize=10,
            textColor=p_color,
            alignment=TA_CENTER
        )
        elements.append(PinnedCloture("Signature et Cachet", cloture_style))

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
