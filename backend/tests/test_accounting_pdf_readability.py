import inspect

from backend.services.generators.accounting_gen import AccountingGenerator
from backend.services.generators.accounting_pdf_readability import (
    is_readable_accounting_font_size,
    readable_accounting_font_floor,
)
from backend.services.generators.document_typography import MIN_READABLE_SIZE


def test_accounting_font_floor_rejects_legacy_two_point_request():
    assert readable_accounting_font_floor(2.0) == float(MIN_READABLE_SIZE)


def test_accounting_font_floor_preserves_stricter_request():
    assert readable_accounting_font_floor(9.0) == 9.0


def test_accounting_readability_uses_central_typography_contract():
    assert is_readable_accounting_font_size(MIN_READABLE_SIZE)
    assert not is_readable_accounting_font_size(MIN_READABLE_SIZE - 0.1)


def test_devis_generator_wraps_instead_of_using_legacy_two_point_floor():
    source = inspect.getsource(AccountingGenerator.generate_devis)

    assert "min_fs=2.0" not in source
    assert "readable_accounting_font_floor()" in source
    assert "Paragraph(item.acte, acte_style)" in source
    assert "repeatRows=1" in source
