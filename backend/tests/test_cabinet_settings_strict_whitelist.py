from backend.schemas import CabinetConfigUpdate
from pydantic import ValidationError
import pytest


def test_cabinet_update_rejects_unknown_field():
    with pytest.raises(ValidationError):
        CabinetConfigUpdate.model_validate({
            "nom_cabinet": "Cabinet Test",
            "owner_id": 999,
        })


def test_cabinet_update_accepts_documented_aliases():
    model = CabinetConfigUpdate.model_validate({
        "adresse": "10 rue Test",
        "telephone": "0500000000",
        "if": "12345",
    })
    dumped = model.model_dump(by_alias=True)
    assert dumped["adresse"] == "10 rue Test"
    assert dumped["telephone"] == "0500000000"
    assert dumped["if"] == "12345"


def test_cabinet_update_endpoint_rejects_mass_assignment(client, auth_headers):
    response = client.put(
        "/api/clinics/me",
        json={"nom_cabinet": "Cabinet sûr", "owner_id": 999999},
        headers=auth_headers,
    )
    assert response.status_code == 422
