"""P4D runtime tests for two-phase onboarding persistence."""
import pytest

from backend import models
from backend.security import get_password_hash


PASSWORD = "TestPass123!"


def _owner(db, email="p4d-owner@test.ma", name="Dr Account Truth"):
    user = models.User(
        email=email,
        hashed_password=get_password_hash(PASSWORD),
        role="DENTISTE",
        nom_complet=name,
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    client.cookies.clear()
    return headers


def _draft_payload(**overrides):
    payload = {
        "nom_cabinet": "Cabinet Setup",
        "nom": "Dr Wizard Truth",
        "nom_praticien_ar": "د. الحقيقة",
        "footer_address": "Rabat, Maroc",
        "inpe": "PRO-SETUP",
        "inpe_etablissement": "EST-SETUP",
        "ice": "ICE-SETUP",
        "if_": "IF-SETUP",
        "specialty_ids": ["generaliste"],
    }
    payload.update(overrides)
    return payload


def test_setup_draft_splits_user_and_organization_truth_and_stays_uninitialized(client, db):
    owner = _owner(db)
    response = client.post(
        "/api/clinics/",
        json=_draft_payload(),
        headers=_headers(client, owner),
    )
    assert response.status_code == 200, response.text

    db.refresh(owner)
    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == owner.id).one()
    assert owner.nom_complet == "Dr Wizard Truth"
    assert owner.nom_complet_ar == "د. الحقيقة"
    assert owner.inpe_professionnel == "PRO-SETUP"
    assert cabinet.nom_cabinet == "Cabinet Setup"
    assert cabinet.inpe_etablissement == "EST-SETUP"
    assert cabinet.ice == "ICE-SETUP"
    assert cabinet.if_ == "IF-SETUP"
    assert cabinet.is_initialized is False
    assert (cabinet.nom_praticien or "") == ""
    assert (cabinet.nom_praticien_ar or "") == ""
    assert (cabinet.inpe or "") == ""


def test_legacy_nom_praticien_alias_still_routes_to_user_not_cabinet(client, db):
    owner = _owner(db, "p4d-legacy-alias@test.ma")
    response = client.post(
        "/api/clinics/",
        json=_draft_payload(nom=None, nom_praticien="Dr Legacy Client"),
        headers=_headers(client, owner),
    )
    assert response.status_code == 200, response.text
    db.refresh(owner)
    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == owner.id).one()
    assert owner.nom_complet == "Dr Legacy Client"
    assert (cabinet.nom_praticien or "") == ""


def test_trial_activation_draft_is_updated_in_place_without_reclassifying_legacy(client, db):
    owner = _owner(db, "p4d-trial@test.ma")
    cabinet = models.CabinetConfig(
        owner_id=owner.id,
        nom_cabinet="Trial Placeholder",
        nom_praticien="Legacy Trial Name",
        inpe="LEGACY-AMBIGUOUS",
        is_initialized=False,
    )
    db.add(cabinet)
    db.commit()
    db.refresh(cabinet)

    response = client.post(
        "/api/clinics/",
        json=_draft_payload(nom_cabinet="Trial Final"),
        headers=_headers(client, owner),
    )
    assert response.status_code == 200, response.text
    assert db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == owner.id).count() == 1

    db.refresh(cabinet)
    db.refresh(owner)
    assert cabinet.id == response.json()["id"]
    assert cabinet.nom_cabinet == "Trial Final"
    assert cabinet.nom_praticien == "Legacy Trial Name"
    assert cabinet.inpe == "LEGACY-AMBIGUOUS"
    assert cabinet.is_initialized is False
    assert owner.nom_complet == "Dr Wizard Truth"
    assert owner.inpe_professionnel == "PRO-SETUP"


def test_complete_setup_is_the_only_transition_to_initialized(client, db):
    owner = _owner(db, "p4d-complete@test.ma")
    headers = _headers(client, owner)
    draft = client.post("/api/clinics/", json=_draft_payload(), headers=headers)
    assert draft.status_code == 200, draft.text

    before = client.get("/api/clinics/init-status", headers=headers)
    assert before.status_code == 200
    assert before.json() == {"is_initialized": False, "needs_setup": True}

    complete = client.post("/api/clinics/complete-setup", headers=headers)
    assert complete.status_code == 200, complete.text
    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == owner.id).one()
    assert cabinet.is_initialized is True

    after = client.get("/api/clinics/init-status", headers=headers)
    assert after.status_code == 200
    assert after.json() == {"is_initialized": True, "needs_setup": False}

    again = client.post("/api/clinics/complete-setup", headers=headers)
    assert again.status_code == 200


def test_complete_setup_refuses_incomplete_minimum_truth(client, db):
    owner = _owner(db, "p4d-incomplete@test.ma")
    cabinet = models.CabinetConfig(
        owner_id=owner.id,
        nom_cabinet="",
        footer_address="",
        is_initialized=False,
    )
    db.add(cabinet)
    db.commit()

    response = client.post("/api/clinics/complete-setup", headers=_headers(client, owner))
    assert response.status_code == 422
    db.refresh(cabinet)
    assert cabinet.is_initialized is False
    assert set(response.json()["detail"]["fields"]) == {"nom_cabinet", "adresse"}


def test_initialized_cabinet_rejects_new_setup_draft_without_mutation(client, db):
    owner = _owner(db, "p4d-initialized@test.ma", name="Dr Stable")
    cabinet = models.CabinetConfig(
        owner_id=owner.id,
        nom_cabinet="Cabinet Stable",
        footer_address="Rabat",
        is_initialized=True,
    )
    db.add(cabinet)
    db.commit()

    response = client.post(
        "/api/clinics/",
        json=_draft_payload(nom_cabinet="Must Not Save", nom="Dr Must Not Save"),
        headers=_headers(client, owner),
    )
    assert response.status_code == 400
    db.refresh(owner)
    db.refresh(cabinet)
    assert owner.nom_complet == "Dr Stable"
    assert cabinet.nom_cabinet == "Cabinet Stable"


def test_setup_draft_commit_failure_rolls_back_user_and_new_organization(client, db, monkeypatch):
    owner = _owner(db, "p4d-rollback@test.ma", name="Dr Before")
    headers = _headers(client, owner)

    def fail_commit():
        raise RuntimeError("forced setup commit failure")

    monkeypatch.setattr(db, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="forced setup commit failure"):
        client.post(
            "/api/clinics/",
            json=_draft_payload(nom="Dr Partial"),
            headers=headers,
        )

    db.refresh(owner)
    assert owner.nom_complet == "Dr Before"
    assert db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == owner.id).first() is None
