from reportlab.lib.units import cm

from backend.services.premium_document_headers import draw_royal


class _BaseStub:
    header_font = "Helvetica"
    header_bold = "Helvetica-Bold"
    arabic_font = "Helvetica"

    @staticmethod
    def _get_val(config, key, default=None):
        return config.get(key, default)

    @staticmethod
    def _prepare_arabic(text):
        return text


class _CanvasStub:
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

    def drawString(self, _x, y, text):
        self.text.append((text, y))

    def drawRightString(self, _x, y, text):
        self.text.append((text, y))

    def drawCentredString(self, _x, y, text):
        self.text.append((text, y))

    def setStrokeColor(self, _color):
        pass

    def setLineWidth(self, _width):
        pass

    def line(self, x1, y1, x2, y2):
        self.lines.append((x1, y1, x2, y2))


def test_royal_header_renders_all_persisted_specialty_lines_and_keeps_rule_below_text():
    canvas = _CanvasStub()
    fr_lines = [
        "Dr. Benmoussa Achraf",
        "Chirurgien Dentiste",
        "Soins - Endodontie",
        "Parodontologie - Orthodontie",
        "Prothèse - Chirurgie",
        "Implantologie - Blanchiment",
    ]
    ar_lines = [
        "د. أشرف بنموسى",
        "طبيب جراح للأسنان",
        "علاج العصب - علاج",
        "تقويم الأسنان - أمراض اللثة",
        "جراحة - تعويض الأسنان",
        "تبييض الأسنان - زراعة الأسنان",
    ]

    draw_royal(
        _BaseStub(),
        canvas,
        {},
        None,
        "#003380",
        "#1e40af",
        "#60a5fa",
        14.8 * cm,
        21 * cm,
        fr_lines,
        ar_lines,
        1.0,
    )

    rendered_texts = {text for text, _y in canvas.text}
    assert fr_lines[-1] in rendered_texts
    assert ar_lines[-1] in rendered_texts

    horizontal_rules = [line for line in canvas.lines if line[1] == line[3]]
    assert horizontal_rules
    rule_y = horizontal_rules[-1][1]
    lowest_text_y = min(y for _text, y in canvas.text)
    assert rule_y < lowest_text_y
