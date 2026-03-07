import os
from datetime import datetime, date
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
        self.styles.add(ParagraphStyle(
            name='TitleA5',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=NAVY_BLUE,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='PatientInfo',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=NAVY_BLUE,
            leading=12
        ))
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='TableText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=NAVY_BLUE,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='ActeText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=NAVY_BLUE,
            alignment=TA_LEFT,
            leading=11
        ))

    def _amount_to_words(self, n):
        """Convertit un montant entier en lettres (Français) pour la clôture légale."""
        units = ["", "Un", "Deux", "Trois", "Quatre", "Cinq", "Six", "Sept", "Huit", "Neuf"]
        tens = ["", "Dix", "Vingt", "Trente", "Quarante", "Cinquante", "Soixante", "Soixante-dix", "Quatre-vingt", "Quatre-vingt-dix"]
        if n == 0: return "Zéro"
        if n == 1000: return "Mille"
        if n < 10: return units[int(n)]
        if 10 <= n < 20:
            return ["Dix", "Onze", "Douze", "Treize", "Quatorze", "Quinze", "Seize", "Dix-sept", "Dix-huit", "Dix-neuf"][int(n-10)]
        if n < 100:
            q, r = divmod(n, 10)
            if q == 7: return "Soixante-dix" if r == 0 else "Soixante-" + self._amount_to_words(10+r).lower()
            if q == 9: return "Quatre-vingt-dix" if r == 0 else "Quatre-vingt-" + self._amount_to_words(10+r).lower()
            return tens[int(q)] + ("-" + self._amount_to_words(r).lower() if r > 0 else "")
        if n < 1000:
            q, r = divmod(n, 100)
            prefix = units[int(q)] + " " if q > 1 else ""
            return prefix + "Cent" + ("s" if r == 0 and q > 1 else "") + (" " + self._amount_to_words(r).lower() if r > 0 else "")
        return str(int(n))

    def _calculate_age(self, born):
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, prefix, data, doc_id=None):
        """Nommage conforme : TYPE_NOM_PRENOM_DD-MM-YYYY.pdf"""
        doc_date = getattr(data, 'doc_date', date.today())
        date_str = doc_date.strftime('%d-%m-%Y')
        save_dir = os.path.join(self.base_output_dir, doc_date.strftime('%Y'), doc_date.strftime('%m'))
        os.makedirs(save_dir, exist_ok=True)
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        return os.path.join(save_dir, f"{prefix}_{safe_name}_{date_str}.pdf")

    def _draw_canvas(self, canvas, doc):
        """Rendu Pixel Perfect avec Identifiants Légaux."""
        self.base_template.draw_static_elements(canvas, doc)
        canvas.saveState()
        canvas.setStrokeColor(NAVY_BLUE)
        canvas.setLineWidth(0.7)
        canvas.line(1.5*cm, 2.5*cm, 13.3*cm, 2.5*cm)

        # Identifiants Légaux
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(NAVY_BLUE)
        legal_ids = "ICE : 001819709000006  |  INP : 104164231  |  IF : 14496345"
        canvas.drawCentredString(14.8*cm / 2, 1.0*cm, legal_ids)
        
        # Clôture dynamique en toutes lettres à 3cm du bas
        if hasattr(doc, 'cloture_text'):
            canvas.setFont('Helvetica-Bold', 9.5)
            canvas.setFillColor(NAVY_BLUE)
            canvas.drawString(1.5*cm, 3.0*cm, doc.cloture_text)
        canvas.restoreState()

    def _create_header(self, patient, data):
        """Header Premium sans Réf."""
        doc_date = getattr(data, 'doc_date', date.today())
        current_date = doc_date.strftime('%d/%m/%Y')
        age = self._calculate_age(patient.date_naissance)
        
        style_right = ParagraphStyle('DocDate', parent=self.styles['Normal'], alignment=TA_RIGHT, textColor=NAVY_BLUE)
        header_content = [[
            Paragraph(f"Nom : {patient.nom.upper()} {patient.prenom.capitalize()}<br/>Âge : {age} ans", self.styles['PatientInfo']),
            Paragraph(f"Le : ....{current_date}....", style_right)
        ]]
        return Table(header_content, colWidths=[7.0*cm, 4.8*cm])

    def generate_note(self, patient, data, facture_number=None, **kwargs):
        filepath = self._get_save_path(patient, "NOTE", data, doc_id=facture_number)
        elements = [
            Spacer(1, 0.5*cm), 
            self._create_header(patient, data), 
            Spacer(1, 1.2*cm), 
            Paragraph("<u><b>NOTE D'HONORAIRES</b></u>", self.styles['TitleA5']), 
            Spacer(1, 0.8*cm)
        ]
        table_data = [[
            Paragraph("ACTE", self.styles['TableHeader']),
            Paragraph("DENT", self.styles['TableHeader']),
            Paragraph("MODE DE PAIEMENT", self.styles['TableHeader']),
            Paragraph("HONORAIRES (MAD)", self.styles['TableHeader'])
        ]]
        total = 0.0
        for p in data.payments:
            acte_para = Paragraph(p.acte, self.styles['ActeText'])
            dent_display = getattr(p, 'dent', '-')
            if hasattr(p, 'dents') and p.dents and len(p.dents) > 0:
                dent_display = ', '.join([str(d) for d in p.dents])
            table_data.append([acte_para, dent_display, getattr(p, 'mode_reglement', 'Espèces'), f"{p.montant:.2f}"])
            total += p.montant

        table_data.append(["", "", Paragraph("<b>TOTAL</b>", self.styles['TableText']), Paragraph(f"<b>{total:.2f}</b>", self.styles['TableText'])])
        
        t = Table(table_data, colWidths=[4.3*cm, 1.5*cm, 3.0*cm, 3.0*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY_BLUE),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-2), 0.3, NAVY_BLUE),
            ('TEXTCOLOR', (0,1), (-1,-1), NAVY_BLUE)
        ]))
        elements.append(t)
        
        total_words = self._amount_to_words(total)
        cloture = f"Arrêtée la présente note à la somme de {total_words} Dirhams TTC."
        return self._build_pdf(filepath, elements, cloture)

    def generate_devis(self, patient, data, document_number=None, **kwargs):
        filepath = self._get_save_path(patient, "DEVIS", data, doc_id=document_number)
        elements = [
            Spacer(1, 0.5*cm), 
            self._create_header(patient, data), 
            Spacer(1, 1.2*cm), 
            Paragraph("<u><b>DEVIS ESTIMATIF</b></u>", self.styles['TitleA5']), 
            Spacer(1, 0.8*cm)
        ]
        table_data = [[
            Paragraph("ACTE", self.styles['TableHeader']),
            Paragraph("DENT", self.styles['TableHeader']),
            Paragraph("PRIX UNITAIRE (MAD)", self.styles['TableHeader'])
        ]]
        total = 0.0
        for item in data.items:
            acte_para = Paragraph(item.acte, self.styles['ActeText'])
            dent_display = getattr(item, 'dent', '-')
            if hasattr(item, 'dents') and item.dents and len(item.dents) > 0:
                dent_display = ', '.join([str(d) for d in item.dents])
            table_data.append([acte_para, dent_display, f"{item.prix_unitaire:.2f}"])
            total += item.prix_unitaire

        table_data.append(["", Paragraph("<b>TOTAL</b>", self.styles['TableText']), Paragraph(f"<b>{total:.2f}</b>", self.styles['TableText'])])
        
        t = Table(table_data, colWidths=[6.8*cm, 2.0*cm, 3.0*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY_BLUE),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-2), 0.3, NAVY_BLUE),
            ('TEXTCOLOR', (0,1), (-1,-1), NAVY_BLUE)
        ]))
        elements.append(t)
        
        total_words = self._amount_to_words(total)
        cloture = f"Arrêté le présent devis à la somme de {total_words} Dirhams TTC."
        return self._build_pdf(filepath, elements, cloture)

    def _build_pdf(self, filepath, elements, cloture_text):
        doc = SimpleDocTemplate(filepath, pagesize=A5, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=3.6*cm, bottomMargin=3.2*cm)
        doc.cloture_text = cloture_text
        doc.build(elements, onFirstPage=self._draw_canvas, onLaterPages=self._draw_canvas)
        return filepath[filepath.find("static"):].replace("\\", "/")