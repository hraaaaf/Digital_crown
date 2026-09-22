from fastapi import HTTPException

from backend import models
from backend.services.prescription_service import prescription_service


def _doctor(db, email: str):
    user = models.User(
        email=email,
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        nom_complet=email,
        permissions={"prescriptions": True},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_prescription_preset_is_doctor_scoped_and_whitelists_reusable_fields(db):
    doctor_a = _doctor(db, "cust04-a@cabinet.test")
    doctor_b = _doctor(db, "cust04-b@cabinet.test")

    prescription_service.learn_habit(
        db,
        doctor_a.id,
        "Mon post-op",
        [{
            "name": "PARACETAMOL",
            "dosage": "1g",
            "forme": "Comprimés",
            "posologie": "1 cp si douleur",
            "type": "MEDICAMENT",
            "quantite": 2,
            "non_substituable": True,
            "patient_id": 999,
            "indication": "NE DOIT PAS ETRE PERSISTEE",
        }],
    )

    presets_a = prescription_service.get_doctor_presets(db, doctor_a.id)
    presets_b = prescription_service.get_doctor_presets(db, doctor_b.id)

    assert len(presets_a) == 1
    assert presets_b == []

    stored = presets_a[0]["drugs"][0]
    assert stored == {
        "name": "PARACETAMOL",
        "dosage": "1g",
        "forme": "Comprimés",
        "posologie": "1 cp si douleur",
        "type": "MEDICAMENT",
        "quantite": 2,
        "non_substituable": True,
    }
    assert "patient_id" not in stored
    assert "indication" not in stored


def test_prescription_preset_same_name_updates_only_current_doctor(db):
    doctor = _doctor(db, "cust04-update@cabinet.test")

    prescription_service.learn_habit(
        db,
        doctor.id,
        "Preset A",
        [{"name": "A", "dosage": "", "forme": "", "posologie": "old"}],
    )
    prescription_service.learn_habit(
        db,
        doctor.id,
        "preset   a",
        [{"name": "B", "dosage": "", "forme": "", "posologie": "new"}],
    )

    presets = prescription_service.get_doctor_presets(db, doctor.id)
    assert len(presets) == 1
    assert presets[0]["act_context"] == "PRESET A"
    assert presets[0]["drugs"][0]["name"] == "B"
    assert presets[0]["drugs"][0]["posologie"] == "new"


def test_other_doctor_cannot_delete_prescription_preset(db):
    owner = _doctor(db, "cust04-owner@cabinet.test")
    other = _doctor(db, "cust04-other@cabinet.test")

    prescription_service.learn_habit(
        db,
        owner.id,
        "Preset protégé",
        [{"name": "A", "dosage": "", "forme": "", "posologie": "x"}],
    )

    try:
        prescription_service.delete_doctor_preset(db, other.id, "Preset protégé")
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("cross-doctor preset deletion must fail closed")

    assert len(prescription_service.get_doctor_presets(db, owner.id)) == 1
