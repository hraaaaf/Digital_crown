import pytest
from pydantic import ValidationError

from backend.schemas.documents import DevisData


def _item(**overrides):
    value = {
        "acte": "Composite 2 faces",
        "dent": "texte libre obsolète",
        "dents": [16],
        "prix_unitaire": 700,
    }
    value.update(overrides)
    return value


def _teeth_data(**overrides):
    value = {
        "tooth_number": 16,
        "treatments": [{"code": "COMP2", "name": "Composite 2 faces", "price": 700}],
        "surfaces": ["M", "O"],
        "notes": "Carie profonde",
    }
    value.update(overrides)
    return value


def test_structured_dents_are_sorted_and_deduplicated():
    data = DevisData(items=[_item(dents=[16, 14, 16])])
    assert data.items[0].dents == [14, 16]
    assert data.items[0].dent == "14, 16"


def test_matching_teeth_data_is_accepted():
    data = DevisData(items=[_item()], teeth_data=[_teeth_data()])
    assert data.teeth_data[0].tooth_number == 16


def test_teeth_data_rejects_orphan_tooth():
    with pytest.raises(ValidationError):
        DevisData(items=[_item(dents=[16])], teeth_data=[_teeth_data(tooth_number=17)])


def test_teeth_data_rejects_orphan_treatment_name():
    with pytest.raises(ValidationError):
        DevisData(
            items=[_item()],
            teeth_data=[_teeth_data(treatments=[{"code": "ENDO", "name": "Traitement canalaire", "price": 700}])],
        )


def test_teeth_data_rejects_price_divergence():
    with pytest.raises(ValidationError):
        DevisData(
            items=[_item(prix_unitaire=700)],
            teeth_data=[_teeth_data(treatments=[{"code": "COMP2", "name": "Composite 2 faces", "price": 701}])],
        )


def test_teeth_data_rejects_duplicate_tooth_entries():
    with pytest.raises(ValidationError):
        DevisData(items=[_item()], teeth_data=[_teeth_data(), _teeth_data()])
