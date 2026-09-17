import pytest

from backend.services.insurance_far_prescription_renderer import _single_line


def test_calibrated_text_rejects_silent_truncation():
    with pytest.raises(ValueError, match="printable width"):
        _single_line("x" * 59, field="posology[0]", max_chars=58)


def test_calibrated_text_normalizes_whitespace_without_inference():
    assert _single_line("  1 cp   matin  ", field="posology[0]", max_chars=58) == "1 cp matin"
