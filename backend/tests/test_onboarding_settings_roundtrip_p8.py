"""P8 end-to-end regression: onboarding persistence must equal Settings truth.

T27 is intentionally cross-surface: it starts through the setup API, completes the
2-phase onboarding, then reloads the canonical Settings facade. This prevents the two
surfaces from drifting while still passing isolated unit tests.
"""
from backend import models
from backend.security import get_password_hash


PASSWORD = "TestPass123!"


def _owner(db):
    user = models.User(
        email="p8-roundtrip@test.ma",
        hashed_password=get_password_hash(PASSWORD),
        role="DENTISTE",
        nom_complet="Dr Before Roundtrip",
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


def test_onboarding_complete_reloads_exactly_through_settings_profile(client, db):
    owner = _owner(db)
    headers = _headers(client, owner)
    contacts = {
        "fixe": {"enabled": True, "value": "0537000000"},
        "mobile": {"enabled": True, "value": "0612345678"},
        "whatsapp": {"enabled": True, "value": "0612345678"},
        "instagram": {"enabled": False, "value": ""},
    }
    payload = {
        "cabinet_type": "CLINIQUE",
        "nom_cabinet": "Centre Dentaire Roundtrip",
        "nom": "Dr Roundtrip Truth",
        "nom_praticien_ar": "د. حقيقة الجولة",
        "footer_address": "12 Avenue de la Vérité, Rabat",
        "ice": "ICE-ROUNDTRIP",
        "if_": "IF-ROUNDTRIP",
        "inpe": "PRO-ROUNDTRIP",
        "inpe_etablissement": "EST-ROUNDTRIP",
        "specialty_ids": ["generaliste"],
        "custom_specialty_fr": "Dentisterie numérique",
        "custom_specialty_ar": "طب الأسنان الرقمي",
        "contacts_json": contacts,
        "primary_color": "#123456",
        "secondary_color": "#234567",
        "accent_color": "#345678",
        "font_fr": "inter",
        "selected_template": "swiss",
        "selected_theme": "elite",
        "qr_code_enabled": True,
        "qr_code_type": "VALIDATION",
        "qr_code_style": "dots",
    }

    draft = client.post("/api/clinics/", json=payload, headers=headers)
    assert draft.status_code == 200, draft.text
    assert draft.json()["is_initialized"] is False

    complete = client.post("/api/clinics/complete-setup", headers=headers)
    assert complete.status_code == 200, complete.text
    assert complete.json()["is_initialized"] is True

    # Reload from the Settings source of truth, not from setup response/session state.
    settings = client.get("/api/clinics/me", headers=headers)
    assert settings.status_code == 200, settings.text
    body = settings.json()

    expected = {
        "cabinet_type": "CLINIQUE",
        "nom_cabinet": payload["nom_cabinet"],
        "nom": payload["nom"],
        "nom_praticien": payload["nom"],
        "nom_praticien_ar": payload["nom_praticien_ar"],
        "footer_address": payload["footer_address"],
        "ice": payload["ice"],
        "if_": payload["if_"],
        "inpe": payload["inpe"],
        "inpe_professionnel": payload["inpe"],
        "inpe_etablissement": payload["inpe_etablissement"],
        "specialty_ids": payload["specialty_ids"],
        "custom_specialty_fr": payload["custom_specialty_fr"],
        "custom_specialty_ar": payload["custom_specialty_ar"],
        "contacts_json": contacts,
        "primary_color": payload["primary_color"],
        "secondary_color": payload["secondary_color"],
        "accent_color": payload["accent_color"],
        "font_fr": "inter",
        "selected_template": "swiss",
        "selected_theme": "elite",
        "qr_code_enabled": True,
        "qr_code_type": "VALIDATION",
        "qr_code_style": "dots",
        "is_initialized": True,
    }
    for key, value in expected.items():
        assert body[key] == value, f"Settings drift on {key}: {body.get(key)!r} != {value!r}"

    db.refresh(owner)
    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == owner.id).one()
    assert owner.nom_complet == payload["nom"]
    assert owner.nom_complet_ar == payload["nom_praticien_ar"]
    assert owner.inpe_professionnel == payload["inpe"]
    assert cabinet.inpe_etablissement == payload["inpe_etablissement"]

    # Legacy duplicate practitioner identity must not be repopulated by the round-trip.
    assert (cabinet.nom_praticien or "") == ""
    assert (cabinet.nom_praticien_ar or "") == ""
    assert (cabinet.inpe or "") == ""
