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


def test_legacy_preference_defaults_to_protocol_and_remains_compatible(db):
    doctor = _doctor(db, "neo-reusable-legacy@cabinet.test")
    prescription_service.learn_habit(
        db,
        doctor.id,
        "Post-op",
        [{"name": "MED TEST", "dosage": "1", "forme": "COMPRIME", "posologie": "x"}],
    )

    item = prescription_service.get_doctor_presets(db, doctor.id)[0]
    assert item["kind"] == "PROTOCOL"
    assert item["label"] == "Post-op"
    assert item["is_favorite"] is False
    assert item["usage_count"] == 0
    assert item["last_used"] is None


def test_saved_prescription_keeps_indication_without_patient_data(db):
    doctor = _doctor(db, "neo-reusable-saved@cabinet.test")
    prescription_service.learn_habit(
        db,
        doctor.id,
        "Ordonnance post-op",
        [{
            "name": "MED TEST",
            "dosage": "1",
            "forme": "COMPRIME",
            "posologie": "x",
            "catalogPresentationId": "ammps:test-1",
            "catalogDci": "PARACETAMOL",
            "catalogSourceId": "ammps-current",
            "catalogMarketingStatusVerified": True,
            "patient_id": 999,
        }],
        label="Ordonnance post-op",
        preference_type="SAVED_PRESCRIPTION",
        indication="Douleur postopératoire",
        is_favorite=True,
    )

    item = prescription_service.get_doctor_presets(db, doctor.id)[0]
    assert item["kind"] == "SAVED_PRESCRIPTION"
    assert item["indication"] == "Douleur postopératoire"
    assert item["is_favorite"] is True
    assert item["drugs"][0]["catalogPresentationId"] == "ammps:test-1"
    assert item["drugs"][0]["catalogDci"] == "PARACETAMOL"
    assert item["drugs"][0]["catalogSourceId"] == "ammps-current"
    assert item["drugs"][0]["catalogMarketingStatusVerified"] is True
    assert "patient_id" not in item["drugs"][0]


def test_reusable_usage_is_doctor_scoped_and_updates_dynamic_rank_fields(db):
    owner = _doctor(db, "neo-reusable-owner@cabinet.test")
    other = _doctor(db, "neo-reusable-other@cabinet.test")
    prescription_service.learn_habit(
        db,
        owner.id,
        "Extraction simple",
        [{"name": "MED TEST", "dosage": "", "forme": "", "posologie": ""}],
    )
    item = prescription_service.get_doctor_presets(db, owner.id)[0]

    prescription_service.record_reusable_use(db, owner.id, item["id"])
    updated = prescription_service.get_doctor_presets(db, owner.id)[0]
    assert updated["usage_count"] == 1
    assert updated["last_used"] is not None

    try:
        prescription_service.record_reusable_use(db, other.id, item["id"])
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 404
    else:
        raise AssertionError("cross-doctor reusable usage must fail closed")


def test_same_label_protocol_and_saved_prescription_do_not_overwrite_each_other(db):
    doctor = _doctor(db, "neo-reusable-same-label@cabinet.test")
    prescription_service.learn_habit(
        db,
        doctor.id,
        "Post-op",
        [{"name": "PROTO", "dosage": "1", "forme": "COMPRIME", "posologie": "p"}],
        label="Post-op",
        preference_type="PROTOCOL",
    )
    prescription_service.learn_habit(
        db,
        doctor.id,
        "Post-op",
        [{"name": "SAVED", "dosage": "2", "forme": "GELULE", "posologie": "s"}],
        label="Post-op",
        preference_type="SAVED_PRESCRIPTION",
        indication="Indication sauvegardée",
    )

    rows = prescription_service.get_doctor_presets(db, doctor.id)
    assert len(rows) == 2
    by_kind = {row["kind"]: row for row in rows}
    assert by_kind["PROTOCOL"]["drugs"][0]["name"] == "PROTO"
    assert by_kind["SAVED_PRESCRIPTION"]["drugs"][0]["name"] == "SAVED"
