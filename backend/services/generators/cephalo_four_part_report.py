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
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LAYOUT_VERSION = "CLINICAL_FOUR_PART_A4_V1"
_AUTHORITY = "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO"
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
    if config.get("qr_code_type") in ("VALIDATION", "PAYMENT"):
        # No genuine archived document ID is yet available at rendering time.
        config["qr_code_enabled"] = False
    generator.update_active_fonts(config)
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily(generator.premium_font, normal=generator.premium_font,
                       bold=generator.premium_bold, italic=generator.premium_font,
                       boldItalic=generator.premium_bold)
    primary = colors.HexColor(config.get("primary_color") or "#003380")
    secondary = colors.HexColor(config.get("secondary_color") or "#64748B")
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
        fontName=generator.premium_bold, fontSize=9.6, leading=13, textColor=primary,
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
        Paragraph("BILAN ORTHODONTIQUE", title),
        Paragraph("BROUILLON — NON SIGNÉ · Document de travail du praticien", muted),
        Paragraph("Patient : <b>" + escape(str(vm.patient_nom)) + " " +
                  escape(str(vm.patient_prenom)) + "</b> · Date : " +
                  escape(str(vm.date_generation)), body),
    ]

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

    elements.append(Paragraph("II — EXAMEN DES MOULAGES ET DES IMAGES", section))
    elements.append(Paragraph(
        "L'examen des arcades, des rapports occlusaux et de la DDM par arcade "
        "sera consigné ici après validation clinique des moulages ou scans.", muted))
    photos = images.get("photos") or []
    if isinstance(photos, list):
        for photo in photos[:8]:
            if not isinstance(photo, dict):
                continue
            picture = _verified_picture(photo.get("jpeg"), available * 0.5, 2.1)
            if picture is not None:
                label = escape(str(photo.get("label") or "Photographie clinique"))
                elements.append(KeepTogether([picture, Paragraph(label, muted)]))

    elements.append(Paragraph("III — BILAN DIAGNOSTIQUE ET DIAGNOSTIC FINAL", section))
    elements.append(Paragraph(
        "Synthèse des observations et diagnostic final à rédiger et confirmer "
        "par le praticien sur les preuves des parties I et II.", body))
    elements.append(Paragraph("Aucun diagnostic automatique n'est produit à partir des mesures.", muted))

    elements.append(Paragraph("IV — PLAN DE TRAITEMENT", section))
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
