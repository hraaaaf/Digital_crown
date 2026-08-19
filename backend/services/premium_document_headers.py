"""Premium document header system for Settings document templates.

This module keeps the clinical prescription body stable while making the five
persisted template IDs visually distinct. It also centralizes truthful font
selection and Arabic font discovery without network dependencies.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable

from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


def _register_ttf(name: str, path: str | os.PathLike[str] | None) -> bool:
    if not path:
        return False
    path = str(path)
    if not os.path.exists(path):
        return False
    try:
        pdfmetrics.getFont(name)
        return True
    except Exception:
        pass
    try:
        pdfmetrics.registerFont(TTFont(name, path))
        return True
    except Exception as exc:
        logger.warning("Impossible d'enregistrer la police %s depuis %s: %s", name, path, exc)
        return False


def _arabic_font_candidates(font_dir: Path) -> Iterable[Path]:
    explicit = os.getenv("DIGITAL_CROWN_ARABIC_FONT")
    if explicit:
        yield Path(explicit)

    # Optional bundled font if a future packaging step provides it.
    yield font_dir / "Amiri-Regular.ttf"

    windir = os.getenv("WINDIR") or os.getenv("SystemRoot")
    if windir:
        fonts = Path(windir) / "Fonts"
        # Tahoma and Arial both include Arabic glyphs on standard Windows installs.
        yield fonts / "tahoma.ttf"
        yield fonts / "arial.ttf"
        yield fonts / "times.ttf"

    # Linux distributions / CI runners.
    yield Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    yield Path("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf")
    yield Path("/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf")
    yield Path("/usr/share/fonts/truetype/freefont/FreeSerif.ttf")

    # macOS common locations.
    yield Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    yield Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")


def register_document_fonts(base) -> None:
    """Register only fonts that truly exist and discover a local Arabic font."""
    font_dir = Path(os.path.dirname(base.font_path))

    base.premium_font = "Helvetica"
    base.premium_bold = "Helvetica-Bold"
    base.header_font = "Helvetica"
    base.header_bold = "Helvetica-Bold"

    outfit_reg = font_dir / "Outfit-Regular.ttf"
    outfit_bold = font_dir / "Outfit-Bold.ttf"
    if _register_ttf("Outfit", outfit_reg) and _register_ttf("Outfit-Bold", outfit_bold):
        base.outfit_font = "Outfit"
        base.outfit_bold = "Outfit-Bold"
    else:
        base.outfit_font = "Helvetica"
        base.outfit_bold = "Helvetica-Bold"

    base.arabic_font = None
    for candidate in _arabic_font_candidates(font_dir):
        if _register_ttf("ArabicFont", candidate):
            base.arabic_font = "ArabicFont"
            base.arabic_font_path = str(candidate)
            break

    if not base.arabic_font:
        logger.warning(
            "Aucune police arabe Unicode disponible. Les lignes arabes seront omises plutôt que rendues avec des glyphes cassés."
        )


def update_document_fonts(base, config) -> None:
    """Map persisted font IDs to deterministic PDF fonts.

    Legacy IDs are preserved for backward compatibility, but every mapping here
    corresponds to a font that is actually available at runtime.
    """
    font_fr = base._get_val(config, "font_fr", "inter")

    if font_fr == "outfit":
        regular = getattr(base, "outfit_font", "Helvetica")
        bold = getattr(base, "outfit_bold", "Helvetica-Bold")
    elif font_fr in {"playfair", "serif"}:
        regular, bold = "Times-Roman", "Times-Bold"
    elif font_fr == "mono":
        regular, bold = "Courier", "Courier-Bold"
    else:  # `inter` legacy ID -> truthful clinical sans fallback.
        regular, bold = "Helvetica", "Helvetica-Bold"

    base.premium_font = regular
    base.premium_bold = bold
    base.header_font = regular
    base.header_bold = bold


def _scale(base, config, h_scale: float) -> tuple[float, float, float]:
    font_scale = float(base._get_val(config, "header_font_scale", 1.0)) * h_scale
    logo_scale = float(base._get_val(config, "header_logo_scale", 1.0)) * h_scale
    line_scale = float(base._get_val(config, "header_line_height", 1.0))
    return font_scale, logo_scale, line_scale


def _fr_block(base, canvas, lines, x, y, *, align="left", title_size=11.5, sub_size=7.2, font=None, bold=None, color=None, line_scale=1.0):
    if not lines:
        return
    regular = font or base.header_font
    strong = bold or base.header_bold
    line_gap = 0.34 * cm * line_scale
    for idx, raw in enumerate(lines[:3]):
        text = str(raw or "").strip()
        if not text:
            continue
        canvas.setFillColor(color)
        canvas.setFont(strong if idx == 0 else regular, title_size if idx == 0 else sub_size)
        yy = y - idx * line_gap
        if align == "center":
            canvas.drawCentredString(x, yy, text)
        elif align == "right":
            canvas.drawRightString(x, yy, text)
        else:
            canvas.drawString(x, yy, text)


def _ar_block(base, canvas, lines, x, y, *, align="right", title_size=10.5, sub_size=7.5, color=None, line_scale=1.0):
    if not lines or not base.arabic_font:
        return
    line_gap = 0.36 * cm * line_scale
    for idx, raw in enumerate(lines[:3]):
        text = str(raw or "").strip()
        if not text:
            continue
        prepared = base._prepare_arabic(text)
        canvas.setFillColor(color)
        canvas.setFont(base.arabic_font, title_size if idx == 0 else sub_size)
        yy = y - idx * line_gap
        if align == "center":
            canvas.drawCentredString(x, yy, prepared)
        elif align == "left":
            canvas.drawString(x, yy, prepared)
        else:
            canvas.drawRightString(x, yy, prepared)


def _logo(base, canvas, config, logo_path, x, y, size):
    if logo_path:
        base._draw_header_logo(canvas, config, logo_path, x, y, size)


def draw_swiss(base, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
    """Swiss Clinic: compact asymmetric grid with a short accent rule."""
    canvas.saveState()
    fs, ls, line_scale = _scale(base, config, h_scale)
    margin = 1.5 * cm
    top = p_height - 1.05 * cm
    logo_size = 1.42 * cm * ls
    text_x = margin
    if logo_path:
        _logo(base, canvas, config, logo_path, margin, top - logo_size + 0.08 * cm, logo_size)
        text_x = margin + 1.75 * cm

    _fr_block(
        base, canvas, fr_lines, text_x, top - 0.15 * cm,
        title_size=11.6 * fs, sub_size=7.1 * fs, color=p_color, line_scale=line_scale,
    )
    _ar_block(
        base, canvas, ar_lines, p_width - margin, top - 0.12 * cm,
        title_size=10.4 * fs, sub_size=7.4 * fs, color=s_color, line_scale=line_scale,
    )

    line_y = p_height - 2.72 * cm
    canvas.setStrokeColor(a_color)
    canvas.setLineWidth(1.4)
    canvas.line(text_x, line_y, min(text_x + 3.55 * cm, p_width - margin), line_y)
    canvas.restoreState()


def draw_royal(base, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
    """Royal Elite: centered emblem with balanced bilingual identity."""
    canvas.saveState()
    fs, ls, line_scale = _scale(base, config, h_scale)
    margin = 1.5 * cm
    center = p_width / 2
    logo_size = 1.28 * cm * ls
    if logo_path:
        _logo(base, canvas, config, logo_path, center - logo_size / 2, p_height - 1.45 * cm, logo_size)

    identity_y = p_height - 2.05 * cm
    _fr_block(
        base, canvas, fr_lines, margin, identity_y,
        title_size=9.6 * fs, sub_size=6.8 * fs, color=p_color, line_scale=line_scale,
    )
    _ar_block(
        base, canvas, ar_lines, p_width - margin, identity_y,
        title_size=9.5 * fs, sub_size=7.0 * fs, color=s_color, line_scale=line_scale,
    )

    line_y = p_height - 2.78 * cm
    canvas.setStrokeColor(a_color)
    canvas.setLineWidth(0.65)
    canvas.line(margin, line_y, p_width - margin, line_y)
    canvas.restoreState()


def draw_clinical(base, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
    """Clinical Grid: explicit institutional grid and bilingual separation."""
    canvas.saveState()
    fs, ls, line_scale = _scale(base, config, h_scale)
    margin = 1.5 * cm
    top = p_height - 1.05 * cm
    logo_size = 1.28 * cm * ls
    text_x = margin
    if logo_path:
        _logo(base, canvas, config, logo_path, margin, top - logo_size + 0.05 * cm, logo_size)
        text_x = margin + 1.62 * cm

    divider_x = p_width * 0.56
    _fr_block(
        base, canvas, fr_lines, text_x, top - 0.12 * cm,
        title_size=10.8 * fs, sub_size=7.0 * fs, color=p_color, line_scale=line_scale,
    )
    _ar_block(
        base, canvas, ar_lines, p_width - margin, top - 0.12 * cm,
        title_size=10.0 * fs, sub_size=7.2 * fs, color=s_color, line_scale=line_scale,
    )

    bottom = p_height - 2.76 * cm
    canvas.setStrokeColor(a_color)
    canvas.setLineWidth(0.55)
    canvas.line(divider_x, top + 0.1 * cm, divider_x, bottom)
    canvas.line(margin, bottom, p_width - margin, bottom)
    canvas.restoreState()


def draw_modern(base, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
    """Modern Flush: one vertical accent rail and flush asymmetric content."""
    canvas.saveState()
    fs, ls, line_scale = _scale(base, config, h_scale)
    margin = 1.5 * cm
    top = p_height - 1.02 * cm
    bottom = p_height - 2.78 * cm

    canvas.setStrokeColor(a_color)
    canvas.setLineWidth(2.2)
    canvas.line(margin, top + 0.08 * cm, margin, bottom)

    logo_size = 1.12 * cm * ls
    content_x = margin + 0.42 * cm
    if logo_path:
        _logo(base, canvas, config, logo_path, content_x, top - logo_size + 0.04 * cm, logo_size)
        content_x += 1.38 * cm

    _fr_block(
        base, canvas, fr_lines, content_x, top - 0.12 * cm,
        title_size=11.2 * fs, sub_size=7.0 * fs, color=p_color, line_scale=line_scale,
    )
    _ar_block(
        base, canvas, ar_lines, p_width - margin, top - 0.12 * cm,
        title_size=10.1 * fs, sub_size=7.2 * fs, color=s_color, line_scale=line_scale,
    )
    canvas.restoreState()


def draw_heritage(base, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
    """L'Héritage: centered stationery, real serif identity, restrained double rule."""
    canvas.saveState()
    fs, ls, line_scale = _scale(base, config, h_scale)
    margin = 1.5 * cm
    center = p_width / 2
    logo_size = 1.08 * cm * ls
    if logo_path:
        _logo(base, canvas, config, logo_path, center - logo_size / 2, p_height - 1.38 * cm, logo_size)

    # Compact but non-overlapping stacked identity: 3 FR lines, then 2 AR lines.
    fr_y = p_height - 1.76 * cm
    _fr_block(
        base, canvas, fr_lines, center, fr_y, align="center",
        title_size=10.6 * fs, sub_size=6.7 * fs,
        font="Times-Roman", bold="Times-Bold", color=p_color, line_scale=line_scale * 0.82,
    )
    _ar_block(
        base, canvas, ar_lines, center, p_height - 2.64 * cm, align="center",
        title_size=8.2 * fs, sub_size=6.4 * fs, color=s_color, line_scale=line_scale * 0.82,
    )

    line_y = p_height - 3.22 * cm
    canvas.setStrokeColor(s_color)
    canvas.setLineWidth(0.35)
    canvas.line(margin, line_y, p_width - margin, line_y)
    canvas.setStrokeColor(a_color)
    canvas.setLineWidth(0.65)
    canvas.line(margin + 0.35 * cm, line_y - 0.11 * cm, p_width - margin - 0.35 * cm, line_y - 0.11 * cm)
    canvas.restoreState()
