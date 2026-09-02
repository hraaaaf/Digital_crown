import pytest
from pydantic import ValidationError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm

from backend.schemas.cabinet import CabinetConfigUpdate
from backend.services.premium_document_headers import _fr_block, draw_heritage, draw_swiss


class _Base:
    header_font = "Helvetica"
    header_bold = "Helvetica-Bold"
    arabic_font = None

    @staticmethod
    def _get_val(config, key, default=None):
        return config.get(key, default)


class _Canvas:
    def __init__(self):
        self.text = []
        self.lines = []
        self.alignments = []

    def saveState(self):
        pass

    def restoreState(self):
        pass

    def setFillColor(self, _color):
        pass

    def setFont(self, _font, _size):
        pass

    def setStrokeColor(self, _color):
        pass

    def setLineWidth(self, _width):
        pass

    def drawString(self, x, y, text):
        self.text.append((x, y, text))
        self.alignments.append("left")

    def drawCentredString(self, x, y, text):
        self.text.append((x, y, text))
        self.alignments.append("center")

    def drawRightString(self, x, y, text):
        self.text.append((x, y, text))
        self.alignments.append("right")

    def line(self, x1, y1, x2, y2):
        self.lines.append((x1, y1, x2, y2))


def _max_current_header_lines():
    """Exact maximum produced by ProfileTab: 9 built-ins + 1 custom, paired by two."""
    return [
        "Dr. Achraf Benmoussa",
        "Chirurgien Dentiste",
        "Soins - Endodontie",
        "Parodontologie - Orthodontie",
        "Prothèse - Chirurgie",
        "Implantologie - Blanchiment",
        "Esthétique - Spécialité personnalisée",
    ]


def test_fr_block_renders_every_configured_specialty():
    canvas = _Canvas()
    configured = _max_current_header_lines()

    _fr_block(
        _Base(),
        canvas,
        configured,
        10,
        200,
        color=colors.black,
    )

    assert [item[2] for item in canvas.text] == configured


def test_swiss_separator_moves_below_long_specialty_block():
    canvas = _Canvas()
    configured = _max_current_header_lines()
    width, height = A5

    draw_swiss(
        _Base(),
        canvas,
        {},
        None,
        colors.black,
        colors.grey,
        colors.blue,
        width,
        height,
        configured,
        [],
        1.0,
    )

    assert len(canvas.text) == len(configured)
    assert len(canvas.lines) == 1
    separator_y = canvas.lines[0][1]
    last_text_y = canvas.text[-1][1]
    assert separator_y < last_text_y
    assert separator_y < height - 2.72 * cm


def test_dense_heritage_switches_to_compact_left_column():
    canvas = _Canvas()
    configured = _max_current_header_lines()
    width, height = A5

    draw_heritage(
        _Base(),
        canvas,
        {},
        None,
        colors.black,
        colors.grey,
        colors.blue,
        width,
        height,
        configured,
        [],
        1.0,
    )

    assert [item[2] for item in canvas.text] == configured
    assert canvas.alignments == ["left"] * len(configured)
    assert len(canvas.lines) == 2
    last_text_y = canvas.text[-1][1]
    assert canvas.lines[0][1] < last_text_y


def test_cabinet_config_accepts_full_current_specialty_header():
    lines = _max_current_header_lines()

    payload = CabinetConfigUpdate(header_lines_fr=lines, header_lines_ar=lines)

    assert payload.header_lines_fr == lines
    assert payload.header_lines_ar == lines


def test_cabinet_config_rejects_header_beyond_current_ui_contract():
    lines = _max_current_header_lines() + ["Ligne surnuméraire"]

    with pytest.raises(ValidationError):
        CabinetConfigUpdate(header_lines_fr=lines)
