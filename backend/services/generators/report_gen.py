import os
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Import centralisé du Design System
from backend.services.base_template import BaseTemplate, NAVY_BLUE

class ReportGenerator:
    def __init__(self, base_output_dir="static/documents/reports"):
        self.base_output_dir = base_output_dir
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()
        self._init_styles()
        os.makedirs(self.base_output_dir, exist_ok=True)

    def _init_styles(self):
        """Styles Premium unifiés via NAVY_BLUE."""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=NAVY_BLUE,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.gray,
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        self.styles.add(ParagraphStyle(
            name='ReportTableHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='ReportTableText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=NAVY_BLUE,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='ReportTotalText',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=NAVY_BLUE,
            alignment=TA_RIGHT
        ))

    def generate_accounting_report(self, items, total_amount, filters=None):
        """
        Génère un rapport PDF A4 récapitulant les honoraires.
        items: liste de HonoraireItem
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_honoraires_{timestamp}.pdf"
        filepath = os.path.join(self.base_output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=4*cm, bottomMargin=3*cm)
        
        elements = []
        
        # Titre
        elements.append(Paragraph("Rapport des Honoraires & Encaissements", self.styles['ReportTitle']))
        
        # Sous-titre avec filtres
        filter_str = "Filtres appliqués : "
        if filters:
            checks = []
            if filters.get('assurance'): checks.append(f"Assurance: {filters['assurance']}")
            if filters.get('month'): checks.append(f"Mois: {filters['month']}")
            if filters.get('year'): checks.append(f"Année: {filters['year']}")
            filter_str += ", ".join(checks) if checks else "Aucun"
        else:
            filter_str += "Aucun"
            
        elements.append(Paragraph(filter_str, self.styles['ReportSubtitle']))
        elements.append(Spacer(1, 1*cm))
        
        # Tableau
        table_data = [[
            Paragraph("DATE", self.styles['ReportTableHeader']),
            Paragraph("PATIENT", self.styles['ReportTableHeader']),
            Paragraph("ASSURANCE", self.styles['ReportTableHeader']),
            Paragraph("DÉSIGNATION", self.styles['ReportTableHeader']),
            Paragraph("MONTANT (MAD)", self.styles['ReportTableHeader'])
        ]]
        
        for item in items:
            date_str = item.date.strftime("%d/%m/%Y")
            table_data.append([
                Paragraph(date_str, self.styles['ReportTableText']),
                Paragraph(item.patient_name, self.styles['ReportTableText']),
                Paragraph(item.assurance or "Privé", self.styles['ReportTableText']),
                Paragraph(item.title, self.styles['ReportTableText']),
                Paragraph(f"{item.amount:,.2f}", self.styles['ReportTableText'])
            ])
            
        # Ligne de total
        table_data.append([
            "", "", "", 
            Paragraph("<b>TOTAL GÉNÉRAL</b>", self.styles['ReportTableText']),
            Paragraph(f"<b>{total_amount:,.2f}</b>", self.styles['ReportTableText'])
        ])
        
        t = Table(table_data, colWidths=[2.5*cm, 4.5*cm, 2.5*cm, 5.0*cm, 3.0*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY_BLUE),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.whitesmoke])
        ]))
        
        elements.append(t)
        
        # Pied de page (Canvas)
        def draw_canvas(canvas, doc):
            self.base_template.draw_static_elements(canvas, doc)
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 8)
            canvas.setFillColor(NAVY_BLUE)
            canvas.drawCentredString(A4[0]/2, 1.5*cm, f"Page {canvas.getPageNumber()} | Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            canvas.restoreState()

        doc.build(elements, onFirstPage=draw_canvas, onLaterPages=draw_canvas)
        
        return filepath[filepath.find("static"):].replace("\\", "/")
