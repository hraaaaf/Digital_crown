from types import SimpleNamespace

from backend.services.generators.certificat_gen import _certificate_render_config


def _config(**kwargs):
    defaults = {
        "qr_code_enabled": True,
        "qr_code_type": "VCARD",
        "primary_color": "#003380",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_certificate_disables_unverifiable_validation_qr_only():
    original = _config(qr_code_type="VALIDATION")
    rendered = _certificate_render_config(original)

    assert rendered is not original
    assert rendered.qr_code_enabled is False
    assert rendered.qr_code_type == "VALIDATION"
    assert rendered.primary_color == original.primary_color
    assert original.qr_code_enabled is True


def test_certificate_keeps_contact_qr_configuration_unchanged():
    original = _config(qr_code_type="VCARD")
    assert _certificate_render_config(original) is original


def test_certificate_keeps_disabled_qr_configuration_unchanged():
    original = _config(qr_code_enabled=False, qr_code_type="VALIDATION")
    assert _certificate_render_config(original) is original
