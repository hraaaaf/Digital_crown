from types import SimpleNamespace

from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm

from backend.services.base_template import BaseTemplate, PinnedCloture


HEADER_FR = ["Dr.", "Chirurgien Dentiste", "Soins", "Parodontologie", "Prothèse", "Implantologie", "Esthétique"]
HEADER_AR = ["د.", "طبيب جراح للأسنان", "علاج", "أمراض اللثة", "تعويض الأسنان", "زراعة الأسنان", "تجميل الأسنان"]


def _config(template: str, margin_top: float):
    return SimpleNamespace(
        selected_template=template,
        margin_top=margin_top,
        margin_bottom=3.2,
        header_scale=1.0,
        header_font_scale=1.0,
        header_line_height=1.0,
        header_lines_fr=HEADER_FR,
        header_lines_ar=HEADER_AR,
        letterhead_path=None,
        use_letterhead=False,
    )


def test_content_position_moves_down_and_never_crosses_header_guard():
    base = BaseTemplate()
    for template in ["swiss", "royal", "clinical", "modern", "heritage"]:
        top_up, *_ = base.get_document_margins(_config(template, 2.8), A5[0])
        top_neutral, *_ = base.get_document_margins(_config(template, 3.6), A5[0])
        top_down, *_ = base.get_document_margins(_config(template, 5.1), A5[0])

        assert top_up <= top_neutral <= top_down
        assert top_down - top_up >= 0.2 * cm
        # The collision guard may clamp the user's upward request, but never
        # below a physically plausible header/body separation on A5.
        assert top_up >= 3.0 * cm


def test_pinned_cloture_reserves_footer_adjacent_band():
    style = ParagraphStyle("cloture-test", fontName="Helvetica", fontSize=9, leading=12)
    flowable = PinnedCloture(
        "Arrêtée la présente note d'honoraires à la somme de DIX-HUIT MILLE CENT DIRHAMS TTC.",
        style,
    )
    _, reserved_height = flowable.wrap(11.8 * cm, 10 * cm)
    assert reserved_height >= 1.6 * cm
