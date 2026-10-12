#!/usr/bin/env python3
"""Add explicitly fictitious dental appointments to the disposable Pocket PWA lab.

Runs ONLY inside the dedicated GitHub Actions test runner after T2 boot. Never
run against a real practice, shared database, or persistent clinical environment.
"""
import os
from datetime import datetime, time
from pathlib import Path

if os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
    raise SystemExit("Refusing to seed outside the disposable CI lab")
if os.environ.get("ENVIRONMENT") != "test":
    raise SystemExit("Refusing to seed outside the test environment")
if os.environ.get("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db":
    raise SystemExit("Refusing to seed any non-allowlisted database")
if not Path("t2-runtime-cert.db").is_file():
    raise SystemExit("Synthetic SQLite database not initialized")
if os.environ.get("T2_USER") != "t2-browser@cabinet.ma":
    raise SystemExit("Unknown synthetic tenant; refusing seed")

from backend import database, models

# Patient names, appointments and timestamps are invented demonstrations;
# no medical records from a real practice enter this test environment.
SLOTS = (
    ("09:00", "Amine", "DÉMO", "Consultation initiale", 30, models.AppointmentStatus.TERMINE),
    ("09:45", "Salma", "DÉMO", "Détartrage", 45, models.AppointmentStatus.CONFIRME),
    ("10:45", "Yassine", "DÉMO", "Contrôle orthodontique", 30, models.AppointmentStatus.EN_SALLE_ATTENTE),
    ("11:30", "Lina", "DÉMO", "Pose d'appareil orthodontique", 60, models.AppointmentStatus.PREVU),
    ("14:00", "Adam", "DÉMO", "Soin conservateur", 45, models.AppointmentStatus.PREVU),
    ("15:00", "Nour", "DÉMO", "Contrôle de suivi", 30, models.AppointmentStatus.PREVU),
)

with database.SessionLocal() as db:
    user = db.query(models.User).filter(
        models.User.email == "t2-browser@cabinet.ma",
        models.User.is_active.is_(True),
    ).one()
    if user.get_employer_id() != user.id:
        raise SystemExit("Unexpected test tenant topology")

    for index, (clock, first, last, motif, duration, status) in enumerate(SLOTS, 1):
        patient_ref = f"POCKET-DEMO-{index:02d}"
        patient = db.query(models.Patient).filter(
            models.Patient.numero_dossier == patient_ref,
            models.Patient.employer_id == user.id,
        ).one_or_none()
        if patient is None:
            patient = models.Patient(
                numero_dossier=patient_ref,
                prenom=first,
                nom=last,
                date_naissance=datetime(2000, 1, 1),
                sexe="X",
                employer_id=user.id,
                assurance="AUCUNE",
            )
            db.add(patient)
            db.flush()

        hour, minute = map(int, clock.split(":"))
        day = datetime.now().date()
        starts = datetime.combine(day, time(hour, minute))
        existing = db.query(models.Appointment).filter(
            models.Appointment.employer_id == user.id,
            models.Appointment.patient_id == patient.id,
            models.Appointment.datetime_start == starts,
        ).one_or_none()
        if existing is None:
            db.add(models.Appointment(
                employer_id=user.id,
                patient_id=patient.id,
                datetime_start=starts,
                duration_minutes=duration,
                motif=motif,
                status=status,
                source="internal",
            ))
    db.commit()

    count = db.query(models.Appointment).filter(
        models.Appointment.employer_id == user.id,
        models.Appointment.datetime_start >= datetime.combine(datetime.now().date(), time.min),
        models.Appointment.datetime_start <= datetime.combine(datetime.now().date(), time.max),
        models.Appointment.deleted_at.is_(None),
    ).count()
    if count < len(SLOTS):
        raise SystemExit("Agenda seed verification failed")
    print(f"POCKET_FUE_DEMO_APPOINTMENTS={count} (synthetic today only)", flush=True)
