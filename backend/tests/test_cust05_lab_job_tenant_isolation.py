from datetime import datetime, timedelta

from fastapi import HTTPException

from backend import models
from backend.routers import lab_jobs


def _user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        nom_complet=email,
        permissions={"patients": True},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _patient(db, employer_id: int, suffix: str):
    patient = models.Patient(
        nom=f"Patient{suffix}",
        prenom="Test",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _act(db, patient_id: int, practitioner_id: int, label: str):
    act = models.Acte(
        patient_id=patient_id,
        praticien_id=practitioner_id,
        type_acte=models.ActeType.SOIN,
        libelle=label,
        montant=100.0,
        statut_paiement=models.PaiementStatut.EN_ATTENTE,
    )
    db.add(act)
    db.commit()
    db.refresh(act)
    return act


def _job(db, patient_id: int, act_id: int, label: str):
    job = models.LabJob(
        patient_id=patient_id,
        act_id=act_id,
        material="Zircone",
        type=label,
        deadline=datetime.now() + timedelta(days=7),
        status=models.LabJobStatus.PRESCRIPTION,
        is_remake=False,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_lab_job_list_is_scoped_to_current_cabinet(db):
    doctor_a = _user(db, "cust05-a@cabinet.test")
    doctor_b = _user(db, "cust05-b@cabinet.test")
    patient_a = _patient(db, doctor_a.id, "A")
    patient_b = _patient(db, doctor_b.id, "B")
    act_a = _act(db, patient_a.id, doctor_a.id, "Couronne A")
    act_b = _act(db, patient_b.id, doctor_b.id, "Couronne B")
    job_a = _job(db, patient_a.id, act_a.id, "A")
    _job(db, patient_b.id, act_b.id, "B")

    rows = lab_jobs.get_lab_jobs(db=db, current_user=doctor_a)

    assert [row["id"] for row in rows] == [job_a.id]


def test_lab_job_patch_rejects_cross_tenant_access(db):
    doctor_a = _user(db, "cust05-owner@cabinet.test")
    doctor_b = _user(db, "cust05-other@cabinet.test")
    patient_a = _patient(db, doctor_a.id, "A")
    act_a = _act(db, patient_a.id, doctor_a.id, "Couronne")
    job = _job(db, patient_a.id, act_a.id, "Couronne")

    try:
        lab_jobs.update_lab_job(
            job.id,
            {"status": models.LabJobStatus.SENT.value},
            db=db,
            current_user=doctor_b,
        )
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("cross-tenant lab job patch must fail closed")


def test_lab_job_create_rejects_cross_tenant_patient(db):
    doctor_a = _user(db, "cust05-create-a@cabinet.test")
    doctor_b = _user(db, "cust05-create-b@cabinet.test")
    patient_b = _patient(db, doctor_b.id, "B")
    act_b = _act(db, patient_b.id, doctor_b.id, "Couronne B")

    req = lab_jobs.LabJobCreate(
        patient_id=patient_b.id,
        act_id=act_b.id,
        material="Zircone",
        type="Couronne",
        deadline=(datetime.now() + timedelta(days=7)).isoformat(),
    )

    try:
        lab_jobs.create_lab_job(req, db=db, current_user=doctor_a)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("cross-tenant lab job creation must fail closed")


def test_lab_job_create_rejects_act_from_another_patient(db):
    doctor = _user(db, "cust05-act-check@cabinet.test")
    patient_a = _patient(db, doctor.id, "A")
    patient_b = _patient(db, doctor.id, "B")
    act_b = _act(db, patient_b.id, doctor.id, "Couronne B")

    req = lab_jobs.LabJobCreate(
        patient_id=patient_a.id,
        act_id=act_b.id,
        material="Zircone",
        type="Couronne",
        deadline=(datetime.now() + timedelta(days=7)).isoformat(),
    )

    try:
        lab_jobs.create_lab_job(req, db=db, current_user=doctor)
    except HTTPException as exc:
        assert exc.status_code == 422
        assert "Acte incompatible" in exc.detail
    else:
        raise AssertionError("lab job must reject an act belonging to another patient")
