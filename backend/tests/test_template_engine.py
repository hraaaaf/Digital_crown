"""Tests services/template_engine.py — SecureTemplateRenderer & CSSGenerator."""
import pytest
from unittest.mock import patch

from backend.services.template_engine import SecureTemplateRenderer, CSSGenerator
from backend.schemas import DesignConfig


# ── SecureTemplateRenderer ────────────────────────────────────────────────────

class TestSecureTemplateRenderer:
    def setup_method(self):
        self.renderer = SecureTemplateRenderer()

    def test_renders_simple_template(self):
        html = "<p>Bonjour {{ patient_nom }}</p>"
        result = self.renderer.render(html, {"patient_nom": "DUPONT"})
        assert "DUPONT" in result

    def test_filters_unknown_variables(self):
        # 'secret' is not in ALLOWED_VARIABLES → stripped; StrictUndefined raises ValueError
        html = "<p>{{ patient_nom }} {{ secret }}</p>"
        with pytest.raises(ValueError):
            self.renderer.render(html, {"patient_nom": "Alice", "secret": "HIDDEN"})

    def test_renders_multiple_allowed_vars(self):
        html = "{{ patient_nom }} {{ patient_prenom }} — {{ date }}"
        result = self.renderer.render(html, {
            "patient_nom": "BEN ALI",
            "patient_prenom": "Youssef",
            "date": "01/01/2025"
        })
        assert "BEN ALI" in result
        assert "Youssef" in result
        assert "01/01/2025" in result

    def test_empty_template_renders(self):
        result = self.renderer.render("<p>Aucune variable</p>", {})
        assert "Aucune variable" in result

    # SSTI detection
    def test_blocks_import_injection(self):
        with pytest.raises(ValueError, match="non autorisé"):
            self.renderer.render("{{ __import__('os').system('id') }}", {})

    def test_blocks_eval_injection(self):
        with pytest.raises(ValueError, match="non autorisé"):
            self.renderer.render("<p>{% if eval('1+1') %}ok{% endif %}</p>", {})

    def test_blocks_exec_injection(self):
        with pytest.raises(ValueError, match="non autorisé"):
            self.renderer.render("exec('import os')", {})

    def test_blocks_subprocess(self):
        with pytest.raises(ValueError, match="non autorisé"):
            self.renderer.render("subprocess.run(['ls'])", {})

    def test_blocks_os_access(self):
        with pytest.raises(ValueError, match="non autorisé"):
            self.renderer.render("os.path.join('a', 'b')", {})

    def test_blocks_sys_access(self):
        with pytest.raises(ValueError, match="non autorisé"):
            self.renderer.render("sys.version", {})

    def test_blocks_from_import(self):
        with pytest.raises(ValueError, match="non autorisé"):
            self.renderer.render("from os import getcwd", {})

    def test_blocks_read_call(self):
        with pytest.raises(ValueError, match="non autorisé"):
            self.renderer.render("open('file').read()", {})

    def test_blocks_config_var(self):
        with pytest.raises(ValueError, match="non autorisé"):
            self.renderer.render("{{ config.SECRET_KEY }}", {})

    def test_allows_safe_content(self):
        html = """
        <html>
        <body>
            <h1>{{ titre }}</h1>
            <p>Patient: {{ patient_nom }} {{ patient_prenom }}</p>
        </body>
        </html>
        """
        result = self.renderer.render(html, {
            "titre": "Ordonnance",
            "patient_nom": "TEST",
            "patient_prenom": "User"
        })
        assert "Ordonnance" in result
        assert "TEST" in result


# ── CSSGenerator ──────────────────────────────────────────────────────────────

class TestCSSGenerator:
    def test_generates_css_string(self):
        config = DesignConfig()
        css = CSSGenerator.generate(config)
        assert isinstance(css, str)
        assert len(css) > 100

    def test_css_contains_font_face(self):
        config = DesignConfig()
        css = CSSGenerator.generate(config)
        assert "font-family" in css

    def test_css_contains_page_rule(self):
        config = DesignConfig()
        css = CSSGenerator.generate(config)
        assert "@page" in css

    def test_css_contains_primary_color(self):
        from backend.schemas.cabinet import ColorConfig
        colors = ColorConfig(primary="#123456")
        config = DesignConfig(colors=colors)
        css = CSSGenerator.generate(config)
        assert "#123456" in css

    def test_css_contains_body_font_size(self):
        from backend.schemas.cabinet import TypographyConfig
        typography = TypographyConfig(body_size=12)
        config = DesignConfig(typography=typography)
        css = CSSGenerator.generate(config)
        assert "12pt" in css

    def test_letterhead_css_when_enabled(self):
        from backend.schemas.cabinet import LetterheadConfig
        letterhead = LetterheadConfig(enabled=True, image_url="http://example.com/letter.png")
        config = DesignConfig(letterhead=letterhead)
        css = CSSGenerator.generate(config)
        assert "background-image" in css

    def test_no_letterhead_css_when_disabled(self):
        from backend.schemas.cabinet import LetterheadConfig
        letterhead = LetterheadConfig(enabled=False)
        config = DesignConfig(letterhead=letterhead)
        css = CSSGenerator.generate(config)
        assert "background-image" not in css

    def test_watermark_opacity_included(self):
        from backend.schemas.cabinet import WatermarkConfig
        watermark = WatermarkConfig(opacity=0.15, size_cm=8.0)
        config = DesignConfig(watermark=watermark)
        css = CSSGenerator.generate(config)
        assert "0.15" in css

    def test_header_border_line_included(self):
        from backend.schemas.cabinet import BorderConfig
        borders = BorderConfig(header_line=True, header_line_color="#FF0000")
        config = DesignConfig(borders=borders)
        css = CSSGenerator.generate(config)
        assert "border-bottom" in css

    def test_header_border_color_not_in_css_when_disabled(self):
        from backend.schemas.cabinet import BorderConfig
        unique_color = "#AB1234"
        borders = BorderConfig(header_line=False, header_line_color=unique_color)
        config = DesignConfig(borders=borders)
        css = CSSGenerator.generate(config)
        # border-bottom with this specific color should not appear when header_line=False
        assert f"border-bottom: 1px solid {unique_color}" not in css

    def test_page_size_a4(self):
        from backend.schemas.cabinet import LayoutConfig
        layout = LayoutConfig(page_size="A4")
        config = DesignConfig(layout=layout)
        css = CSSGenerator.generate(config)
        assert "A4" in css
