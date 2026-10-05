import inspect

from backend.services.generators.accounting_gen import AccountingGenerator\nfrom backend.services.generators.ordonnance_gen import OrdonnanceGenerator
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


def test_honoraires_mad_amounts_use_french_financial_format():
    generator = AccountingGenerator()

    assert generator._format_mad_amount(321) == "321,00"
    assert generator._format_mad_amount(1662) == "1 662,00"
    assert generator._format_mad_amount(999999.99) == "999 999,99"


def test_honoraires_total_row_uses_same_french_amount_formatter():
    source = inspect.getsource(AccountingGenerator.generate_note)

    assert 'amount_text = self._format_mad_amount(p.montant)' in source
    assert 'total_amount_text = f"<b>{self._format_mad_amount(total)}' in source


def test_devis_amounts_and_alignment_match_accounting_pdf_contract():
    source = inspect.getsource(AccountingGenerator.generate_devis)

    assert "price_text = self._format_mad_amount(item.prix_unitaire)" in source
    assert 'total_amount_text = f"<b>{self._format_mad_amount(total)}' in source
    assert "alignment=TA_CENTER, leading=base_fs * 1.25" in source
    assert "fontSize=9.0, textColor=p_color, alignment=TA_LEFT, leading=12" in source


def test_ordonnance_dense_layout_preserves_readability_and_row_grouping():
    source = inspect.getsource(OrdonnanceGenerator)

    assert "compression_factor *= 0.90" in source
    assert "base_poso_fs = max(base_poso_fs, MIN_READABLE_SIZE)" in source
    assert "min_name_fs = max(min_name_fs, MIN_READABLE_SIZE)" in source
    assert "elements.append(KeepTogether(med_block))" in source
    assert "compression_factor *= 0.82" not in source
