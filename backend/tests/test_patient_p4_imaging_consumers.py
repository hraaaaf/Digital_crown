from datetime import datetime

from backend import models
from backend.models_imaging_p4 import ImagingTrashRecord
from backend.services.cmo_agent_service import cmo_agent


def _make_patient(db, owner, dossier):
    patient = models.Patient(
        numero_dossier=dossier,
        nom="P4",
        prenom="Consumers",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_journey_excludes_trashed_imaging(client, db, dentiste, auth_headers):
    patient = _make_patient(db, dentiste, "P4-CONS-JOURNEY")
    pano = models.PanoramicAnalysis(
        patient_id=patient.id,
        image_path="journey-pano.jpg",
        detections_data={},
        report_narrative="Repérage panoramique enregistré.",
    )
    ceph = models.CephaloAnalysis(
        patient_id=patient.id,
        image_original_path="journey-ceph.jpg",
        landmarks_data={},
        angles_data={},
        is_calibrated=False,
    )
    db.add_all([pano, ceph])
    db.commit()
    db.refresh(pano)
    db.refresh(ceph)

    before = client.get(f"/api/patients/{patient.id}/journey?full_history=true", headers=auth_headers)
    assert before.status_code == 200, before.text
    before_events = before.json()["events"]
    assert any(e["source"] == "panoramic_analysis" and e["ref_id"] == pano.id for e in before_events)
    assert any(e["source"] == "cephalo_analysis" and e["ref_id"] == ceph.id for e in before_events)

    db.add_all([
        ImagingTrashRecord(modality="panoramic", analysis_id=pano.id, patient_id=patient.id, deleted_by=dentiste.id),
        ImagingTrashRecord(modality="cephalo", analysis_id=ceph.id, patient_id=patient.id, deleted_by=dentiste.id),
    ])
    db.commit()

    after = client.get(f"/api/patients/{patient.id}/journey?full_history=true", headers=auth_headers)
    assert after.status_code == 200, after.text
    after_events = after.json()["events"]
    assert not any(e["source"] == "panoramic_analysis" and e["ref_id"] == pano.id for e in after_events)
    assert not any(e["source"] == "cephalo_analysis" and e["ref_id"] == ceph.id for e in after_events)


def test_cmo_ignores_trashed_imaging_and_uses_patient_employer(db, dentiste, monkeypatch):
    patient = _make_patient(db, dentiste, "P4-CONS-CMO")
    pano = models.PanoramicAnalysis(
        patient_id=patient.id,
        image_path="cmo-pano.jpg",
        detections_data={},
        report_narrative="carie",
    )
    db.add(pano)
    db.commit()
    db.refresh(pano)

    captured = []
    monkeypatch.setattr(
        "backend.services.cmo_agent_service.ghost_memory.add_memory",
        lambda **kwargs: captured.append(kwargs),
    )

    active = cmo_agent.generate_global_synthesis(db, patient.id, employer_id=999999)
    assert active["is_fallback"] is False
    assert captured, "Active imaging should emit a documentary signal memory"
    assert captured[-1]["employer_id"] == patient.employer_id

    db.add(ImagingTrashRecord(
        modality="panoramic",
        analysis_id=pano.id,
        patient_id=patient.id,
        deleted_by=dentiste.id,
    ))
    db.commit()
    captured.clear()

    trashed = cmo_agent.generate_global_synthesis(db, patient.id, employer_id=999999)
    assert trashed["is_fallback"] is True
    assert captured == [], "Trashed imaging must not feed active CMO memory"
