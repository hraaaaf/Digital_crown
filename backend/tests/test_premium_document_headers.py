from pathlib import Path

from reportlab.pdfbase import pdfmetrics

from backend.services import premium_document_headers as premium


class _FakeBase:
    def __init__(self):
        self.outfit_font = "Outfit"
        self.outfit_bold = "Outfit-Bold"
        self.premium_font = "Helvetica"
        self.premium_bold = "Helvetica-Bold"
        self.header_font = "Helvetica"
        self.header_bold = "Helvetica-Bold"

    @staticmethod
    def _get_val(config, key, default=None):
        return (config or {}).get(key, default)


def test_document_font_ids_map_to_real_pdf_fonts():
    base = _FakeBase()

    expected = {
        "inter": ("Helvetica", "Helvetica-Bold"),
        "playfair": ("Times-Roman", "Times-Bold"),
        "serif": ("Times-Roman", "Times-Bold"),  # legacy persisted ID
        "mono": ("Courier", "Courier-Bold"),
    }

    for font_id, pair in expected.items():
        premium.update_document_fonts(base, {"font_fr": font_id})
        assert (base.premium_font, base.premium_bold) == pair
        pdfmetrics.getFont(base.premium_font)
        pdfmetrics.getFont(base.premium_bold)


def test_outfit_mapping_uses_registered_runtime_names():
    base = _FakeBase()
    premium.update_document_fonts(base, {"font_fr": "outfit"})
    assert (base.premium_font, base.premium_bold) == ("Outfit", "Outfit-Bold")


def test_arabic_font_env_candidate_has_priority(monkeypatch, tmp_path):
    custom = tmp_path / "custom-arabic.ttf"
    custom.write_bytes(b"placeholder")
    monkeypatch.setenv("DIGITAL_CROWN_ARABIC_FONT", str(custom))

    candidates = list(premium._arabic_font_candidates(Path("/unused")))

    assert candidates[0] == custom


def test_arabic_fallback_candidates_cover_local_desktop_and_linux():
    candidates = [str(path).lower() for path in premium._arabic_font_candidates(Path("/bundle"))]

    assert any("amiri-regular.ttf" in path for path in candidates)
    assert any("dejavusans.ttf" in path for path in candidates)


def test_five_premium_header_drawers_are_explicit():
    for name in ("swiss", "royal", "clinical", "modern", "heritage"):
        drawer = getattr(premium, f"draw_{name}")
        assert callable(drawer)
