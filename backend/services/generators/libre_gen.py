# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5, A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE, PinnedCloture, PageCounter

class LibreGenerator:
    def __init__(self, output_dir="static/documents"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()

    def _calculate_age(self, born):
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, titre):
        now = datetime.now()
        date_str = now.strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join(self.output_dir, now.strftime('%Y'), now.strftime('%m'))
        os.makedirs(save_dir, exist_ok=True)
        
        safe_titre = re.sub(r'[^\w\s-]', '', titre).strip().replace(' ', '_')[:30]
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        filename = f"LIBRE_{date_str}_{safe_titre}_{safe_name}.pdf"
        return os.path.join(save_dir, filename)

    def _draw_canvas(self, canvas, doc, config=None, user=None):
        """Rendu Elite avec identifiants légaux - IDENTIQUE À ACCOUNTING."""
        self.base_template.draw_static_elements(canvas, doc, config=config, draw_legal_ids=True, user=user)

    def _create_header(self, patient, data, p_color, config=None):
        """En-tête flexible : Supporte les surcharges utilisateur."""
        # 1. Gestion de la Date (Priorité à custom_date)
        custom_date = getattr(data, 'custom_date', None)
        if custom_date:
            current_date = custom_date
        else:
            doc_date = getattr(data, 'doc_date', date.today())
            current_date = doc_date.strftime('%d/%m/%Y') if hasattr(doc_date, 'strftime') else str(doc_date)
        
        # 2. Gestion du Destinataire (PrioritÃ© Ã  custom_patient)
        custom_patient = getattr(data, 'custom_patient', None)
        hide_patient = getattr(data, 'hide_patient_header', False)
        
        if hide_patient:
            return Spacer(1, 0.1*cm)

        font_name = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

        patient_style = ParagraphStyle(
            name='PatientInfo', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=11, 
            textColor=p_color, 
            leading=14
        )
        style_right = ParagraphStyle(
            'DocDate', 
            parent=self.styles['Normal'], 
            alignment=TA_RIGHT, 
            textColor=p_color,
            fontName=font_name,
            fontSize=11
        )
        
        if custom_patient:
            # Mode personnalisé : On affiche juste le texte saisi par l'utilisateur
            left_content = Paragraph(f"<b>Destinataire :</b> {custom_patient}", patient_style)
        else:
            # Mode standard : Nom, Âge, Dossier
            age = self._calculate_age(patient.date_naissance)
            left_content = Paragraph(f"<b>{patient.nom.upper()} {patient.prenom.upper()}</b><br/>Âge : {age} ans", patient_style)

        header_content = [
            [
                left_content, 
                Paragraph(f"Le : {current_date}", style_right)
            ]
        ]
        
        header_table = Table(header_content, colWidths=[7.0*cm, 4.8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        return header_table

    def generate(self, patient, data, db=None, user_id=None):
        titre = getattr(data, 'titre', 'Document Libre')
        contenu_html = getattr(data, 'contenu', '')
        # CTO Fix: Preserve newlines for ReportLab Paragraph
        contenu_html = contenu_html.replace('\n', '<br/>')
        filepath = self._get_save_path(patient, titre)
        
        config = None
        user_obj = None
        if db and user_id:
            from backend.models import CabinetConfig, User
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
            user_obj = db.query(User).filter(User.id == user_id).first()
        
        self.base_template.update_active_fonts(config)
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        font_name = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

        titre_nbsp = titre.replace(' ', ' ')
        title_base_fs = 17
        title_w = (getattr(data, 'page_size_val', None) or A5)[0] if isinstance(getattr(data, 'page_size_val', None) or A5, tuple) else 14.8 * cm
        title_base_fs = self.base_template.get_adaptive_font_size(titre_nbsp, font_bold, title_base_fs, title_w * 0.7)
        title_style = ParagraphStyle(
            name='TitleA5',
            parent=self.styles['Normal'],
            fontName=font_bold,
            fontSize=title_base_fs,
            textColor=p_color,
            alignment=TA_CENTER,
            leading=title_base_fs * 1.3,
            spaceAfter=12
        )
        
        # 3. Style du corps (Flexible)
        alignment_map = {
            'left': TA_LEFT,
            'center': TA_CENTER,
            'right': TA_RIGHT,
            'justify': TA_JUSTIFY
        }
        user_align = getattr(data, 'alignment', 'justify')
        final_align = alignment_map.get(user_align, TA_JUSTIFY)
        
        body_style = ParagraphStyle(
            name='LibreBody', 
            parent=self.styles['Normal'], 
            fontName=font_name, 
            fontSize=11, 
            textColor=p_color, # Respect du Branding Forcing
            alignment=final_align, 
            leading=16
        )
        
        # 4. Parsing du contenu pour gérer les tableaux Markdown
        contenu_raw = getattr(data, 'contenu', '')
        lines = contenu_raw.split('\n')
        
        parsed_elements = []
        current_text = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith('|') and line.strip().endswith('|'):
                if current_text:
                    parsed_elements.append(Paragraph("<br/>".join(current_text), body_style))
                    current_text = []
                
                table_data = []
                while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    row_line = lines[i].strip()
                    if not re.match(r'^\|[\s\-\|]+\|$', row_line):
                        cells = [cell.strip() for cell in row_line.strip('|').split('|')]
                        # Envelopper les cellules dans des Paragraph pour supporter le HTML interne (<b>, <i>...)
                        # Si c'est la première ligne, on peut forcer le gras
                        is_header = (len(table_data) == 0)
                        cell_style = ParagraphStyle(
                            'Cell', parent=body_style, 
                            fontName=font_bold if is_header else font_name,
                            alignment=TA_LEFT
                        )
                        paragraph_cells = [Paragraph(cell, cell_style) for cell in cells]
                        table_data.append(paragraph_cells)
                    i += 1
                
                if table_data:
                    # Calcul automatique des largeurs non nécessaire si on laisse Table faire,
                    # mais on peut limiter à la largeur dispo (ex: 13cm max divisé par colonnes)
                    t = Table(table_data, colWidths=None)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
                        ('TEXTCOLOR', (0,0), (-1,0), p_color),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('FONTNAME', (0,0), (-1,0), font_bold),
                        ('BOTTOMPADDING', (0,0), (-1,0), 8),
                        ('TOPPADDING', (0,0), (-1,0), 8),
                        ('BACKGROUND', (0,1), (-1,-1), colors.white),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                        ('PADDING', (0,0), (-1,-1), 6)
                    ]))
                    parsed_elements.append(t)
                    parsed_elements.append(Spacer(1, 0.4*cm))
                continue
            else:
                current_text.append(line)
                i += 1
                
        if current_text:
            parsed_elements.append(Paragraph("<br/>".join(current_text), body_style))

        elements = [
            Spacer(1, 0.4*cm),
            Paragraph(f"<u><b>{titre_nbsp.upper()}</b></u>", title_style),
            Spacer(1, 0.8*cm),
            self._create_header(patient, data, p_color, config),
            Spacer(1, 1.2*cm)
        ]
        elements.extend(parsed_elements)

        cloture_text = ""
        cloture_style = ParagraphStyle(
            name='LibreCloture', 
            parent=self.styles['Normal'], 
            fontName=font_bold, 
            fontSize=10, 
            textColor=p_color, 
            alignment=TA_CENTER
        )
        elements.append(PinnedCloture(cloture_text, cloture_style))

        # Gestion du format de page (A4 vs A5)
        page_format = getattr(data, 'page_size', 'A5').upper()
        page_size = A4 if page_format == 'A4' else A5

        # Forçage d'une marge supérieure minimale de sécurité (v5.0)
        m_top = (max(config.margin_top, 4.8) if config and config.margin_top else 4.8) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm
        
        
        p_width_val = page_size[0] if isinstance(page_size, tuple) else (14.8*cm if page_size == 'A5' else 21.0*cm)
        m_top, m_bottom, m_left, m_right = self.base_template.get_document_margins(config, p_width_val)
        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user_obj)
        doc_id = f"LIBRE-{datetime.now().strftime('%m%H%M')}"

        # Single-Page Force : compression progressive si contenu dépasse la page
        compression_factor = 1.0
        for _ in range(5):
            doc = SimpleDocTemplate(filepath, pagesize=page_size, rightMargin=m_right, leftMargin=m_left, topMargin=m_top, bottomMargin=m_bottom)
            doc.qr_type = 'WEBSITE'
            doc.doc_id = doc_id
            doc.cloture_text = cloture_text
            scaled = self._scale_elements(elements, compression_factor)
            page_counter = PageCounter()
            doc.build(scaled, onFirstPage=draw_method, onLaterPages=draw_method,
                      canvasmaker=page_counter.make_canvas_class())
            if page_counter.page_count <= 1:
                break
            compression_factor *= 0.85
            if compression_factor < 0.4:
                break

        return filepath.replace("\\", "/")

    def _scale_elements(self, elements, factor):
        if factor >= 0.99:
            return elements
        from reportlab.platypus import Paragraph as RLParagraph, Spacer as RLSpacer
        from reportlab.lib.styles import ParagraphStyle
        scaled = []
        for el in elements:
            if isinstance(el, RLParagraph):
                style = el.style
                new_style = ParagraphStyle(
                    style.name + '_s',
                    parent=style,
                    fontSize=max(style.fontSize * factor, 6),
                    leading=max((style.leading if style.leading else style.fontSize * 1.2) * factor, 7),
                    spaceAfter=(style.spaceAfter or 0) * factor,
                )
                scaled.append(RLParagraph(el.text, new_style))
            elif isinstance(el, RLSpacer):
                scaled.append(RLSpacer(el.width, max(el.height * factor, 2)))
            else:
                scaled.append(el)
        return scaled
