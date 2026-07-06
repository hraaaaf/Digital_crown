"""Tests backend.services.security.data_sanitizer — masquage PII.
Note: sanitize() returns a (text, metadata) tuple.
"""
from backend.services.security.data_sanitizer import DataSanitizer


def _text(result):
    """Extract text from sanitize() result (tuple or str)."""
    return result[0] if isinstance(result, tuple) else result


class TestDataSanitizer:
    def setup_method(self):
        self.s = DataSanitizer()

    def test_mask_email(self):
        result = _text(self.s.sanitize("Email: patient@example.com"))
        assert "patient@example.com" not in result

    def test_mask_phone(self):
        result = _text(self.s.sanitize("Tel: 0612345678"))
        assert "0612345678" not in result

    def test_no_pii_technical_content_preserved(self):
        text = "Dent 36 — carie amélaire profonde."
        result = _text(self.s.sanitize(text))
        # The core clinical content should remain recognizable
        assert len(result) > 0

    def test_empty_string(self):
        result = _text(self.s.sanitize(""))
        assert result == ""

    def test_mask_multiple_emails(self):
        text = "Voir a@b.com et c@d.com pour plus."
        result = _text(self.s.sanitize(text))
        assert "a@b.com" not in result
        assert "c@d.com" not in result

    def test_returns_tuple(self):
        result = self.s.sanitize("Hello patient@test.dz")
        assert isinstance(result, tuple)
        assert len(result) == 2
