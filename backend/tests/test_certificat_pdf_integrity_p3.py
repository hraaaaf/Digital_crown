from datetime import date
from types import SimpleNamespace

from backend.services.generators.certificat_gen import (
    CertificatGenerator,
    _certificate_config_owner_id,
    _safe_pdf_text,
)


def test_certificate_age_is_computed_on_issue_date_not_runtime_date(tmp_path):
    generator = CertificatGenerator(output_dir=str(tmp_path))
    born = date(2010, 8, 16)

    assert generator._calculate_age(born, date(2025, 8, 15)) == 14
    assert generator._calculate_age(born, date(2025, 8, 16)) == 15


def test_certificate_dynamic_text_is_escaped_before_reportlab_markup():
    assert _safe_pdf_text('Dr A&B <Test>') == 'Dr A&amp;B &lt;Test&gt;'


def test_certificate_branding_uses_employer_for_sub_dentist():
    user = SimpleNamespace(get_employer_id=lambda: 42)
    assert _certificate_config_owner_id(user, 7) == 42


def test_certificate_branding_falls_back_to_current_user_without_user_object():
    assert _certificate_config_owner_id(None, 7) == 7
