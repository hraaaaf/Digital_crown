import os
import re
import logging
from typing import List, Dict
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
import importlib.util

from backend.services.base_template import BaseTemplate
from backend.services.panoramic_pdf_outline import parse_panoramic_report
from backend import models
from backend.utils.access_control import assert_patient_access
from sqlalchemy.orm import Session

WEASYPRINT_AVAILABLE = importlib.util.find_spec("weasyprint") is not None

logger = logging.getLogger(__name__)


class PanoramicEliteGenerator(BaseTemplate):
    """Générateur PDF du seul compte rendu radiographique panoramique, sans image.

    Scientific boundary: the PDF is a presentation layer. It must not infer
    dentition status, cephalometric status, diagnosis, treatment, or clinician
    specialty when those facts are not explicitly documented upstream.
    """

    def __init__(self, output_dir="static/reports/panoramic"):
        super().__init__()
        self.output_dir = output_dir
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.full_output_dir = os.path.join(self.base_path, self.output_dir)
        os.makedirs(self.full_output_dir, exist_ok=True)
        template_dir = os.path.join(self.base_path, "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(enabled_extensions=('html', 'xml'), default=True),
        )

    def generate(self, db: Session, analysis_id: int, current_user: models.User) -> str:
        """Génère le PDF uniquement après validation de l'accès au patient."""
        analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == analysis_id).first()
        if not analysis:
            raise ValueError("Analyse introuvable")

        assert_patient_access(analysis.patient_id, current_user, db)

        patient = db.query(models.Patient).filter(models.Patient.id == analysis.patient_id).first()
        config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == current_user.id).first()
        # The panoramic PDF is the written report ONLY; do not resolve/read
        # radiographs or query cephalometric records to render a PDF.
        categories = self._categorize_findings(analysis.report_narrative or "")

        p_color = config.primary_color if config and config.primary_color else '#003380'
        s_color = config.secondary_color if config and config.secondary_color else '#64748B'

        age = self._calculate_age(patient.date_naissance)
        context = {
            "primary_color": p_color,
            "secondary_color": s_color,
            "patient_nom": patient.nom,
            "patient_prenom": patient.prenom,
            "patient_id": patient.id,
            "patient_age": age,
            "date_analyse": analysis.created_at.strftime('%d/%m/%Y'),
            "doctor_name": current_user.nom_complet or "Dr. " + current_user.username,
            "categories": categories,
            "denture_type": self._documented_denture_type(analysis),
        }

        template = self.jinja_env.get_template("panoramic_elite.html")
        html_content = self._sanitize_rendered_html(template.render(context))
        filename = f"PANORAMIQUE_BILAN_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"
        file_path = os.path.join(self.full_output_dir, filename)

        if WEASYPRINT_AVAILABLE:
            import weasyprint
            weasyprint.HTML(string=html_content).write_pdf(file_path)
        else:
            logger.error("WeasyPrint indisponible pour PanoramicEliteGenerator")
            raise ImportError("WeasyPrint est requis pour le Bilan Élite.")

        return f"api/static/reports/panoramic/{filename}"

    def _calculate_age(self, born):
        if not born:
            return "N/A"
        today = datetime.now()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def _documented_denture_type(self, analysis) -> str:
        """Return only explicitly persisted dentition information.

        Age is intentionally not used as a proxy. Absence of a finding means the
        dentition type is not documented by this panoramic analysis.
        """
        data = analysis.detections_data if isinstance(analysis.detections_data, dict) else {}
        findings = data.get("global_findings") or []
        if "denture_mixte" in findings:
            return "Denture mixte (documentée)"
        return "Non documenté"

    def _categorize_findings(self, markdown: str) -> List[Dict]:
        """Preserve every authored section and paragraph, without diagnosis."""
        return parse_panoramic_report(markdown)

    def _sanitize_rendered_html(self, html_content: str) -> str:
        """Neutralise les assertions de présentation incompatibles avec le contrat fail-closed."""
        replacements = {
            "Bilan Radiographique & Clinique": "Bilan radiographique panoramique",
            "Intelligence Artificielle Loki-Silvres v4.0": "Repérage dentaire assisté",
            "Analyse IA Multi-Quadrant": "Repérage dentaire assisté",
            "Analyse Clinique & Diagnostics": "Observations radiographiques documentées",
            "Spécialiste en Orthodontie": "Praticien",
            "Sceau d'Authenticité": "Vérification documentaire",
            "Rapport validé numériquement par": "Praticien associé au dossier",
            "Ce document est cryptographiquement signé. Scannez pour consulter l'original sur le portail Digital Crown.": "Scannez pour accéder à la référence de vérification du document Digital Crown.",
            "Digital Crown Elite Compliance v4.0.": "Digital Crown.",
        }
        for source, target in replacements.items():
            html_content = html_content.replace(source, target)

        disclaimer = (
            '<div class="confidentiality-note" style="font-style: italic;">'
            "Le traitement automatique est limité au repérage dentaire. "
            "Les observations cliniques affichées proviennent des annotations du praticien. "
            "L'absence d'annotation ne constitue pas une conclusion de normalité. "
            "Aucun diagnostic ni traitement n'est généré automatiquement."
            "</div>"
        )
        html_content = re.sub(
            r'<div class="confidentiality-note" style="font-style: italic;">.*?</div>',
            disclaimer,
            html_content,
            count=1,
            flags=re.DOTALL,
        )
        return html_content


panoramic_elite_generator = PanoramicEliteGenerator()
