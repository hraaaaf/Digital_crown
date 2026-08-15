from datetime import date, datetime
from types import SimpleNamespace

from backend.services.generators.certificat_gen import _resolve_certificate_date


def test_certificate_date_prefers_start_date_from_document_studio():
    data = SimpleNamespace(start_date=date(2026, 8, 10), doc_date=date(2026, 8, 1))
    assert _resolve_certificate_date(data) == date(2026, 8, 10)


def test_certificate_date_accepts_legacy_doc_date_when_start_date_missing():
    data = SimpleNamespace(start_date=None, doc_date='2026-08-09')
    assert _resolve_certificate_date(data) == date(2026, 8, 9)


def test_certificate_date_accepts_datetime_values():
    data = SimpleNamespace(start_date=datetime(2026, 8, 8, 12, 30), doc_date=None)
    assert _resolve_certificate_date(data) == date(2026, 8, 8)
