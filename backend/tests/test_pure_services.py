"""Tests for pure-Python services: anonymizer, file_validator, css_generator."""
import io
import pytest


# ── anonymizer ────────────────────────────────────────────────────────────────

class TestAnonymizer:
    def test_dossier_number_masked(self):
        from backend.services.anonymizer import anonymize_text
        result = anonymize_text("Dossier P-123456 du patient")
        assert "[DOSSIER]" in result
        assert "P-123456" not in result

    def test_telephone_moroccan_masked(self):
        from backend.services.anonymizer import anonymize_text
        result = anonymize_text("Tel: 0612345678")
        assert "[TELEPHONE]" in result

    def test_email_masked(self):
        from backend.services.anonymizer import anonymize_text
        result = anonymize_text("Contact: patient@gmail.com")
        assert "[EMAIL]" in result
        assert "patient@gmail.com" not in result

    def test_patient_name_after_prefix_masked(self):
        from backend.services.anonymizer import anonymize_text
        result = anonymize_text("Patient Alami Karim")
        assert "[NOM]" in result

    def test_plain_text_unchanged(self):
        from backend.services.anonymizer import anonymize_text
        text = "Ordonnance pour carie de classe II"
        result = anonymize_text(text)
        assert result == text

    def test_non_string_returned_as_is(self):
        from backend.services.anonymizer import anonymize_text
        assert anonymize_text(42) == 42
        assert anonymize_text(None) is None

    def test_anonymize_payload_dict(self):
        from backend.services.anonymizer import anonymize_payload
        payload = {"email": "dr@clinic.ma", "note": "RAS"}
        result = anonymize_payload(payload)
        assert result["email"] == "[EMAIL]"
        assert result["note"] == "RAS"

    def test_anonymize_payload_list(self):
        from backend.services.anonymizer import anonymize_payload
        payload = ["patient@gmail.com", "RAS"]
        result = anonymize_payload(payload)
        assert result[0] == "[EMAIL]"
        assert result[1] == "RAS"

    def test_anonymize_payload_nested(self):
        from backend.services.anonymizer import anonymize_payload
        payload = {"patient": {"contact": "0612345678", "nom": "Ali"}}
        result = anonymize_payload(payload)
        assert "[TELEPHONE]" in result["patient"]["contact"]

    def test_anonymize_payload_non_string_passthrough(self):
        from backend.services.anonymizer import anonymize_payload
        assert anonymize_payload(42) == 42
        assert anonymize_payload(True) is True


# ── file_validator ────────────────────────────────────────────────────────────

class TestSanitizeFilename:
    def test_normal_filename_unchanged(self):
        from backend.services.file_validator import sanitize_filename
        result = sanitize_filename("radio_pano_2025.jpg")
        assert result == "radio_pano_2025.jpg"

    def test_path_traversal_removed(self):
        from backend.services.file_validator import sanitize_filename
        result = sanitize_filename("../../etc/passwd.jpg")
        assert ".." not in result

    def test_forward_slash_removed(self):
        from backend.services.file_validator import sanitize_filename
        result = sanitize_filename("path/to/file.png")
        assert "/" not in result

    def test_backslash_removed(self):
        from backend.services.file_validator import sanitize_filename
        result = sanitize_filename("path\\to\\file.png")
        assert "\\" not in result

    def test_special_chars_removed(self):
        from backend.services.file_validator import sanitize_filename
        result = sanitize_filename("file<>:\"|?*.jpg")
        for char in "<>|?*:":
            assert char not in result

    def test_long_filename_truncated(self):
        from backend.services.file_validator import sanitize_filename
        long_name = "a" * 250 + ".jpg"
        result = sanitize_filename(long_name)
        assert len(result) <= 201

    def test_empty_string_returns_empty(self):
        from backend.services.file_validator import sanitize_filename
        result = sanitize_filename("")
        assert result == ""


# ── css_generator ─────────────────────────────────────────────────────────────

class TestCSSGenerator:
    def test_default_css_generated(self):
        from backend.services.css_generator import CSSGenerator
        gen = CSSGenerator()
        css = gen.generate_document_css()
        assert isinstance(css, str)
        assert len(css) > 100

    def test_page_size_in_output(self):
        from backend.services.css_generator import CSSGenerator
        gen = CSSGenerator()
        css = gen.generate_document_css(page_size="A4")
        assert "A4" in css

    def test_a5_page_size(self):
        from backend.services.css_generator import CSSGenerator
        gen = CSSGenerator()
        css = gen.generate_document_css(page_size="A5")
        assert "A5" in css

    def test_primary_color_in_variables(self):
        from backend.services.css_generator import CSSGenerator, ColorConfig
        gen = CSSGenerator(colors=ColorConfig(primary="#FF0000"))
        css = gen.generate_document_css()
        assert "#FF0000" in css

    def test_custom_margins_applied(self):
        from backend.services.css_generator import CSSGenerator, MarginConfig
        gen = CSSGenerator(margins=MarginConfig(top=5.0, bottom=3.0, left=2.0, right=2.0))
        css = gen.generate_document_css()
        assert "5.0cm" in css

    def test_letterhead_margins_override(self):
        from backend.services.css_generator import CSSGenerator, HeaderFooterConfig, MarginConfig
        lhm = MarginConfig(top=7.0, bottom=3.0, left=2.0, right=2.0)
        hf = HeaderFooterConfig(letterhead_enabled=True, letterhead_margins=lhm)
        gen = CSSGenerator(header_footer=hf)
        css = gen.generate_document_css()
        assert "7.0cm" in css

    def test_css_has_root_variables(self):
        from backend.services.css_generator import CSSGenerator
        css = CSSGenerator().generate_document_css()
        assert ":root" in css

    def test_css_has_page_rule(self):
        from backend.services.css_generator import CSSGenerator
        css = CSSGenerator().generate_document_css()
        assert "@page" in css

    def test_default_colors_used(self):
        from backend.services.css_generator import CSSGenerator, ColorConfig
        default_primary = ColorConfig().primary
        css = CSSGenerator().generate_document_css()
        assert default_primary in css

    def test_css_has_typography(self):
        from backend.services.css_generator import CSSGenerator
        css = CSSGenerator().generate_document_css()
        assert "font" in css.lower()
