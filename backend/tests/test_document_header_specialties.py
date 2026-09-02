from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm

from backend.services.premium_document_headers import _fr_block, draw_swiss


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

    def drawCentredString(self, x, y, text):
        self.text.append((x, y, text))

    def drawRightString(self, x, y, text):
        self.text.append((x, y, text))

    def line(self, x1, y1, x2, y2):
        self.lines.append((x1, y1, x2, y2))


def test_fr_block_renders_every_configured_specialty():
    canvas = _Canvas()
    configured = [
        "Dr. Achraf Benmoussa",
        "Chirurgie dentaire",
        "Implantologie",
        "Parodontologie",
        "Endodontie",
        "Orthodontie",
        "Dentisterie esthétique",
    ]

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
    configured = [
        "Dr. Achraf Benmoussa",
        "Chirurgie dentaire",
        "Implantologie",
        "Parodontologie",
        "Endodontie",
        "Orthodontie",
        "Dentisterie esthétique",
    ]
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
