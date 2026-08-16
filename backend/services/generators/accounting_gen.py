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
from backend.services.base_template import BaseTemplate, NAVY_BLUE, PageCounter
from backend.services.generators.document_layout_safety import join_unbreakable
from backend.services.generators.accounting_pdf_readability import readable_accounting_font_floor

class AccountingGenerator:
    def __init__(self, base_output_dir="static/documents"):
        self.base_output_dir = base_output_dir
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        """Styles Premium unifiés avec contraste maximal Gras/Normal."""
        font_main = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

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

    def _draw_canvas(self, canvas, doc, config=None, user=None, highlighted_teeth=None, cloture_text=None, p_color=None):
        """Rendu canvas : header/footer statiques + clôture en coordonnées absolues de page."""
        self.base_template.draw_static_elements(canvas, doc, config=config, draw_legal_ids=True, user=user)
        if cloture_text:
            self._draw_cloture_absolute(canvas, doc, cloture_text, p_color or NAVY_BLUE)

    def _draw_cloture_absolute(self, canvas, doc, text, p_color):
        """Dessine la clôture en coordonnées absolues de page (comme le footer)."""
        import re
        clean = re.sub(r'<[^>]+>', '', text).strip()
        if not clean:
            return

        p_width, _ = doc.pagesize
        left_x   = 1.5 * cm
        # L'espace à droite est désormais libéré grâce au nouveau placement du QR Code
        usable_w = p_width - 3.0 * cm
        font_name = self.base_template.premium_bold
        font_size = 8.5

        canvas.saveState()
        canvas.setFont(font_name, font_size)
        canvas.setFillColor(p_color)

        # Word-wrap manuel
        avg_char_w = font_size * 0.55
        max_chars  = max(1, int(usable_w / avg_char_w))
        lines, remaining = [], clean
        while len(remaining) > max_chars:
            cut = remaining[:max_chars].rfind(' ')
            if cut <= 0:
                cut = max_chars
            lines.append(remaining[:cut])
            remaining = remaining[cut:].strip()
        lines.append(remaining)

        # Positionné au-dessus du trait de footer (2.5cm) et en-dessous du contenu (marge de 5cm)
        y_start = 3.2 * cm
        line_h  = font_size * 0.04 * cm + 0.4 * cm
        for i, line in enumerate(lines):
            canvas.drawString(left_x, y_start - i * line_h, line)
        canvas.restoreState()

    def _create_header(self, patient, data, p_color):
        doc_date = getattr(data, 'doc_date', None) or date.today()
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
        
        patient_text = f"<b>{patient.nom.upper()} {patient.prenom.capitalize()}, {join_unbreakable(age, 'ans')}</b>"
        patient_w = 7.0 * cm
        adaptive_patient_style = self.base_template.get_adaptive_style(patient_style, patient_text, patient_w - 0.2*cm)
        
        header_content = [
            [
                Paragraph(patient_text, adaptive_patient_style), 
                Paragraph(f"Le : <u>{current_date}</u>", style_right)
            ]
        ]
        return Table(header_content, colWidths=[7.0*cm, 4.8*cm])

    # _get_dynamic_acte_style is now replaced by self.base_template.get_adaptive_style

    def _create_installments_table(self, installments, total_honoraires, p_color):
        """Crée un tableau de suivi des règlements (échéancier)."""
        if not installments:
            return None
            
        font_bold = self.base_template.premium_bold
        font_main = self.base_template.premium_font
        
        header_style = ParagraphStyle(name='InstHeader', fontName=font_bold, fontSize=9, textColor=colors.white, alignment=TA_CENTER)
        text_style = ParagraphStyle(name='InstText', fontName=font_main, fontSize=9, textColor=p_color, alignment=TA_CENTER)
        
        table_data = [[Paragraph("ÉCHÉANCE / AVANCE", header_style), Paragraph("DATE", header_style), Paragraph("MONTANT (MAD)", header_style)]]
        
        total_verse = 0.0
        for inst in installments:
            d_str = inst.date.strftime('%d/%m/%Y') if hasattr(inst.date, 'strftime') else str(inst.date)
            table_data.append([
                Paragraph(inst.label.replace(' ', ' '), text_style),
                Paragraph(d_str.replace(' ', ' '), text_style),
                Paragraph(f"{inst.amount:.2f}", text_style)
            ])
            total_verse += inst.amount
            
        reste = total_honoraires - total_verse
        
        summary_style = ParagraphStyle(name='InstSummary', fontName=font_bold, fontSize=10, textColor=p_color, alignment=TA_RIGHT)
        reste_style = ParagraphStyle(name='ResteStyle', fontName=font_bold, fontSize=10, textColor=colors.HexColor("#B45309"), alignment=TA_CENTER) # Amber-700

        amt_col_w = 3.2*cm - 2*3  # moins LEFTPADDING/RIGHTPADDING (3pt chacun)
        verse_text = f"<b>{total_verse:.2f}\u00A0MAD</b>"
        reste_text = f"<b>{reste:.2f}\u00A0MAD</b>"
        verse_amount_style = self.base_template.get_adaptive_style(text_style, verse_text, amt_col_w, min_fs=6.5)
        reste_amount_style = self.base_template.get_adaptive_style(reste_style, reste_text, amt_col_w, min_fs=6.5)

        table_data.append([Paragraph("TOTAL VERSÉ", summary_style), "", Paragraph(verse_text, verse_amount_style)])
        table_data.append([Paragraph("RESTE À PAYER", summary_style), "", Paragraph(reste_text, reste_amount_style)])
        
        t = Table(table_data, colWidths=[5.3*cm, 3.3*cm, 3.2*cm])  # 11.8cm total
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
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ]))
        return t

    def generate_note(self, patient, data, facture_number=None, db=None, user_id=None, **kwargs):
        filepath = self._get_save_path(patient, "NOTE", data, doc_id=facture_number)
        config = None
        if db and user_id:
            from backend.models import CabinetConfig
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
        self.base_template.update_active_fonts(config)
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        
        font_main = self.base_template.premium_font
        font_bold = self.base_template.premium_bold
        
        is_global = getattr(data, 'is_global_note', False)
        title_text = "NOTE D'HONORAIRES GLOBALE" if is_global else "NOTE D'HONORAIRES"
        if facture_number:
            title_text += f" N° {facture_number}"

        # Détermination du facteur de compression si trop d'actes (Single Page Force)
        num_acts = len(data.payments)
        compression_factor = 1.0
        if num_acts > 10:
            compression_factor = 0.75
        elif num_acts > 6:
            compression_factor = 0.85
            
        title_style = ParagraphStyle(name='TitleA5', parent=self.styles['Normal'], fontName=font_bold, fontSize=17 * compression_factor, textColor=p_color, alignment=TA_CENTER, spaceAfter=12 * compression_factor)
        elements = [Spacer(1, 0.4*cm), Paragraph(f"<u><b>{title_text}</b></u>", title_style), Spacer(1, 0.8*cm if num_acts > 8 else 1.0*cm), self._create_header(patient, data, p_color), Spacer(1, 1.0*cm if num_acts > 8 else 1.2*cm)]
        
        header_style = ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName=font_bold, fontSize=10 * compression_factor, textColor=colors.white, alignment=TA_CENTER)
        table_data = [[Paragraph("ACTE", header_style), Paragraph("DENT", header_style), Paragraph("PAIEMENT", header_style), Paragraph("HONORAIRES", header_style)]]
        
        base_fs = 10 * compression_factor
        text_style = ParagraphStyle(name='TableText', parent=self.styles['Normal'], fontName=font_main, fontSize=base_fs, textColor=p_color, alignment=TA_CENTER, leading=base_fs * 1.4)
        acte_style = ParagraphStyle(name='ActeText', parent=self.styles['Normal'], fontName=font_main, fontSize=base_fs, textColor=p_color, alignment=TA_LEFT, leading=base_fs * 1.4)

        total = 0.0
        acte_w, dent_w, pay_w, hon_w = 4.5*cm, 1.8*cm, 2.75*cm, 2.75*cm  # total = 11.8cm (A5)
        min_fs = base_fs
        for p in data.payments:
            _dent_pre = getattr(p, 'dent', '-')
            if hasattr(p, 'dents') and p.dents and len(p.dents) > 0:
                _dent_pre = ', '.join([str(d) for d in p.dents])
            for _ct, _cw in [
                (p.acte.replace(' ', ' '), acte_w - 0.22*cm),
                (str(_dent_pre).replace(' ', ' '), dent_w - 0.22*cm),
                (getattr(p, 'mode_reglement', 'Espèces').replace(' ', ' '), pay_w - 0.22*cm),
                (f"{p.montant:.2f}", hon_w - 0.22*cm),
            ]:
                _dyn = self.base_template.get_adaptive_style(text_style, _ct, _cw, min_fs=2.0)
                if _dyn.fontSize < min_fs:
                    min_fs = _dyn.fontSize

        uniform_style = ParagraphStyle(name='UniformAll', parent=text_style, fontSize=min_fs, leading=min_fs * 1.4)
        uniform_acte_style = ParagraphStyle(name='UniformActe', parent=acte_style, fontSize=min_fs, leading=min_fs * 1.4)

        for p in data.payments:
            acte_nbsp = p.acte.replace(' ', ' ')
            acte_para = Paragraph(acte_nbsp, uniform_acte_style)
            dent_display = getattr(p, 'dent', '-')
            if hasattr(p, 'dents') and p.dents and len(p.dents) > 0:
                dent_display = ', '.join([str(d) for d in p.dents])
            dent_nbsp = str(dent_display).replace(' ', ' ')
            mode_nbsp = getattr(p, 'mode_reglement', 'Espèces').replace(' ', ' ')
            table_data.append([acte_para, Paragraph(dent_nbsp, uniform_style), Paragraph(mode_nbsp, uniform_style), Paragraph(f"{p.montant:.2f}", uniform_style)])
            total += p.montant

        total_words_style = ParagraphStyle(name='TotalWords', parent=self.styles['Normal'], fontName=font_bold, fontSize=11, textColor=p_color, alignment=TA_RIGHT)
        total_amount_style = ParagraphStyle(name='TotalAmount', parent=self.styles['Normal'], fontName=font_bold, fontSize=10.5, textColor=p_color, alignment=TA_CENTER)
        total_amount_text = f"<b>{total:.2f}\u00A0MAD</b>"
        total_amount_style = self.base_template.get_adaptive_style(total_amount_style, total_amount_text, hon_w - 0.22*cm, min_fs=6.5)

        table_data.append([Paragraph("<b>TOTAL GÉNÉRAL</b>", total_words_style), "", "", Paragraph(total_amount_text, total_amount_style)])
        
        t = Table(table_data, colWidths=[4.5*cm, 1.8*cm, 2.75*cm, 2.75*cm])  # 11.8cm total
        # Ajustement du padding pour gagner de l'espace si num_acts est élevé
        v_pad = 8 if num_acts <= 5 else (4 if num_acts <= 8 else 2)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), p_color), 
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-2), 0.3, p_color), 
            ('SPAN', (0, -1), (2, -1)),
            ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
            ('TEXTCOLOR', (0,1), (-1,-1), p_color), 
            ('BOTTOMPADDING', (0,0), (-1,-1), v_pad),
            ('TOPPADDING', (0,0), (-1,-1), v_pad),
            ('BOTTOMPADDING', (0,-1), (-1,-1), v_pad + 4),
            ('TOPPADDING', (0,-1), (-1,-1), v_pad + 4),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(t)
        
        inst_table = self._create_installments_table(getattr(data, 'installments', []), total, p_color)
        if inst_table:
            elements.append(Spacer(1, 1.2*cm))
            elements.append(Paragraph("SUIVI DES RÈGLEMENTS", ParagraphStyle('InstTitle', fontName=font_bold, fontSize=10, textColor=p_color, spaceAfter=8)))
            elements.append(inst_table)

        total_words = self._amount_to_words(total)
        total_words_elite = f"<b>{total_words.upper()}</b>"
        
        template = config.cloture_note_template if config and hasattr(config, 'cloture_note_template') else None
        if not template:
            template = "Arrêtée la présente note d'honoraires à la somme de : {total_words} TTC."
            
        # Nettoyage des caractères de contrôle ou erreurs d'encodage (v5.9)
        template = template.replace('Arrte', 'Arrêté').replace('prsente', 'présente')
        
        # Forcer la suppression du montant en chiffres même si le template vient de la base de données
        import re
        template = re.sub(r',?\s*soit\s+\{total_amount\}.*?(?=\.)', ' TTC', template)
        template = template.replace('{total_amount}', '')
        
        cloture = template.format(total_words=total_words_elite, total_amount=f"{total:,.2f}".replace(',', ' '))
        
        # Cloture Flowable
        cloture_style = ParagraphStyle(
            name='Cloture', parent=self.styles['Normal'],
            fontName=self.base_template.premium_font, fontSize=9.5,
            textColor=p_color, alignment=TA_CENTER, leading=14
        )
        
        cloture_nbsp = cloture.replace(' ', '\u00A0')
        adaptive_cloture = self.base_template.get_adaptive_style(cloture_style, cloture_nbsp, 11.5*cm, min_fs=6.0)
        
        from backend.services.base_template import PinnedCloture
        elements.append(PinnedCloture(cloture_nbsp, adaptive_cloture))
        
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
        return self._build_pdf(filepath, elements, "", config=config, user=user_obj, highlighted_teeth=list(set(highlighted_teeth)), doc_id=facture_number, p_color=p_color)

    def generate_devis(self, patient, data, document_number=None, db=None, user_id=None, **kwargs):
        filepath = self._get_save_path(patient, "DEVIS", data, doc_id=document_number)
        config = None
        if db and user_id:
            from backend.models import CabinetConfig
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
        self.base_template.update_active_fonts(config)
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        
        font_main = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

        # Compression limitée aux espacements/titres. Les lignes Devis doivent
        # rester lisibles et sont autorisées à s'étendre sur plusieurs pages.
        num_items = len(data.items)
        compression_factor = 1.0
        if num_items > 10:
            compression_factor = 0.75
        elif num_items > 6:
            compression_factor = 0.85
            
        title_style = ParagraphStyle(name='TitleA5', parent=self.styles['Normal'], fontName=font_bold, fontSize=17 * compression_factor, textColor=p_color, alignment=TA_CENTER, spaceAfter=12 * compression_factor)
        elements = [Spacer(1, 0.4*cm), Paragraph(f"<u><b>DEVIS N° {document_number}</b></u>" if document_number else "<u><b>DEVIS DENTAIRE</b></u>", title_style), Spacer(1, 0.8*cm if num_items > 8 else 1.0*cm), self._create_header(patient, data, p_color), Spacer(1, 1.0*cm if num_items > 8 else 1.2*cm)]
        
        header_style = ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName=font_bold, fontSize=10 * compression_factor, textColor=colors.white, alignment=TA_CENTER)
        table_data = [[Paragraph("ACTE", header_style), Paragraph("DENT", header_style), Paragraph("PRIX (MAD)", header_style)]]
        
        readable_floor = readable_accounting_font_floor()
        base_fs = max(10 * compression_factor, readable_floor)
        text_style = ParagraphStyle(name='TableText', parent=self.styles['Normal'], fontName=font_main, fontSize=base_fs, textColor=p_color, alignment=TA_CENTER, leading=base_fs * 1.4)
        acte_style = ParagraphStyle(name='ActeText', parent=self.styles['Normal'], fontName=font_main, fontSize=base_fs, textColor=p_color, alignment=TA_LEFT, leading=base_fs * 1.4)

        total = 0.0
        acte_w, dent_w, prix_w = 6.5*cm, 2.65*cm, 2.65*cm  # total = 11.8cm (A5)
        for item in data.items:
            # Garder les espaces ordinaires : ReportLab peut ainsi wrapper une
            # description longue au lieu de réduire toute la table à 2 pt.
            acte_para = Paragraph(item.acte, acte_style)
            dent_display = getattr(item, 'dent', '-')
            if hasattr(item, 'dents') and item.dents and len(item.dents) > 0:
                dent_display = ', '.join([str(d) for d in item.dents])
            dent_text = str(dent_display)
            dent_style = self.base_template.get_adaptive_style(
                text_style, dent_text, dent_w - 0.22*cm, min_fs=readable_floor
            )
            price_text = f"{item.prix_unitaire:.2f}"
            price_style = self.base_template.get_adaptive_style(
                text_style, price_text, prix_w - 0.22*cm, min_fs=readable_floor
            )
            table_data.append([
                acte_para,
                Paragraph(dent_text, dent_style),
                Paragraph(price_text, price_style),
            ])
            total += item.prix_unitaire

        total_words_style = ParagraphStyle(name='TotalWords', parent=self.styles['Normal'], fontName=font_bold, fontSize=11, textColor=p_color, alignment=TA_RIGHT)
        total_amount_style = ParagraphStyle(name='TotalAmount', parent=self.styles['Normal'], fontName=font_bold, fontSize=10.5, textColor=p_color, alignment=TA_CENTER)
        total_amount_text = f"<b>{total:.2f}\u00A0MAD</b>"
        total_amount_style = self.base_template.get_adaptive_style(
            total_amount_style, total_amount_text, prix_w - 0.22*cm, min_fs=readable_floor
        )

        table_data.append([Paragraph("<b>TOTAL GÉNÉRAL</b>", total_words_style), "", Paragraph(total_amount_text, total_amount_style)])
        
        t = Table(table_data, colWidths=[6.5*cm, 2.65*cm, 2.65*cm], repeatRows=1)  # 11.8cm total
        # Ajustement du padding pour gagner de l'espace si num_items est élevé
        v_pad = 8 if num_items <= 5 else (4 if num_items <= 8 else 2)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), p_color), 
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-2), 0.3, p_color), 
            ('SPAN', (0, -1), (1, -1)),
            ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
            ('TEXTCOLOR', (0,1), (-1,-1), p_color), 
            ('BOTTOMPADDING', (0,0), (-1,-1), v_pad),
            ('TOPPADDING', (0,0), (-1,-1), v_pad),
            ('BOTTOMPADDING', (0,-1), (-1,-1), v_pad + 4),
            ('TOPPADDING', (0,-1), (-1,-1), v_pad + 4),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(t)
        
        inst_table = self._create_installments_table(getattr(data, 'installments', []), total, p_color)
        if inst_table:
            elements.append(Spacer(1, 1.2*cm))
            elements.append(Paragraph("ÉCHÉANCIER PRÉVISIONNEL", ParagraphStyle('InstTitle', fontName=font_bold, fontSize=10, textColor=p_color, spaceAfter=8)))
            elements.append(inst_table)

        total_words = self._amount_to_words(total)
        total_words_elite = f"<b>{total_words.upper()}</b>"
        
        template = config.cloture_devis_template if config and hasattr(config, 'cloture_devis_template') else None
        if not template:
            template = "Arrêté le présent devis à la somme de : {total_words} TTC."
            
        # Nettoyage encoding (v5.9)
        template = template.replace('Arrte', 'Arrêté').replace('prsente', 'présente')
        
        # Forcer la suppression du montant en chiffres même si le template vient de la base de données
        import re
        template = re.sub(r',?\s*soit\s+\{total_amount\}.*?(?=\.)', ' TTC', template)
        template = template.replace('{total_amount}', '')
        
        cloture = template.format(total_words=total_words_elite, total_amount=f"{total:,.2f}".replace(',', ' '))
        
        # La clôture conserve sa taille normale et peut wrapper. Elle ne doit pas
        # être rendue insécable puis rapetissée pour simuler une seule ligne.
        cloture_style = ParagraphStyle(
            name='Cloture', parent=self.styles['Normal'],
            fontName=self.base_template.premium_font, fontSize=9.5,
            textColor=p_color, alignment=TA_CENTER, leading=14
        )
        
        from backend.services.base_template import PinnedCloture
        elements.append(PinnedCloture(cloture, cloture_style))

        # Bloc de signature électronique
        sig_image_path = kwargs.get("signature_path")
        if not sig_image_path and hasattr(data, "clinical_data") and data.clinical_data:
            sig_image_path = data.clinical_data.get("signature_path")
        elif not sig_image_path and hasattr(data, "signature_path") and data.signature_path:
            sig_image_path = data.signature_path

        sig_label_style = ParagraphStyle(
            name='SigLabel', parent=self.styles['Normal'],
            fontName=font_bold, fontSize=8, textColor=p_color, alignment=TA_LEFT
        )
        sig_label_right = ParagraphStyle(
            name='SigLabelRight', parent=self.styles['Normal'],
            fontName=font_bold, fontSize=8, textColor=p_color, alignment=TA_RIGHT
        )

        patient_sig_flowable = Paragraph("", sig_label_style)
        if sig_image_path:
            resolved_path = sig_image_path
            if not os.path.isabs(resolved_path):
                resolved_path = os.path.abspath(resolved_path)
                if not os.path.exists(resolved_path):
                    # Try from parent path of project
                    resolved_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", sig_image_path))
            
            if os.path.exists(resolved_path):
                from reportlab.platypus import Image
                patient_sig_flowable = Image(resolved_path, width=3.5*cm, height=1.5*cm)

        sig_data = [
            [Paragraph("<b>Signature et Cachet :</b>", sig_label_style), Paragraph("<b>Signature du Patient (lu et approuvé) :</b>", sig_label_right)]
        ]
        sig_data.append([Paragraph("", sig_label_style), patient_sig_flowable])

        sig_table = Table(sig_data, colWidths=[6.0*cm, 6.8*cm])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(Spacer(1, 0.4*cm))
        elements.append(sig_table)

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
        return self._build_pdf(filepath, elements, "", config=config, user=user_obj, highlighted_teeth=list(set(highlighted_teeth)), doc_id=document_number, p_color=p_color)

    def _build_pdf(self, filepath, elements, cloture_text, config=None, user=None, highlighted_teeth=None, doc_id=None, p_color=None):
        # Utilisation des marges configurées.
        m_top_val = config.margin_top if config and config.margin_top is not None else 4.8
        m_bottom_val = config.margin_bottom if config and config.margin_bottom is not None else 1.8
        
        lh_path_str = getattr(config, 'letterhead_path', None) if config else None
        
        has_letterhead = False
        if lh_path_str and str(lh_path_str) not in ["null", "None", ""]:
            import os
            import sys
            base_p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            lh_full_path = os.path.join(base_p, "static", "uploads", str(lh_path_str))
            if os.path.exists(lh_full_path):
                has_letterhead = True
        
        if has_letterhead:
            m_top = m_top_val * cm
        else:
            m_top = max(m_top_val, 4.8) * cm
            
        m_bottom = m_bottom_val * cm
        
        p_width_val = A5[0] if isinstance(A5, tuple) else (14.8*cm if A5 == 'A5' else 21.0*cm)
        m_top, m_bottom, m_left, m_right = self.base_template.get_document_margins(config, p_width_val)
        draw_method = lambda canv, d: self._draw_canvas(
            canv, d,
            config=config, user=user, highlighted_teeth=highlighted_teeth,
            cloture_text="", p_color=p_color
        )
        compression = 1.0
        for _ in range(7):
            scaled = BaseTemplate.scale_elements(elements, compression)
            doc = SimpleDocTemplate(filepath, pagesize=A5, rightMargin=m_right, leftMargin=m_left, topMargin=m_top, bottomMargin=m_bottom)
            doc.doc_id = doc_id
            doc.qr_type = 'PAYMENT'
            page_counter = PageCounter()
            doc.build(scaled, onFirstPage=draw_method, onLaterPages=draw_method,
                      canvasmaker=page_counter.make_canvas_class())
            if page_counter.page_count <= 1:
                break
            compression *= 0.82
            if compression < 0.35:
                break
        return filepath.replace("\\", "/")