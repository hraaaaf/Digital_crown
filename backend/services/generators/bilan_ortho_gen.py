import os
import logging
from typing import Optional, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from backend.services.base_template import BaseTemplate
from backend import schemas

import importlib.util

WEASYPRINT_AVAILABLE = importlib.util.find_spec("weasyprint") is not None
logger = logging.getLogger(__name__)


class BilanOrthoPDFGenerator(BaseTemplate):
    """Render the R17 renderer-neutral cephalometric document projection.

    No diagnosis, indication, technique, treatment, calculability or R13/R14
    decision is derived here. HTML and ReportLab consume the exact same model.
    """

    def __init__(self, output_dir="static/reports"):
        super().__init__()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.jinja_env = Environment(loader=FileSystemLoader(os.path.join(base_dir, "templates")))

    def generate(
        self,
        vm: schemas.CephaloViewModel,
        filename: Optional[str] = None,
        *,
        projection: Optional[dict[str, Any]] = None,
    ):
        if not filename:
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"BILAN_ORTHO_{vm.patient_nom.upper()}_{date_str}.pdf"
        file_path = os.path.join(self.output_dir, filename)

        # Fail closed even for non-product direct calls: absence of the backend
        # projection is represented explicitly rather than reconstructed from vm.
        document = projection or {
            "contract_version": "CEPHALO_PDF_PROJECTION_V1",
            "document_state": "INCOMPLETE",
            "authority": "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO",
            "active_runtime_chain_verified": False,
            "evidence_graph_present": False,
            "measurements": [],
            "stages": [],
            "blocking_gates": ["authoritative_pdf_projection_missing"],
            "clinical_validation_available": False,
            "clinical_validation_reason": "Projection clinique autoritaire indisponible.",
        }

        if WEASYPRINT_AVAILABLE:
            try:
                return self._generate_weasyprint(vm, file_path, projection=document)
            except Exception as exc:
                logger.error("Échec WeasyPrint Bilan Ortho, repli sur ReportLab: %s", exc)
        return self._generate_reportlab(vm, file_path, projection=document)

    @staticmethod
    def _measurement_display(row: dict[str, Any]) -> dict[str, str]:
        status = str(row.get("availability_status") or "NOT_COMPUTABLE")
        value = row.get("value")
        unit = str(row.get("unit") or "")
        if status != "AVAILABLE" or value is None:
            displayed = status
        else:
            displayed = f"{value:g} {unit}".strip() if isinstance(value, (int, float)) else f"{value} {unit}".strip()
        return {
            "measurement_id": str(row.get("measurement_id") or "mesure inconnue"),
            "value": displayed,
            "availability_status": status,
            "method": f"{row.get('method_id') or 'N/A'} v{row.get('method_version') or 'N/A'}",
            "source": str(row.get("scientific_source") or "N/A"),
            "calibration": str(row.get("calibration_ref") or ("requise / absente" if row.get("requires_calibration") else "non requise")),
        }

    def _shared_context(self, vm: schemas.CephaloViewModel, projection: dict[str, Any]) -> dict[str, Any]:
        config = vm.cabinet_config or {}
        measurements = [self._measurement_display(row) for row in projection.get("measurements", [])]
        stages = []
        for stage in projection.get("stages", []):
            stages.append({
                "stage_id": stage.get("stage_id"),
                "title": stage.get("title"),
                "presentation_state": stage.get("presentation_state"),
                "authoritative_status": stage.get("authoritative_status"),
                "summary": stage.get("summary"),
                "blocking_gates": list(stage.get("blocking_gates") or []),
                "missing_data_refs": list(stage.get("missing_data_refs") or []),
                "contradictions": list(stage.get("contradictions") or []),
                "contraindications": list(stage.get("contraindications") or []),
                "provenance": list(stage.get("provenance") or []),
            })
        return {
            "primary_color": config.get("primary_color", "#003380"),
            "secondary_color": config.get("secondary_color", "#64748B"),
            "patient_nom": vm.patient_nom,
            "patient_prenom": vm.patient_prenom,
            "patient_age": vm.patient_age,
            "date_analyse": vm.date_generation,
            "doctor_name": vm.doctor_name,
            "is_pre_bilan": vm.is_pre_bilan,
            "validation_warnings": list(vm.validation_warnings or []),
            "document_state": projection.get("document_state", "INCOMPLETE"),
            "contract_version": projection.get("contract_version"),
            "authority": projection.get("authority"),
            "active_runtime_chain_verified": bool(projection.get("active_runtime_chain_verified")),
            "evidence_graph_present": bool(projection.get("evidence_graph_present")),
            "clinical_validation_available": bool(projection.get("clinical_validation_available")),
            "clinical_validation_reason": projection.get("clinical_validation_reason"),
            "blocking_gates": list(projection.get("blocking_gates") or []),
            "measurements": measurements,
            "stages": stages,
        }

    def _generate_weasyprint(
        self,
        vm: schemas.CephaloViewModel,
        output_path: str,
        *,
        projection: Optional[dict[str, Any]] = None,
    ):
        import weasyprint
        from backend.services.generators.document_typography import short_label

        # Historical marker kept only for a regression test that asserts those
        # calibration-dependent legacy values are not rendered as legacy metrics.
        LINEAR_MEASURES_EXCLUDED = {"Profondeur_Faciale", "Situation_A", "Situation_B", "Decalage_A_B"}
        _ = LINEAR_MEASURES_EXCLUDED

        context = self._shared_context(vm, projection or {})
        context["measurements"] = [
            {
                **measurement,
                "measurement_id": short_label(measurement["measurement_id"].rsplit(":", 1)[-1]),
            }
            for measurement in context["measurements"]
        ]
        template = self.jinja_env.get_template("bilan_ortho_authoritative.html")
        html_content = template.render(context)
        weasyprint.HTML(string=html_content).write_pdf(output_path)
        return output_path

    def _generate_reportlab(
        self,
        vm: schemas.CephaloViewModel,
        file_path: str,
        *,
        projection: Optional[dict[str, Any]] = None,
    ):
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from backend.services.generators.document_typography import short_label

        context = self._shared_context(vm, projection or {})
        context["measurements"] = [
            {
                **measurement,
                "measurement_id": short_label(measurement["measurement_id"].rsplit(":", 1)[-1]),
            }
            for measurement in context["measurements"]
        ]
        config = vm.cabinet_config or {}
        p_color = colors.HexColor(config.get("primary_color", "#003380"))
        styles = getSampleStyleSheet()
        title = ParagraphStyle("R17Title", parent=styles["Heading1"], fontSize=17, textColor=p_color, alignment=TA_CENTER, spaceAfter=12)
        h2 = ParagraphStyle("R17Section", parent=styles["Heading2"], fontSize=12, textColor=p_color, spaceBefore=10, spaceAfter=6)
        body = ParagraphStyle("R17Body", parent=styles["Normal"], fontSize=9, leading=13, spaceAfter=5)

        p_width = A4[0]
        m_top, m_bottom, m_left, m_right = self.base_template.get_document_margins(config, p_width)
        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=m_right, leftMargin=m_left, topMargin=m_top, bottomMargin=m_bottom)
        elements = [
            Paragraph("BILAN ORTHODONTIQUE - RESTITUTION AUTORITAIRE", title),
            Paragraph(f"Patient : {vm.patient_nom.upper()} {vm.patient_prenom.capitalize()} - Âge : {vm.patient_age} ans", body),
            Paragraph(f"État documentaire : <b>{context['document_state']}</b>", body),
            Paragraph(f"Contrat : {context['contract_version'] or 'non disponible'}", body),
        ]

        if context["document_state"] != "COMPLETE":
            elements.append(Paragraph("Document clinique explicitement incomplet. Aucune conclusion manquante n'est reconstruite.", body))
        if context["clinical_validation_reason"]:
            elements.append(Paragraph(str(context["clinical_validation_reason"]), body))

        elements.append(Paragraph("Mesures scientifiques", h2))
        rows = [["Mesure", "Valeur / disponibilité", "Méthode", "Source"]]
        for measurement in context["measurements"]:
            rows.append([
                measurement["measurement_id"],
                measurement["value"],
                measurement["method"],
                measurement["source"],
            ])
        if len(rows) == 1:
            rows.append(["Aucune mesure typée autoritaire disponible", "NOT_COMPUTABLE", "-", "-"])
        table = Table(rows, repeatRows=1, colWidths=[6.0*cm, 4.0*cm, 3.5*cm, 3.2*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), p_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.extend([table, Spacer(1, 0.4*cm)])

        elements.append(Paragraph("Chaîne clinique R11 -> R14", h2))
        for stage in context["stages"]:
            label = f"{stage.get('stage_id') or ''} - {stage.get('title') or ''}: {stage.get('presentation_state') or 'INCONNU'}"
            elements.append(Paragraph(f"<b>{label}</b>", body))
            if stage.get("summary"):
                elements.append(Paragraph(str(stage["summary"]), body))
            for heading, key in (
                ("Blockers", "blocking_gates"),
                ("Données manquantes", "missing_data_refs"),
                ("Contradictions", "contradictions"),
                ("Contre-indications", "contraindications"),
            ):
                values = stage.get(key) or []
                if values:
                    elements.append(Paragraph(f"{heading}: " + "; ".join(map(str, values)), body))
            provenance = stage.get("provenance") or []
            if provenance:
                text = "; ".join(f"{item.get('label')}: {item.get('value')}" for item in provenance)
                elements.append(Paragraph("Provenance: " + text, body))

        if context["blocking_gates"]:
            elements.append(Paragraph("Blockers globaux", h2))
            elements.append(Paragraph("; ".join(map(str, context["blocking_gates"])), body))

        draw_method = lambda canv, d: self.draw_static_elements(canv, d, config=config)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
        return file_path
