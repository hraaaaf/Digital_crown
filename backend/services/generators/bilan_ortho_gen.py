import os
import logging
from typing import Optional, Any
from datetime import datetime
from secrets import token_hex
from xml.sax.saxutils import escape
from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.services.base_template import BaseTemplate
from backend.services.cephalo_pdf_presentation import clinical_term, measurement_value, practitioner_stage
from backend.services.ortho_bilan_document_v5 import build_ortho_bilan_document
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
        self.jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(base_dir, "templates")),
            autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True),
        )

    def generate(
        self,
        vm: schemas.CephaloViewModel,
        filename: Optional[str] = None,
        *,
        projection: Optional[dict[str, Any]] = None,
        user=None,
    ):
        if not filename:
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            identity = ("_ETUDE_" + str(projection["analysis_id"])) if projection and isinstance(projection.get("analysis_id"), int) else ""
            version = ("_REV_" + str(projection["analysis_revision"])) if projection and isinstance(projection.get("analysis_revision"), int) else ""
            filename = f"BILAN_ORTHO_{vm.patient_nom.upper()}{identity}{version}_{date_str}_{token_hex(6)}.pdf"
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
                return self._generate_weasyprint(vm, file_path, projection=document, user=user)
            except Exception as exc:
                logger.error("Échec WeasyPrint Bilan Ortho, repli sur ReportLab: %s", exc)
        return self._generate_reportlab(vm, file_path, projection=document, user=user)

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

    @staticmethod
    def _protocol_row_display(row: dict[str, Any]) -> dict[str, str]:
        status=str(row.get("availability_status") or "NOT_COMPUTABLE")
        value=row.get("value") if status=="AVAILABLE" else None
        unit=str(row.get("unit") or "")
        reference=row.get("historical_reference")
        delta=row.get("reference_delta")
        def show(number):
            return f"{number:g}" if isinstance(number,(int,float)) else "?"
        interpretation = str(row.get("interpretation_status") or "")
        if interpretation == "REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION":
            interpretation = "Référence historique — aucune classification clinique"
        return {
            "canonical_measurement_id":str(row.get("canonical_measurement_id") or ""),
            "label":str(row.get("label") or row.get("canonical_measurement_id") or "Mesure"),
            "layer":str(row.get("layer") or ""),
            "value":f"{show(value)} {unit}".strip() if value is not None else "Non calculable",
            "reference":f"{show(reference)} {unit}".strip() if reference is not None else "?",
            "delta":f"{show(delta)} {unit}".strip() if delta is not None else "?",
            "reference_authority":str(row.get("reference_authority") or ""),
            "interpretation_status":interpretation,
        }

    def _shared_context(self, vm: schemas.CephaloViewModel, projection: dict[str, Any]) -> dict[str, Any]:
        config = vm.cabinet_config or {}
        measurements = [self._measurement_display(row) for row in projection.get("measurements", [])]
        for measurement in measurements:
            measurement.update({
                "display_value": measurement_value(
                    measurement["value"], measurement["availability_status"]),
                "display_availability_status": clinical_term(
                    measurement["availability_status"], "Mesure indisponible"),
                "display_method": clinical_term(
                    measurement["method"], "Méthode consultable dans le dossier technique"),
                "display_source": clinical_term(
                    measurement["source"], "Source scientifique consultable dans le dossier"),
                "display_calibration": clinical_term(
                    measurement["calibration"], "Calibration à vérifier"),
            })
        protocol_profiles = dict(projection.get("protocol_profiles") or {})
        steiner_profile = dict(protocol_profiles.get("steiner") or {})
        steiner_rows = [self._protocol_row_display(row) for row in steiner_profile.get("rows", [])]
        for row in steiner_rows:
            row["display_interpretation_status"] = clinical_term(
                row["interpretation_status"], "Référence contextuelle — sans diagnostic")
        tweed_merrifield_profile = dict(protocol_profiles.get("tweed_merrifield") or {})
        tweed_merrifield_rows = []
        for row in tweed_merrifield_profile.get("rows", []):
            value = row.get("value")
            unit = str(row.get("unit") or "")
            tweed_merrifield_rows.append({
                "label": str(row.get("label") or row.get("canonical_measurement_id") or "Mesure"),
                "value": f"{value:g} {unit}".strip() if isinstance(value, (int, float)) else "Non calculable",
                "profile_section": str(row.get("profile_section") or ""),
                "reference_authority": str(row.get("reference_authority") or ""),
                "interpretation_status": str(row.get("interpretation_status") or ""),
                "display_profile_section": clinical_term(
                    row.get("profile_section"), "Profil scientifique documenté"),
                "display_reference_authority": clinical_term(
                    row.get("reference_authority"), "Référence à consulter dans le dossier"),
                "display_interpretation_status": clinical_term(
                    row.get("interpretation_status"), "Mesure brute — sans classification"),
            })
        stages = []
        for stage_index, stage in enumerate(projection.get("stages", []), 1):
            stages.append({
                "display_title": practitioner_stage(stage, stage_index),
                "display_presentation_state": clinical_term(
                    stage.get("presentation_state"), "Validation en attente"),
                "display_summary": clinical_term(stage.get("summary"), ""),
                "display_blocking_gates": [clinical_term(item) for item in (stage.get("blocking_gates") or [])],
                "display_missing_data_refs": [clinical_term(item) for item in (stage.get("missing_data_refs") or [])],
                "display_contradictions": [clinical_term(item) for item in (stage.get("contradictions") or [])],
                "display_contraindications": [clinical_term(item) for item in (stage.get("contraindications") or [])],
                "display_provenance": [
                    {"label": clinical_term(item.get("label"), "Référence"),
                     "value": clinical_term(item.get("value"), "Source consultable dans le dossier")}
                    for item in (stage.get("provenance") or []) if isinstance(item, dict)
                ],
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
            "document_branding_applied": True,
            "body_font_family": {
                "outfit": "Outfit, DejaVu Sans, sans-serif",
                "inter": "DejaVu Sans, sans-serif",
                "serif": "DejaVu Serif, serif",
                "playfair": "DejaVu Serif, serif",
            }.get(str(config.get("font_fr") or "").lower(), "DejaVu Sans, sans-serif"),
            "patient_nom": vm.patient_nom,
            "patient_prenom": vm.patient_prenom,
            "patient_age": vm.patient_age,
            "cephalo_source_patient_id": projection.get("patient_id"),
            "cephalo_source_analysis_id": projection.get("analysis_id"),
            "cephalo_source_analysis_revision": projection.get("analysis_revision"),
            "date_analyse": vm.date_generation,
            "doctor_name": vm.doctor_name,
            "is_pre_bilan": vm.is_pre_bilan,
            "validation_warnings": list(vm.validation_warnings or []),
            "display_validation_warnings": [clinical_term(item) for item in (vm.validation_warnings or [])],
            "document_state": projection.get("document_state", "INCOMPLETE"),
            "contract_version": projection.get("contract_version"),
            "authority": projection.get("authority"),
            "active_runtime_chain_verified": bool(projection.get("active_runtime_chain_verified")),
            "evidence_graph_present": bool(projection.get("evidence_graph_present")),
            "clinical_validation_available": bool(projection.get("clinical_validation_available")),
            "clinical_validation_reason": projection.get("clinical_validation_reason"),
            "display_clinical_validation_reason": clinical_term(
                projection.get("clinical_validation_reason"), "La validation clinique n'est pas confirmée."),
            "display_authority": clinical_term(
                projection.get("authority"), "Données issues du dossier scientifique"),
            "display_document_state": clinical_term(
                projection.get("document_state", "INCOMPLETE"), "Dossier incomplet"),
            "blocking_gates": list(projection.get("blocking_gates") or []),
            "display_blocking_gates": [clinical_term(item) for item in (projection.get("blocking_gates") or [])],
            "measurements": measurements,
            "odf": build_ortho_bilan_document(projection),
            "steiner_protocol": {
                "protocol_profile_id": steiner_profile.get("protocol_profile_id"),
                "source_lock_status": (steiner_profile.get("source_lock_gate") or {}).get("status"),
                "display_source_lock_status": clinical_term(
                    (steiner_profile.get("source_lock_gate") or {}).get("status"), "Référence non vérifiée"),
                "final_gate_status": (steiner_profile.get("final_gate") or {}).get("status"),
                "norm_set": dict(steiner_profile.get("norm_set") or {}),
                "rows": steiner_rows,
            } if steiner_profile else None,
            "tweed_merrifield_protocol": {
                "protocol_profile_id": tweed_merrifield_profile.get("protocol_profile_id"),
                "source_lock_status": (tweed_merrifield_profile.get("source_lock_gate") or {}).get("status"),
                "display_source_lock_status": clinical_term(
                    (tweed_merrifield_profile.get("source_lock_gate") or {}).get("status"), "Référence non vérifiée"),
                "final_gate_status": (tweed_merrifield_profile.get("final_gate") or {}).get("status"),
                "rows": tweed_merrifield_rows,
                "reference_contexts": list(tweed_merrifield_profile.get("reference_contexts") or []),
            } if tweed_merrifield_profile else None,
            "stages": stages,
        }

    @staticmethod
    def _clinician_measurement_label(identifier, index, short_label):
        """No leaked machine IDs when a measurement has no approved short name."""
        raw = str(identifier).rsplit(":", 1)[-1]
        approved = short_label(raw)
        if "_" in raw and approved == raw.replace("_", " "):
            return ""  # fail closed: never invent a clinical measurement name
        return approved

    def _generate_weasyprint(
        self,
        vm: schemas.CephaloViewModel,
        output_path: str,
        *,
        projection: Optional[dict[str, Any]] = None,
        user=None,
    ):
        import weasyprint
        from backend.services.generators.document_typography import short_label

        # Historical marker kept only for a regression test that asserts those
        # calibration-dependent legacy values are not rendered as legacy metrics.
        LINEAR_MEASURES_EXCLUDED = {"Profondeur_Faciale", "Situation_A", "Situation_B", "Decalage_A_B"}
        _ = LINEAR_MEASURES_EXCLUDED

        context = self._shared_context(vm, projection or {})
        config = vm.cabinet_config or {}
        from reportlab.lib.pagesizes import A4
        self.update_active_fonts(config)
        top, bottom, left, right = self.get_document_margins(config, A4[0])
        context["page_margins_pt"] = {
            "top": round(top, 3), "bottom": round(bottom, 3),
            "left": round(left, 3), "right": round(right, 3),
        }
        # Practitioner-facing four-phase document. R17 raw audit template is
        # retained independently for legacy regression / technical previews.
        template = self.jinja_env.get_template("bilan_ortho_v5.html")
        html_content = template.render(context)
        # The brand stationery is drawn by the SAME BaseTemplate instance as
        # an ordonnance, not imitated with a parallel CSS implementation.
        from io import BytesIO
        from types import SimpleNamespace
        from reportlab.pdfgen.canvas import Canvas
        from PyPDF2 import PdfReader, PdfWriter

        body_pdf = weasyprint.HTML(string=html_content, base_url=self.base_path).write_pdf()
        reader = PdfReader(BytesIO(body_pdf))
        if not reader.pages:
            raise ValueError("Bilan PDF sans page : habillage impossible")
        stationery_bytes = BytesIO()
        stationery = Canvas(stationery_bytes, pagesize=A4)
        doc = SimpleNamespace(pagesize=A4, doc_id=(
            projection or {}).get("analysis_id") or "CEPHALO")
        self.draw_static_elements(stationery, doc, config=config, user=user)
        stationery.showPage()
        stationery.save()
        stationery_pdf = stationery_bytes.getvalue()
        writer = PdfWriter()
        for page in reader.pages:
            # PyPDF2 3.x has no merge_page(over=False); merge the clinical
            # content ON TOP of a fresh canonical BaseTemplate stationery page.
            branded_page = PdfReader(BytesIO(stationery_pdf)).pages[0]
            branded_page.merge_page(page)
            writer.add_page(branded_page)
        with open(output_path, "wb") as target:
            writer.write(target)
        return output_path

    def _generate_reportlab(
        self,
        vm: schemas.CephaloViewModel,
        file_path: str,
        *,
        projection: Optional[dict[str, Any]] = None,
        user=None,
    ):
        """ReportLab fallback renders the same V5 four-phase model as Weasy."""
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image as RLImage, KeepTogether

        context = self._shared_context(vm, projection or {})
        odf = context["odf"]
        config = vm.cabinet_config or {}
        self.update_active_fonts(config)
        p_color = colors.HexColor(config.get("primary_color", "#003380"))
        styles = getSampleStyleSheet()
        title = ParagraphStyle(
            "ODFV5Title", parent=styles["Heading1"], fontSize=17,
            textColor=p_color, alignment=TA_CENTER, spaceAfter=13)
        heading = ParagraphStyle(
            "ODFV5Heading", parent=styles["Heading2"], fontSize=12,
            textColor=p_color, spaceBefore=13, spaceAfter=7)
        subheading = ParagraphStyle(
            "ODFV5Subheading", parent=styles["Heading3"], fontSize=10,
            textColor=p_color, spaceBefore=9, spaceAfter=5)
        body = ParagraphStyle(
            "ODFV5Body", parent=styles["Normal"], fontSize=9, leading=13,
            spaceAfter=7)
        cell_style = ParagraphStyle(
            "ODFV5Cell", parent=body, fontSize=8.5, leading=11, spaceAfter=1)
        def cell(value):
            return Paragraph(escape(str(value)), cell_style)

        m_top, m_bottom, m_left, m_right = self.get_document_margins(config, A4[0])
        doc = SimpleDocTemplate(
            file_path, pagesize=A4, rightMargin=m_right, leftMargin=m_left,
            topMargin=m_top, bottomMargin=m_bottom)
        elements = [
            Paragraph("Bilan orthodontique", title),
            Paragraph(
                "Patient : " + escape(str(vm.patient_nom).upper()) + " " +
                escape(str(vm.patient_prenom).capitalize()) +
                "  |  Âge : " + escape(str(vm.patient_age)) +
                " ans  |  Date : " + escape(str(vm.date_generation)), body),
        ]
        def add_table(rows, columns):
            table = Table(
                [[cell(a), cell(b)] for a, b in
                 [(columns[0], columns[1])] +
                 [(r["label"], r["value"]) for r in rows]],
                repeatRows=1, colWidths=[9.0 * cm, 7.0 * cm],
                hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf1f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), p_color),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25,
                 colors.HexColor("#e1e8ec")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.13 * cm))

        trace = odf.get("research_figure")
        if trace:
            from io import BytesIO
            from base64 import b64decode
            traced_image = b64decode(trace["image_b64"], validate=True)
            legend = ", ".join(x["name"] for x in trace.get("legend", []))
            # Keep the traced image and its source in PHASE 01, with the same
            # geometry (no distortion) as the WeasyPrint view.
            elements.append(KeepTogether([
                Paragraph("01  Analyse céphalométrique", heading),
                Paragraph("Tracé céphalométrique — téléradiographie de profil", subheading),
                RLImage(BytesIO(traced_image),
                        width=11.0 * cm, height=(11.0 * 2400 / 1935) * cm),
                Spacer(1, 0.16 * cm),
                Paragraph(escape("Plans : " + legend), body),
                Paragraph(escape(trace["caption"]), body),
                Paragraph("Source : " + escape(trace["source_url"]), body),
            ]))
            if trace.get("kind") == "G5_MANUAL_ANATOMICAL_TRACE":
                # Same manual curves on a separate white drawing — never an
                # illustration synthesized from unrelated landmarks.
                clean_bytes=b64decode(trace["anatomical_only_b64"],validate=True)
                elements.append(KeepTogether([
                    Paragraph("Tracé anatomique — vue épurée",subheading),
                    RLImage(BytesIO(clean_bytes),width=11.0*cm,
                            height=(11.0*2400/1935)*cm),
                    Spacer(1,0.18*cm),
                    Paragraph("Les mêmes six contours approuvés sur fond blanc. "
                              "Aucune silhouette générée automatiquement.",body),
                ]))
        else:
            elements.append(Paragraph("01  Analyse céphalométrique", heading))
        for key, label in (
            ("osseuse", "A. Analyse osseuse"),
            ("dentoalveolaire", "B. Analyse dento-alvéolaire"),
        ):
            elements.append(Paragraph(label, subheading))
            if odf[key]:
                add_table(odf[key], ("Mesure", "Résultat"))
            else:
                elements.append(Paragraph(
                    "Mesures à renseigner par le praticien.", body))

        elements.append(Paragraph("02  Examen des moulages", heading))
        if odf["moulages"]:
            add_table(odf["moulages"], ("Observation", "Constat"))
        else:
            elements.append(Paragraph(
                "Examen des moulages à renseigner par le praticien.", body))

        elements.append(Paragraph("03  Résumé diagnostique", heading))
        elements.append(Paragraph(
            escape(odf["resume_diagnostique"]) if odf["resume_diagnostique"]
            else "Synthèse diagnostique à renseigner par le praticien.",
            body))
        elements.append(Paragraph("04  Plan de traitement", heading))
        elements.append(Paragraph(
            escape(odf["plan_traitement"]) if odf["plan_traitement"]
            else "Plan de traitement à renseigner par le praticien.",
            body))
        if odf["clinical_alerts"]:
            elements.append(Paragraph(
                "Éléments cliniques nécessitant une attention particulière",
                heading))
            for alert in odf["clinical_alerts"]:
                elements.append(Paragraph(escape(str(alert)), body))
        draw_method = lambda canv, d: self.draw_static_elements(
            canv, d, config=config, user=user)
        doc.build(elements, onFirstPage=draw_method, onLaterPages=draw_method)
        return file_path
