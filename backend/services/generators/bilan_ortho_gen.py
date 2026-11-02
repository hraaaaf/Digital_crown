import os
import logging
from typing import Optional, Any
from datetime import datetime
from secrets import token_hex
from xml.sax.saxutils import escape
from jinja2 import Environment, FileSystemLoader, select_autoescape

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
        user: Any = None,
        media: Optional[dict[str, Any]] = None,
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

        # Official A4 and its preview must share the same ReportLab BaseTemplate
        # letterhead, branding, footer and QR renderer as every cabinet document.
        # The HTML renderer remains for contract tests, never a divergent output.
        return self._generate_reportlab(vm, file_path, projection=document, user=user, media=media)

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
        protocol_profiles = dict(projection.get("protocol_profiles") or {})
        steiner_profile = dict(protocol_profiles.get("steiner") or {})
        steiner_rows = [self._protocol_row_display(row) for row in steiner_profile.get("rows", [])]
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
            })
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
            "cephalo_source_patient_id": projection.get("patient_id"),
            "cephalo_source_analysis_id": projection.get("analysis_id"),
            "cephalo_source_analysis_revision": projection.get("analysis_revision"),
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
            "steiner_protocol": {
                "protocol_profile_id": steiner_profile.get("protocol_profile_id"),
                "source_lock_status": (steiner_profile.get("source_lock_gate") or {}).get("status"),
                "final_gate_status": (steiner_profile.get("final_gate") or {}).get("status"),
                "norm_set": dict(steiner_profile.get("norm_set") or {}),
                "rows": steiner_rows,
            } if steiner_profile else None,
            "tweed_merrifield_protocol": {
                "protocol_profile_id": tweed_merrifield_profile.get("protocol_profile_id"),
                "source_lock_status": (tweed_merrifield_profile.get("source_lock_gate") or {}).get("status"),
                "final_gate_status": (tweed_merrifield_profile.get("final_gate") or {}).get("status"),
                "rows": tweed_merrifield_rows,
                "reference_contexts": list(tweed_merrifield_profile.get("reference_contexts") or []),
            } if tweed_merrifield_profile else None,
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
        user: Any = None,
        media: Optional[dict[str, Any]] = None,
    ):
        """Official A4 report. Source-locked content, shared cabinet letterhead."""
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
        from backend.services.generators.document_typography import short_label

        context = self._shared_context(vm, projection or {})
        context["measurements"] = [
            {**item, "measurement_id": short_label(item["measurement_id"].rsplit(":", 1)[-1])}
            for item in context["measurements"]
        ]
        config = dict(vm.cabinet_config or {})
        # A validation/payment QR without an issued document ID would link to
        # DOC-TEMP, falsely suggesting an official verified document. Never do so.
        if config.get("qr_code_type") in {"VALIDATION", "PAYMENT"}:
            config["qr_code_enabled"] = False
        p_color = colors.HexColor(config.get("primary_color") or "#003380")
        s_color = colors.HexColor(config.get("secondary_color") or "#64748B")
        styles = getSampleStyleSheet()
        title = ParagraphStyle(
            "CephA4Title", parent=styles["Heading1"], fontSize=17,
            textColor=p_color, alignment=TA_CENTER, spaceAfter=10,
        )
        h2 = ParagraphStyle(
            "CephA4Section", parent=styles["Heading2"], fontSize=12,
            textColor=p_color, spaceBefore=12, spaceAfter=7,
            keepWithNext=True,
        )
        h3 = ParagraphStyle(
            "CephA4Sub", parent=styles["Heading3"], fontSize=10,
            textColor=p_color, spaceBefore=8, spaceAfter=5,
            keepWithNext=True,
        )
        body = ParagraphStyle(
            "CephA4Body", parent=styles["Normal"], fontSize=9,
            leading=13, textColor=colors.HexColor("#1f2937"), spaceAfter=5,
        )
        small = ParagraphStyle(
            "CephA4Small", parent=body, fontSize=7.5,
            leading=10.5, textColor=s_color,
        )
        page_width = A4[0]
        m_top, m_bottom, m_left, m_right = self.get_document_margins(config, page_width)
        doc = SimpleDocTemplate(
            file_path, pagesize=A4, rightMargin=m_right, leftMargin=m_left,
            topMargin=m_top, bottomMargin=m_bottom,
        )
        available_width = page_width - m_left - m_right
        elements = [
            Paragraph("BILAN ORTHODONTIQUE", title),
            Paragraph(
                "Patient : <b>" + escape(str(vm.patient_nom).upper()) + " "
                + escape(str(vm.patient_prenom).capitalize()) + "</b> — "
                + "Âge : " + escape(str(vm.patient_age)) + " ans — "
                + "Date : " + escape(str(context["date_analyse"])), body,
            ),
            Paragraph(
                "Étude céphalo : " + escape(str(context.get("cephalo_source_analysis_id") or "NON VÉRIFIÉ"))
                + " — Révision : " + escape(str(context.get("cephalo_source_analysis_revision") or "NON VÉRIFIÉE"))
                + " — État : <b>" + escape(str(context["document_state"])) + "</b>", small,
            ),
        ]
        if context["document_state"] != "COMPLETE":
            elements.append(Paragraph(
                "<b>DOCUMENT CLINIQUE INCOMPLET — NON SIGNÉ.</b> "
                "Les observations et mesures non validées ne constituent ni un diagnostic "
                "ni un plan thérapeutique définitif.", body,
            ))
        if vm.is_pre_bilan:
            elements.append(Paragraph("PRÉ-BILAN — aperçu/document de travail non archivé.", small))
        if context["clinical_validation_reason"]:
            elements.append(Paragraph(escape(str(context["clinical_validation_reason"])), small))

        # Patient media: only byte streams previously resolved by the authenticated
        # backend, never a client-supplied URL or arbitrary filesystem path.
        verified_media = media or {}
        radio = verified_media.get("radio_jpeg")
        photos = verified_media.get("photos") or []
        if radio or photos:
            elements.append(Paragraph("DOSSIER ICONOGRAPHIQUE", h2))
            if radio:
                elements.append(Paragraph("Téléradiographie de profil — image source", h3))
                elements.append(Image(
                    BytesIO(radio),
                    width=min(available_width, 13.5 * cm),
                    height=9 * cm, kind="proportional",
                ))
                elements.append(Spacer(1, 0.2 * cm))
                elements.append(Paragraph(
                    "Tracé anatomique : non inclus tant qu'un rendu source-locké, "
                    "persisté et concordant avec cette révision n'est pas disponible.", small,
                ))
            for group in ("Extra-buccales", "Intra-buccales"):
                selected = [p for p in photos if p.get("group") == group]
                if not selected:
                    continue
                elements.append(Paragraph("Photographies " + group.lower(), h3))
                for index in range(0, len(selected), 3):
                    trio = selected[index:index + 3]
                    cell_width = available_width / 3
                    cells = []
                    for photo in trio:
                        picture = Image(
                            BytesIO(photo["jpeg"]),
                            width=cell_width - 0.35 * cm, height=4.3 * cm,
                            kind="proportional",
                        )
                        cells.append([
                            picture,
                            Paragraph(escape(str(photo["label"])), small),
                        ])
                    # ReportLab tables wrap each cell as a vertical Flowable stack.
                    cells.extend([""] * (3 - len(cells)))
                    table = Table([cells], colWidths=[cell_width] * 3)
                    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
                    elements.extend([table, Spacer(1, 0.15 * cm)])
        for missing in verified_media.get("media_unavailable") or []:
            elements.append(Paragraph(
                "Pièce image indisponible ou non vérifiable : " + escape(str(missing)), small,
            ))

        elements.append(Paragraph("I — ANALYSE CÉPHALOMÉTRIQUE", h2))
        elements.append(Paragraph(
            "Mesures et disponibilités issues du graphe scientifique de l'étude "
            "sélectionnée. Les résultats non calculables sont explicitement signalés.", body,
        ))
        elements.append(Paragraph("Analyse dento-alvéolaire et analyse osseuse", h3))
        elements.append(Paragraph(
            "La séparation dento-alvéolaire / osseuse dépend du classement scientifique "
            "de la méthode retenue ; aucune mesure n'est reclassée arbitrairement.", small,
        ))
        rows = [["Mesure", "Valeur / disponibilité", "Méthode", "Source"]]
        for item in context["measurements"]:
            rows.append([
                item["measurement_id"], item["value"], item["method"], item["source"],
            ])
        if len(rows) == 1:
            rows.append(["Aucune mesure typée autoritaire disponible", "NOT_COMPUTABLE", "—", "—"])
        widths = [0.35 * available_width, 0.26 * available_width,
                  0.20 * available_width, 0.19 * available_width]
        table = Table(rows, repeatRows=1, colWidths=widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), p_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 0), (-1, -1), 7.2),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.extend([table, Spacer(1, 0.25 * cm)])

        if context["steiner_protocol"]:
            profile = context["steiner_protocol"]
            elements.append(Paragraph("Analyse Steiner — registre source", h3))
            elements.append(Paragraph(
                "Références historiques contextuelles, sans classification patient universelle.", small,
            ))
            protocol_rows = [["Mesure", "Valeur", "Réf. hist.", "Écart", "Statut"]]
            for item in profile["rows"]:
                protocol_rows.append([
                    item["label"], item["value"], item["reference"],
                    item["delta"], item["interpretation_status"],
                ])
            t = Table(protocol_rows, repeatRows=1, colWidths=[
                0.22 * available_width, 0.15 * available_width, 0.15 * available_width,
                0.15 * available_width, 0.33 * available_width,
            ])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), p_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(t)
        # Do not insert unrelated comparison protocols into a V1 COM/Steiner PDF
        # without a persisted authoritative protocol selection.

        elements.append(Paragraph("II — EXAMEN DES MOULAGES", h2))
        elements.append(Paragraph(
            "ED, EN et DDM par arcade : en attente de projection serveur autoritaire "
            "liée à cette étude et à sa révision. Une donnée absente n'est jamais 0 mm.", body,
        ))
        elements.append(Paragraph("III — BILAN DIAGNOSTIQUE", h2))
        stages = {stage.get("stage_id"): stage for stage in context["stages"]}
        for key in ("R11", "R12"):
            stage = stages.get(key)
            if stage:
                elements.append(Paragraph(
                    "<b>" + escape(str(stage.get("title") or key)) + "</b> — "
                    + escape(str(stage.get("presentation_state") or "BLOCKED")), body,
                ))
                if stage.get("summary"):
                    elements.append(Paragraph(escape(str(stage["summary"])), body))
        if not stages.get("R11"):
            elements.append(Paragraph("Bilan diagnostique autoritaire indisponible.", body))

        elements.append(Paragraph("IV — PLAN DE TRAITEMENT", h2))
        for key in ("R13", "R14"):
            stage = stages.get(key)
            if stage:
                elements.append(Paragraph(
                    "<b>" + escape(str(stage.get("title") or key)) + "</b> — "
                    + escape(str(stage.get("presentation_state") or "BLOCKED")), body,
                ))
                if stage.get("summary"):
                    elements.append(Paragraph(escape(str(stage["summary"])), body))
        if not context.get("clinical_validation_available"):
            elements.append(Paragraph(
                "Aucune option thérapeutique ni signature praticien n'est promue en "
                "l'absence de validation R14 persistée.", body,
            ))

        elements.append(Paragraph("ANNEXE — TRAÇABILITÉ SCIENTIFIQUE", h2))
        for stage in context["stages"]:
            elements.append(Paragraph(
                "<b>" + escape(str(stage.get("stage_id") or ""))
                + " — " + escape(str(stage.get("title") or "")) + "</b> : "
                + escape(str(stage.get("presentation_state") or "BLOCKED")), small,
            ))
            for heading, key in (
                ("Blocages", "blocking_gates"),
                ("Données manquantes", "missing_data_refs"),
                ("Contradictions", "contradictions"),
                ("Contre-indications", "contraindications"),
            ):
                if stage.get(key):
                    elements.append(Paragraph(
                        heading + " : " + escape("; ".join(str(x) for x in stage[key])), small,
                    ))
            if stage.get("provenance"):
                elements.append(Paragraph(
                    "Provenance : " + escape("; ".join(
                        str(p.get("label")) + " : " + str(p.get("value"))
                        for p in stage["provenance"]
                    )), small,
                ))
        if context["blocking_gates"]:
            elements.append(Paragraph(
                "Blocages globaux : " + escape("; ".join(str(x) for x in context["blocking_gates"])), small,
            ))

        draw = lambda canvas, page: self.draw_static_elements(
            canvas, page, config=config, user=user,
        )
        doc.build(elements, onFirstPage=draw, onLaterPages=draw)
        return file_path
