from backend.schemas.documents import CertificatData
from backend.services.generators.certificat_gen import (
    _format_free_certificate_content,
    _is_free_medical_certificate,
)


def test_certificat_data_accepts_explicit_practitioner_content():
    data = CertificatData(
        reason='Certificat médical',
        days=0,
        content='Texte libre du praticien',
    )
    assert data.reason == 'Certificat médical'
    assert data.content == 'Texte libre du praticien'
    assert data.days == 0


def test_free_certificate_reason_is_explicit_not_fuzzy():
    assert _is_free_medical_certificate('Certificat médical') is True
    assert _is_free_medical_certificate('CERTIFICAT MEDICAL') is True
    assert _is_free_medical_certificate('Certificat de Présence') is False
    assert _is_free_medical_certificate('Arrêt de travail') is False


def test_free_certificate_content_is_preserved_but_reportlab_markup_is_escaped():
    rendered = _format_free_certificate_content('Ligne 1
<diagnostic> & contrôle')
    assert rendered == 'Ligne 1<br/>&lt;diagnostic&gt; &amp; contrôle'


def test_free_certificate_rejects_empty_content():
    try:
        _format_free_certificate_content('   ')
    except ValueError as exc:
        assert 'contenu du certificat médical' in str(exc).lower()
    else:
        raise AssertionError('Un certificat médical libre vide doit être refusé')
