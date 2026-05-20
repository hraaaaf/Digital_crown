import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend import models
from backend.services.notification_service import notification_service

# Configuration of test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        models.Base.metadata.drop_all(bind=engine)

def test_format_reminder_message():
    dt = datetime(2026, 5, 20, 14, 30)
    msg = notification_service._format_reminder_message("Jean Dupont", dt, "El Fassi")
    assert "Jean Dupont" in msg
    assert "El Fassi" in msg
    assert "20/05/2026" in msg
    assert "14:30" in msg

def test_send_appointment_reminder_success(db):
    # 1. Create a doctor
    doctor = models.User(
        email="doctor@digitalcrown.com",
        hashed_password="hashed_password",
        nom_complet="Ali Alami",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    # 2. Create a patient
    patient = models.Patient(
        numero_dossier="PT-001",
        nom="Dupont",
        prenom="Jean",
        sexe=models.SexeType.M,
        date_naissance=datetime(1985, 4, 12),
        telephone="+212600000000",
        adresse="Rabat",
        assurance="CNSS",
        employer_id=doctor.id
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # 3. Create an appointment scheduled tomorrow (24 hours from now)
    tomorrow = datetime.now() + timedelta(hours=24)
    appt = models.Appointment(
        patient_id=patient.id,
        patient_name=f"{patient.prenom} {patient.nom}",
        datetime_start=tomorrow,
        duration_minutes=30,
        motif="Consultation générale",
        status=models.AppointmentStatus.PREVU,
        employer_id=doctor.id
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    # 4. Trigger sending reminder
    success = notification_service.send_appointment_reminder(db, appt.id)
    assert success is True

    # 5. Check database states
    db.refresh(appt)
    assert appt.reminder_sent is True
    assert appt.reminder_sent_at is not None

    # Check AuditLog
    logs = db.query(models.AuditLog).filter(models.AuditLog.action == "SEND_REMINDER").all()
    assert len(logs) == 1
    assert "Jean DUPONT" in logs[0].details
    assert "+212600000000" in logs[0].details

def test_cron_send_reminders(db):
    # 1. Create a doctor and patient
    doctor = models.User(
        email="doctor2@digitalcrown.com",
        hashed_password="hashed",
        nom_complet="Dr. Salim",
        role=models.UserRole.DENTISTE,
        is_active=True
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    patient = models.Patient(
        numero_dossier="PT-002",
        nom="Sami",
        prenom="Amine",
        sexe=models.SexeType.M,
        date_naissance=datetime(1990, 1, 1),
        telephone="+212611111111",
        employer_id=doctor.id
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # 2. Create 3 appointments:
    # Appt 1: Scheduled in 24 hours (within 20-28h window) - Should be sent
    # Appt 2: Scheduled in 48 hours (outside window) - Should NOT be sent
    # Appt 3: Scheduled in 24 hours, but already sent - Should NOT be sent
    
    appt1 = models.Appointment(
        patient_id=patient.id,
        datetime_start=datetime.now() + timedelta(hours=24),
        status=models.AppointmentStatus.PREVU,
        employer_id=doctor.id,
        reminder_sent=False
    )
    appt2 = models.Appointment(
        patient_id=patient.id,
        datetime_start=datetime.now() + timedelta(hours=48),
        status=models.AppointmentStatus.PREVU,
        employer_id=doctor.id,
        reminder_sent=False
    )
    appt3 = models.Appointment(
        patient_id=patient.id,
        datetime_start=datetime.now() + timedelta(hours=24),
        status=models.AppointmentStatus.PREVU,
        employer_id=doctor.id,
        reminder_sent=True,
        reminder_sent_at=datetime.now() - timedelta(hours=1)
    )

    db.add_all([appt1, appt2, appt3])
    db.commit()

    # Run the cron service
    sent_count = notification_service.cron_send_reminders(db)
    
    # Assertions
    assert sent_count == 1
    
    db.refresh(appt1)
    db.refresh(appt2)
    db.refresh(appt3)

    assert appt1.reminder_sent is True
    assert appt2.reminder_sent is False
    assert appt3.reminder_sent is True  # Stayed true
