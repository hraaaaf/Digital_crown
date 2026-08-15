# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime, date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5, A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE, PinnedCloture, PageCounter
from backend.services.generators.document_layout_safety import join_unbreakable


_ALLOWED_PAGE_SIZES = {"A4": A4, "A5": A5}
_ALLOWED_ALIGNMENTS = {
    "left": TA_LEFT,
    "center": TA_CENTER,
    "right": TA_RIGHT,
    "justify": TA_JUSTIFY,
}
_ALLOWED_INLINE_TOKEN = re.compile(
    r'(<b>|</b>|<i>|</i>|<u>|</u>|<font\s+size\s*=\s*["\']16["\']\s*>|</font>)',
    re.IGNORECASE,
)
_FILENAME_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _field_was_explicitly_provided(data, field_name: str) -> bool:
    fields_set = getattr(data, "model_fields_set", None)
    if fields_set is None:
        return True
    return field_name in fields_set


def _normalize_and_validate_libre_data(data):
    """Fail closed on direct API calls and normalize non-clinical layout options."""
    if not _field_was_explicitly_provided(data, "titre"):
        raise ValueError("Le titre du document libre doit être saisi explicitement.")
    if not _field_was_explicitly_provided(data, "contenu"):
        raise ValueError("Le contenu du document libre doit être saisi explicitement.")

    title = str(getattr(data, "titre", "") or "").strip()
    content = str(getattr(data, "contenu", "") or "")
    if not title:
        raise ValueError("Le titre du document libre est requis.")
    if not content.strip():
        raise ValueError("Le contenu du document libre est requis.")
    if len(title) > 200:
        raise ValueError("Le titre du document libre ne peut pas dépasser 200 caractères.")
    if len(content) > 100_000:
        raise ValueError("Le contenu du document libre est trop volumineux.")

    page_size = str(getattr(data, "page_size", "A5") or "A5").upper()
    if page_size not in _ALLOWED_PAGE_SIZES:
        raise ValueError("Le format du document libre doit être A4 ou A5.")

    alignment = str(getattr(data, "alignment", "justify") or "justify").lower()
    if alignment not in _ALLOWED_ALIGNMENTS:
        raise ValueError("L'alignement du document libre est invalide.")

    custom_patient = str(getattr(data, "custom_patient", "") or "").strip()
    custom_date = str(getattr(data, "custom_date", "") or "").strip()
    if len(custom_patient) > 500:
        raise ValueError("Le destinataire du document libre est trop long.")
    if len(custom_date) > 120:
        raise ValueError("La date/le lieu personnalisé du document libre est trop long.")

    data.titre = title
    data.contenu = content
    data.page_size = page_size
    data.alignment = alignment
    data.custom_patient = custom_patient or None
    data.custom_date = custom_date or None
    return data


def _safe_pdf_text(value) -> str:
    return escape(str(value or ""))


def _sanitize_inline_markup(value) -> str:
    """Keep only toolbar-supported inline markup and escape everything else.

    Unbalanced supported tags are made safe by escaping mismatched closes and
    auto-closing remaining opens. This prevents malformed ReportLab Paragraph XML.
    """
    text = str(value or "")
    parts = _ALLOWED_INLINE_TOKEN.split(text)
    stack: list[str] = []
    output: list[str] = []

    for part in parts:
        if not part:
            continue
        if not _ALLOWED_INLINE_TOKEN.fullmatch(part):
            output.append(escape(part))
            continue

        lowered = part.lower().strip()
        is_close = lowered.startswith("</")
        if lowered.startswith("<font"):
            tag_name = "font"
            canonical = '<font size="16">'
        elif lowered == "</font>":
            tag_name = "font"
            canonical = "</font>"
        else:
            tag_name = lowered.replace("<", "").replace(">", "").replace("/", "")
            canonical = f"</{tag_name}>" if is_close else f"<{tag_name}>"

        if is_close:
            if stack and stack[-1] == tag_name:
                stack.pop()
                output.append(canonical)
            else:
                output.append(escape(part))
        else:
            stack.append(tag_name)
            output.append(canonical)

    while stack:
        output.append(f"</{stack.pop()}>")
    return "".join(output)


def _safe_filename_component(value: str, fallback: str = "DOCUMENT") -> str:
    value = _FILENAME_UNSAFE.sub("_", str(value or ""))
    value = re.sub(r"\s+", "_", value.strip())
    value = re.sub(r"_+", "_", value).strip("._ ")
    return (value[:80] or fallback)


def _coerce_document_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today()


def _config_owner_id(user, fallback_user_id: int) -> int:
    if user is None:
        return fallback_user_id
    getter = getattr(user, "get_employer_id", None)
    if callable(getter):
        return getter()
    return getattr(user, "employer_id", None) or getattr(user, "id", fallback_user_id)


class LibreGenerator:
    def __init__(self, output_dir="static/documents"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()

    def _calculate_age(self, born, reference_date: date | None = None):
        if not born:
            return None
        ref_date = reference_date or date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return ref_date.year - birth.year - ((ref_date.month, ref_date.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, titre):
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")
        save_dir = os.path.join(self.output_dir, now.strftime("%Y"), now.strftime("%m"))
        os.makedirs(save_dir, exist_ok=True)

        safe_titre = _safe_filename_component(titre, "DOCUMENT")[:30]
        patient_label = f"{getattr(patient, 'nom', '')}_{getattr(patient, 'prenom', '')}"
        safe_name = _safe_filename_component(patient_label, "PATIENT")
        filename = f"LIBRE_{date_str}_{safe_titre}_{safe_name}.pdf"
        return os.path.join(save_dir, filename)

    def _draw_canvas(self, canvas, doc, config=None, user=None):
        self.base_template.draw_static_elements(
            canvas,
            doc,
            config=config,
            draw_legal_ids=True,
            user=user,
        )

    def _create_header(self, patient, data, p_color, available_width):
        doc_date = _coerce_document_date(getattr(data, "doc_date", None))
        custom_date = getattr(data, "custom_date", None)
        right_text = _safe_pdf_text(custom_date) if custom_date else f"Le : {doc_date.strftime('%d/%m/%Y')}"

        custom_patient = getattr(data, "custom_patient", None)
        hide_patient = bool(getattr(data, "hide_patient_header", False))
        font_name = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

        patient_style = ParagraphStyle(
            name="PatientInfo",
            parent=self.styles["Normal"],
            fontName=font_bold,
            fontSize=11,
            textColor=p_color,
            leading=14,
        )
        style_right = ParagraphStyle(
            "DocDate",
            parent=self.styles["Normal"],
            alignment=TA_RIGHT,
            textColor=p_color,
            fontName=font_name,
            fontSize=11,
        )

        if hide_patient:
            left_content = Paragraph("", patient_style)
        elif custom_patient:
            left_content = Paragraph(
                f"<b>Destinataire :</b> {_safe_pdf_text(custom_patient)}",
                patient_style,
            )
        else:
            patient_name = (
                f"{_safe_pdf_text(str(getattr(patient, 'nom', '') or '').upper())} "
                f"{_safe_pdf_text(str(getattr(patient, 'prenom', '') or '').upper())}"
            ).strip()
            age = self._calculate_age(getattr(patient, "date_naissance", None), doc_date)
            age_line = f"<br/>Âge : {join_unbreakable(age, 'ans')}" if age is not None else ""
            left_content = Paragraph(f"<b>{patient_name}</b>{age_line}", patient_style)

        header_table = Table(
            [[left_content, Paragraph(right_text, style_right)]],
            colWidths=[available_width * 0.62, available_width * 0.38],
        )
        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ])
        )
        return header_table

    def _parse_content(self, content: str, body_style, font_name, font_bold, p_color, available_width):
        lines = content.split("\n")
        parsed_elements = []
        current_text: list[str] = []

        def flush_text():
            if not current_text:
                return
            safe_block = _sanitize_inline_markup("\n".join(current_text)).replace("\n", "<br/>")
            parsed_elements.append(Paragraph(safe_block, body_style))
            current_text.clear()

        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("|") and line.strip().endswith("|"):
                flush_text()
                raw_rows: list[list[str]] = []
                while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    row_line = lines[i].strip()
                    if not re.match(r"^\|[\s\-:\|]+\|$", row_line):
                        raw_rows.append([cell.strip() for cell in row_line.strip("|").split("|")])
                    i += 1

                if raw_rows:
                    max_cols = max(len(row) for row in raw_rows)
                    table_data = []
                    for row_index, row in enumerate(raw_rows):
                        padded = row + [""] * (max_cols - len(row))
                        cell_style = ParagraphStyle(
                            f"LibreCell{row_index}",
                            parent=body_style,
                            fontName=font_bold if row_index == 0 else font_name,
                            alignment=TA_LEFT,
                        )
                        table_data.append([
                            Paragraph(_sanitize_inline_markup(cell), cell_style)
                            for cell in padded
                        ])
                    col_width = available_width / max_cols
                    table = Table(table_data, colWidths=[col_width] * max_cols, repeatRows=1)
                    table.setStyle(
                        TableStyle([
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), p_color),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("FONTNAME", (0, 0), (-1, 0), font_bold),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                            ("TOPPADDING", (0, 0), (-1, 0), 8),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                            ("PADDING", (0, 0), (-1, -1), 6),
                        ])
                    )
                    parsed_elements.extend([table, Spacer(1, 0.4 * cm)])
                continue

            current_text.append(line)
            i += 1

        flush_text()
        return parsed_elements

    def generate(self, patient, data, db=None, user_id=None):
        data = _normalize_and_validate_libre_data(data)
        titre = data.titre
        filepath = self._get_save_path(patient, titre)

        config = None
        user_obj = None
        if db and user_id:
            from backend.models import CabinetConfig, User

            user_obj = db.query(User).filter(User.id == user_id).first()
            owner_id = _config_owner_id(user_obj, user_id)
            config = db.query(CabinetConfig).filter(CabinetConfig.owner_id == owner_id).first()

        self.base_template.update_active_fonts(config)
        p_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        font_name = self.base_template.premium_font
        font_bold = self.base_template.premium_bold

        page_size = _ALLOWED_PAGE_SIZES[data.page_size]
        p_width_val = page_size[0]
        m_top, m_bottom, m_left, m_right = self.base_template.get_document_margins(config, p_width_val)
        available_width = p_width_val - m_left - m_right

        safe_title = _safe_pdf_text(titre).replace(" ", " ")
        title_base_fs = self.base_template.get_adaptive_font_size(
            safe_title,
            font_bold,
            17,
            available_width * 0.7,
        )
        title_style = ParagraphStyle(
            name="TitleLibre",
            parent=self.styles["Normal"],
            fontName=font_bold,
            fontSize=title_base_fs,
            textColor=p_color,
            alignment=TA_CENTER,
            leading=title_base_fs * 1.3,
            spaceAfter=12,
        )
        body_style = ParagraphStyle(
            name="LibreBody",
            parent=self.styles["Normal"],
            fontName=font_name,
            fontSize=11,
            textColor=p_color,
            alignment=_ALLOWED_ALIGNMENTS[data.alignment],
            leading=16,
        )

        elements = [
            Spacer(1, 0.4 * cm),
            Paragraph(f"<u><b>{safe_title.upper()}</b></u>", title_style),
            Spacer(1, 0.8 * cm),
            self._create_header(patient, data, p_color, available_width),
            Spacer(1, 1.2 * cm),
        ]
        elements.extend(
            self._parse_content(
                data.contenu,
                body_style,
                font_name,
                font_bold,
                p_color,
                available_width,
            )
        )

        cloture_style = ParagraphStyle(
            name="LibreCloture",
            parent=self.styles["Normal"],
            fontName=font_bold,
            fontSize=10,
            textColor=p_color,
            alignment=TA_CENTER,
        )
        elements.append(PinnedCloture("", cloture_style))

        doc = SimpleDocTemplate(
            filepath,
            pagesize=page_size,
            rightMargin=m_right,
            leftMargin=m_left,
            topMargin=m_top,
            bottomMargin=m_bottom,
        )
        doc.qr_type = "WEBSITE"
        doc.doc_id = f"LIBRE-{datetime.now().strftime('%m%H%M')}"
        doc.cloture_text = ""
        draw_method = lambda canv, d: self._draw_canvas(canv, d, config=config, user=user_obj)
        page_counter = PageCounter()
        doc.build(
            elements,
            onFirstPage=draw_method,
            onLaterPages=draw_method,
            canvasmaker=page_counter.make_canvas_class(),
        )
        return filepath.replace("\\", "/")
