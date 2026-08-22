from pathlib import Path

from backend.schemas.branding import BrandingPreviewPayload
from backend.services import document_factory as document_factory_module
from backend.services.base_template import BaseTemplate


class _FakeGenerator:
    calls = []

    def __init__(self, output_dir):
        self.output_dir = str(output_dir)

    def generate(self, patient, data, db=None, user_id=None, custom_config=None):
        target = Path(self.output_dir) / "2026" / "08"
        target.mkdir(parents=True, exist_ok=True)
        pdf_path = target / "preview.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
        self.__class__.calls.append(
            {
                "output_dir": self.output_dir,
                "user_id": user_id,
                "custom_config": dict(custom_config or {}),
            }
        )
        return str(pdf_path)


class _NoopGenerator:
    def __init__(self, *args, **kwargs):
        pass


def _build_factory(monkeypatch, tmp_path):
    _FakeGenerator.calls = []
    monkeypatch.setattr(document_factory_module, "OrdonnanceGenerator", _FakeGenerator)
    monkeypatch.setattr(document_factory_module, "CertificatGenerator", _NoopGenerator)
    monkeypatch.setattr(document_factory_module, "AccountingGenerator", _NoopGenerator)
    monkeypatch.setattr(document_factory_module, "LibreGenerator", _NoopGenerator)
    monkeypatch.setattr(document_factory_module, "BilanOrthoPDFGenerator", _NoopGenerator)
    return document_factory_module.DocumentFactory(
        output_dir=str(tmp_path / "documents"),
        static_dir=str(tmp_path / "static"),
    )


def test_branding_payload_accepts_internal_settings_preview_flag():
    payload = BrandingPreviewPayload(settings_preview=True, selected_template="royal")

    assert payload.settings_preview is True
    assert payload.selected_template == "royal"


def test_settings_preview_is_isolated_and_replaces_previous_pdf(monkeypatch, tmp_path):
    factory = _build_factory(monkeypatch, tmp_path)
    preview_root = tmp_path / "documents" / ".previews" / "settings_branding" / "7"
    stale = preview_root / "2026" / "07" / "stale.pdf"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_bytes(b"old preview")

    result = factory.create_ordonnance(
        patient=object(),
        data=object(),
        db=None,
        user_id=7,
        custom_config={"settings_preview": True, "selected_template": "royal"},
    )

    assert str(preview_root) in result
    assert not stale.exists()
    assert len(list(preview_root.rglob("*.pdf"))) == 1
    assert _FakeGenerator.calls[-1]["custom_config"] == {"selected_template": "royal"}

    factory.create_ordonnance(
        patient=object(),
        data=object(),
        db=None,
        user_id=7,
        custom_config={"settings_preview": True, "selected_template": "modern"},
    )

    assert len(list(preview_root.rglob("*.pdf"))) == 1
    assert _FakeGenerator.calls[-1]["custom_config"] == {"selected_template": "modern"}


def test_normal_ordonnance_keeps_regular_output_path(monkeypatch, tmp_path):
    factory = _build_factory(monkeypatch, tmp_path)

    result = factory.create_ordonnance(
        patient=object(),
        data=object(),
        db=None,
        user_id=7,
        custom_config={"selected_template": "swiss"},
    )

    assert ".previews/settings_branding" not in result.replace("\\", "/")
    assert _FakeGenerator.calls[-1]["output_dir"] == str(tmp_path / "documents")
    assert _FakeGenerator.calls[-1]["custom_config"] == {"selected_template": "swiss"}


def test_official_settings_templates_dispatch_to_real_pdf_headers():
    base_template = object.__new__(BaseTemplate)
    calls = []

    def record(name):
        def _renderer(*args, **kwargs):
            calls.append(name)
        return _renderer

    base_template._draw_header_swiss = record("swiss")
    base_template._draw_header_royal = record("royal")
    base_template._draw_header_clinical = record("clinical")
    base_template._draw_header_modern = record("modern")
    base_template._draw_header_heritage = record("heritage")

    for template_id in ["swiss", "royal", "clinical", "modern", "heritage"]:
        base_template._draw_auto_header(
            canvas=None,
            config={
                "selected_template": template_id,
                "header_lines_fr": ["Dr Test"],
                "header_lines_ar": ["د. اختبار"],
            },
            logo_path=None,
            p_color=None,
            s_color=None,
            a_color=None,
            p_width=420,
            p_height=594,
        )
        assert calls[-1] == template_id
