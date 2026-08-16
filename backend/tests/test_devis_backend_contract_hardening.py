import pytest
from pydantic import ValidationError

from backend.schemas.documents import DevisData


def _item(**overrides):
    value = {
        "acte": "Composite",
        "dent": "texte libre obsolète",
        "dents": [11],
        "prix_unitaire": 500,
    }
    value.update(overrides)
    return value


def _tooth_data(**overrides):
    value = {
        "tooth_number": 11,
        "treatments": [{"code": "COMP", "name": "Composite", "price": 500}],
        "surfaces": ["M", "O"],
        "notes": "Carie profonde",
    }
    value.update(overrides)
    return value


def test_devis_requires_at_least_one_real_item_after_phase_sanitizing():
    with pytest.raises(ValidationError):
        DevisData(items=[{"acte": "--- PHASE 1 ---", "prix_unitaire": 0}])


def test_devis_rejects_non_empty_installments():
    with pytest.raises(ValidationError):
        DevisData(
            items=[_item()],
            installments=[{"label": "Versement", "amount": 100, "date": "2026-09-01"}],
        )


def test_devis_rejects_negative_or_excessive_amounts():
    with pytest.raises(ValidationError):
        DevisData(items=[_item(prix_unitaire=-1)])
    with pytest.raises(ValidationError):
        DevisData(items=[_item(prix_unitaire=1_000_001)])


def test_devis_rejects_invalid_fdi_numbers():
    with pytest.raises(ValidationError):
        DevisData(items=[_item(dents=[19])])


def test_structured_teeth_are_canonical_over_free_text_dent():
    data = DevisData(items=[_item(dents=[11, "21"])])
    assert data.items[0].dents == [11, 21]
    assert data.items[0].dent == "11, 21"


def test_empty_installment_list_remains_backward_compatible():
    data = DevisData(items=[_item()], installments=[])
    assert data.installments == []


def test_devis_accepts_teeth_data_matching_item_tooth_act_and_price():
    data = DevisData(items=[_item()], teeth_data=[_tooth_data()])
    assert data.teeth_data[0].tooth_number == 11
    assert data.teeth_data[0].treatments[0].name == "Composite"


def test_devis_rejects_orphan_teeth_data_tooth():
    with pytest.raises(ValidationError):
        DevisData(items=[_item()], teeth_data=[_tooth_data(tooth_number=21)])


def test_devis_rejects_teeth_data_act_not_present_on_item():
    with pytest.raises(ValidationError):
        DevisData(
            items=[_item()],
            teeth_data=[_tooth_data(treatments=[{"code": "ENDO", "name": "Endodontie", "price": 500}])],
        )


def test_devis_rejects_teeth_data_price_mismatch():
    with pytest.raises(ValidationError):
        DevisData(
            items=[_item()],
            teeth_data=[_tooth_data(treatments=[{"code": "COMP", "name": "Composite", "price": 650}])],
        )


def test_devis_rejects_invalid_fdi_in_teeth_data():
    with pytest.raises(ValidationError):
        DevisData(items=[_item()], teeth_data=[_tooth_data(tooth_number=19)])


def test_devis_rejects_empty_teeth_data_treatments():
    with pytest.raises(ValidationError):
        DevisData(items=[_item()], teeth_data=[_tooth_data(treatments=[])])
