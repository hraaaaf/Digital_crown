from types import SimpleNamespace

from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph

from backend.services.base_template import BaseTemplate, PinnedCloture


HEADER_FR = ["Dr.", "Chirurgien Dentiste", "Soins", "Parodontologie", "Prothèse", "Implantologie", "Esthétique"]
HEADER_AR = ["د.", "طبيب جراح للأسنان", "علاج", "أمراض اللثة", "تعويض الأسنان", "زراعة الأسنان", "تجميل الأسنان"]


def _config(template: str, content_offset_y: float):
    return SimpleNamespace(
        selected_template=template,
        margin_top=3.6,
        margin_bottom=3.2,
        content_offset_y=content_offset_y,
        header_scale=1.0,
        header_font_scale=1.0,
        header_line_height=1.0,
        header_lines_fr=HEADER_FR,
        header_lines_ar=HEADER_AR,
        letterhead_path=None,
        use_letterhead=False,
    )


def test_content_offset_preserves_neutral_layout_and_header_safe_upward_clamp():
    base = BaseTemplate()
    for template in ["swiss", "royal", "clinical", "modern", "heritage"]:
        top_up, *_ = base.get_document_margins(_config(template, -0.8), A5[0])
        top_neutral, *_ = base.get_document_margins(_config(template, 0.0), A5[0])
        top_down, *_ = base.get_document_margins(_config(template, 1.5), A5[0])

        assert top_up <= top_neutral < top_down
        assert top_neutral - top_up <= 0.8 * cm
        assert abs((top_down - top_neutral) - 1.5 * cm) <= 0.01
        # Dense 7-line bilingual headers consume the available upward headroom;
        # the body must stop at the guard rather than overlap the header.
        assert top_up >= 3.0 * cm


def test_content_offset_is_clamped_to_supported_range():
    base = BaseTemplate()
    top_min, *_ = base.get_document_margins(_config("swiss", -99.0), A5[0])
    top_supported_min, *_ = base.get_document_margins(_config("swiss", -0.8), A5[0])
    top_max, *_ = base.get_document_margins(_config("swiss", 99.0), A5[0])
    top_supported_max, *_ = base.get_document_margins(_config("swiss", 1.5), A5[0])
    assert top_min == top_supported_min
    assert top_max == top_supported_max


def _cloture():
    style = ParagraphStyle("cloture-test", fontName="Helvetica", fontSize=9, leading=12)
    return PinnedCloture(
        "Arrêtée la présente note d'honoraires à la somme de DIX-HUIT MILLE CENT DIRHAMS TTC.",
        style,
    )


def test_only_final_cloture_is_footer_pinned():
    body = Paragraph("Body", ParagraphStyle("body-test", fontName="Helvetica", fontSize=9))
    final = _cloture()
    story = BaseTemplate.scale_elements([body, final], 1.0)
    assert story[-1] is final
    assert final._pin_to_footer is True

    non_final = _cloture()
    trailing = Paragraph("Signature", ParagraphStyle("sig-test", fontName="Helvetica", fontSize=9))
    BaseTemplate.scale_elements([non_final, trailing], 1.0)
    assert non_final._pin_to_footer is False


def test_final_cloture_uses_footer_band_when_body_ends_high_enough():
    flowable = _cloture()
    BaseTemplate.scale_elements([flowable], 1.0)
    flowable._frame = SimpleNamespace(_y=4.0 * cm)
    available = 0.5 * cm
    _, reserved_height = flowable.wrap(11.8 * cm, available)
    assert reserved_height == 0
    assert flowable._cloture_draw_y >= 2.65 * cm


def test_final_cloture_forces_page_break_before_overlapping_body():
    flowable = _cloture()
    BaseTemplate.scale_elements([flowable], 1.0)
    flowable._frame = SimpleNamespace(_y=3.2 * cm)
    tight_available = 0.2 * cm
    _, required_height = flowable.wrap(11.8 * cm, tight_available)
    assert required_height > tight_available


def test_non_final_cloture_keeps_normal_flow_height():
    flowable = _cloture()
    trailing = Paragraph("Signature", ParagraphStyle("sig-flow-test", fontName="Helvetica", fontSize=9))
    BaseTemplate.scale_elements([flowable, trailing], 1.0)
    _, required_height = flowable.wrap(11.8 * cm, 10 * cm)
    assert required_height > 0
