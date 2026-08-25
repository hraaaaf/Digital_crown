import base64
import inspect
from io import BytesIO

import pytest
from fastapi import HTTPException
from PIL import Image, ImageDraw

from backend.routers import mobile_legacy


def _data_url(*, blank=False, size=(360, 210)):
    image = Image.new('RGBA', size, (255, 255, 255, 0))
    if not blank:
        draw = ImageDraw.Draw(image)
        draw.line([(45, 120), (110, 80), (175, 135), (300, 75)], fill=(30, 27, 75, 255), width=6)
    output = BytesIO()
    image.save(output, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode()


def test_mobile_signature_validator_accepts_real_png_and_rewrites_it():
    normalized = mobile_legacy._validated_mobile_signature_png(_data_url())
    with Image.open(BytesIO(normalized)) as image:
        assert image.format == 'PNG'
        assert image.size == (360, 210)
        assert image.mode == 'RGBA'
        assert image.info == {}


@pytest.mark.parametrize('payload', [
    '',
    'not-a-data-url',
    'data:image/jpeg;base64,ZmFrZQ==',
    'data:image/png;base64,***',
])
def test_mobile_signature_validator_rejects_malformed_payload(payload):
    with pytest.raises(HTTPException) as exc:
        mobile_legacy._validated_mobile_signature_png(payload)
    assert exc.value.status_code in {400, 413, 422}


def test_mobile_signature_validator_rejects_blank_canvas():
    with pytest.raises(HTTPException) as exc:
        mobile_legacy._validated_mobile_signature_png(_data_url(blank=True))
    assert exc.value.status_code == 422
    assert 'vide' in str(exc.value.detail).lower()


def test_mobile_signature_validator_enforces_byte_and_pixel_limits(monkeypatch):
    monkeypatch.setattr(mobile_legacy, '_MOBILE_SIGNATURE_MAX_BYTES', 64)
    with pytest.raises(HTTPException) as exc:
        mobile_legacy._validated_mobile_signature_png(_data_url())
    assert exc.value.status_code == 413

    monkeypatch.setattr(mobile_legacy, '_MOBILE_SIGNATURE_MAX_BYTES', 2 * 1024 * 1024)
    monkeypatch.setattr(mobile_legacy, '_MOBILE_SIGNATURE_MAX_PIXELS', 100)
    with pytest.raises(HTTPException) as exc:
        mobile_legacy._validated_mobile_signature_png(_data_url(size=(32, 32)))
    assert exc.value.status_code == 413


def test_mobile_signature_routes_keep_tenant_permission_and_block_resign():
    listing = inspect.getsource(mobile_legacy.get_mobile_patient_documents)
    signing = inspect.getsource(mobile_legacy.sign_mobile_document)

    assert 'require_mobile_permission("patients")' in signing
    assert 'models.Patient.employer_id == employer_id' in signing
    assert 'models.DocumentArchive.document_type == models.DocumentType.DEVIS' in signing
    assert 'with_for_update()' in signing
    assert 'cdata.get("signed", False)' in signing
    assert 'status_code=409' in signing
    assert 'if signed:' in listing and 'continue' in listing
