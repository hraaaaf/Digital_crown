"""Four-part A4 clinical report presentation; no diagnosis or therapy is inferred.

This is a renderer for a backend-authoritative projection. It is not a clinical
signing engine: without a separately persisted, approved clinical record it emits
an unmistakably unsigned draft and never promotes the R15 stages to a diagnosis.
"""
from __future__ import annotations

from io import BytesIO
from math import isfinite
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import CondPageBreak, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LAYOUT_VERSION = "CLINICAL_FOUR_PART_A4_V1"
_AUTHORITY = "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO"
_CLINICIAN_EVIDENCE_VERSION = "CEPHALO_CLINICIAN_PDF_EVIDENCE_V1"
_DENTAL = ("U1", "L1", "IMPA", "INCIS", "SURPLOMB", "RECOUVREMENT", "OVERJET", "OVERBITE")
_SKELETAL = ("SNA", "SNB", "ANB", "WITS", "FMA", "GO-GN", "S-N", "A_B", "ABP", "SITUATION_A", "SITUATION_B")


def select_verified_measurements(projection: dict, *, max_per_group: int = 5) -> dict[str, list[tuple[str, str]]]:
    """Presentation-only selection; never extrapolates norms or clinical classes."""
    output: dict[str, list[tuple[str, str]]] = {"dental": [], "skeletal": []}
    if projection.get("authority") != _AUTHORITY or not projection.get("active_runtime_chain_verified"):
        return output
    seen: set[str] = set()
    for item in projection.get("measurements") or []:
        if not isinstance(item, dict) or item.get("availability_status") != "AVAILABLE":
            continue
        if item.get("scientific_source") != "EVIDENCE_GRAPH_V1":
            continue
        if item.get("requires_calibration") and not item.get("calibration_ref"):
            continue
        number = item.get("value")
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not isfinite(number):
            continue
        raw_id = item.get("measurement_id")
        unit = item.get("unit")
        if not isinstance(raw_id, str) or not isinstance(unit, str) or not raw_id or not unit:
            continue
        label = raw_id.rsplit(":", 1)[-1].replace("_", " ").strip()
        if len(label) > 46 or raw_id in seen:
            continue
        upper = label.upper()
        group = ("dental" if any(key in upper for key in _DENTAL) else
                 "skeletal" if any(key in upper for key in _SKELETAL) else None)
        if group and len(output[group]) < max_per_group:
            output[group].append((label, f"{number:g} {unit}"))
            seen.add(raw_id)
    return output


def _scoped_clinician_evidence(projection: dict, patient_id: object) -> dict:
    """Display only the server-produced case/revision-bound clinical snapshot.

    This is not document signing approval; every output remains BROUILLON.
    """
    evidence = projection.get("clinician_evidence")
    if (
        not isinstance(evidence, dict)
        or evidence.get("version") != _CLINICIAN_EVIDENCE_VERSION
        or not projection.get("active_runtime_chain_verified")
        or not projection.get("evidence_graph_present")
        or type(patient_id) is not int or patient_id <= 0
        or evidence.get("patient_id") != patient_id
        or evidence.get("analysis_id") != projection.get("analysis_id")
        or evidence.get("analysis_revision") != projection.get("analysis_revision")
        or evidence.get("report_signed") is not False
    ):
        return {"diagnoses": [], "plan": None}
    return evidence


def _verified_picture(raw: object, available_width: float, max_height_cm: float):
    """Only in-memory bytes delivered by the already-authorized backend loader."""
    if not isinstance(raw, bytes) or not raw:
        return None
    try:
        return Image(BytesIO(raw), width=min(available_width, 12.5 * cm),
                     height=max_height_cm * cm, kind="proportional")
    except Exception:
        return None


def render_four_part_a4(generator, vm, file_path: str, *, projection: dict, user=None, media=None):
    """Render the true A4/letterhead/QR via the existing BaseTemplate.

    No unpersisted diagnosis/plan is accepted from the legacy VM or media.
    The current R15 snapshot does not supply approved clinical text; do not
    claim a signed final report even if its historical COMPLETE flag is set.
    """
    if projection.get("authority") != _AUTHORITY or projection.get("layout_version") != LAYOUT_VERSION:
        raise ValueError("Four-part report requires authoritative backend projection")

    config = dict(vm.cabinet_config or {})
    descriptive = projection.get("document_kind") == "CEPH_A4_DESCRIPTIVE_APPROVAL_V1"
    if descriptive:
        # The generic document template contains visible placeholders. An
        # approved A4 must always name its actual authenticated practitioner
        # rather than print "Dr. Nom Prénom" or a fabricated Arabic doctor.
        doctor = str(vm.doctor_name or "").strip()
        if not doctor or doctor.lower() in {"dr. saninova", "docteur", "dr. nom prénom"}:
            raise ValueError("Nom du praticien responsable requis pour l'A4 descriptif")
        previous = config.get("header_lines_fr")
        if isinstance(previous, list) and previous:
            config["header_lines_fr"] = [doctor] + [str(value) for value in previous[1:] if value]
        else:
            config["header_lines_fr"] = [doctor, "Chirurgien-dentiste"]
        if not config.get("header_lines_ar"):
            # Empty visual block instead of the base template's fictitious
            # Arabic practitioner identity.
            config["header_lines_ar"] = [" "]
    if config.get("qr_code_type") in ("VALIDATION", "PAYMENT"):
        # No genuine archived document ID is yet available at rendering time.
        config["qr_code_enabled"] = False
    generator.update_active_fonts(config)
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily(generator.premium_font, normal=generator.premium_font,
                       bold=generator.premium_bold, italic=generator.premium_font,
                       boldItalic=generator.premium_bold)
    # Resolve the exact same cabinet theme tokens as BaseTemplate.draw_static_elements.
    # Never maintain an independent cephalometric PDF palette.
    primary = colors.HexColor(generator._get_val(config, "primary_color", "#003380"))
    secondary = colors.HexColor(generator._get_val(config, "secondary_color", "#666666"))
    accent = colors.HexColor(generator._get_val(config, "accent_color", "#0055AA"))
    width = A4[0]
    top, bottom, left, right = generator.get_document_margins(config, width)
    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=right,
                            leftMargin=left, topMargin=top, bottomMargin=bottom)
    available = width - left - right
    base_styles = getSampleStyleSheet()
    title = ParagraphStyle("DCCeph4Title", parent=base_styles["Heading1"],
        fontName=generator.premium_bold, fontSize=16, leading=19, alignment=TA_CENTER,
        textColor=primary, spaceAfter=9)
    section = ParagraphStyle("DCCeph4Section", parent=base_styles["Heading2"],
        fontName=generator.premium_bold, fontSize=11.5, leading=15,
        textColor=primary, spaceBefore=12, spaceAfter=6, keepWithNext=True)
    subhead = ParagraphStyle("DCCeph4Subhead", parent=base_styles["Heading3"],
        fontName=generator.premium_bold, fontSize=9.6, leading=13, textColor=accent,
        spaceBefore=6, spaceAfter=4, keepWithNext=True)
    body = ParagraphStyle("DCCeph4Body", parent=base_styles["Normal"],
        fontName=generator.premium_font, fontSize=9.0, leading=13, spaceAfter=6)
    muted = ParagraphStyle("DCCeph4Muted", parent=body, fontSize=8.1,
        leading=11.5, textColor=secondary)
    tbl_head = ParagraphStyle("DCCeph4TableHead", parent=muted,
        fontName=generator.premium_bold, textColor=colors.white)
    tbl_cell = ParagraphStyle("DCCeph4TableCell", parent=body, fontSize=8.3, leading=11,
        spaceAfter=0)

    elements = [
        Paragraph("BILAN CÉPHALOMÉTRIQUE DESCRIPTIF" if descriptive else "BILAN ORTHODONTIQUE", title),
        *([] if descriptive else [
            Paragraph("BROUILLON — NON SIGNÉ · Document de travail du praticien", muted),
        ]),
        Paragraph("Patient : <b>" + escape(str(vm.patient_nom)) + " " +
                  escape(str(vm.patient_prenom)) + "</b> · Date : " +
                  escape(str(vm.date_generation)), body),
    ]
    study_id = projection.get("analysis_id")
    revision = projection.get("analysis_revision")
    if (
        type(study_id) is int and study_id > 0
        and type(revision) is int and revision > 0
        and projection.get("active_runtime_chain_verified")
    ):
        # Human-readable study binding without exposing storage paths or
        # claiming that the associated clinical diagnosis has been signed.
        elements.append(Paragraph(
            "Étude céphalométrique n°" + str(study_id) +
            " · Révision " + str(revision), muted,
        ))

    def add_measurements(name: str, data: list[tuple[str, str]]):
        elements.append(Paragraph(name, subhead))
        if not data:
            elements.append(Paragraph("Mesures sélectionnées à confirmer sur l'étude.", muted))
            return
        rows = [[Paragraph("Mesure", tbl_head), Paragraph("Valeur", tbl_head)]]
        rows.extend([Paragraph(escape(label), tbl_cell), Paragraph(escape(value), tbl_cell)]
                    for label, value in data)
        table = Table(rows, colWidths=[0.60 * available, 0.40 * available], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 1), (-1, -1), 0.25, secondary),
        ]))
        elements.append(table)

    elements.append(Paragraph("I — CÉPHALOMÉTRIE ET TRACÉ", section))
    images = media if isinstance(media, dict) else {}
    radio = _verified_picture(images.get("radio_jpeg"), available, 5.6)
    if radio is not None:
        elements.append(KeepTogether([
            Paragraph("Téléradiographie de profil de l'étude", subhead), radio,
        ]))
        elements.append(Spacer(1, 0.1 * cm))
    # Only a clinician-verified, study-matched tracing could be included here.
    # No verified tracing payload is currently emitted by cephalo_pdf_media.
    elements.append(Paragraph("Tracé : à confirmer sur l'étude avant finalisation du bilan.", muted))
    selected = select_verified_measurements(projection)
    add_measurements("Analyse dento-alvéolaire", selected["dental"])
    add_measurements("Analyse squelettique", selected["skeletal"])

    if descriptive:
        # The candidate's bytes are shown BEFORE validation and archived unchanged
        # AFTER the authenticated clinician explicitly approves them. Therefore
        # no "signed" or "approved" claim may be printed inside these same bytes.
        # This strictly descriptive variant never renders diagnosis, treatment
        # selection, R11-R14, optional free text, or unverified patient media.
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            "Périmètre : restitution descriptive de mesures issues de l'étude "
            "scientifique versionnée, sans diagnostic ni proposition de traitement.", muted,
        ))
        elements.append(Paragraph(
            "Praticien responsable : " + escape(str(vm.doctor_name or "À renseigner")), body,
        ))
        stamp = str(config.get("nom_cabinet") or "").strip()
        if stamp:
            elements.append(Paragraph(
                "Cachet imprimé du cabinet : <b>" + escape(stamp[:200]) + "</b>", muted,
            ))
        else:
            # Never invent the presence or text of a professional stamp.
            elements.append(Paragraph(
                "Cachet professionnel non configuré — validation du document requise.", muted,
            ))
        elements.append(Paragraph(
            "Statut d'approbation et intégrité : vérifiables dans le dossier patient "
            "Digital Crown. Le PDF isolé n'atteste pas à lui seul sa validation.", muted,
        ))
        draw = lambda canvas, page: generator.draw_static_elements(
            canvas, page, config=config, user=user,
        )
        doc.build(elements, onFirstPage=draw, onLaterPages=draw)
        return file_path

    elements.append(Paragraph("II — EXAMEN DES MOULAGES ET DES IMAGES", section))
    elements.append(Paragraph(
        "L'examen des arcades, des rapports occlusaux et de la DDM par arcade "
        "sera consigné ici après validation clinique des moulages ou scans.", muted))
    # Only the authorized Media Core loader supplies these dated photo records.
    # Their metadata remains attached to the image in the PDF without exposing
    # opaque asset IDs, blob keys, or a second copy of the clinical media.
    photos = images.get("photos") or []
    if isinstance(photos, list):
        for group in ("Extra-buccales", "Intra-buccales"):
            cells = []
            for photo in photos[:8]:
                if not isinstance(photo, dict) or photo.get("group") != group:
                    continue
                if photo.get("timepoint") != "T0" or type(photo.get("asset_id")) is not int:
                    continue
                date = str(photo.get("captured_at") or "")
                if len(date) != 10 or date[2:3] != "/" or date[5:6] != "/":
                    continue
                picture = _verified_picture(photo.get("jpeg"), available / 4 - 0.2 * cm, 2.1)
                if picture is None:
                    continue
                label = escape(str(photo.get("label") or "Photographie clinique")[:65])
                caption = Paragraph(label + " · T0 · " + escape(date), muted)
                cells.append([picture, caption])
            if not cells:
                continue
            elements.append(Paragraph("Photographies " + group.lower(), subhead))
            column_width = available / 4
            for start in range(0, len(cells), 4):
                row = cells[start:start + 4]
                row.extend([""] * (4 - len(row)))
                gallery = Table([row], colWidths=[column_width] * 4)
                gallery.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                elements.append(gallery)

    # These fields are projected server-side only after a full typed-graph case
    # validation and matching clinician audit. Free client text is ignored.
    clinician = _scoped_clinician_evidence(projection, vm.patient_id)
    diagnoses = clinician.get("diagnoses") or []
    plan = clinician.get("plan")

    # Keep the diagnosis and the first lines of the treatment strategy on a
    # coherent sheet whenever the photo gallery nearly fills the first page.
    # Remaining long clinician text remains naturally multipage.
    elements.append(CondPageBreak(8.5 * cm))
    elements.append(Paragraph("III — BILAN DIAGNOSTIQUE ET DIAGNOSTIC FINAL", section))
    if diagnoses:
        elements.append(Paragraph(
            "Diagnostics consignés dans l'étude avec preuve de validation praticien "
            "— restitution en brouillon, hors signature de ce document.", muted,
        ))
        for item in diagnoses[:12]:
            if not isinstance(item, dict):
                continue
            statement = str(item.get("statement") or "").strip()
            if statement:
                elements.append(Paragraph("• " + escape(statement[:1500]), body))
    else:
        elements.append(Paragraph(
            "Synthèse des observations et diagnostic final à rédiger et confirmer "
            "par le praticien sur les preuves des parties I et II.", body))
        elements.append(Paragraph(
            "Aucun diagnostic automatique n'est produit à partir des mesures.", muted))

    elements.append(Paragraph("IV — PLAN DE TRAITEMENT", section))
    if isinstance(plan, dict) and diagnoses:
        elements.append(Paragraph(
            "Séquence consignée et auditée dans l'étude, reproduite comme brouillon "
            "sans signature du présent bilan.", muted,
        ))
        objectives = [o for o in plan.get("objectives", []) if isinstance(o, dict)]
        if objectives:
            elements.append(Paragraph("Objectifs cliniques", subhead))
            for objective in objectives[:12]:
                target = str(objective.get("target") or "").strip()
                criterion = str(objective.get("success_criterion") or "").strip()
                if target and criterion:
                    elements.append(Paragraph(
                        "• " + escape(target[:1000]) + " — " +
                        escape(criterion[:1000]), body,
                    ))
        phases = [p for p in plan.get("phases", []) if isinstance(p, dict)]
        if phases:
            elements.append(Paragraph("Phases et surveillance", subhead))
            for phase in phases[:12]:
                name = str(phase.get("title") or "").strip()
                if name:
                    elements.append(Paragraph("• " + escape(name[:600]), body))
                for field in ("procedures", "mechanics_or_appliances", "monitoring", "reassessment_criteria"):
                    for item in (phase.get(field) or [])[:8]:
                        elements.append(Paragraph("  " + escape(str(item)[:500]), muted))
        option_context = plan.get("option_context") if isinstance(plan.get("option_context"), dict) else {}
        for field, label in (
            ("benefits", "Bénéfices documentés"),
            ("limits", "Limites documentées"),
            ("risks", "Risques documentés"),
        ):
            values = option_context.get(field) or []
            if values:
                elements.append(Paragraph(label, subhead))
                for value in values[:8]:
                    elements.append(Paragraph("• " + escape(str(value)[:500]), body))
        if plan.get("retention"):
            elements.append(Paragraph("Contention", subhead))
            for item in plan["retention"][:8]:
                elements.append(Paragraph("• " + escape(str(item)[:500]), body))
    else:
        elements.append(Paragraph(
            "Objectifs, stratégie choisie, justification, alternatives et suivi : "
            "à renseigner et valider distinctement par le praticien.", body))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Praticien responsable : " +
        escape(str(vm.doctor_name or "À renseigner")) +
        " · Brouillon sans signature clinique.", muted))

    draw = lambda canvas, page: generator.draw_static_elements(
        canvas, page, config=config, user=user)
    doc.build(elements, onFirstPage=draw, onLaterPages=draw)
    return file_path
