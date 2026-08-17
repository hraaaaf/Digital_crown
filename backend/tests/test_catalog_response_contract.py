from backend import models
from backend.routers import catalog
from backend.schemas.catalog import SpecialtyCreate


def test_created_specialty_matches_response_contract(db):
    owner = models.User(
        email="response-contract@cabinet.test",
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        nom_complet="Response Contract",
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    row = catalog.create_specialty(
        SpecialtyCreate(name="Pédodontie", color="#334455"),
        db=db,
        current_user=owner,
    )

    assert row["name"] == "Pédodontie"
    assert row["pathologies"] == []
    assert row["acts"] == []
