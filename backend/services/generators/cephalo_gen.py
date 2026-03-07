# ==============================================================================
# FICHIER 1 : backend/services/generators/cephalo_gen.py
# ==============================================================================
import os
import logging
from datetime import date, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE

logger = logging.getLogger(__name__)

class CephaloPDFGenerator(BaseTemplate):
    """
    Usine PDF Officielle COM. Hérite de BaseTemplate.
    Intègre les données patient, la radio tracée, la table des valeurs déviantes et la synthèse SLM structurée (Dict).
    """
    
    def __init__(self, output_dir="static/reports"):
        super().__init__()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        self.styles.add(ParagraphStyle(
            name='PatientInfo', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=NAVY_BLUE, leading=14
        ))
        self.styles.add(ParagraphStyle(
            name='ReportTitle', parent=self.styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=NAVY_BLUE, alignment=TA_CENTER, spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='SectionTitle', parent=self.styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=NAVY_BLUE, spaceBefore=15, spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='Narrative', parent=self.styles['Normal'], fontName='Helvetica', fontSize=10, leading=15, alignment=TA_JUSTIFY, spaceAfter=6
        ))

    def _calculate_age(self, born):
        if not born:
            return "N/A"
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _draw_canvas(self, canvas, doc):
        """Appel de la fonction de dessin statique (Header/Footer) héritée de BaseTemplate"""
        self.draw_static_elements(canvas, doc)

    def generate(self, patient_data, analysis_payload, image_path=None, filename=None):
        """Génère le PDF et retourne le chemin d'accès absolu."""
        
        # Extraction sécurisée des données patient (support objet SQLAlchemy ou Dict)
        if isinstance(patient_data, dict):
            p_nom = patient_data.get('nom', 'Inconnu')
            p_prenom = patient_data.get('prenom', '')
            p_age = patient_data.get('age', 'N/A')
        else:
            p_nom = getattr(patient_data, 'nom', 'Inconnu')
            p_prenom = getattr(patient_data, 'prenom', '')
            p_age = self._calculate_age(getattr(patient_data, 'date_naissance', None))

        if not filename:
            date_str = datetime.now().strftime('%d%m%Y_%H%M')
            filename = f"RAPPORT_CEPHALO_{p_nom.upper()}_{date_str}.pdf"

        file_path = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            file_path, 
            pagesize=A4, 
            rightMargin=1.5*cm, 
            leftMargin=1.5*cm, 
            topMargin=4.5*cm,  
            bottomMargin=3.5*cm 
        )
        
        elements = []

        # --- 1. HEADER (Titre & Patient) ---
        elements.append(Paragraph("RAPPORT D'ANALYSE CÉPHALOMÉTRIQUE IA", self.styles['ReportTitle']))

        date_display = datetime.now().strftime('%d/%m/%Y')
        info_text = f"<b>Patient(e):</b> {p_nom.upper()} {p_prenom.capitalize()}<br/>"
        info_text += f"<b>Âge:</b> {p_age} ans<br/>"
        info_text += f"<b>Date d'analyse:</b> {date_display}"
        elements.append(Paragraph(info_text, self.styles['PatientInfo']))
        elements.append(Spacer(1, 0.5*cm))

        # --- 2. MILIEU (Radio Burn-in & Tableau des Déviants) ---
        used_image_path = image_path or analysis_payload.get('image_path')
        if used_image_path:
            local_path = used_image_path.split("8000/")[-1] if "8000/" in used_image_path else used_image_path
            if os.path.exists(local_path):
                try:
                    img = Image(local_path, width=14*cm, height=10*cm, kind='proportional')
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 0.5*cm))
                except Exception as e:
                    logger.error(f"Erreur d'intégration de l'image PDF: {e}")

        elements.append(Paragraph("Analyse des Valeurs Déviantes", self.styles['SectionTitle']))
        
        table_data = [["Métrique", "Valeur", "Norme", "Statut"]]
        
        # Sécurisation: results peut exister mais être None
        results_data = analysis_payload.get("results") or analysis_payload or {}
        if not isinstance(results_data, dict):
            results_data = {}
        metrics = results_data.get("metrics", {})
        has_deviants = False
        
        for category, measures in metrics.items():
            for metric_name, data in measures.items():
                status = data.get('status', 'Normal')
                
                # RECTIFICATION : Prise en compte du statut "Compensated"
                if status in ["High", "Low", "Compensated"]:
                    has_deviants = True
                    val = str(data.get('value', 'N/A'))
                    norm = f"{data.get('norm_mean', 0)} ({data.get('norm_min', 0)} - {data.get('norm_max', 0)})"
                    name_clean = metric_name.replace("_", " ")
                    table_data.append([name_clean, val, norm, status])

        if not has_deviants:
            table_data.append(["Aucune déviation significative détectée.", "", "", ""])

        t = Table(table_data, colWidths=[6.5*cm, 3*cm, 4.5*cm, 3*cm])
        t_style = [
            ('BACKGROUND', (0,0), (-1,0), NAVY_BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,1), (0,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8FAFC")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9)
        ]
        
        for row_idx, row in enumerate(table_data[1:], start=1):
            if len(row) > 1:
                if row[3] == "High":
                    t_style.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.red))
                    t_style.append(('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'))
                elif row[3] == "Low":
                    t_style.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.darkorange))
                    t_style.append(('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'))
                elif row[3] == "Compensated":
                    t_style.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.orange))
                    t_style.append(('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'))

        t.setStyle(TableStyle(t_style))
        elements.append(t)
        elements.append(Spacer(1, 0.5*cm))

        # --- 3. BAS (Narrateur SLM - Format Dictionnaire) ---
        elements.append(Paragraph("Synthèse Clinique IA (SLM)", self.styles['SectionTitle']))

        # Récupération du dictionnaire (ai_diagnostic ou ai_narrative)
        results_for_ai = analysis_payload.get("results") or {}
        if not isinstance(results_for_ai, dict):
            results_for_ai = {}
        ai_diag = analysis_payload.get("ai_diagnostic") or analysis_payload.get("ai_narrative") or results_for_ai.get("ai_diagnostic") or {}

        narrative_blocks = []
        if isinstance(ai_diag, dict) and ai_diag:
            if ai_diag.get("diagnostic_squelettique"):
                narrative_blocks.append(Paragraph(f"<b>Squelettique :</b> {ai_diag.get('diagnostic_squelettique')}", self.styles['Narrative']))
            if ai_diag.get("analyse_dentaire"):
                narrative_blocks.append(Paragraph(f"<b>Dentaire :</b> {ai_diag.get('analyse_dentaire')}", self.styles['Narrative']))
            if ai_diag.get("strategie_therapeutique"):
                narrative_blocks.append(Paragraph(f"<b>Stratégie :</b> {ai_diag.get('strategie_therapeutique')}", self.styles['Narrative']))
        else:
            fallback_text = str(ai_diag) if ai_diag else "Aucune synthèse clinique générée."
            narrative_blocks.append(Paragraph(fallback_text, self.styles['Narrative']))

        elements.append(KeepTogether(narrative_blocks))

        # Génération avec callbacks pour BaseTemplate
        try:
            doc.build(elements, onFirstPage=self._draw_canvas, onLaterPages=self._draw_canvas)
            logger.info(f"PDF COM généré avec succès: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Échec de la génération du PDF: {e}")
            raise