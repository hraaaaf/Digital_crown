from datetime import datetime

from backend import database, models


with database.SessionLocal() as db:
    user = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").first()
    if user is None:
        raise RuntimeError("T1 runtime seed requires the isolated T2 certification user")

    patient = db.query(models.Patient).filter(
        models.Patient.numero_dossier == "T2-0002",
        models.Patient.employer_id == user.id,
    ).first()

    if patient is None:
        patient = models.Patient(
            numero_dossier="T2-0002",
            nom="CERTIFICATION-B",
            prenom="T2B",
            date_naissance=datetime(1992, 2, 2),
            sexe="F",
            employer_id=user.id,
            telephone="0611111111",
            email="patient.t2b.certification@example.com",
            assurance="AUCUNE",
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
        db.commit()

    print(f"T1_RUNTIME_PATIENT_B_ID={patient.id}", flush=True)
