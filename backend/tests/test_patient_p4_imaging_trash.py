from datetime import datetime

from backend import models
from backend.security import get_password_hash


PASSWORD = "TestPass123!"


def _make_patient(db, owner, dossier):
    patient = models.Patient(
        numero_dossier=dossier,
        nom="IMAGERIE",
        prenom="Patient",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _make_user(db, email, *, employer_id=None, permissions=None, role="DENTISTE"):
    user = models.User(
        email=email,
        hashed_password=get_password_hash(PASSWORD),
        role=role,
        nom_complet="Dr P4 Test",
        is_active=True,
        is_licensed=True,
        employer_id=employer_id,
        permissions=permissions or {},
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
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_panoramic_delete_is_recoverable_and_preserves_file(client, db, dentiste, auth_headers, tmp_path):
    patient = _make_patient(db, dentiste, "P4-PANO-TRASH")
    image = tmp_path / "pano.jpg"
    image.write_bytes(b"pano")
    analysis = models.PanoramicAnalysis(
        patient_id=patient.id,
        image_path=str(image),
        detections_data={},
        report_narrative=None,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    analysis_id = analysis.id

    deleted = client.delete(f"/api/ia/panoramic/{analysis_id}", headers=auth_headers)
    assert deleted.status_code == 204, deleted.text
    db.expire_all()
    persisted = db.get(models.PanoramicAnalysis, analysis_id)
    assert persisted is not None
    assert persisted.deleted_at is not None
    assert persisted.deleted_by == dentiste.id
    assert image.exists(), "Normal trash must never remove the clinical image file"

    active = client.get(f"/api/ia/patients/{patient.id}/panoramic-analyses", headers=auth_headers)
    assert active.status_code == 200, active.text
    assert all(row["id"] != analysis_id for row in active.json())

    trash = client.get(f"/api/ia/patients/{patient.id}/panoramic-trash", headers=auth_headers)
    assert trash.status_code == 200, trash.text
    assert any(row["id"] == analysis_id for row in trash.json())

    restored = client.post(f"/api/ia/panoramic/{analysis_id}/restore", headers=auth_headers)
    assert restored.status_code == 200, restored.text
    assert restored.json()["deleted_at"] is None
    assert image.exists()


def test_cephalo_delete_is_recoverable_and_preserves_file(client, db, dentiste, auth_headers, tmp_path):
    patient = _make_patient(db, dentiste, "P4-CEPH-TRASH")
    image = tmp_path / "cephalo.jpg"
    image.write_bytes(b"cephalo")
    analysis = models.CephaloAnalysis(
        patient_id=patient.id,
        image_original_path=str(image),
        landmarks_data={},
        angles_data={},
        is_calibrated=False,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    analysis_id = analysis.id

    deleted = client.delete(f"/api/ia/cephalo/{analysis_id}", headers=auth_headers)
    assert deleted.status_code == 204, deleted.text
    db.expire_all()
    persisted = db.get(models.CephaloAnalysis, analysis_id)
    assert persisted is not None
    assert persisted.deleted_at is not None
    assert persisted.deleted_by == dentiste.id
    assert image.exists(), "Normal trash must never remove the clinical image file"

    active = client.get(f"/api/ia/patients/{patient.id}/cephalo-analyses", headers=auth_headers)
    assert active.status_code == 200, active.text
    assert all(row["id"] != analysis_id for row in active.json())

    trash = client.get(f"/api/ia/patients/{patient.id}/cephalo-trash", headers=auth_headers)
    assert trash.status_code == 200, trash.text
    assert any(row["id"] == analysis_id for row in trash.json())

    restored = client.post(f"/api/ia/cephalo/{analysis_id}/restore", headers=auth_headers)
    assert restored.status_code == 200, restored.text
    assert restored.json()["deleted_at"] is None
    assert image.exists()


def test_imaging_trash_and_restore_are_tenant_scoped(client, db, dentiste):
    patient = _make_patient(db, dentiste, "P4-TRASH-TENANT")
    pano = models.PanoramicAnalysis(
        patient_id=patient.id,
        image_path="tenant-pano.jpg",
        detections_data={},
        deleted_at=datetime.utcnow(),
        deleted_by=dentiste.id,
    )
    ceph = models.CephaloAnalysis(
        patient_id=patient.id,
        image_original_path="tenant-ceph.jpg",
        landmarks_data={},
        angles_data={},
        is_calibrated=False,
        deleted_at=datetime.utcnow(),
        deleted_by=dentiste.id,
    )
    db.add_all([pano, ceph])
    db.commit()
    db.refresh(pano)
    db.refresh(ceph)

    foreign_owner = _make_user(db, "p4-foreign-owner@test.ma")
    headers = _headers(client, foreign_owner)

    assert client.get(f"/api/ia/patients/{patient.id}/panoramic-trash", headers=headers).status_code == 403
    assert client.get(f"/api/ia/patients/{patient.id}/cephalo-trash", headers=headers).status_code == 403
    assert client.post(f"/api/ia/panoramic/{pano.id}/restore", headers=headers).status_code == 403
    assert client.post(f"/api/ia/cephalo/{ceph.id}/restore", headers=headers).status_code == 403


def test_imaging_lifecycle_requires_modality_permissions(client, db, dentiste):
    patient = _make_patient(db, dentiste, "P4-TRASH-RBAC")
    pano = models.PanoramicAnalysis(patient_id=patient.id, image_path="rbac-pano.jpg", detections_data={})
    ceph = models.CephaloAnalysis(
        patient_id=patient.id,
        image_original_path="rbac-ceph.jpg",
        landmarks_data={},
        angles_data={},
        is_calibrated=False,
    )
    db.add_all([pano, ceph])
    db.commit()
    db.refresh(pano)
    db.refresh(ceph)

    collaborator = _make_user(
        db,
        "p4-no-imaging@test.ma",
        employer_id=dentiste.id,
        permissions={"patients": True, "panoramic": False, "cephalo": False},
    )
    headers = _headers(client, collaborator)

    assert client.get(f"/api/ia/patients/{patient.id}/panoramic-trash", headers=headers).status_code == 403
    assert client.get(f"/api/ia/patients/{patient.id}/cephalo-trash", headers=headers).status_code == 403
    assert client.delete(f"/api/ia/panoramic/{pano.id}", headers=headers).status_code == 403
    assert client.delete(f"/api/ia/cephalo/{ceph.id}", headers=headers).status_code == 403
