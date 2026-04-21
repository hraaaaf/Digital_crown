import os
from datetime import datetime, date
import decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Import centralisé du Design System
from backend.services.base_template import BaseTemplate, NAVY_BLUE

class AccountingGenerator:
    def __init__(self, base_output_dir="static/documents"):
        self.base_output_dir = base_output_dir
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        """Styles Premium unifiés via NAVY_BLUE."""
        # Police dynamique
        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

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
            fontName=font_name,
            fontSize=9,
            textColor=NAVY_BLUE,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='ActeText',
            parent=self.styles['Normal'],
            fontName=font_name,
            fontSize=9,
            textColor=NAVY_BLUE,
            alignment=TA_LEFT,
            leading=11
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

        # Séparation Dirhams / Centimes
        # Séparation Dirhams / Centimes (Utilisation de string pour la robustesse)
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

    def _draw_canvas(self, canvas, doc, config=None, user=None):
        """Rendu de la note comptable avec identifiants et clôture épinglée."""
        self.base_template.draw_static_elements(canvas, doc, config=config, draw_legal_ids=True, user=user)
        
        # Clôture épinglée en bas
        if hasattr(doc, 'cloture_text') and doc.cloture_text:
            p_width, p_height = doc.pagesize
            p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
            font_name = self.base_template.arabic_font
            font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name
            
            style = ParagraphStyle(name='PinnedCloture', fontName=font_bold, fontSize=10, textColor=p_color, alignment=TA_LEFT)
            p = Paragraph(doc.cloture_text, style)
            w, h = p.wrap(p_width - 3*cm, 2*cm)
            p.drawOn(canvas, 1.5*cm, 3.2*cm)

    def _create_header(self, patient, data, p_color):
        doc_date = getattr(data, 'doc_date', date.today())
        current_date = doc_date.strftime('%d/%m/%Y')
        age = self._calculate_age(patient.date_naissance)
        
        # Police dynamique
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
                Paragraph(f"Nom : {patient.nom.upper()} {patient.prenom.capitalize()}<br/>Âge : {age} ans", patient_style), 
                Paragraph(f"Le : {current_date}", style_right)
            ]
        ]
        return Table(header_content, colWidths=[7.0*cm, 4.8*cm])

    def generate_note(self, patient, data, facture_number=None, db=None, user_id=None, **kwargs):
        filepath = self._get_save_path(patient, "NOTE", data, doc_id=facture_number)
        config = None
        if db and user_id:
            from backend.models import CabinetConfig
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        
        # Police dynamique
        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

        title_style = ParagraphStyle(name='TitleA5', parent=self.styles['Normal'], fontName=font_bold, fontSize=17, textColor=p_color, alignment=TA_CENTER, spaceAfter=12)
        elements = [Spacer(1, 0.4*cm), Paragraph(f"NOTE D'HONORAIRES N° {facture_number}" if facture_number else "NOTE D'HONORAIRES", title_style), Spacer(1, 1.0*cm), self._create_header(patient, data, p_color), Spacer(1, 1.5*cm)]
        
        header_style = ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName=font_bold, fontSize=9, textColor=colors.white, alignment=TA_CENTER)
        table_data = [[Paragraph("ACTE", header_style), Paragraph("DENT", header_style), Paragraph("MODE DE PAIEMENT", header_style), Paragraph("HONORAIRES (MAD)", header_style)]]
        text_style = ParagraphStyle(name='TableText', parent=self.styles['Normal'], fontName=font_name, fontSize=10, textColor=p_color, alignment=TA_CENTER)
        acte_style = ParagraphStyle(name='ActeText', parent=self.styles['Normal'], fontName=font_name, fontSize=10, textColor=p_color, alignment=TA_LEFT, leading=13)

        total = 0.0
        for p in data.payments:
            acte_para = Paragraph(p.acte, acte_style)
            dent_display = getattr(p, 'dent', '-')
            if hasattr(p, 'dents') and p.dents and len(p.dents) > 0:
                dent_display = ', '.join([str(d) for d in p.dents])
            table_data.append([acte_para, Paragraph(str(dent_display), text_style), Paragraph(getattr(p, 'mode_reglement', 'Espèces'), text_style), Paragraph(f"{p.montant:.2f}", text_style)])
            total += p.montant

        total_words_style = ParagraphStyle(name='TotalWords', parent=self.styles['Normal'], fontName=font_bold, fontSize=10, textColor=p_color, alignment=TA_CENTER)
        table_data.append(["", "", Paragraph("<b>TOTAL</b>", total_words_style), Paragraph(f"<b>{total:.2f}</b>", total_words_style)])
        
        t = Table(table_data, colWidths=[5.8*cm, 1.2*cm, 2.4*cm, 2.4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), p_color), 
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
            ('VALIGN', (0,0), (-1,-1), 'TOP'), 
            ('GRID', (0,0), (-1,-2), 0.3, p_color), 
            ('TEXTCOLOR', (0,1), (-1,-1), p_color), 
            ('WORDWRAP', (0,0), (-1,-1), True)
        ]))
        elements.append(t)
        
        total_words = self._amount_to_words(total)
        
        # Utilisation de la clôture personnalisée (Database-Driven)
        template = config.cloture_note_template if config and hasattr(config, 'cloture_note_template') else None
        if not template:
            template = "Arrêtée la présente note à la somme de {total_words} TTC."
            
        cloture = template.format(total_words=total_words, total_amount=f"{total:.2f}")
        user_obj = None
        if db and user_id:
            from backend.models import User
            user_obj = db.query(User).filter(User.id == user_id).first()
        return self._build_pdf(filepath, elements, cloture, config=config, user=user_obj)

    def generate_devis(self, patient, data, document_number=None, db=None, user_id=None, **kwargs):
        filepath = self._get_save_path(patient, "DEVIS", data, doc_id=document_number)
        config = None
        if db and user_id:
            from backend.models import CabinetConfig
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == user_id).first()
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        
        # Police dynamique
        font_name = self.base_template.arabic_font
        font_bold = f"{font_name}-Bold" if font_name == "Helvetica" else font_name

        title_style = ParagraphStyle(name='TitleA5', parent=self.styles['Normal'], fontName=font_bold, fontSize=17, textColor=p_color, alignment=TA_CENTER, spaceAfter=12)
        elements = [Spacer(1, 0.4*cm), Paragraph(f"DEVIS N° {document_number}" if document_number else "DEVIS DENTAIRE", title_style), Spacer(1, 1.0*cm), self._create_header(patient, data, p_color), Spacer(1, 1.5*cm)]
        
        header_style = ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName=font_bold, fontSize=9, textColor=colors.white, alignment=TA_CENTER)
        table_data = [[Paragraph("ACTE", header_style), Paragraph("DENT", header_style), Paragraph("PRIX UNITAIRE (MAD)", header_style)]]
        text_style = ParagraphStyle(name='TableText', parent=self.styles['Normal'], fontName=font_name, fontSize=10, textColor=p_color, alignment=TA_CENTER)
        acte_style = ParagraphStyle(name='ActeText', parent=self.styles['Normal'], fontName=font_name, fontSize=10, textColor=p_color, alignment=TA_LEFT, leading=13)

        total = 0.0
        for item in data.items:
            acte_para = Paragraph(item.acte, acte_style)
            dent_display = getattr(item, 'dent', '-')
            if hasattr(item, 'dents') and item.dents and len(item.dents) > 0:
                dent_display = ', '.join([str(d) for d in item.dents])
            table_data.append([acte_para, Paragraph(str(dent_display), text_style), Paragraph(f"{item.prix_unitaire:.2f}", text_style)])
            total += item.prix_unitaire

        total_words_style = ParagraphStyle(name='TotalWords', parent=self.styles['Normal'], fontName=font_bold, fontSize=10, textColor=p_color, alignment=TA_CENTER)
        table_data.append(["", Paragraph("<b>TOTAL</b>", total_words_style), Paragraph(f"<b>{total:.2f}</b>", total_words_style)])
        
        t = Table(table_data, colWidths=[7.8*cm, 1.5*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), p_color), 
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
            ('VALIGN', (0,0), (-1,-1), 'TOP'), 
            ('GRID', (0,0), (-1,-2), 0.3, p_color), 
            ('TEXTCOLOR', (0,1), (-1,-1), p_color), 
            ('WORDWRAP', (0,0), (-1,-1), True)
        ]))
        elements.append(t)
        
        total_words = self._amount_to_words(total)
        
        # Utilisation de la clôture personnalisée (Database-Driven) 
        template = config.cloture_devis_template if config and hasattr(config, 'cloture_devis_template') else None
        if not template:
            template = "Arrêté le présent devis à la somme de {total_words} TTC."
            
        cloture = template.format(total_words=total_words, total_amount=f"{total:.2f}")
        user_obj = None
        if db and user_id:
            from backend.models import User
            user_obj = db.query(User).filter(User.id == user_id).first()
        return self._build_pdf(filepath, elements, cloture, config=config, user=user_obj)

    def _build_pdf(self, filepath, elements, cloture_text, config=None, user=None):
        m_top = (config.margin_top if config else 3.6) * cm
        m_bottom = (config.margin_bottom if config else 3.2) * cm
        doc = SimpleDocTemplate(filepath, pagesize=A5, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=m_top, bottomMargin=m_bottom)
        doc.cloture_text = cloture_text
        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
        return filepath[filepath.find("static"):].replace("\\", "/")