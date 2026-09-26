from fastapi import HTTPException

from backend import models
from backend.routers import motifs, patients
from backend.schemas.patient import PatientCreate


def _user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        nom_complet=email,
        permissions={"settings": True, "patients": True},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_custom_motif_is_tenant_scoped_and_round_trips(db):
    owner_a = _user(db, "motif-a@cabinet.test")
    owner_b = _user(db, "motif-b@cabinet.test")

    created = motifs.create_cabinet_motif(
        motifs.CabinetMotifCreate(
            label="Douleur après pose couronne",
            category_id="PROTHESE",
            urgency="normal",
        ),
        db=db,
        current_user=owner_a,
    )

    assert created["id"].startswith("cm_")
    assert created["source"] == "cabinet"
    assert created["category_id"] == "PROTHESE"
    assert created["is_active"] is True

    assert [row["id"] for row in motifs.list_cabinet_motifs(db=db, current_user=owner_a)] == [created["id"]]
    assert motifs.list_cabinet_motifs(db=db, current_user=owner_b) == []


def test_custom_motif_duplicate_label_is_case_insensitive(db):
    owner = _user(db, "motif-duplicate@cabinet.test")
    motifs.create_cabinet_motif(
        motifs.CabinetMotifCreate(label="Contrôle gouttière", category_id="ORTHODONTIE"),
        db=db,
        current_user=owner,
    )

    try:
        motifs.create_cabinet_motif(
            motifs.CabinetMotifCreate(label="contrôle gouttière", category_id="ORTHODONTIE"),
            db=db,
            current_user=owner,
        )
    except HTTPException as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("duplicate active motif must be rejected")


def test_custom_motif_deactivation_preserves_history_visibility(db):
    owner = _user(db, "motif-inactive@cabinet.test")
    created = motifs.create_cabinet_motif(
        motifs.CabinetMotifCreate(label="Ancien motif cabinet"),
        db=db,
        current_user=owner,
    )

    deactivated = motifs.deactivate_cabinet_motif(created["id"], db=db, current_user=owner)
    assert deactivated["is_active"] is False
    assert motifs.list_cabinet_motifs(db=db, current_user=owner) == []

    all_rows = motifs.list_cabinet_motifs(include_inactive=True, db=db, current_user=owner)
    assert len(all_rows) == 1
    assert all_rows[0]["id"] == created["id"]
    assert all_rows[0]["is_active"] is False


def test_custom_motif_rejects_unknown_category(db):
    owner = _user(db, "motif-category@cabinet.test")
    try:
        motifs.create_cabinet_motif(
            motifs.CabinetMotifCreate(label="Motif", category_id="UNKNOWN"),
            db=db,
            current_user=owner,
        )
    except HTTPException as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("unknown category must fail closed")


def test_custom_motif_round_trip_through_patient_record(db):
    owner = _user(db, "motif-patient-e2e@cabinet.test")
    created_motif = motifs.create_cabinet_motif(
        motifs.CabinetMotifCreate(
            label="Contrôle implant personnalisé",
            category_id="IMPLANTOLOGIE",
            urgency="normal",
        ),
        db=db,
        current_user=owner,
    )

    motif_payload = f'["{created_motif["id"]}"]'
    created_patient = patients.create_patient(
        PatientCreate(
            nom="E2E",
            prenom="Motif",
            date_naissance="1990-01-01",
            sexe="M",
            motif_consultation=motif_payload,
        ),
        db=db,
        current_user=owner,
    )

    reloaded = patients.read_patient(created_patient.id, db=db, current_user=owner)
    assert reloaded.motif_consultation == motif_payload

    catalogue = motifs.list_cabinet_motifs(include_inactive=True, db=db, current_user=owner)
    assert any(
        item["id"] == created_motif["id"] and item["label"] == "Contrôle implant personnalisé"
        for item in catalogue
    )
