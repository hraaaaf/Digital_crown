from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from backend.services.base_template import BaseTemplate


def test_scale_elements_never_exposes_source_list_to_reportlab_consumption():
    source = [Paragraph("Page one", getSampleStyleSheet()["Normal"])]

    disposable = BaseTemplate.scale_elements(source, 1.0)

    assert disposable is not source
    disposable.clear()
    assert len(source) == 1
