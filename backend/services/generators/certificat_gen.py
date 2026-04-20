import os
from datetime import datetime, date
from reportlab.lib import colors
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

    def _calculate_age(self, born):
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, data):
        """Nommage conforme : CERTIFICAT_NOM_PRENOM_YYYYMMDD_HHMMSS.pdf"""
        now = datetime.now()
        date_str = now.strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join(self.output_dir, now.strftime('%Y'), now.strftime('%m'))
        os.makedirs(save_dir, exist_ok=True)
        
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        filename = f"CERTIFICAT_{safe_name}_{date_str}.pdf"
        return os.path.join(save_dir, filename)

    def _draw_canvas(self, canvas, doc, config=None, user=None):
        self.base_template.draw_static_elements(canvas, doc, config=config, draw_legal_ids=False, user=user)

    def _create_header(self, patient, data, p_color):
        doc_date = getattr(data, 'doc_date', date.today())
        current_date = doc_date.strftime('%d/%m/%Y')
        age = self._calculate_age(patient.date_naissance)
        
        # Police dynamique pour l'en-tête
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

    def generate(self, patient, data, db=None, user_id=None):
        filepath = self._get_save_path(patient, data)
        doc_date = getattr(data, 'doc_date', date.today())
        
        config = None
        user_obj = None
        if db and user_id:
            from backend.models import CabinetConfig, User
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
            user_obj = db.query(User).filter(User.id == user_id).first()
        
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        
        # Police dynamique
        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

        title_style = ParagraphStyle(
            name='CertificatTitleA5', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=18, 
            textColor=p_color, 
            alignment=TA_CENTER
        )

        # TOUJOURS dessiner le Titre et le bloc Patient
        elements = [
            Spacer(1, 0.5*cm),
            Paragraph("CERTIFICAT MÉDICAL", title_style),
            Spacer(1, 1.0*cm),
            self._create_header(patient, data, p_color),
            Spacer(1, 1.5*cm)
        ]

        age = self._calculate_age(patient.date_naissance)
        gender = patient.sexe
        hon = "Mr" if gender in ["Homme", "Garçon", "M"] else "Madame"
        
        type_repos = "Arrêt de travail" if getattr(data, 'is_work_stop', False) else "Repos médical"
        start_date_str = getattr(data, 'start_date', doc_date).strftime('%d/%m/%Y')
        
        text_len = len(getattr(data, 'reason', ''))
        spacing_bottom = 2.0 if text_len < 100 else 1.0

        body_style = ParagraphStyle(
            name='CertifBody', 
            parent=self.styles['Normal'], 
            fontName=font_name, 
            fontSize=12, 
            textColor=colors.HexColor('#000000'), 
            alignment=TA_JUSTIFY, 
            leading=18
        )
        
        sig_style = ParagraphStyle(
            name='SignatureStyle', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=11, 
            textColor=p_color, 
            alignment=TA_RIGHT
        )

        dr_name = config.nom_praticien if config and config.nom_praticien else "Docteur"
        
        certif_text = (
            f"Je, soussigné Dr {dr_name}, certifie que l'état de santé de "
            f"{hon} <b>{patient.nom.upper()} {patient.prenom.capitalize()}</b>, âgé(e) de {age} ans, "
            f"nécessite un <b>{type_repos}</b> de <b>{data.days} jours</b>, à partir du {start_date_str}.<br/><br/>"
            f"Ce certificat est délivré à l'intéressé(e) pour servir et faire valoir ce que de droit."
        )
        
        content_block = [Paragraph(certif_text, body_style), Spacer(1, spacing_bottom*cm), Paragraph("Signature et Cachet :", sig_style)]
        elements.append(KeepTogether(content_block))

        # Build dynamique avec marges
        m_top = (config.margin_top if config else 3.6) * cm
        m_bottom = (config.margin_bottom if config else 3.0) * cm
        
        doc = SimpleDocTemplate(filepath, pagesize=A5, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=m_top, bottomMargin=m_bottom)
        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user_obj)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
        
        relative_path = filepath[filepath.find("static"):] if "static" in filepath else filepath
        return relative_path.replace("\\", "/")