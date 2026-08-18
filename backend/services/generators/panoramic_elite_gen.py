import os
import logging
from typing import Optional, List, Dict
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import importlib.util

from backend.services.base_template import BaseTemplate, NAVY_BLUE
from backend import models, schemas, database
from backend.utils.access_control import assert_patient_access
from sqlalchemy.orm import Session

WEASYPRINT_AVAILABLE = importlib.util.find_spec("weasyprint") is not None

logger = logging.getLogger(__name__)

class PanoramicEliteGenerator(BaseTemplate):
    """Générateur PDF du bilan radiographique Élite."""

    def __init__(self, output_dir="static/reports/panoramic"):
        super().__init__()
        self.output_dir = output_dir
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.full_output_dir = os.path.join(self.base_path, self.output_dir)
        os.makedirs(self.full_output_dir, exist_ok=True)
        template_dir = os.path.join(self.base_path, "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def generate(self, db: Session, analysis_id: int, current_user: models.User) -> str:
        """Génère le PDF uniquement après validation de l'accès au patient."""
        analysis = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.id == analysis_id).first()
        if not analysis:
            raise ValueError("Analyse introuvable")

        assert_patient_access(analysis.patient_id, current_user, db)

        patient = db.query(models.Patient).filter(models.Patient.id == analysis.patient_id).first()
        config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == current_user.id).first()
        cephalo = db.query(models.CephaloAnalysis).filter(
            models.CephaloAnalysis.patient_id == analysis.patient_id
        ).order_by(models.CephaloAnalysis.created_at.desc()).first()

        pano_url = self._format_image_url(analysis.image_path)
        cephalo_url = self._format_image_url(cephalo.image_original_path) if cephalo else None
        categories = self._categorize_findings(analysis.report_narrative or "")
        metrics = []
        if cephalo and cephalo.angles_data:
            metrics = self._prepare_metrics(cephalo.angles_data)

        p_color = config.primary_color if config and config.primary_color else '#003380'
        s_color = config.secondary_color if config and config.secondary_color else '#64748B'

        from backend.services.qr_service import qr_service
        qr_color = config.qr_code_color if config and config.qr_code_color else p_color
        qr_style = config.qr_code_style if config and config.qr_code_style else 'dots'
        qr_base64 = qr_service.generate_document_qr_base64("RADIO", str(analysis_id), color=qr_color, qr_style=qr_style)

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
            "pano_url": pano_url,
            "cephalo_url": cephalo_url,
            "categories": categories,
            "metrics": metrics,
            "qr_code_base64": qr_base64,
            "denture_type": "Denture Adulte" if isinstance(age, int) and age > 12 else "Denture Mixte"
        }

        template = self.jinja_env.get_template("panoramic_elite.html")
        html_content = template.render(context)
        filename = f"RADIO_ELITE_{patient.nom.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(self.full_output_dir, filename)

        if WEASYPRINT_AVAILABLE:
            import weasyprint
            weasyprint.HTML(string=html_content).write_pdf(file_path)
        else:
            logger.error("WeasyPrint indisponible pour PanoramicEliteGenerator")
            raise ImportError("WeasyPrint est requis pour le Bilan Élite.")

        return f"api/static/reports/panoramic/{filename}"

    def _format_image_url(self, db_path: str) -> Optional[str]:
        if not db_path:
            return None
        clean_path = db_path.replace("api/", "")
        dev_path = os.path.join(self.base_path, clean_path)
        from backend.core.paths import AppPaths
        media_dir = AppPaths.get_user_data_dir() / "media"
        prod_path = str(media_dir / clean_path.replace("static/", ""))
        abs_path = None
        if os.path.exists(dev_path):
            abs_path = os.path.abspath(dev_path)
        elif os.path.exists(prod_path):
            abs_path = os.path.abspath(prod_path)
        if abs_path:
            return f"file:///{abs_path.replace('\\', '/')}"
        logger.warning(f"Image introuvable pour le PDF: {db_path} (tenté: {dev_path} et {prod_path})")
        return None

    def _calculate_age(self, born):
        if not born:
            return "N/A"
        today = datetime.now()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def _categorize_findings(self, markdown: str) -> List[Dict]:
        categories = []
        if not markdown or len(markdown) < 10:
            return [{"name": "Observations Générales", "findings": ["Examen en cours d'analyse."]}]
        current_cat = None
        lines = markdown.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('## ') or line.startswith('### '):
                name = line.replace('#', '').strip()
                current_cat = {"name": name, "findings": []}
                categories.append(current_cat)
            elif (line.startswith('- ') or line.startswith('* ')) and current_cat is not None:
                item = line[2:].replace('**', '').strip()
                current_cat["findings"].append(item)
        if not categories:
            items = [l[2:].strip() for l in lines if l.startswith('- ') or l.startswith('* ')]
            if not items:
                items = [markdown]
            return [{"name": "Synthèse Clinique", "findings": items}]
        return categories

    def _prepare_metrics(self, angles_data: Dict) -> List[Dict]:
        metrics = []
        key_metrics = ["SNA", "SNB", "ANB", "Angle_de_Tweed", "IMPA", "I_Francfort", "Situation_A"]
        for name in key_metrics:
            data = angles_data.get(name)
            if not data:
                continue
            val = data.get('valeur', 0)
            n_min = data.get('norm_min', 0)
            n_max = data.get('norm_max', 0)
            status = data.get('status', 'Normal')
            n_min_safe = min(n_min, n_max)
            n_max_safe = max(n_min, n_max)
            if n_max_safe != n_min_safe:
                mean = (n_min_safe + n_max_safe) / 2
                dev = (n_max_safe - n_min_safe) / 2
                z = (val - mean) / dev
                percent = 50 + (z * 15)
            else:
                percent = 50 if val == n_min_safe else (75 if val > n_min_safe else 25)
            percent = max(5, min(95, percent))
            status_labels = {
                "High": "Augmenté",
                "Low": "Diminué",
                "Normal": "Harmonieux",
                "Compensated": "Compensé"
            }
            metrics.append({
                "name": name.replace('_', ' '),
                "valeur": f"{val:.1f}",
                "unite": "mm" if "Situation" in name else "°",
                "norme": f"[{n_min} - {n_max}]",
                "visual_percent": int(percent),
                "status": status,
                "status_label": status_labels.get(status, status)
            })
        return metrics

panoramic_elite_generator = PanoramicEliteGenerator()
