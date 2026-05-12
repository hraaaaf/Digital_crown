import os
import logging
from typing import Optional
from datetime import date, datetime
from jinja2 import Environment, FileSystemLoader

from backend.services.base_template import BaseTemplate, NAVY_BLUE
from backend import schemas

import importlib.util
WEASYPRINT_AVAILABLE = importlib.util.find_spec("weasyprint") is not None

logger = logging.getLogger(__name__)

class BilanOrthoPDFGenerator(BaseTemplate):
    """
    Générateur PDF du Bilan Orthodontique Complet (Elite Edition).
    Fusionne Céphalométrie, Moulages, et Plan de Traitement.
    """
    
    def __init__(self, output_dir="static/reports"):
        super().__init__()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_dir = os.path.join(base_dir, "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def _calculate_age(self, born):
        if not born:
            return "N/A"
        today = date.today()
        birth = born.date() if hasattr(born, 'date') else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def generate(self, vm: schemas.CephaloViewModel, filename: Optional[str] = None):
        if not filename:
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"BILAN_ORTHO_{vm.patient_nom.upper()}_{date_str}.pdf"

        file_path = os.path.join(self.output_dir, filename)
        
        if WEASYPRINT_AVAILABLE:
            try:
                return self._generate_weasyprint(vm, file_path)
            except Exception as e:
                logger.error(f"Échec WeasyPrint Bilan Ortho, repli sur ReportLab: {e}")
                return self._generate_reportlab(vm, file_path)
        else:
            return self._generate_reportlab(vm, file_path)

    def _generate_weasyprint(self, vm: schemas.CephaloViewModel, output_path: str):
        import weasyprint
        
        flat_metrics = []
        analysis = vm.analysis
        for cat_name, measures in [("Dentaire", analysis.metrics.analyse_dentaire), 
                                   ("Osseuse", analysis.metrics.analyse_osseuse),
                                   ("Esthétique", analysis.metrics.analyse_esthetique)]:
            for metric_name, data in measures:
                if isinstance(data, schemas.MeasureData) and data.status in ["High", "Low", "Compensated"]:
                    flat_metrics.append({
                        "name": metric_name.replace("_", " "),
                        "valeur": data.valeur if data.valeur is not None else 'N/A',
                        "norme": f"[{data.norm_min} - {data.norm_max}]",
                        "status": data.status,
                        "unite": "mm" if "Ligne" in metric_name or "Surplomb" in metric_name else "°"
                    })

        config = vm.cabinet_config
        p_color = config.get('primary_color', '#1A365D') if config else '#1A365D'
        s_color = config.get('secondary_color', '#64748B') if config else '#64748B'
        
        radio_url = None
        if vm.radio_image_path:
            img_path = vm.radio_image_path
            if "8000/" in img_path:
                img_path = img_path.split("8000/")[-1]
            abs_path = os.path.abspath(img_path)
            if os.path.exists(abs_path):
                radio_url = f"file:///{abs_path.replace('\\', '/')}"

        # Recuperation des 4 blocs du Bilan Ortho
        ai_diag = vm.analysis.ai_diagnostic or vm.analysis.ai_narrative or {}
        if hasattr(ai_diag, "model_dump"):
            ai_diag = ai_diag.model_dump()
            
        diag_squelettique = ai_diag.get("diagnostic_squelettique", "")
        analyse_moulages = ai_diag.get("analyse_moulages", "")
        synthese_diagnostique = ai_diag.get("synthese_diagnostique", "")
        strategie_therapeutique = ai_diag.get("strategie_therapeutique", "")
        
        # Retro-compatibilité si ancien modèle
        if not analyse_moulages and "analyse_dentaire" in ai_diag:
            analyse_moulages = ai_diag.get("analyse_dentaire", "")
        if not synthese_diagnostique:
            synthese_diagnostique = "Bilan généré à partir de données existantes."

        from backend.services.qr_service import qr_service
        qr_data = f"https://digitalcrown.ai/verify/ortho/{vm.patient_id}/{datetime.now().strftime('%Y%m%d')}"
        qr_base64 = qr_service.generate_document_qr_base64("BILAN", str(vm.patient_id or "TEMP"))

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
            "diagnostic_squelettique": diag_squelettique,
            "analyse_moulages": analyse_moulages,
            "synthese_diagnostique": synthese_diagnostique,
            "strategie_therapeutique": strategie_therapeutique,
            "doctor_name": vm.doctor_name,
            "qr_code_base64": qr_base64,
            "denture_type": vm.analysis.clinical_data.denture_type,
            "preference_technique": vm.analysis.clinical_data.preference_technique
        }

        template = self.jinja_env.get_template("bilan_ortho_elite.html")
        html_content = template.render(context)
        weasyprint.HTML(string=html_content).write_pdf(output_path)
        return output_path

    def _generate_reportlab(self, vm: schemas.CephaloViewModel, file_path: str):
        # Fallback simple (identique au précédent, avec titres adaptés)
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        
        styles = getSampleStyleSheet()
        p_color = colors.HexColor('#1A365D')
        report_title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=p_color, alignment=TA_CENTER, spaceAfter=20)
        section_title_style = ParagraphStyle('SectionTitle', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=p_color, spaceBefore=15, spaceAfter=10)
        narrative_style = ParagraphStyle('Narrative', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=15, alignment=TA_JUSTIFY, spaceAfter=6)

        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=4.5*cm, bottomMargin=3.5*cm)
        elements = [Paragraph("BILAN ORTHODONTIQUE (Fallback)", report_title_style)]
        
        ai_diag = vm.analysis.ai_diagnostic or vm.analysis.ai_narrative or {}
        if hasattr(ai_diag, "model_dump"):
            ai_diag = ai_diag.model_dump()
            
        for k, v in ai_diag.items():
            if k not in ["is_fallback"] and v:
                elements.append(Paragraph(k.replace('_', ' ').capitalize(), section_title_style))
                elements.append(Paragraph(str(v).replace('\n', '<br/>'), narrative_style))
                
        try:
            doc.build(elements)
            return file_path
        except Exception as e:
            logger.error(f"Échec ReportLab Bilan: {e}")
            raise
