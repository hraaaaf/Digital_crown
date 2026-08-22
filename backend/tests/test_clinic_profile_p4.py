"""P4C runtime tests for the atomic `/clinics/me` Settings facade."""
import pytest

from backend import models
from backend.security import get_password_hash


def _owner(db, email="p4c-owner@test.ma"):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr User Before",
        is_active=True,
        is_licensed=True,
    )
    user.nom_complet_ar = "د. قبل"
    user.inpe_professionnel = "PRO-BEFORE"
    db.add(user)
    db.commit()
    db.refresh(user)

    cabinet = models.CabinetConfig(
        owner_id=user.id,
        nom_cabinet="Cabinet Before",
        nom_praticien="Legacy Cabinet Practitioner",
        nom_praticien_ar="طبيب قديم",
        inpe="LEGACY-AMBIGUOUS",
        inpe_etablissement="EST-BEFORE",
        is_initialized=True,
    )
    db.add(cabinet)
    db.commit()
    db.refresh(cabinet)
    return user, cabinet


def _headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    client.cookies.clear()
    return headers


def test_get_profile_exposes_user_truth_and_hides_legacy_inpe_meaning(client, db):
    owner, cabinet = _owner(db)
    response = client.get("/api/clinics/me", headers=_headers(client, owner))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["nom_praticien"] == "Dr User Before"
    assert body["nom_praticien_ar"] == "د. قبل"
    assert body["inpe"] == "PRO-BEFORE"
    assert body["inpe_professionnel"] == "PRO-BEFORE"
    assert body["inpe_etablissement"] == "EST-BEFORE"
    assert body["inpe"] != cabinet.inpe


def test_put_profile_updates_user_and_org_in_one_contract_without_legacy_backwrite(client, db):
    owner, cabinet = _owner(db, "p4c-update@test.ma")
    response = client.put(
        "/api/clinics/me",
        json={
            "nom": "Dr User After",
            "nom_praticien_ar": "د. بعد",
            "inpe": "PRO-AFTER",
            "nom_cabinet": "Cabinet After",
            "inpe_etablissement": "EST-AFTER",
            "ice": "ICE-42",
            "if_": "IF-42",
        },
        headers=_headers(client, owner),
    )
    assert response.status_code == 200, response.text

    db.refresh(owner)
    db.refresh(cabinet)
    assert owner.nom_complet == "Dr User After"
    assert owner.nom_complet_ar == "د. بعد"
    assert owner.inpe_professionnel == "PRO-AFTER"
    assert cabinet.nom_cabinet == "Cabinet After"
    assert cabinet.inpe_etablissement == "EST-AFTER"
    assert cabinet.ice == "ICE-42"
    assert cabinet.if_ == "IF-42"
    assert cabinet.nom_praticien == "Legacy Cabinet Practitioner"
    assert cabinet.nom_praticien_ar == "طبيب قديم"
    assert cabinet.inpe == "LEGACY-AMBIGUOUS"


def test_subaccount_full_form_echo_can_update_org_but_not_practitioner(client, db):
    owner, cabinet = _owner(db, "p4c-boss@test.ma")
    child = models.User(
        email="p4c-child@test.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr Child",
        employer_id=owner.id,
        permissions={"settings": True},
        is_active=True,
        is_licensed=True,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    headers = _headers(client, child)

    allowed = client.put(
        "/api/clinics/me",
        json={
            "nom": owner.nom_complet,
            "nom_praticien_ar": owner.nom_complet_ar,
            "inpe": owner.inpe_professionnel,
            "nom_cabinet": "Cabinet Team Edit",
        },
        headers=headers,
    )
    assert allowed.status_code == 200, allowed.text
    db.refresh(cabinet)
    assert cabinet.nom_cabinet == "Cabinet Team Edit"

    forbidden = client.put(
        "/api/clinics/me",
        json={
            "nom": "Dr Forbidden",
            "nom_cabinet": "Must Not Partially Save",
        },
        headers=headers,
    )
    assert forbidden.status_code == 403
    db.refresh(owner)
    db.refresh(cabinet)
    assert owner.nom_complet == "Dr User Before"
    assert cabinet.nom_cabinet == "Cabinet Team Edit"


def test_commit_failure_rolls_back_user_and_organization(client, db, monkeypatch):
    owner, cabinet = _owner(db, "p4c-rollback@test.ma")
    headers = _headers(client, owner)

    def fail_commit():
        raise RuntimeError("forced commit failure")

    monkeypatch.setattr(db, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="forced commit failure"):
        client.put(
            "/api/clinics/me",
            json={"nom": "Partial User", "nom_cabinet": "Partial Cabinet"},
            headers=headers,
        )

    db.refresh(owner)
    db.refresh(cabinet)
    assert owner.nom_complet == "Dr User Before"
    assert cabinet.nom_cabinet == "Cabinet Before"


def test_blank_practitioner_name_is_rejected_without_org_mutation(client, db):
    owner, cabinet = _owner(db, "p4c-blank@test.ma")
    response = client.put(
        "/api/clinics/me",
        json={"nom": "   ", "nom_cabinet": "Must Not Save"},
        headers=_headers(client, owner),
    )
    assert response.status_code == 422
    db.refresh(owner)
    db.refresh(cabinet)
    assert owner.nom_complet == "Dr User Before"
    assert cabinet.nom_cabinet == "Cabinet Before"
