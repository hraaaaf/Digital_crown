from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Spacer

from backend.services.generators.certificat_gen import (
    CertificateSignatureSpace,
    _append_handwritten_signature_space,
)


def test_certificate_signature_space_reserves_real_blank_height():
    space = CertificateSignatureSpace(font_name='Helvetica', text_color=colors.black)
    width, height = space.wrap(300, 500)

    assert width == 300
    assert height == 2.4 * cm
    assert height > 2 * cm


def test_certificate_generator_appends_signature_space_after_body():
    elements = []
    _append_handwritten_signature_space(elements, font_name='Helvetica', text_color=colors.black)

    assert len(elements) == 2
    assert isinstance(elements[0], Spacer)
    assert isinstance(elements[1], CertificateSignatureSpace)


def test_signature_caption_identifies_actual_practitioner_without_instruction_text():
    space = CertificateSignatureSpace(
        font_name='Helvetica',
        text_color=colors.black,
        signer_name='Dentiste Test',
    )

    caption = space._signature_caption()
    assert caption == 'Dr Dentiste Test'
    assert 'signature manuscrite' not in caption.casefold()
    assert 'cachet' not in caption.casefold()
    assert 'griffe' not in caption.casefold()


def test_signature_caption_is_empty_without_signer_name():
    space = CertificateSignatureSpace(font_name='Helvetica', text_color=colors.black)
    assert space._signature_caption() == ''
