from backend import models
from backend.services.generators.ordonnance_gen import OrdonnanceGenerator


def test_ordonnance_resolves_branding_from_employer_cabinet(db):
    owner = models.User(
        email="owner-branding@example.test",
        hashed_password="test",
        role=models.UserRole.ADMIN,
        nom_complet="Dr Owner",
        is_active=True,
        is_licensed=True,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    cabinet = models.CabinetConfig(
        owner_id=owner.id,
        nom_cabinet="Cabinet Branding",
        nom_praticien="Dr Owner",
        logo_path="clinics/cabinet-test/logo.png",
    )
    db.add(cabinet)
    db.commit()
    db.refresh(cabinet)

    practitioner = models.User(
        email="practitioner-branding@example.test",
        hashed_password="test",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Practitioner",
        is_active=True,
        is_licensed=True,
        employer_id=owner.id,
    )
    db.add(practitioner)
    db.commit()
    db.refresh(practitioner)

    generator = OrdonnanceGenerator()
    resolved_config, resolved_actor = generator._resolve_branding_context(db, practitioner.id)

    assert resolved_actor.id == practitioner.id
    assert resolved_config.owner_id == owner.id
    assert resolved_config.logo_path == "clinics/cabinet-test/logo.png"
