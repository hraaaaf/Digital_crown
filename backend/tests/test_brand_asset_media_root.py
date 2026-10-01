from pathlib import Path

from backend.services import base_template_core


def _template(tmp_path):
    template = base_template_core.BaseTemplate.__new__(base_template_core.BaseTemplate)
    template.base_path = str(tmp_path / "release" / "backend")
    return template


def test_brand_asset_prefers_media_root(tmp_path, monkeypatch):
    media_root = tmp_path / "media"
    media_asset = media_root / "clinics" / "cabinet-a" / "logo.png"
    media_asset.parent.mkdir(parents=True)
    media_asset.write_bytes(b"media-logo")

    template = _template(tmp_path)
    monkeypatch.setattr(base_template_core, "get_media_root", lambda: media_root)

    resolved = template._resolve_brand_asset("clinics/cabinet-a/logo.png")

    assert resolved == str(media_asset.resolve())


def test_brand_asset_falls_back_to_legacy_uploads(tmp_path, monkeypatch):
    media_root = tmp_path / "media"
    media_root.mkdir()
    template = _template(tmp_path)

    legacy_asset = Path(template.base_path) / "static" / "uploads" / "clinics" / "cabinet-a" / "logo.png"
    legacy_asset.parent.mkdir(parents=True)
    legacy_asset.write_bytes(b"legacy-logo")

    monkeypatch.setattr(base_template_core, "get_media_root", lambda: media_root)

    resolved = template._resolve_brand_asset("clinics/cabinet-a/logo.png")

    assert resolved == str(legacy_asset.resolve())


def test_brand_asset_rejects_path_escape(tmp_path, monkeypatch):
    media_root = tmp_path / "media"
    media_root.mkdir()
    outside = tmp_path / "secret.png"
    outside.write_bytes(b"secret")

    template = _template(tmp_path)
    monkeypatch.setattr(base_template_core, "get_media_root", lambda: media_root)

    assert template._resolve_brand_asset("../secret.png") is None
    assert template._resolve_brand_asset(str(outside.resolve())) is None
