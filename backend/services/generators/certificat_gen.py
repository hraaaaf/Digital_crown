# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE, PageCounter
from backend.services.certificate_signer_policy import resolve_certificate_signer_name
from backend.services.generators.document_layout_safety import join_unbreakable

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


SIGNATURE_LABEL = 'Signature manuscrite du praticien'


class CertificateSignatureSpace(Flowable):
    """Réserve une vraie zone blanche à signer à la main sur le certificat imprimé.

    Aucun fac-similé, tampon ou autre procédé n'est injecté par le logiciel :
    la zone reste volontairement vide pour la signature manuscrite du praticien.
    """

    def __init__(self, font_name: str, text_color=NAVY_BLUE, height=2.4 * cm, line_width=4.8 * cm):
        super().__init__()
        self.font_name = font_name
        self.text_color = text_color
        self.signature_height = height
        self.line_width = line_width

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.height = self.signature_height
        return availWidth, self.signature_height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        effective_line_width = min(self.line_width, self.width * 0.55)
        line_start = self.width - effective_line_width
        line_y = 0.62 * cm

        canvas.setStrokeColor(self.text_color)
        canvas.setLineWidth(0.5)
        canvas.line(line_start, line_y, self.width, line_y)

        canvas.setFillColor(self.text_color)
        canvas.setFont(self.font_name, 7.5)
        canvas.drawCentredString(
            line_start + effective_line_width / 2,
            0.26 * cm,
            SIGNATURE_LABEL,
        )
        canvas.restoreState()


def _append_handwritten_signature_space(elements, font_name: str, text_color) -> None:
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(CertificateSignatureSpace(font_name=font_name, text_color=text_color))


def _days_in_words(n: int) -> str:
    return _DAYS_WORDS.get(n, str(n))


def _is_free_medical_certificate(reason: str) -> bool:
    return (reason or '').strip().casefold() in {'certificat médical', 'certificat medical'}


def _format_free_certificate_content(content: str) -> str:
    cleaned = (content or '').strip()
    if not cleaned:
        raise ValueError('Le contenu du certificat médical est requis.')
    return '<br/>'.join(escape(line) for line in cleaned.splitlines())


def _coerce_certificate_date(value, fallback: date) -> date:
    if not value:
        return fallback
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return fallback
    return fallback


def _resolve_certificate_dates(data, today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    issue_date = _coerce_certificate_date(getattr(data, 'doc_date', None), today)
    rest_start_date = _coerce_certificate_date(getattr(data, 'start_date', None), issue_date)
    return issue_date, rest_start_date


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
        doc_date, _ = _resolve_certificate_dates(data)
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
        patient_line += f", {join_unbreakable(age, 'ans')}"

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
            # Le praticien demande explicitement "arrêt de travail"
            eviction_term = "un arrêt de travail"
            reprise_term = "la reprise de son activité professionnelle"
            ne_e = "né" if is_male else "née"

        # Déterminer la spécialité (Ortho vs Dentaire)
        is_ortho = False
        if hasattr(patient, 'dossier') and patient.dossier:
            is_ortho = patient.dossier.is_ortho_active

        reason = (getattr(data, 'reason', "Arrêt de travail") or "Arrêt de travail").strip()
        days = getattr(data, 'days', 1)
        free_content = getattr(data, 'content', None)
        observations = getattr(data, 'observations', '').strip()
        reason_lower = reason.lower()
        is_free_medical = _is_free_medical_certificate(reason)
        dr_name = resolve_certificate_signer_name(user_obj)

        # Nettoyage pour éviter "Dr Dr."
        dr_name_clean = dr_name.replace("Dr.", "").replace("Dr ", "").replace("Docteur ", "").strip()

        nom_complet = f"{patient.nom.upper()} {patient.prenom.capitalize()}"

        certif_text = ""

        from datetime import timedelta
        issue_date_obj, rest_start_date_obj = _resolve_certificate_dates(data)

        days_int = int(days or 0)
        days_words = _days_in_words(days_int)
        days_label = f"({days_int} jours)"

        if days_int > 0:
            end_date = rest_start_date_obj + timedelta(days=days_int - 1)
            date_phrase = (
                f"du <b>{rest_start_date_obj.strftime('%d/%m/%Y')}</b> "
                f"au <b>{end_date.strftime('%d/%m/%Y')} inclus</b>"
            )
        else:
            date_phrase = f"le <b>{rest_start_date_obj.strftime('%d/%m/%Y')}</b>"

        age = self._calculate_age(patient.date_naissance)
        age_text = f", âgé(e) de {join_unbreakable(age, 'ans')}"

        if is_free_medical:
            certif_text = _format_free_certificate_content(free_content)
        elif "présence" in reason_lower:
            spec = "orthodontiques" if is_ortho else "bucco-dentaires"
            certif_text = (
                f"Je soussigné Dr <b>{dr_name_clean}</b>, chirurgien-dentiste, certifie que "
                f"{hon} <b>{nom_complet}</b> a été <b>{pres} à notre cabinet</b> "
                f"le <b>{issue_date_obj.strftime('%d/%m/%Y')}</b> de façon effective, pour y recevoir des soins {spec}.<br/><br/>"
            )
        else:
            certif_text = (
                f"Je soussigné Dr <b>{dr_name_clean}</b>, chirurgien-dentiste, certifie que l'état de santé de "
                f"{hon} <b>{nom_complet}</b>{age_text}, nécessite <b>{eviction_term}</b> "
                f"{date_phrase} {days_label}.<br/><br/>"
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

        if not is_free_medical:
            certif_text += (
                f"Ce certificat est délivré à {int_}, remis en main propre à sa demande, "
                f"pour servir et valoir ce que de droit."
            )

        elements.append(Paragraph(certif_text, body_style))
        _append_handwritten_signature_space(elements, font_name=font_bold, text_color=p_color)

        m_top = (max(config.margin_top, 4.8) if config and config.margin_top else 4.8) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm

        p_width_val = A5[0] if isinstance(A5, tuple) else (14.8*cm if A5 == 'A5' else 21.0*cm)
        m_top, m_bottom, m_left, m_right = self.base_template.get_document_margins(config, p_width_val)
        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user_obj)

        # Single-Page Force : compression progressive jusqu'à ce que tout tienne sur 1 page
        compression_factor = 1.0
        for _ in range(6):
            scaled_elements = self._scale_elements(elements, compression_factor)
            doc = SimpleDocTemplate(
                filepath, pagesize=A5,
                rightMargin=m_right, leftMargin=m_left,
                topMargin=m_top, bottomMargin=m_bottom,
            )
            doc.qr_type = 'VALIDATION'
            doc.doc_id = getattr(data, 'id', 'CERT-TEMP')
            doc.cloture_text = None
            page_counter = PageCounter()
            doc.build(scaled_elements, onFirstPage=draw_method, onLaterPages=draw_method,
                      canvasmaker=page_counter.make_canvas_class())
            if page_counter.page_count <= 1:
                break
            compression_factor *= 0.85
            if compression_factor < 0.4:
                break

        return filepath.replace("\\", "/")

    def _scale_elements(self, elements, factor):
        """Retourne une copie des éléments avec les ParagraphStyle redimensionnés."""
        if factor >= 0.99:
            return elements
        from reportlab.platypus import Paragraph as RLParagraph, Spacer as RLSpacer
        from reportlab.lib.styles import ParagraphStyle
        scaled = []
        for el in elements:
            if isinstance(el, RLParagraph):
                style = el.style
                new_style = ParagraphStyle(
                    style.name + '_scaled',
                    parent=style,
                    fontSize=max(style.fontSize * factor, 6),
                    leading=max(style.leading * factor if hasattr(style, 'leading') and style.leading else style.fontSize * factor * 1.2, 7),
                    spaceAfter=style.spaceAfter * factor if hasattr(style, 'spaceAfter') else 0,
                )
                scaled.append(RLParagraph(el.text, new_style))
            elif isinstance(el, RLSpacer):
                scaled.append(RLSpacer(el.width, max(el.height * factor, 2)))
            else:
                scaled.append(el)
        return scaled
