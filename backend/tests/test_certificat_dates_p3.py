from datetime import date
from types import SimpleNamespace

from backend.schemas.documents import CertificatData
from backend.services.generators.certificat_gen import _resolve_certificate_dates


def test_certificate_schema_keeps_issue_and_rest_start_dates_distinct():
    data = CertificatData(
        reason="Arrêt de travail",
        days=3,
        doc_date=date(2026, 8, 15),
        start_date=date(2026, 8, 17),
    )
    assert data.doc_date == date(2026, 8, 15)
    assert data.start_date == date(2026, 8, 17)


def test_generator_resolves_issue_and_rest_start_independently():
    data = SimpleNamespace(doc_date="2026-08-15", start_date="2026-08-17")
    issue_date, rest_start = _resolve_certificate_dates(data, today=date(2026, 1, 1))
    assert issue_date == date(2026, 8, 15)
    assert rest_start == date(2026, 8, 17)


def test_legacy_certificate_without_doc_date_falls_back_safely():
    data = SimpleNamespace(doc_date=None, start_date="2026-08-17")
    issue_date, rest_start = _resolve_certificate_dates(data, today=date(2026, 8, 15))
    assert issue_date == date(2026, 8, 15)
    assert rest_start == date(2026, 8, 17)


def test_new_certificate_without_explicit_start_uses_issue_date():
    data = SimpleNamespace(doc_date="2026-08-15", start_date=None)
    issue_date, rest_start = _resolve_certificate_dates(data, today=date(2026, 1, 1))
    assert issue_date == date(2026, 8, 15)
    assert rest_start == date(2026, 8, 15)
