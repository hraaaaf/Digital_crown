# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
import decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Import centralisé du Design System
from backend.services.base_template import BaseTemplate, NAVY_BLUE, PinnedCloture

class AccountingGenerator:
    def __init__(self, base_output_dir="static/documents"):
        self.base_output_dir = base_output_dir
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        """Styles Premium unifiés avec contraste maximal Gras/Normal."""
        font_main = "Helvetica"
        font_bold = "Helvetica-Bold"

        self.styles.add(ParagraphStyle(
            name='TitleA5',
            parent=self.styles['Normal'],
            fontName=font_bold,
            fontSize=16,
            textColor=NAVY_BLUE,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='PatientInfo',
            parent=self.styles['Normal'],
            fontName=font_bold,
            fontSize=10,
            textColor=NAVY_BLUE,
            leading=12
        ))
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontName=font_bold,
            fontSize=8,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='TableText',
            parent=self.styles['Normal'],
            fontName=font_main,
            fontSize=9,
            textColor=NAVY_BLUE,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='ActeText',
            parent=self.styles['Normal'],
            fontName=font_main,
            fontSize=10,
            textColor=NAVY_BLUE,
            alignment=TA_LEFT,
            leading=14 
        ))

    def _amount_to_words(self, amount):
        """Convertit un montant (float) en lettres."""
        units = ["", "Un", "Deux", "Trois", "Quatre", "Cinq", "Six", "Sept", "Huit", "Neuf"]
        tens = ["", "Dix", "Vingt", "Trente", "Quarante", "Cinquante", "Soixante", "Soixante-dix", "Quatre-vingt", "Quatre-vingt-dix"]
        
        def _to_words_int(n):
            if n == 0: return "Zéro"
            if n == 1000: return "Mille"
            if n < 10: return units[int(n)]
            if 10 <= n < 20:
                return ["Dix", "Onze", "Douze", "Treize", "Quatorze", "Quinze", "Seize", "Dix-sept", "Dix-huit", "Dix-neuf"][int(n-10)]
            if n < 100:
                q, r = divmod(n, 10)
                if q == 7: return "Soixante-dix" if r == 0 else "Soixante-" + _to_words_int(10+r).lower()
                if q == 9: return "Quatre-vingt-dix" if r == 0 else "Quatre-vingt-" + _to_words_int(10+r).lower()
                return tens[int(q)] + ("-" + _to_words_int(r).lower() if r > 0 else "")
            if n < 1000:
                q, r = divmod(n, 100)
                if q == 0: return _to_words_int(r)
                prefix = units[int(q)] + " " if q > 1 else ""
                suffix = "Cent" + ("s" if r == 0 and q > 1 else "")
                return prefix + suffix + (" " + _to_words_int(r).lower() if r > 0 else "")
            
            if n < 1000000:
                q, r = divmod(n, 1000)
                prefix = _to_words_int(q) + " " if q > 1 else ""
                return prefix + "Mille" + (" " + _to_words_int(r).lower() if r > 0 else "")
                
            return str(int(n))

        d_amount = decimal.Decimal(str(amount)).quantize(decimal.Decimal('0.01'), rounding='ROUND_HALF_UP')
        dirhams = int(d_amount)
        centimes = int((d_amount - dirhams) * 100)

        res = _to_words_int(dirhams)
        res += " Dirham" if dirhams <= 1 else " Dirhams"
        if centimes > 0:
            res += " et " + _to_words_int(centimes).lower()
            res += " Centime" if centimes <= 1 else " Centimes"
        return res

    def _calculate_age(self, born):
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, prefix, data, doc_id=None):
        now = datetime.now()
        date_str = now.strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join(self.base_output_dir, now.strftime('%Y'), now.strftime('%m'))
        os.makedirs(save_dir, exist_ok=True)
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        return os.path.join(save_dir, f"{prefix}_{safe_name}_{date_str}.pdf")

    def _draw_canvas(self, canvas, doc, config=None, user=None, highlighted_teeth=None):
        """Rendu de la note comptable avec identifiants."""
        self.base_template.draw_static_elements(canvas, doc, config=config, draw_legal_ids=True, user=user)

    def _create_header(self, patient, data, p_color):
        doc_date = getattr(data, 'doc_date', date.today())
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
        
        header_content = [
            [
                Paragraph(f"<b>{patient.nom.upper()} {patient.prenom.capitalize()}, {age} ans</b>", patient_style), 
                Paragraph(f"Le : <u>{current_date}</u>", style_right)
            ]
        ]
        return Table(header_content, colWidths=[7.0*cm, 4.8*cm])

    def _get_dynamic_acte_style(self, base_style, text, max_chars_at_10pt):
        """Ajuste dynamiquement la taille de la police pour tenir sur une ligne."""
        text_len = len(text) if text else 0
        fs = 10.0
        if text_len > max_chars_at_10pt:
            # On réduit proportionnellement pour tout faire rentrer, avec une taille minimum de 5.5
            fs = max(5.5, 10.0 * (max_chars_at_10pt / text_len))
            
        return ParagraphStyle(
            name='DynamicActeText',
            parent=base_style,
            fontSize=fs,
            leading=fs + 3.0
        )

    def _create_installments_table(self, installments, total_honoraires, p_color):
        """Crée un tableau de suivi des règlements (échéancier)."""
        if not installments:
            return None
            
        font_bold = "Helvetica-Bold"
        font_main = "Helvetica"
        
        header_style = ParagraphStyle(name='InstHeader', fontName=font_bold, fontSize=9, textColor=colors.white, alignment=TA_CENTER)
        text_style = ParagraphStyle(name='InstText', fontName=font_main, fontSize=9, textColor=p_color, alignment=TA_CENTER)
        
        table_data = [[Paragraph("ÉCHÉANCE / AVANCE", header_style), Paragraph("DATE", header_style), Paragraph("MONTANT (MAD)", header_style)]]
        
        total_verse = 0.0
        for inst in installments:
            d_str = inst.date.strftime('%d/%m/%Y') if hasattr(inst.date, 'strftime') else str(inst.date)
            table_data.append([
                Paragraph(inst.label, text_style),
                Paragraph(d_str, text_style),
                Paragraph(f"{inst.amount:.2f}", text_style)
            ])
            total_verse += inst.amount
            
        reste = total_honoraires - total_verse
        
        summary_style = ParagraphStyle(name='InstSummary', fontName=font_bold, fontSize=10, textColor=p_color, alignment=TA_RIGHT)
        reste_style = ParagraphStyle(name='ResteStyle', fontName=font_bold, fontSize=10, textColor=colors.HexColor("#B45309"), alignment=TA_CENTER) # Amber-700
        
        table_data.append([Paragraph("TOTAL VERSÉ", summary_style), "", Paragraph(f"<b>{total_verse:.2f} MAD</b>", text_style)])
        table_data.append([Paragraph("RESTE À PAYER", summary_style), "", Paragraph(f"<b>{reste:.2f} MAD</b>", reste_style)])
        
        t = Table(table_data, colWidths=[5.3*cm, 3.5*cm, 4.0*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), p_color),
            ('GRID', (0,0), (-1,-3), 0.3, p_color),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('SPAN', (0,-2), (1,-2)),
            ('SPAN', (0,-1), (1,-1)),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#FFFBEB")),
            ('BOX', (0,-1), (-1,-1), 0.3, colors.HexColor("#FDE68A")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        return t

    def generate_note(self, patient, data, facture_number=None, db=None, user_id=None, **kwargs):
        filepath = self._get_save_path(patient, "NOTE", data, doc_id=facture_number)
        config = None
        if db and user_id:
            from backend.models import CabinetConfig
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        
        font_main = "Helvetica"
        font_bold = "Helvetica-Bold"

        title_style = ParagraphStyle(name='TitleA5', parent=self.styles['Normal'], fontName=font_bold, fontSize=17, textColor=p_color, alignment=TA_CENTER, spaceAfter=12)
        elements = [Spacer(1, 0.4*cm), Paragraph(f"<u><b>NOTE D'HONORAIRES N° {facture_number}</b></u>" if facture_number else "<u><b>NOTE D'HONORAIRES</b></u>", title_style), Spacer(1, 1.0*cm), self._create_header(patient, data, p_color), Spacer(1, 1.2*cm)]
        
        header_style = ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName=font_bold, fontSize=10, textColor=colors.white, alignment=TA_CENTER)
        table_data = [[Paragraph("ACTE", header_style), Paragraph("DENT", header_style), Paragraph("PAIEMENT", header_style), Paragraph("HONORAIRES", header_style)]]
        text_style = ParagraphStyle(name='TableText', parent=self.styles['Normal'], fontName=font_main, fontSize=10, textColor=p_color, alignment=TA_CENTER, leading=14)
        acte_style = ParagraphStyle(name='ActeText', parent=self.styles['Normal'], fontName=font_main, fontSize=10, textColor=p_color, alignment=TA_LEFT, leading=14)

        total = 0.0
        for p in data.payments:
            dyn_style = self._get_dynamic_acte_style(acte_style, p.acte, max_chars_at_10pt=24)
            acte_para = Paragraph(p.acte, dyn_style)
            dent_display = getattr(p, 'dent', '-')
            if hasattr(p, 'dents') and p.dents and len(p.dents) > 0:
                dent_display = ', '.join([str(d) for d in p.dents])
            table_data.append([acte_para, Paragraph(str(dent_display), text_style), Paragraph(getattr(p, 'mode_reglement', 'Espèces'), text_style), Paragraph(f"{p.montant:.2f}", text_style)])
            total += p.montant

        total_words_style = ParagraphStyle(name='TotalWords', parent=self.styles['Normal'], fontName=font_bold, fontSize=11, textColor=p_color, alignment=TA_RIGHT)
        total_amount_style = ParagraphStyle(name='TotalAmount', parent=self.styles['Normal'], fontName=font_bold, fontSize=12, textColor=p_color, alignment=TA_CENTER)
        
        table_data.append([Paragraph("<b>TOTAL GÉNÉRAL</b>", total_words_style), "", "", Paragraph(f"<b>{total:.2f} MAD</b>", total_amount_style)])
        
        t = Table(table_data, colWidths=[4.8*cm, 2.0*cm, 3.0*cm, 3.0*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), p_color), 
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-2), 0.3, p_color), 
            ('SPAN', (0, -1), (2, -1)),
            ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
            ('TEXTCOLOR', (0,1), (-1,-1), p_color), 
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 12),
            ('TOPPADDING', (0,-1), (-1,-1), 12),
            ('WORDWRAP', (0,0), (-1,-1), True)
        ]))
        elements.append(t)
        
        inst_table = self._create_installments_table(getattr(data, 'installments', []), total, p_color)
        if inst_table:
            elements.append(Spacer(1, 1.2*cm))
            elements.append(Paragraph("SUIVI DES RÈGLEMENTS", ParagraphStyle('InstTitle', fontName=font_bold, fontSize=10, textColor=p_color, spaceAfter=8)))
            elements.append(inst_table)

        total_words = self._amount_to_words(total)
        template = config.cloture_note_template if config and hasattr(config, 'cloture_note_template') else None
        if not template:
            template = "Arrêtée la présente note à la somme de {total_words} TTC."
            
        cloture = template.format(total_words=total_words, total_amount=f"{total:.2f}")
        
        # Ajout direct dans les éléments pour visibilité immédiate (v5.3)
        cloture_style_normal = ParagraphStyle(name='ClotureNormal', fontName=font_bold, fontSize=11, textColor=p_color, spaceBefore=15, leading=14)
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(cloture, cloture_style_normal))
        
        font_name = self.base_template.arabic_font
        font_bold_local = f"{font_name}-Bold" if font_name == "Helvetica" else font_name
        cloture_style = ParagraphStyle(name='PinnedCloture', fontName=font_bold_local, fontSize=10, textColor=p_color, alignment=TA_LEFT)
        # On utilise le Flowable épinglé au lieu d'un paragraphe simple (v4.9)
        elements.append(PinnedCloture(cloture, cloture_style))
        
        highlighted_teeth = []
        for p in data.payments:
            if hasattr(p, 'dents') and p.dents:
                highlighted_teeth.extend([int(d) for d in p.dents])
            elif hasattr(p, 'dent') and p.dent and str(p.dent).isdigit():
                highlighted_teeth.append(int(p.dent))
                
        user_obj = None
        if db and user_id:
            from backend.models import User
            user_obj = db.query(User).filter(User.id == user_id).first()
        return self._build_pdf(filepath, elements, cloture, config=config, user=user_obj, highlighted_teeth=list(set(highlighted_teeth)), doc_id=facture_number)

    def generate_devis(self, patient, data, document_number=None, db=None, user_id=None, **kwargs):
        filepath = self._get_save_path(patient, "DEVIS", data, doc_id=document_number)
        config = None
        if db and user_id:
            from backend.models import CabinetConfig
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        
        font_main = "Helvetica"
        font_bold = "Helvetica-Bold"

        title_style = ParagraphStyle(name='TitleA5', parent=self.styles['Normal'], fontName=font_bold, fontSize=17, textColor=p_color, alignment=TA_CENTER, spaceAfter=12)
        elements = [Spacer(1, 0.4*cm), Paragraph(f"<u><b>DEVIS N° {document_number}</b></u>" if document_number else "<u><b>DEVIS DENTAIRE</b></u>", title_style), Spacer(1, 1.0*cm), self._create_header(patient, data, p_color), Spacer(1, 1.2*cm)]
        
        header_style = ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName=font_bold, fontSize=10, textColor=colors.white, alignment=TA_CENTER)
        table_data = [[Paragraph("ACTE", header_style), Paragraph("DENT", header_style), Paragraph("PRIX (MAD)", header_style)]]
        text_style = ParagraphStyle(name='TableText', parent=self.styles['Normal'], fontName=font_main, fontSize=10, textColor=p_color, alignment=TA_CENTER, leading=14)
        acte_style = ParagraphStyle(name='ActeText', parent=self.styles['Normal'], fontName=font_main, fontSize=10, textColor=p_color, alignment=TA_LEFT, leading=14)

        total = 0.0
        for item in data.items:
            dyn_style = self._get_dynamic_acte_style(acte_style, item.acte, max_chars_at_10pt=36)
            acte_para = Paragraph(item.acte, dyn_style)
            dent_display = getattr(item, 'dent', '-')
            if hasattr(item, 'dents') and item.dents and len(item.dents) > 0:
                dent_display = ', '.join([str(d) for d in item.dents])
            table_data.append([acte_para, Paragraph(str(dent_display), text_style), Paragraph(f"{item.prix_unitaire:.2f}", text_style)])
            total += item.prix_unitaire

        total_words_style = ParagraphStyle(name='TotalWords', parent=self.styles['Normal'], fontName=font_bold, fontSize=11, textColor=p_color, alignment=TA_RIGHT)
        total_amount_style = ParagraphStyle(name='TotalAmount', parent=self.styles['Normal'], fontName=font_bold, fontSize=12, textColor=p_color, alignment=TA_CENTER)
        
        table_data.append([Paragraph("<b>TOTAL GÉNÉRAL</b>", total_words_style), "", Paragraph(f"<b>{total:.2f} MAD</b>", total_amount_style)])
        
        t = Table(table_data, colWidths=[6.8*cm, 3.0*cm, 3.0*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), p_color), 
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-2), 0.3, p_color), 
            ('SPAN', (0, -1), (1, -1)),
            ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
            ('TEXTCOLOR', (0,1), (-1,-1), p_color), 
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 12),
            ('TOPPADDING', (0,-1), (-1,-1), 12),
            ('WORDWRAP', (0,0), (-1,-1), True)
        ]))
        elements.append(t)
        
        inst_table = self._create_installments_table(getattr(data, 'installments', []), total, p_color)
        if inst_table:
            elements.append(Spacer(1, 1.2*cm))
            elements.append(Paragraph("ÉCHÉANCIER PRÉVISIONNEL", ParagraphStyle('InstTitle', fontName=font_bold, fontSize=10, textColor=p_color, spaceAfter=8)))
            elements.append(inst_table)

        total_words = self._amount_to_words(total)
        template = config.cloture_devis_template if config and hasattr(config, 'cloture_devis_template') else None
        if not template:
            template = "Arrêté le présent devis à la somme de {total_words} TTC."
            
        cloture = template.format(total_words=total_words, total_amount=f"{total:.2f}")

        # Ajout direct dans les éléments pour visibilité immédiate (v5.3)
        cloture_style_normal = ParagraphStyle(name='ClotureNormal', fontName=font_bold, fontSize=11, textColor=p_color, spaceBefore=15, leading=14)
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(cloture, cloture_style_normal))
        
        font_name = self.base_template.arabic_font
        font_bold_local = f"{font_name}-Bold" if font_name == "Helvetica" else font_name
        cloture_style = ParagraphStyle(name='PinnedCloture', fontName=font_bold_local, fontSize=10, textColor=p_color, alignment=TA_LEFT)
        # On utilise le Flowable épinglé au lieu d'un paragraphe simple (v4.9)
        elements.append(PinnedCloture(cloture, cloture_style))
        
        highlighted_teeth = []
        for item in data.items:
            if hasattr(item, 'dents') and item.dents:
                highlighted_teeth.extend([int(d) for d in item.dents])
            elif hasattr(item, 'dent') and item.dent and str(item.dent).isdigit():
                highlighted_teeth.append(int(item.dent))

        user_obj = None
        if db and user_id:
            from backend.models import User
            user_obj = db.query(User).filter(User.id == user_id).first()
        return self._build_pdf(filepath, elements, cloture, config=config, user=user_obj, highlighted_teeth=list(set(highlighted_teeth)), doc_id=document_number)

    def _build_pdf(self, filepath, elements, cloture_text, config=None, user=None, highlighted_teeth=None, doc_id=None):
        # Utilisation des marges configurées avec un seuil minimal de sécurité (v5.0)
        m_top = (max(config.margin_top, 4.8) if config and config.margin_top is not None else 4.8) * cm
        m_bottom = (config.margin_bottom if config and config.margin_bottom is not None else 3.2) * cm
        doc = SimpleDocTemplate(filepath, pagesize=A5, rightMargin=1.0*cm, leftMargin=1.0*cm, topMargin=m_top, bottomMargin=m_bottom)
        doc.doc_id = doc_id
        doc.qr_type = 'PAYMENT'
        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user, highlighted_teeth=highlighted_teeth)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
        return filepath.replace("\\", "/")