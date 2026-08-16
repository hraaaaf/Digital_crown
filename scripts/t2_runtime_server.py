import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Runtime CI volontairement isolé : SQLite jetable, aucune donnée cabinet réelle.
# Le mode "cabinet" reste fail-closed sur SQLCipher dans le produit normal.
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "t2-runtime-certification-secret-key-000001"
os.environ["DATABASE_URL"] = "sqlite:///./t2-runtime-cert.db"
os.environ["TELEMETRY_ENABLED"] = "false"
os.environ["CLOUD_AI_ENABLED"] = "false"
os.environ["DEBUG"] = "false"
os.environ["ALLOWED_ORIGINS"] = '["http://127.0.0.1:5173","http://localhost:5173"]'

from backend import database, models
from backend.security import get_password_hash

models.Base.metadata.create_all(bind=database.engine)

with database.SessionLocal() as db:
    user = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").first()
    if not user:
        user = models.User(
            email="t2-browser@cabinet.ma",
            hashed_password=get_password_hash("T2BrowserPass123!"),
            role=models.UserRole.DENTISTE,
            nom_complet="Dr T2 Browser",
            is_active=True,
            is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first():
        db.add(models.CabinetConfig(
            owner_id=user.id,
            nom_cabinet="Cabinet T2 Certification",
            nom_praticien="Dr T2 Browser",
            is_initialized=True,
            hide_header=False,
            hide_footer=False,
        ))

    patient = db.query(models.Patient).filter(
        models.Patient.numero_dossier == "T2-0001",
        models.Patient.employer_id == user.id,
    ).first()
    if not patient:
        patient = models.Patient(
            numero_dossier="T2-0001",
            nom="CERTIFICATION",
            prenom="T2",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=user.id,
            telephone="0600000000",
            email="patient.t2.certification@example.com",
            assurance="AUCUNE",
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
        db.add(models.Acte(
            patient_id=patient.id,
            praticien_id=user.id,
            type_acte=models.ActeType.SOIN,
            libelle="Soin T2",
            montant=1000.0,
            statut_paiement=models.PaiementStatut.EN_ATTENTE,
            is_accounted=False,
            is_collected=False,
        ))
    db.commit()
    print(f"T2_RUNTIME_PATIENT_ID={patient.id}", flush=True)

import backend.main as main

async def _noop_async(*args, **kwargs):
    return None

main._sync_all_licenses_from_firebase = _noop_async
main.panoramic_engine.initialize = _noop_async
main.sync_manager.start_listening = lambda: None
main.run_full_seed = lambda db: None
main.seed_clinical_data = lambda db: None
main.seed_admin_user = lambda: None

import backend.services.daily_scheduler as daily_scheduler
daily_scheduler.start_daily_scheduler = lambda: None

import uvicorn
uvicorn.run(main.app, host="127.0.0.1", port=8005, log_level="info")
