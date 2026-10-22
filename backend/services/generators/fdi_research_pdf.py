"""LOT05/J10G - Standalone research-only panoramic FDI report PDF (not a clinic route).

Uses ReportLab already present in Digital Crown. No model loading, database writes,
patient lookup, network, or in-app activation. Caller provides explicit, reviewed
tooth observations and manually chosen acts. This cannot certify clinical safety.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import math
from pathlib import Path
import re
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from PIL import Image, UnidentifiedImageError

VERSION = "digital-crown-panoramic-fdi-pdf-research-v1"
FDI_CODES = frozenset(str(10 * q + tooth) for q in (1, 2, 3, 4) for tooth in range(1, 9))
SAFE_TEXT_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
MAX_IMAGE_BYTES = 20_000_000
MAX_IMAGE_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = min(Image.MAX_IMAGE_PIXELS or MAX_IMAGE_PIXELS, MAX_IMAGE_PIXELS)


class FDIReportError(ValueError):
    """Input is unsuitable for a signed or unsigned FDI research report."""


def _label(value: Any, key: str, *, max_len: int = 700, required: bool = True) -> str:
    if not isinstance(value, str) or SAFE_TEXT_RE.search(value):
        raise FDIReportError(f"invalid_{key}")
    value = value.strip()
    if len(value) > max_len or (required and not value):
        raise FDIReportError(f"invalid_{key}")
    return value


def _box(value: Any) -> tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4 or any(
        isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) for x in value
    ):
        raise FDIReportError("invalid_tooth_box")
    x1, y1, x2, y2 = value
    if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        raise FDIReportError("out_of_frame_tooth_box")
    return float(x1), float(y1), float(x2), float(y2)


def validate_report_data(data: Any) -> dict:
    if not isinstance(data, dict) or data.get("schema") != VERSION:
        raise FDIReportError("invalid_report_schema")
    clinic = data.get("clinic")
    patient = data.get("patient")
    exam = data.get("exam")
    reviewer = data.get("reviewer")
    if not all(isinstance(x, dict) for x in (clinic, patient, exam, reviewer)):
        raise FDIReportError("missing_research_report_identity")
    identities = {
        "clinic": _label(clinic.get("name"), "clinic"),
        "patient": _label(patient.get("display_name"), "patient"),
        "record": _label(patient.get("record_ref"), "record_ref"),
        "exam_date": _label(exam.get("date"), "exam_date", max_len=20),
        "exam_id": _label(exam.get("reference"), "exam_ref", max_len=80),
        "reviewer": _label(reviewer.get("display_name"), "reviewer"),
    }
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", identities["exam_date"]):
        raise FDIReportError("invalid_exam_date")
    from datetime import date
    try:
        date.fromisoformat(identities["exam_date"])
    except ValueError as exc:
        raise FDIReportError("invalid_exam_date") from exc
    if data.get("clinical_status") != "RESEARCH_ONLY_NOT_SAVED_TO_PATIENT":
        raise FDIReportError("clinical_activation_not_authorized")
    approved = data.get("clinician_review_confirmed") is True
    signed_at = reviewer.get("reviewed_at")
    if approved:
        identities["reviewed_at"] = _label(signed_at, "reviewed_at", max_len=40)
    elif signed_at not in (None, ""):
        raise FDIReportError("review_timestamp_without_review")
    else:
        identities["reviewed_at"] = ""
    teeth = data.get("teeth")
    if not isinstance(teeth, list) or len(teeth) > 32:
        raise FDIReportError("invalid_teeth_collection")
    if approved and not teeth:
        raise FDIReportError("cannot_approve_without_confirmed_tooth")
    normalized, seen = [], set()
    for raw in teeth:
        if not isinstance(raw, dict) or raw.get("confirmed") is not True:
            raise FDIReportError("unconfirmed_tooth_in_report")
        fdi = raw.get("fdi")
        if not isinstance(fdi, str) or fdi not in FDI_CODES or fdi in seen:
            raise FDIReportError("invalid_or_duplicate_permanent_fdi")
        seen.add(fdi)
        bbox = _box(raw.get("bbox"))
        notes = raw.get("practitioner_observations")
        acts = raw.get("manually_selected_acts")
        if not isinstance(notes, list) or not isinstance(acts, list) or len(notes) > 20 or len(acts) > 20:
            raise FDIReportError("invalid_manual_observations")
        if any(not isinstance(a, dict) or a.get("selected_by_clinician") is not True for a in acts):
            raise FDIReportError("unverified_auto_act_forbidden")
        normalized.append({
            "fdi": fdi, "bbox": bbox,
            "notes": [_label(text, "manual_observation", max_len=350) for text in notes],
            "acts": [(
                _label(a.get("specialty"), "manual_specialty", max_len=75),
                _label(a.get("label"), "manual_act", max_len=125)
            ) for a in acts],
        })
    identities["teeth"] = sorted(normalized, key=lambda t: (int(t["fdi"][0]), int(t["fdi"][1])))
    identities["summary"] = _label(data.get("practitioner_summary", ""), "summary", max_len=2000, required=False)
    identities["review_confirmed"] = approved
    return identities


def _image_bytes(data: bytes) -> tuple[bytes, tuple[int, int]]:
    if not isinstance(data, bytes) or not data or len(data) > MAX_IMAGE_BYTES:
        raise FDIReportError("invalid_local_research_image_bytes")
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in ("PNG", "JPEG", "WEBP") or image.width * image.height > MAX_IMAGE_PIXELS:
                raise FDIReportError("invalid_image_format_or_dimensions")
            if not (64 <= image.width <= 10000 and 64 <= image.height <= 10000):
                raise FDIReportError("invalid_image_dimensions")
            image.load()
            rgb = image.convert("RGB")
            size = rgb.size
            out = BytesIO()
            rgb.save(out, format="PNG")
            return out.getvalue(), size
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise FDIReportError("invalid_or_corrupt_research_image") from exc


class AnnotatedPanoramic(Flowable):
    def __init__(self, image: bytes, dimensions: tuple[int, int], teeth: list, available_width: float):
        super().__init__()
        self.image = image
        self.dimensions = dimensions
        self.teeth = teeth
        self.width = available_width
        self.height = available_width * dimensions[1] / dimensions[0]
        if self.height > 240:
            self.height = 240
            self.width = 240 * dimensions[0] / dimensions[1]

    def draw(self):
        self.canv.drawImage(ImageReader(BytesIO(self.image)), 0, 0,
                            width=self.width, height=self.height, preserveAspectRatio=False)
        for t in self.teeth:
            x1, y1, x2, y2 = t["bbox"]
            self.canv.setStrokeColor(colors.HexColor("#08798a"))
            self.canv.setLineWidth(1.2)
            self.canv.rect(x1 * self.width, (1 - y2) * self.height,
                           (x2 - x1) * self.width, (y2-y1) * self.height, stroke=1, fill=0)
            label_x = x1 * self.width
            label_y = min(self.height - 10, (1-y1) * self.height + 3)
            self.canv.setFillColor(colors.HexColor("#0b1522"))
            self.canv.roundRect(label_x-1, label_y-2, 19, 11, 2, fill=1, stroke=0)
            self.canv.setFillColor(colors.white)
            self.canv.setFont("Helvetica-Bold", 9)
            self.canv.drawString(label_x+2, label_y, t["fdi"])


def _patient_safe(text: str) -> str:
    return escape(text).replace("\n", "<br/>")


def render_research_pdf(data: dict, image_bytes: bytes) -> bytes:
    """Return a PDF in memory. No database, filesystem, patient API or model invocation."""
    normalized = validate_report_data(data)
    pixels, dims = _image_bytes(image_bytes)
    out = BytesIO()
    page_w, _ = A4
    navy = colors.HexColor("#103454")
    teal = colors.HexColor("#08798a")
    muted = colors.HexColor("#52677a")
    style_title = ParagraphStyle("FDIPdfTitle", fontName="Helvetica-Bold", fontSize=18,
                                 leading=23, textColor=navy, spaceAfter=9)
    section = ParagraphStyle("FDIPdfSection", fontName="Helvetica-Bold", fontSize=12,
                             leading=15, textColor=navy, spaceBefore=13, spaceAfter=7)
    body = ParagraphStyle("FDIPdfBody", fontName="Helvetica", fontSize=9.2,
                          leading=13.5, textColor=navy)
    subdued = ParagraphStyle("FDIPdfSubdued", parent=body, fontSize=8, textColor=muted)
    warning = ParagraphStyle("FDIPdfWarning", parent=body, textColor=colors.HexColor("#a04b18"))
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=42, leftMargin=42,
                            topMargin=45, bottomMargin=42, title="Compte rendu panoramique FDI - Recherche")
    w = page_w - 84
    items = [
        Paragraph("COMPTE RENDU PANORAMIQUE", style_title),
        Paragraph("Prototype de recherche — document non destiné au soin, ni au dossier patient.", warning),
        Spacer(1, 13),
    ]
    infos = [
        ["CABINET", normalized["clinic"], "EXAMEN", normalized["exam_id"]],
        ["PATIENT", normalized["patient"], "DATE", normalized["exam_date"]],
        ["DOSSIER (DEMO)", normalized["record"], "PRATICIEN", normalized["reviewer"]],
    ]
    table_rows = []
    for row in infos:
        table_rows.append([Paragraph(_patient_safe(cell), subdued if i % 2 == 0 else body)
                           for i, cell in enumerate(row)])
    t = Table(table_rows, colWidths=[67, w * .37, 65, w * .63 - 132], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#eef3f7")),
        ("LINEBELOW",(0,-1),(-1,-1),.7,teal),
        ("TOPPADDING",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    items.append(t)
    items.append(Paragraph("1 · RADIOGRAPHIE ANNOTÉE", section))
    items.append(Paragraph("Seules les positions explicitement confirmées sont repérées. "
                           "Une dent non listée n'est pas déclarée absente ou saine.", subdued))
    items.append(Spacer(1, 9))
    items.append(AnnotatedPanoramic(pixels, dims, normalized["teeth"], w))
    items.append(Paragraph("2 · DENTS VÉRIFIÉES ET CONSTATATIONS DU PRATICIEN", section))
    if not normalized["teeth"]:
        items.append(Paragraph("Aucune dent confirmée. Aucun résultat clinique présenté.", subdued))
    else:
        cells = [[Paragraph("<b>FDI</b>", subdued), Paragraph("<b>Observations documentées</b>", subdued),
                  Paragraph("<b>Actes sélectionnés manuellement</b>", subdued)]]
        for t in normalized["teeth"]:
            notes = "; ".join(t["notes"]) if t["notes"] else "Aucune observation saisie"
            acts = "; ".join(f"{specialty} : {label}" for specialty, label in t["acts"]) if t["acts"] else "Aucun acte associé"
            cells.append([Paragraph(t["fdi"], body), Paragraph(_patient_safe(notes), body),
                          Paragraph(_patient_safe(acts), body)])
        tbl = Table(cells, colWidths=[45, w * .48, w * .52 - 45], repeatRows=1, hAlign="LEFT")
        tbl.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"), ("LINEBELOW",(0,0),(-1,0),1,teal),
            ("LINEBELOW",(0,1),(-1,-1),.3,colors.HexColor("#cbd5e1")),
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e4f2f3")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f7fafc")]),
            ("TOPPADDING",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8),
        ]))
        items.append(tbl)
    items.append(Paragraph("3 · SYNTHÈSE DU PRATICIEN", section))
    items.append(Paragraph(_patient_safe(normalized["summary"]) if normalized["summary"]
                           else "Aucune synthèse rédigée par le praticien.", body))
    items.append(Spacer(1, 16))
    if normalized["review_confirmed"]:
        note = f"Relecture déclarée par {_patient_safe(normalized['reviewer'])}, le {_patient_safe(normalized['reviewed_at'])}."
    else:
        note = "RELECTURE NON FINALISÉE — DOCUMENT DE TRAVAIL."
    items.append(Paragraph(note, warning))

    def page(canvas, pdfdoc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(muted)
        canvas.drawCentredString(page_w / 2, 23,
            f"Digital Crown • Recherche uniquement • Non archivé au dossier • page {pdfdoc.page}")
        canvas.restoreState()

    doc.build(items, onFirstPage=page, onLaterPages=page)
    return out.getvalue()
