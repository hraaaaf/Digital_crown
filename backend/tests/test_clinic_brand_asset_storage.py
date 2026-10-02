from datetime import datetime

import fitz
import pytest
from PIL import Image

from backend.core.clinic_assets import resolve_clinic_asset


def test_external_branding_takes_precedence_and_legacy_remains_readable(tmp_path, monkeypatch):
    media = tmp_path / 'media'
    legacy = tmp_path / 'legacy'
    monkeypatch.setenv('MEDIA_ROOT', str(media))
    relative = 'clinics/test-cabinet/logo.png'
    for root in (media, legacy):
        asset = root / relative
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b'logo')
    assert resolve_clinic_asset(relative, legacy, 'test-cabinet') == str((media / relative).resolve())
    (media / relative).unlink()
    assert resolve_clinic_asset(relative, legacy, 'test-cabinet') == str((legacy / relative).resolve())


@pytest.mark.parametrize('value', ['../outside.png', '/outside.png', 'C:/outside.png',
                                  'clinics/another-cabinet/logo.png', 'bad\x00.png'])
def test_branding_rejects_escaping_or_other_cabinet_paths(tmp_path, monkeypatch, value):
    monkeypatch.setenv('MEDIA_ROOT', str(tmp_path / 'media'))
    assert resolve_clinic_asset(value, tmp_path / 'legacy', 'test-cabinet') is None


@pytest.mark.parametrize('asset_field', ['logo_path', 'letterhead_path'])
def test_real_document_preview_embeds_external_cabinet_logo(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch, asset_field
):
    """HTTP route, real generator and PDF image decoding; isolated synthetic DB."""
    from backend import database, models
    from backend.routers import documents
    from backend.services.generators.libre_gen import LibreGenerator

    assert str(database.engine.url) == 'sqlite:///:memory:'
    media = tmp_path / 'media'
    monkeypatch.setenv('MEDIA_ROOT', str(media))
    relative = 'clinics/logo-smoke/logo.png'
    logo = media / relative
    logo.parent.mkdir(parents=True)
    Image.new('RGB', (83, 47), '#d73161').save(logo)
    config = models.CabinetConfig(owner_id=dentiste.id, public_id='logo-smoke',
                                 use_letterhead=asset_field == 'letterhead_path',
                                 **{asset_field: relative})
    patient = models.Patient(nom='TEST', prenom='Logo', date_naissance=datetime(1990, 1, 1),
                             sexe='M', employer_id=dentiste.id)
    db.add_all([config, patient])
    db.commit()
    db.refresh(patient)
    monkeypatch.setattr(documents.doc_factory, 'libre_gen', LibreGenerator(str(tmp_path / 'documents')))
    before = db.query(models.DocumentArchive).count()
    payload = {'type': 'libre', 'patient_id': patient.id, 'is_accounted': False,
               'data': {'titre': 'Test logo', 'contenu': 'Document de verification.'}}
    # Reconstruct the previous lookup failure using only isolated test assets.
    logo.rename(logo.with_suffix('.unavailable'))
    baseline = client.post('/api/documents/generate?preview=true', headers=auth_headers, json=payload)
    assert baseline.status_code == 200, baseline.text
    with fitz.open(baseline.json()['pdf_url']) as pdf:
        assert not any(image[2:4] == (83, 47) for image in pdf[0].get_images())
        pdf[0].get_pixmap().save(str(tmp_path / 'before.png'))
    logo.with_suffix('.unavailable').rename(logo)
    response = client.post('/api/documents/generate?preview=true', headers=auth_headers, json=payload)
    assert response.status_code == 200, response.text
    pdf_path = response.json()['pdf_url']
    with fitz.open(pdf_path) as pdf:
        images = [pdf.extract_image(image[0]) for image in pdf[0].get_images()]
        assert any(image['width'] == 83 and image['height'] == 47 for image in images)
        pdf[0].get_pixmap().save(str(tmp_path / 'after.png'))
    assert db.query(models.DocumentArchive).count() == before

