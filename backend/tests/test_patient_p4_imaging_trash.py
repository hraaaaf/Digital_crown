from datetime import datetime

from backend import models


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
