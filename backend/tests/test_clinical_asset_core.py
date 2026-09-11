from datetime import datetime

import pytest

from backend.models import Patient, User
from backend.models_media_core import ClinicalAsset
from backend.security import get_password_hash
from backend.services.clinical_asset_service import (
    ClinicalAssetInvariantError,
    create_clinical_asset,
    get_clinical_asset_for_patient,
)


def _make_user(db, *, suffix: str, employer_id=None):
    user = User(
        email=f"media-{suffix}@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet=f"Dr Media {suffix}",
        is_active=True,
        is_licensed=True,
        employer_id=employer_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_patient(db, employer_id: int, *, suffix: str):
    patient = Patient(
        numero_dossier=f"MC-{suffix}",
        nom=f"Patient{suffix}",
        prenom="Synthetic",
        date_naissance=datetime(2000, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_clinical_asset_model_is_registered_in_shared_metadata():
    from backend import models

    assert ClinicalAsset.__table__ is models.Base.metadata.tables["clinical_assets"]


def test_clinical_asset_metadata_roundtrip_and_scoped_read(db):
    employer = _make_user(db, suffix="owner")
    patient = _make_patient(db, employer.id, suffix="001")

    asset = create_clinical_asset(
        db,
        employer_id=employer.id,
        patient_id=patient.id,
        asset_type="radiograph",
        source_kind="upload",
        source_ref="synthetic-import-001",
        original_filename="ceph_t0.png",
        mime_type="image/png",
        byte_size=2048,
        sha256="A" * 64,
        timepoint="t0",
        created_by=employer.id,
        provenance_json={"origin_system": "test-fixture", "origin_entity": "synthetic"},
    )
    db.commit()
    db.refresh(asset)

    assert asset.asset_type == "RADIOGRAPH"
    assert asset.source_kind == "UPLOAD"
    assert asset.sha256 == "a" * 64
    assert asset.timepoint == "T0"
    assert asset.employer_id == employer.id
    assert asset.patient_id == patient.id
    assert asset.provenance_json["origin_system"] == "test-fixture"

    assert get_clinical_asset_for_patient(
        db, employer_id=employer.id, patient_id=patient.id, asset_id=asset.id
    ).id == asset.id
    assert get_clinical_asset_for_patient(
        db, employer_id=employer.id + 999, patient_id=patient.id, asset_id=asset.id
    ) is None


def test_cross_tenant_patient_creation_fails_closed(db):
    owner_a = _make_user(db, suffix="a")
    owner_b = _make_user(db, suffix="b")
    patient_b = _make_patient(db, owner_b.id, suffix="B01")

    with pytest.raises(ClinicalAssetInvariantError, match="patient does not belong"):
        create_clinical_asset(
            db,
            employer_id=owner_a.id,
            patient_id=patient_b.id,
            asset_type="PHOTO",
            source_kind="UPLOAD",
        )

    assert db.query(ClinicalAsset).count() == 0


def test_created_by_must_belong_to_asset_tenant(db):
    owner_a = _make_user(db, suffix="creator-a")
    owner_b = _make_user(db, suffix="creator-b")
    patient_a = _make_patient(db, owner_a.id, suffix="A02")

    with pytest.raises(ClinicalAssetInvariantError, match="created_by user"):
        create_clinical_asset(
            db,
            employer_id=owner_a.id,
            patient_id=patient_a.id,
            asset_type="DOCUMENT",
            source_kind="IMPORT",
            created_by=owner_b.id,
        )


def test_parent_asset_must_match_tenant_and_patient(db):
    employer = _make_user(db, suffix="parent")
    patient_a = _make_patient(db, employer.id, suffix="P01")
    patient_b = _make_patient(db, employer.id, suffix="P02")

    parent = create_clinical_asset(
        db,
        employer_id=employer.id,
        patient_id=patient_a.id,
        asset_type="PHOTO",
        source_kind="UPLOAD",
    )
    db.commit()

    with pytest.raises(ClinicalAssetInvariantError, match="same tenant and patient"):
        create_clinical_asset(
            db,
            employer_id=employer.id,
            patient_id=patient_b.id,
            asset_type="PHOTO",
            source_kind="DERIVED",
            parent_asset_id=parent.id,
        )


def test_metadata_guards_reject_paths_phi_bad_hash_and_bad_timepoint(db):
    employer = _make_user(db, suffix="guards")
    patient = _make_patient(db, employer.id, suffix="G01")

    base = dict(
        db=db,
        employer_id=employer.id,
        patient_id=patient.id,
        asset_type="PHOTO",
        source_kind="UPLOAD",
    )

    with pytest.raises(ClinicalAssetInvariantError, match="not a path"):
        create_clinical_asset(**base, original_filename="patient/secret.png")

    with pytest.raises(ClinicalAssetInvariantError, match="patient-identifying"):
        create_clinical_asset(**base, provenance_json={"patient_email": "synthetic@example.invalid"})

    with pytest.raises(ClinicalAssetInvariantError, match="64 hexadecimal"):
        create_clinical_asset(**base, sha256="not-a-digest")

    with pytest.raises(ClinicalAssetInvariantError, match="T0..T999"):
        create_clinical_asset(**base, timepoint="baseline")
