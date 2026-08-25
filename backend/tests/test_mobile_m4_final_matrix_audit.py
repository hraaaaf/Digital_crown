from datetime import datetime, timedelta

import pytest

from backend import models
from backend.tests.test_mobile_m4d_appointment_context import _appointment, _cabinet, _claim, _issue, _patient


@pytest.fixture(autouse=True)
def _isolate_final_matrix_runtime(tmp_path, monkeypatch):
    from backend.main import _license_cache
    from backend.utils import rate_limit

    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm4-final-rate-limit.json'))
    yield
    _license_cache.clear()


def test_resource_pairing_expiry_is_terminal(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(dentiste)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste, dossier='M4-FINAL-EXP')
    appointment = _appointment(db, dentiste, patient)

    issued = _issue(client, auth_headers, appointment.id)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    assert pairing is not None
    pairing.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.add(pairing)
    db.commit()

    expired = _claim(client, pairing.token)
    assert expired.status_code == 404, expired.text
    assert 'expir' in str(expired.json().get('detail', '')).lower()
    db.refresh(pairing)
    assert pairing.used_at is None


def test_resource_pairing_is_one_shot(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(dentiste)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste, dossier='M4-FINAL-ONCE')
    appointment = _appointment(db, dentiste, patient)

    issued = _issue(client, auth_headers, appointment.id)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    first = _claim(client, pairing.token)
    assert first.status_code == 200, first.text
    second = _claim(client, pairing.token)
    assert second.status_code == 404, second.text
    assert 'utilis' in str(second.json().get('detail', '')).lower()
