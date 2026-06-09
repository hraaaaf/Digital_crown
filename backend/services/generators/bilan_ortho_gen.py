import os
import logging
from typing import Optional
from datetime import date, datetime
from jinja2 import Environment, FileSystemLoader

from backend.services.base_template import BaseTemplate, NAVY_BLUE
from backend import schemas

import importlib.util
import markdown
import re

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
        
    def _clean_markdown(self, text: str) -> str:
        if not text:
            return ""
        # Remove markdown English words that AI might leave
        text = text.replace("Here is the assessment", "").replace("Here is the analysis", "")
        # Convert markdown to HTML
        html = markdown.markdown(text, extensions=['nl2br'])
        return html

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
        p_color = config.get('primary_color', '#003380') if config else '#003380'
        s_color = config.get('secondary_color', '#64748B') if config else '#64748B'
        
        radio_url = None
        if vm.radio_image_path:
            img_path = vm.radio_image_path.replace("api/", "")
            # On cherche dans le dossier backend (dev)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            abs_path = os.path.join(base_dir, img_path)
            
            if not os.path.exists(abs_path):
                # Backup mode prod
                from backend.core.paths import AppPaths
                media_dir = AppPaths.get_user_data_dir() / "media"
                abs_path = str(media_dir / img_path.replace("static/", ""))
                
            if os.path.exists(abs_path):
                radio_url = f"file:///{os.path.abspath(abs_path).replace('\\', '/')}"
            else:
                logger.warning(f"Image radio introuvable pour le Bilan Ortho: {vm.radio_image_path}")

        # Recuperation des 4 blocs du Bilan Ortho
        ai_diag = vm.analysis.ai_diagnostic or vm.analysis.ai_narrative or {}
        if hasattr(ai_diag, "model_dump"):
            ai_diag = ai_diag.model_dump()
            
        analyse_dentaire = self._clean_markdown(ai_diag.get("analyse_dentaire", ""))
        diag_squelettique = self._clean_markdown(ai_diag.get("diagnostic_squelettique", ""))
        analyse_moulages = self._clean_markdown(ai_diag.get("analyse_moulages", ""))
        synthese_diagnostique = self._clean_markdown(ai_diag.get("synthese_diagnostique", ""))
        strategie_therapeutique = self._clean_markdown(ai_diag.get("strategie_therapeutique", ""))
        
        # Retro-compatibilité si ancien modèle
        if not analyse_moulages and "analyse_dentaire" in ai_diag and not analyse_dentaire:
            analyse_moulages = self._clean_markdown(ai_diag.get("analyse_dentaire", ""))
        if not synthese_diagnostique:
            synthese_diagnostique = "Bilan généré à partir de données existantes."

        from backend.services.qr_service import qr_service
        qr_color = config.get('qr_code_color') or p_color
        qr_style = config.get('qr_code_style', 'dots')
        qr_base64 = qr_service.generate_document_qr_base64("BILAN", str(vm.patient_id or "TEMP"), color=qr_color, qr_style=qr_style)

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
            "analyse_dentaire": analyse_dentaire,
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
        """Mode de secours ReportLab avec intégration du Design System."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        
        config = vm.cabinet_config
        p_color_hex = config.get('primary_color', '#003380') if config else '#003380'
        p_color = colors.HexColor(p_color_hex)
        
        styles = getSampleStyleSheet()
        report_title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=p_color, alignment=TA_CENTER, spaceAfter=20)
        section_title_style = ParagraphStyle('SectionTitle', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=p_color, spaceBefore=15, spaceAfter=10)
        narrative_style = ParagraphStyle('Narrative', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=16, alignment=TA_JUSTIFY, spaceAfter=8)

        # Marges configurables
        m_top = (max(config.get('margin_top', 4.5), 4.5) if config else 4.5) * cm
        m_bottom = (max(config.get('margin_bottom', 3.5), 3.5) if config else 3.5) * cm

        
        p_width_val = A4[0] if isinstance(A4, tuple) else (14.8*cm if A4 == 'A5' else 21.0*cm)
        m_top, m_bottom, m_left, m_right = self.base_template.get_document_margins(config, p_width_val)
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=m_right, leftMargin=m_left, topMargin=m_top, bottomMargin=m_bottom)
        elements = [
            Spacer(1, 1*cm),
            Paragraph("BILAN ORTHODONTIQUE COMPLET", report_title_style),
            Spacer(1, 0.5*cm)
        ]
        
        ai_diag = vm.analysis.ai_diagnostic or vm.analysis.ai_narrative or {}
        if hasattr(ai_diag, "model_dump"):
            ai_diag = ai_diag.model_dump()
            
        def clean_rl(t):
            if not t: return ""
            t = t.replace("Here is the assessment", "").replace("Here is the analysis", "")
            # Basic cleanup for ReportLab since it doesn't parse full HTML/markdown easily
            t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', t)
            t = re.sub(r'\*(.*?)\*', r'<i>\1</i>', t)
            t = re.sub(r'#(.*)', r'<b>\1</b>', t)
            return t

        sections = [
            ("Analyse Dentaire et Alvéolaire", clean_rl(ai_diag.get("analyse_dentaire"))),
            ("Analyse Squelettique", clean_rl(ai_diag.get("diagnostic_squelettique"))),
            ("Examen des Moulages", clean_rl(ai_diag.get("analyse_moulages"))),
            ("Diagnostic / Synthèse", clean_rl(ai_diag.get("synthese_diagnostique"))),
            ("Stratégie Thérapeutique", clean_rl(ai_diag.get("strategie_therapeutique")))
        ]

        for title, content in sections:
            if content:
                elements.append(Paragraph(title.upper(), section_title_style))
                elements.append(Paragraph(str(content).replace('\n', '<br/>'), narrative_style))
                elements.append(Spacer(1, 0.5*cm))

        # Intégration du Header/Footer Master
        draw_method = lambda canv, d: self.draw_static_elements(canv, d, config=config)
        
        try:
            doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
            return file_path
        except Exception as e:
            logger.error(f"Échec ReportLab Bilan: {e}")
            raise
