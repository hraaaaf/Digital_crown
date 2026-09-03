import base64
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

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
os.environ["ALLOWED_ORIGINS"] = "http://127.0.0.1:5173,http://localhost:5173"

from backend import database, models
from backend.license_security import (
    LICENSE_AUDIENCE,
    LICENSE_ISSUER,
    LICENSE_SCHEMA_VERSION,
    sign_license,
)
from backend.license_trust import TRUSTED_LICENSE_PUBLIC_KEYS
from backend.security import get_password_hash
from backend.services.license_service import LicenseService


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _provision_ephemeral_signed_license(cabinet: models.CabinetConfig, user: models.User) -> None:
    """Provision a genuine signed entitlement for isolated runtime certification.

    The issuer keypair exists only in this process. The product path remains
    fail-closed: no middleware bypass, mutable SQLite flag, or committed private
    key can authorize the mutation probes.
    """
    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_raw = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    key_id = "t2-ephemeral-cert"
    TRUSTED_LICENSE_PUBLIC_KEYS.clear()
    TRUSTED_LICENSE_PUBLIC_KEYS[key_id] = _b64url(public_raw)

    now = datetime.now(timezone.utc) - timedelta(seconds=1)
    clinic_id = str(cabinet.clinic_id or cabinet.public_id)
    claims = {
        "schema_version": LICENSE_SCHEMA_VERSION,
        "issuer": LICENSE_ISSUER,
        "audience": LICENSE_AUDIENCE,
        "license_id": "t2-runtime-cert-license",
        "cabinet_id": clinic_id,
        "license_type": "PAID",
        "status": "ACTIVE",
        "issued_at": now.isoformat(),
        "not_before": now.isoformat(),
        "expires_at": (now + timedelta(days=2)).isoformat(),
        "release_channel": "stable",
        "feature_set": models.SubscriptionPlan.ELITE.value,
        "max_devices": 1,
        "policy_version": "ci-runtime-v1",
        "created_by_user_id": int(user.id),
    }
    signed_license = sign_license(claims, _b64url(private_raw), key_id)

    LicenseService._instance = None
    LicenseService._db = None
    service = LicenseService()
    service._db = None
    service._write_local_vault(
        {
            "clinic_id": clinic_id,
            "signed_license": signed_license,
            "last_validated": now.isoformat(),
            "max_seen_time": now.isoformat(),
        }
    )
    verified = service._validate_offline_vault(clinic_id, datetime.now(timezone.utc))
    if not verified.get("active") or verified.get("license_id") != "t2-runtime-cert-license":
        raise RuntimeError("T2 signed-license certification bootstrap failed")


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
            # Mirror only. SEC-1 authorization comes from the signed proof below.
            is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
    if not cabinet:
        cabinet = models.CabinetConfig(
            owner_id=user.id,
            nom_cabinet="Cabinet T2 Certification",
            nom_praticien="Dr T2 Browser",
            is_initialized=True,
            hide_header=False,
            hide_footer=False,
        )
        db.add(cabinet)
        db.flush()

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
        db.flush()
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
    db.refresh(cabinet)
    db.refresh(patient)
    _provision_ephemeral_signed_license(cabinet, user)
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
