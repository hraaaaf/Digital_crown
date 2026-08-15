from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Spacer

from backend.services.generators.certificat_gen import (
    SIGNATURE_LABEL,
    CertificateSignatureSpace,
    _append_handwritten_signature_space,
)


def test_certificate_signature_label_requires_handwritten_signature_without_stamp_substitution():
    assert SIGNATURE_LABEL == 'Signature manuscrite du praticien'
    assert 'manuscrite' in SIGNATURE_LABEL.casefold()
    assert 'cachet' not in SIGNATURE_LABEL.casefold()
    assert 'griffe' not in SIGNATURE_LABEL.casefold()


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


def test_signature_caption_identifies_actual_practitioner_without_changing_body_text():
    space = CertificateSignatureSpace(
        font_name='Helvetica',
        text_color=colors.black,
        signer_name='Dentiste Test',
    )

    caption = space._signature_caption()
    assert caption == f'Dr Dentiste Test — {SIGNATURE_LABEL}'
    assert 'manuscrite' in caption.casefold()


def test_signature_caption_remains_backward_compatible_without_signer_name():
    space = CertificateSignatureSpace(font_name='Helvetica', text_color=colors.black)
    assert space._signature_caption() == SIGNATURE_LABEL
