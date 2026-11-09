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

        # Switch only for a server-generated typed PDF projection. Existing R17
        # renderer and its regression harness remain available for old snapshots.
        if (document.get("layout_version") == "CLINICAL_FOUR_PART_A4_V1"
                and document.get("authority") == "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO"):
            from backend.services.generators.cephalo_four_part_report import render_four_part_a4
            return render_four_part_a4(
                self, vm, file_path, projection=document, user=user, media=media,
            )

        # Official A4 and its preview must share the same ReportLab BaseTemplate
        # letterhead, branding, footer and QR renderer as every cabinet document.
        # The HTML renderer remains for contract tests, never a divergent output.
        if user is None and media is None:
            return self._generate_reportlab(vm, file_path, projection=document)
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
    def _pdf_method_label(method: Any) -> str:
        method_id = str(method or "").split(" v", 1)[0].strip().upper()
        return {
            "STEINER": "Steiner",
            "COM": "COM",
            "CRANIOM": "Craniométrie",
            "TWEED": "Tweed",
            "TWEED_MERRIFIELD": "Tweed–Merrifield",
            "MCNAMARA": "McNamara",
        }.get(method_id, "Méthode non précisée")

    @staticmethod
    def _pdf_measurement_value(value: Any) -> str:
        display = str(value)
        if display in {"NOT_COMPUTABLE", "MISSING", "UNAVAILABLE", "CALIBRATION_REQUIRED"}:
            return "Non calculable"
        return display

    @staticmethod
    def _pdf_stage_state(state: Any, *, complete: bool) -> str:
        status = str(state or "").upper()
        if not complete and status in {"VALIDATED", "APPROVED", "SIGNED", "COMPLETE"}:
            return "Non validé"
        return {
            "BLOCKED": "Non validé",
            "AWAITING_CLINICIAN": "En attente du praticien",
            "PENDING": "En attente",
            "EVALUABLE": "À examiner",
            "READY": "À examiner",
            "AVAILABLE": "Disponible, non validé",
            "VALIDATED": "Validé",
            "APPROVED": "Validé",
            "SIGNED": "Validé",
            "COMPLETE": "Validé",
        }.get(status, "Non validé")

    @staticmethod
    def _pdf_stage_summary(summary: Any) -> str:
        value = str(summary or "").strip()
        if not value:
            return ""
        technical_terms = (
            "R11", "R12", "R13", "R14", "SNAPSHOT",
            "SOURCE_LOCK", "SOURCE NON PERSIST", "AUTHORITATIVE",
            "NOT PERSISTED", "AUTHORITY UNAVAILABLE", "EVALUABLE",
        )
        if any(term in value.upper() for term in technical_terms):
            return "Éléments en attente de validation clinique."
        return value

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
        self.update_active_fonts(config)
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily(
            self.premium_font,
            normal=self.premium_font, bold=self.premium_bold,
            italic=self.premium_font, boldItalic=self.premium_bold,
        )
        p_color = colors.HexColor(config.get("primary_color") or "#003380")
        s_color = colors.HexColor(config.get("secondary_color") or "#64748B")
        styles = getSampleStyleSheet()
        title = ParagraphStyle(
            "CephA4Title", parent=styles["Heading1"], fontName=self.premium_bold, fontSize=17,
            textColor=p_color, alignment=TA_CENTER, spaceAfter=10,
        )
        h2 = ParagraphStyle(
            "CephA4Section", parent=styles["Heading2"], fontName=self.premium_bold, fontSize=12,
            textColor=p_color, spaceBefore=9, spaceAfter=6,
            keepWithNext=True,
        )
        h3 = ParagraphStyle(
            "CephA4Sub", parent=styles["Heading3"], fontName=self.premium_bold, fontSize=10,
            textColor=p_color, spaceBefore=8, spaceAfter=5,
            keepWithNext=True,
        )
        body = ParagraphStyle(
            "CephA4Body", parent=styles["Normal"], fontName=self.premium_font, fontSize=9,
            leading=13, textColor=colors.black, spaceAfter=5,
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
                "Étude Céphalo ID : " + escape(str(context.get("cephalo_source_analysis_id") or "NON VÉRIFIÉ"))
                + " — Révision : " + escape(str(context.get("cephalo_source_analysis_revision") or "NON VÉRIFIÉE"))
                + " — État : <b>" + ("Validé" if context["document_state"] == "COMPLETE" else "Non validé") + "</b>", small,
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
        # A non-validated document is marked above; internal gate details
        # remain in the server projection rather than in the print layout.

        # Patient media: only byte streams previously resolved by the authenticated
        # backend, never a client-supplied URL or arbitrary filesystem path.
        verified_media = media or {}
        radio = verified_media.get("radio_jpeg")
        photos = verified_media.get("photos") or []
        if radio or photos:
            elements.append(Paragraph("DOSSIER ICONOGRAPHIQUE", h2))
            if radio:
                elements.append(Paragraph("Téléradiographie de profil", h3))
                elements.append(Image(
                    BytesIO(radio),
                    width=min(available_width, 13.5 * cm),
                    height=6.0 * cm, kind="proportional",
                ))
                elements.append(Spacer(1, 0.2 * cm))
                elements.append(Paragraph(
                    "Tracé céphalométrique non disponible pour cette étude.", small,
                ))
            for group in ("Extra-buccales", "Intra-buccales"):
                selected = [p for p in photos if p.get("group") == group]
                if not selected:
                    continue
                photo_group = [Paragraph("Photographies " + group.lower(), h3)]
                # Four compact columns preserve full photo aspect ratios and
                # prevent an iconography-only continuation page.
                photo_columns = 4
                for index in range(0, len(selected), photo_columns):
                    trio = selected[index:index + photo_columns]
                    cell_width = available_width / photo_columns
                    cells = []
                    for photo in trio:
                        picture = Image(
                            BytesIO(photo["jpeg"]),
                            width=cell_width - 0.2 * cm, height=2.4 * cm,
                            kind="proportional",
                        )
                        cells.append([
                            picture,
                            Paragraph(escape(str(photo["label"])), small),
                        ])
                    # ReportLab tables wrap each cell as a vertical Flowable stack.
                    cells.extend([""] * (photo_columns - len(cells)))
                    table = Table([cells], colWidths=[cell_width] * photo_columns)
                    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
                    photo_group.extend([table, Spacer(1, 0.10 * cm)])
                # Do not leave a single intraoral view stranded on the next page.
                # Keep the full coherent group together; ReportLab moves it
                # intact to the following A4 page if necessary.
                elements.append(KeepTogether(photo_group))
        for missing in verified_media.get("media_unavailable") or []:
            elements.append(Paragraph(
                "Pièce image indisponible ou non vérifiable : " + escape(str(missing)), small,
            ))

        elements.append(Paragraph("I — ANALYSE CÉPHALOMÉTRIQUE", h2))
        elements.append(Paragraph(
            "Mesures de l'étude sélectionnée. Les valeurs non calculables sont signalées.", body,
        ))
        elements.append(Paragraph("Analyse dento-alvéolaire et analyse osseuse", h3))
        elements.append(Paragraph(
            "Le classement dento-alvéolaire et osseux reste à confirmer selon la méthode retenue.", small,
        ))
        # Paragraph cells wrap opaque authority identifiers inside the table:
        # ReportLab raw strings never wrap and can overlap the next column.
        table_body_style = ParagraphStyle(
            "CephA4TableCell", parent=small, fontName=self.premium_font,
            fontSize=6.5, leading=8.0, splitLongWords=True, spaceAfter=0,
        )
        table_header_style = ParagraphStyle(
            "CephA4TableHeader", parent=table_body_style, fontName=self.premium_bold,
            textColor=colors.white,
        )
        rows = [["Mesure", "Valeur / disponibilité", "Méthode"]]
        for item in context["measurements"]:
            rows.append([
                item["measurement_id"],
                self._pdf_measurement_value(item["value"]),
                self._pdf_method_label(item["method"]),
            ])
        if len(rows) == 1:
            rows.append(["Aucune mesure disponible", "Non calculable", "—"])
        widths = [0.34 * available_width, 0.26 * available_width,
                  0.40 * available_width]
        wrapped_rows = [
            [Paragraph(escape(str(value)), table_header_style if row_number == 0
                       else table_body_style) for value in row]
            for row_number, row in enumerate(rows)
        ]
        table = Table(wrapped_rows, repeatRows=1, colWidths=widths, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), p_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, s_color),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.extend([table, Spacer(1, 0.25 * cm)])

        if context["steiner_protocol"]:
            profile = context["steiner_protocol"]
            elements.append(Paragraph("Analyse protocolaire Steiner", h3))
            elements.append(Paragraph(
                "Références historiques affichées à titre comparatif uniquement; "
                "aucune classification clinique universelle n'est produite. "
                "Ce protocole demeure non vérifié sans validation clinique.", small,
            ))
            protocol_rows = [["Mesure", "Valeur", "Réf. hist.", "Écart réf.", "Statut"]]
            for item in profile["rows"]:
                protocol_rows.append([
                    item["label"], item["value"], item["reference"],
                    item["delta"], item["interpretation_status"],
                ])
            protocol_table = Table(protocol_rows, repeatRows=1, colWidths=[
                0.22 * available_width, 0.15 * available_width, 0.15 * available_width,
                0.15 * available_width, 0.33 * available_width,
            ])
            protocol_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), p_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, s_color),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(protocol_table)
        # Legacy Tweed remains renderable only with an explicit, backend-persisted
        # protocol selection; V1 COM/Steiner cannot silently include it.
        if context["tweed_merrifield_protocol"] and (projection or {}).get("selected_protocol") == "TWEED":
            tweed = context["tweed_merrifield_protocol"]
            elements.append(Paragraph("Analyse protocolaire Tweed–Merrifield", h3))
            elements.append(Paragraph(
                "Variante Digital Crown Po_anatomic-Or / Go-Me; "
                "aucune équivalence géométrique stricte avec Tweed 1954 n'est revendiquée. "
                "Références historiques à titre comparatif; aucune classification automatique.", small,
            ))
            protocol_rows = [["Mesure", "Valeur", "Profil", "Autorité", "Statut"]]
            for row in tweed["rows"]:
                protocol_rows.append([
                    row["label"], row["value"], row["profile_section"],
                    row["reference_authority"], row["interpretation_status"],
                ])
            protocol_table = Table(protocol_rows, repeatRows=1, colWidths=[
                0.20 * available_width, 0.14 * available_width, 0.20 * available_width,
                0.20 * available_width, 0.26 * available_width,
            ])
            protocol_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), p_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, s_color),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(protocol_table)

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
                    "<b>" + escape(str(stage.get("title") or "Diagnostic")) + "</b> — "
                    + escape(self._pdf_stage_state(
                        stage.get("presentation_state"),
                        complete=context["document_state"] == "COMPLETE",
                    )), body,
                ))
                if stage.get("summary"):
                    summary = self._pdf_stage_summary(stage["summary"])
                    if summary:
                        elements.append(Paragraph(escape(summary), body))
                for evidence_key, evidence_label in (
                    ("contradictions", "Contradictions"),
                    ("contraindications", "Contre-indications"),
                ):
                    if stage.get(evidence_key):
                        elements.append(Paragraph(
                            evidence_label + " : " + escape("; ".join(
                                str(value) for value in stage[evidence_key]
                            )), small,
                        ))
        if not stages.get("R11"):
            elements.append(Paragraph("Bilan diagnostique autoritaire indisponible.", body))

        elements.append(Paragraph("IV — PLAN DE TRAITEMENT", h2))
        for key in ("R13", "R14"):
            stage = stages.get(key)
            if stage:
                elements.append(Paragraph(
                    "<b>" + escape(str(stage.get("title") or "Traitement")) + "</b> — "
                    + escape(self._pdf_stage_state(
                        stage.get("presentation_state"),
                        complete=context["document_state"] == "COMPLETE",
                    )), body,
                ))
                if stage.get("summary"):
                    summary = self._pdf_stage_summary(stage["summary"])
                    if summary:
                        elements.append(Paragraph(escape(summary), body))
                for evidence_key, evidence_label in (
                    ("contradictions", "Contradictions"),
                    ("contraindications", "Contre-indications"),
                ):
                    if stage.get(evidence_key):
                        elements.append(Paragraph(
                            evidence_label + " : " + escape("; ".join(
                                str(value) for value in stage[evidence_key]
                            )), small,
                        ))
        if not context.get("clinical_validation_available"):
            elements.append(Paragraph(
                "Aucune option thérapeutique ni signature praticien n'est promue en "
                "l'absence de validation finale du praticien.", body,
            ))

        draw = lambda canvas, page: self.draw_static_elements(
            canvas, page, config=config, user=user,
        )
        doc.build(elements, onFirstPage=draw, onLaterPages=draw)
        return file_path
