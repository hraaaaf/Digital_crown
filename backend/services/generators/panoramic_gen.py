import os
import re

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.utils import ImageReader

from backend.services.base_template import BaseTemplate, NAVY_BLUE

class PanoramicGenerator:
    def __init__(self, base_output_dir="static/documents/panoramic"):
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = os.path.join(self.base_path, base_output_dir)
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()
        self._init_styles()
        os.makedirs(self.output_dir, exist_ok=True)

    def _init_styles(self):
        """Initialisation des styles Elite pour le bilan."""
        self.styles.add(ParagraphStyle(
            name='BilanTitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=NAVY_BLUE,
            alignment=TA_CENTER,
            spaceAfter=25,
            leading=26
        ))
        self.styles.add(ParagraphStyle(
            name='BilanSection',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            textColor=NAVY_BLUE,
            spaceBefore=18,
            spaceAfter=12,
            borderPadding=5,
            leftIndent=0
        ))
        self.styles.add(ParagraphStyle(
            name='BilanText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155'),
            alignment=TA_LEFT
        ))
        self.styles.add(ParagraphStyle(
            name='ClinicalSummaryBox',
            parent=self.styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            leading=15,
            textColor=colors.white,
            backColor=NAVY_BLUE,
            borderPadding=10,
            borderRadius=5,
            alignment=TA_LEFT,
            spaceBefore=20,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='TableHead',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#1e293b'),
            alignment=TA_CENTER
        ))

    def _markdown_to_flowables(self, markdown_text):
        """Convertit le markdown en une structure Elite (Tirets + Callouts)."""
        flowables = []
        lines = markdown_text.split('\n')
        
        in_summary = False
        summary_text = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('---'): 
                continue
            
            # 1. Gestion des Titres Majeurs
            if line.startswith('# '):
                flowables.append(Paragraph(line[2:].upper(), self.styles['BilanTitle']))
                continue
                
            if line.startswith('## '):
                title = line[3:].upper()
                if "SYNTHÈSE" in title or "PRÉCONISATIONS" in title:
                    in_summary = True
                else:
                    in_summary = False
                    flowables.append(Paragraph(title, self.styles['BilanSection']))
                continue

            # 2. Gestion des Secteurs (Sous-titres ###)
            if line.startswith('### '):
                flowables.append(Paragraph(line[4:], self.styles['BilanSection']))
                continue

            # 3. Gestion du contenu (Points ou Texte)
            if line.startswith('- ') or line.startswith('* '):
                clean_line = line[2:].replace('**', '')
                if in_summary:
                    summary_text.append(f"• {clean_line}")
                else:
                    # Affichage sous forme de tiret simple (BilanText)
                    flowables.append(Paragraph(f"• {clean_line}", self.styles['BilanText']))
            elif line.startswith('> '):
                # Disclaimer ou citation
                text = line[2:].replace('*', '')
                flowables.append(Spacer(1, 0.5*cm))
                flowables.append(Paragraph(f"<i>{text}</i>", self.styles['BilanText']))
            else:
                if in_summary:
                    summary_text.append(line)
                else:
                    flowables.append(Paragraph(line, self.styles['BilanText']))
        
        # Callout de Synthèse Clinique
        if summary_text:
            flowables.append(Spacer(1, 0.8*cm))
            flowables.append(Paragraph("SYNTHÈSE CLINIQUE & PRÉCONISATIONS", self.styles['BilanSection']))
            full_summary = "<br/>".join(summary_text)
            flowables.append(Paragraph(full_summary, self.styles['ClinicalSummaryBox']))

        return flowables


    def generate_pdf(self, patient_name, img_rel_path, report_markdown, config=None, user=None):
        """Génère le document PDF Elite."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bilan_panoramique_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath, 
            pagesize=A4, 
            rightMargin=1.5*cm, 
            leftMargin=1.5*cm, 
            topMargin=4.5*cm, 
            bottomMargin=3*cm
        )
        
        elements = []
        
        # 1. Header Patient (Plus élégant)
        from reportlab.platypus import Table, TableStyle
        header_data = [[
            Paragraph(f"<font color='#64748b' size='9'>PATIENT</font><br/><b>{patient_name.upper()}</b>", self.styles['BilanText']),
            Paragraph(f"<font color='#64748b' size='9'>DATE D'EXAMEN</font><br/><b>{datetime.now().strftime('%d/%m/%Y')}</b>", self.styles['BilanText'])
        ]]
        header_table = Table(header_data, colWidths=[12*cm, 6*cm])
        header_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 1, NAVY_BLUE),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.8*cm))

        
        # 3. Contenu structuré
        content_flowables = self._markdown_to_flowables(report_markdown)
        elements.extend(content_flowables)
        
        def draw_canvas(canvas, doc):
            self.base_template.draw_static_elements(canvas, doc, config=config, user=user)
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#94a3b8'))
            canvas.drawCentredString(A4[0]/2, 0.8*cm, f"Document clinique généré par Digital Crown AI - Page {canvas.getPageNumber()}")
            canvas.restoreState()

        doc.build(elements, onFirstPage=draw_canvas, onLaterPages=draw_canvas)
        return f"api/static/documents/panoramic/{filename}"


panoramic_generator = PanoramicGenerator()
