from datetime import date
from types import SimpleNamespace

import fitz
from PIL import Image

from backend.services.base_template import BaseTemplate
from backend.services.generators.installment_gen import (
    _cabinet_logo_flowable,
    generate_installment_plan,
)


def _config(logo_path="clinics/cabinet/logo.png", scale=1.0):
    return SimpleNamespace(
        logo_path=logo_path,
        header_logo_scale=scale,
        nom_cabinet="Cabinet Logo",
        footer_address="1 rue Test",
        footer_phones="0500000000",
        contacts_json={},
    )


def test_installment_logo_flowable_uses_configured_brand_asset(monkeypatch, tmp_path):
    logo_file = tmp_path / "logo.png"
    Image.new("RGB", (600, 240), "white").save(logo_file)
    monkeypatch.setattr(BaseTemplate, "_resolve_brand_asset", lambda self, value: str(logo_file))

    flowable = _cabinet_logo_flowable(_config())

    assert flowable is not None
    assert flowable.filename == str(logo_file)
    assert flowable.hAlign == "CENTER"


def test_installment_logo_flowable_is_optional(monkeypatch):
    monkeypatch.setattr(BaseTemplate, "_resolve_brand_asset", lambda self, value: None)
    assert _cabinet_logo_flowable(_config(logo_path=None)) is None


def test_installment_pdf_contains_configured_logo_image(monkeypatch, tmp_path):
    logo_file = tmp_path / "logo.png"
    Image.new("RGB", (600, 240), "white").save(logo_file)
    monkeypatch.setattr(BaseTemplate, "_resolve_brand_asset", lambda self, value: str(logo_file))

    patient = SimpleNamespace(nom="TEST", prenom="Patient")
    installment = SimpleNamespace(
        label="Acompte",
        due_date=date(2026, 10, 10),
        amount=500.0,
        status="EN_ATTENTE",
    )
    plan = SimpleNamespace(
        title="Traitement test",
        total_amount=500.0,
        installments=[installment],
    )

    filepath = generate_installment_plan(plan, patient, _config(), str(tmp_path / "out"))
    pdf = fitz.open(filepath)
    try:
        assert pdf.page_count == 1
        assert pdf[0].get_images(full=True)
    finally:
        pdf.close()
