from types import SimpleNamespace

import pytest

from backend.schemas.documents import CertificatData
from backend.services.certificate_payload_policy import (
    CERTIFICATE_TYPE_FREE,
    CERTIFICATE_TYPE_PRESENCE,
    CERTIFICATE_TYPE_WORK_STOP,
    normalize_and_validate_certificate_data,
)


def _data(**kwargs):
    defaults = {
        "reason": CERTIFICATE_TYPE_WORK_STOP,
        "days": 1,
        "start_date": None,
        "content": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_api_default_reason_is_rejected_when_practitioner_did_not_send_it():
    data = CertificatData()
    with pytest.raises(ValueError, match="nature du certificat.*explicitement"):
        normalize_and_validate_certificate_data(data)


def test_api_default_days_are_rejected_when_work_stop_duration_was_not_sent():
    data = CertificatData(reason=CERTIFICATE_TYPE_WORK_STOP)
    with pytest.raises(ValueError, match="durée.*explicitement"):
        normalize_and_validate_certificate_data(data)


def test_explicit_empty_reason_is_rejected_instead_of_becoming_work_stop():
    data = CertificatData(reason="", days=3)
    with pytest.raises(ValueError, match="nature du certificat.*explicitement"):
        normalize_and_validate_certificate_data(data)


def test_explicit_work_stop_reason_and_duration_are_accepted():
    data = CertificatData(reason=CERTIFICATE_TYPE_WORK_STOP, days=3)
    validated = normalize_and_validate_certificate_data(data)
    assert validated.reason == CERTIFICATE_TYPE_WORK_STOP
    assert validated.days == 3


def test_legacy_work_stop_is_normalized_without_changing_valid_duration():
    data = normalize_and_validate_certificate_data(_data(reason="Repos Post-Opératoire", days=4))
    assert data.reason == CERTIFICATE_TYPE_WORK_STOP
    assert data.days == 4


def test_unknown_legacy_reason_becomes_free_certificate_not_work_stop():
    data = normalize_and_validate_certificate_data(_data(reason="Contrôle postopératoire", days=5))
    assert data.reason == CERTIFICATE_TYPE_FREE
    assert data.content == "Contrôle postopératoire"
    assert data.days == 0
    assert data.start_date is None


def test_free_certificate_requires_practitioner_content():
    with pytest.raises(ValueError, match="contenu du certificat médical"):
        normalize_and_validate_certificate_data(_data(reason=CERTIFICATE_TYPE_FREE, content="   "))


@pytest.mark.parametrize("days", [None, True, 0, -1, 366])
def test_work_stop_rejects_invalid_duration(days):
    with pytest.raises(ValueError, match="1 et 365 jours"):
        normalize_and_validate_certificate_data(_data(days=days))


def test_presence_discards_stale_duration_start_and_content():
    data = normalize_and_validate_certificate_data(
        _data(
            reason=CERTIFICATE_TYPE_PRESENCE,
            days=12,
            start_date="2026-08-20",
            content="ancien texte",
        )
    )
    assert data.reason == CERTIFICATE_TYPE_PRESENCE
    assert data.days == 0
    assert data.start_date is None
    assert data.content is None


def test_free_certificate_trims_content_and_discards_rest_fields():
    data = normalize_and_validate_certificate_data(
        _data(
            reason=CERTIFICATE_TYPE_FREE,
            days=9,
            start_date="2026-08-20",
            content="  Texte du praticien  ",
        )
    )
    assert data.reason == CERTIFICATE_TYPE_FREE
    assert data.content == "Texte du praticien"
    assert data.days == 0
    assert data.start_date is None
