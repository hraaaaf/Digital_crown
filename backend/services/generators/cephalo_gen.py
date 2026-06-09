import os
import logging
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from jinja2 import Environment, FileSystemLoader

from backend.services.base_template import BaseTemplate, NAVY_BLUE
from backend import schemas

# Imports conditionnels pour WeasyPrint
import importlib.util
WEASYPRINT_AVAILABLE = importlib.util.find_spec("weasyprint") is not None

logger = logging.getLogger(__name__)

class CephaloPDFGenerator(BaseTemplate):
    """
    Usine PDF Officielle COM - ELITE EDITION.
    Utilise WeasyPrint pour un rendu moderne (HTML/CSS) avec fallback ReportLab.
    """
    
    def __init__(self, output_dir="static/reports"):
        super().__init__()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialisation Jinja2
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_dir = os.path.join(base_dir, "backend", "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def _calculate_age(self, born):
        if not born:
            return "N/A"
        today = date.today()
        birth = born.date() if hasattr(born, 'date') else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def generate(self, vm: schemas.CephaloViewModel, filename: Optional[str] = None):
        """Génère le PDF via WeasyPrint (Elite) avec fallback ReportLab."""
        
        if not filename:
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"RAPPORT_CEPHALO_{vm.patient_nom.upper()}_{date_str}.pdf"

        file_path = os.path.join(self.output_dir, filename)
        
        if WEASYPRINT_AVAILABLE:
            try:
                return self._generate_weasyprint(vm, file_path)
            except Exception as e:
                logger.error(f"Échec WeasyPrint, repli sur ReportLab: {e}")
                return self._generate_reportlab(vm, file_path)
        else:
            return self._generate_reportlab(vm, file_path)

    def _generate_weasyprint(self, vm: schemas.CephaloViewModel, output_path: str):
        """Rendu Moderne via WeasyPrint."""
        import weasyprint
        
        # 1. Préparation des données métriques (aplatissement)
        flat_metrics = []
        analysis = vm.analysis
        for cat_name, measures in [("Dentaire", analysis.metrics.analyse_dentaire), 
                                   ("Osseuse", analysis.metrics.analyse_osseuse),
                                   ("Esthétique", analysis.metrics.analyse_esthetique)]:
            for metric_name, data in measures:
                if isinstance(data, schemas.MeasureData):
                    flat_metrics.append({
                        "name": metric_name.replace("_", " "),
                        "valeur": data.valeur if data.valeur is not None else 'N/A',
                        "norm_mean": data.norm_mean,
                        "norm_min": data.norm_min,
                        "norm_max": data.norm_max,
                        "status": data.status,
                        "unite": "mm" if "Ligne" in metric_name or "Surplomb" in metric_name else ""
                    })

        # 2. Préparation du contexte Jinja
        config = vm.cabinet_config
        p_color = config.get('primary_color', '#003380') if config else '#003380'
        s_color = config.get('secondary_color', '#64748B') if config else '#64748B'
        
        # Image URL absolue pour WeasyPrint
        radio_url = None
        if vm.radio_image_path:
            # Nettoyage du path
            img_path = vm.radio_image_path
            if "8000/" in img_path:
                img_path = img_path.split("8000/")[-1]
            
            abs_path = os.path.abspath(img_path)
            if os.path.exists(abs_path):
                radio_url = f"file:///{abs_path.replace('\\', '/')}"

        context = {
            "primary_color": p_color,
            "secondary_color": s_color,
            "patient_nom": vm.patient_nom,
            "patient_prenom": vm.patient_prenom,
            "patient_age": vm.patient_age,
            "patient_id": vm.patient_id,
            "date_analyse": vm.date_generation,
            "radio_url": radio_url,
            "metrics": flat_metrics,
            "ai_diag": vm.analysis.ai_narrative,
            "doctor_name": vm.doctor_name
        }

        # 3. Rendu
        template = self.jinja_env.get_template("cephalo_report_elite.html")
        html_content = template.render(context)
        
        # WeasyPrint
        weasyprint.HTML(string=html_content).write_pdf(output_path)
        logger.info(f"Rendu WeasyPrint réussi: {output_path}")
        return output_path

    def _generate_reportlab(self, vm: schemas.CephaloViewModel, file_path: str):
        """Fallback ReportLab (Ancienne méthode stable)."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        
        styles = getSampleStyleSheet()
        config = vm.cabinet_config
        p_color_hex = config.get('primary_color', '#003380') if config else '#003380'
        p_color = colors.HexColor(p_color_hex)
        s_color = colors.HexColor(config.get('secondary_color', '#666666')) if config else colors.grey
        
        report_title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=p_color, alignment=TA_CENTER, spaceAfter=20)
        section_title_style = ParagraphStyle('SectionTitle', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=p_color, spaceBefore=15, spaceAfter=10)
        patient_info_style = ParagraphStyle('PatientInfo', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.black, leading=14)
        narrative_style = ParagraphStyle('Narrative', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=15, alignment=TA_JUSTIFY, spaceAfter=6)

        # Marges configurables
        m_top = (max(config.get('margin_top', 4.5), 4.5) if config else 4.5) * cm
        m_bottom = (max(config.get('margin_bottom', 3.5), 3.5) if config else 3.5) * cm

        
        p_width_val = A4[0] if isinstance(A4, tuple) else (14.8*cm if A4 == 'A5' else 21.0*cm)
        m_top, m_bottom, m_left, m_right = self.base_template.get_document_margins(config, p_width_val)
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=m_right, leftMargin=m_left, topMargin=m_top, bottomMargin=m_bottom)
        elements = [
            Spacer(1, 0.5*cm),
            Paragraph("RAPPORT D'ANALYSE CÉPHALOMÉTRIQUE IA", report_title_style),
            Paragraph(f"<b>Patient(e):</b> {vm.patient_nom.upper()} {vm.patient_prenom.capitalize()}<br/><b>Âge:</b> {vm.patient_age} ans<br/><b>Date:</b> {vm.date_generation}", patient_info_style),
            Spacer(1, 0.5*cm)
        ]

        # Image
        if vm.radio_image_path:
            img_path = vm.radio_image_path.split("8000/")[-1] if "8000/" in vm.radio_image_path else vm.radio_image_path
            if os.path.exists(img_path):
                img = Image(img_path, width=14*cm, height=10*cm, kind='proportional')
                img.hAlign = 'CENTER'
                elements.append(img)
                elements.append(Spacer(1, 0.5*cm))

        # Table
        table_data = [["Métrique", "Valeur", "Norme", "Statut"]]
        for cat_name, measures in [("Dentaire", vm.analysis.metrics.analyse_dentaire), ("Osseuse", vm.analysis.metrics.analyse_osseuse), ("Esthétique", vm.analysis.metrics.analyse_esthetique)]:
            for metric_name, data in measures:
                if isinstance(data, schemas.MeasureData) and data.status in ["High", "Low", "Compensated"]:
                    table_data.append([metric_name.replace("_", "\u00a0"), str(data.valeur), f"{data.norm_mean}\u00a0({data.norm_min}-{data.norm_max})", data.status])

        if len(table_data) > 1:
            t = Table(table_data, colWidths=[6.5*cm, 3*cm, 4.5*cm, 3*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), p_color), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), 
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey), 
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER')
            ]))
            elements.append(t)

        # Narrative
        elements.append(Paragraph("SYNTHÈSE CLINIQUE IA", section_title_style))
        diag = vm.analysis.ai_narrative or {}
        if isinstance(diag, dict):
            for k, v in diag.items():
                elements.append(Paragraph(f"<b>{k.replace('_', ' ').capitalize()} :</b> {v}", narrative_style))
        else:
            elements.append(Paragraph(str(diag), narrative_style))

        # Intégration du Template Maître
        draw_method = lambda canv, d: self.draw_static_elements(canv, d, config=config)

        try:
            doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
            return file_path
        except Exception as e:
            logger.error(f"Échec de la génération du PDF: {e}")
            raise