# V1-07 FINAL EXACT-HEAD EVIDENCE CANDIDATE — trigger only, no runtime behavior change
import os
import sys
import struct
import zlib
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
os.environ["ALLOWED_ORIGINS"] = "http://127.0.0.1:5173,http://localhost:5173"
if os.environ.get("T2_SUPERADMIN_EMAIL") and not os.environ.get("SUPERADMIN_EMAIL"):
    os.environ["SUPERADMIN_EMAIL"] = os.environ["T2_SUPERADMIN_EMAIL"]

# La certification T2 enchaîne plusieurs authentifications valides dans un même
# processus. Le limiteur produit (5 tentatives / 10 min) reste inchangé ; seul
# ce serveur CI jetable relève son plafond afin que les probes ne se bloquent
# pas mutuellement avant le dernier contrôle print/PDF.
import backend.utils.rate_limit as rate_limit
rate_limit.MAX_ATTEMPTS = 100

# check_rate_limit binds its default max_attempts at function definition time.
# Raising the module constant alone does not change that bound default, so the
# long T2 matrix can still hit the production 5-attempt ceiling. This isolated
# CI runtime overrides only the callable seam; product defaults remain intact.
_original_check_rate_limit = rate_limit.check_rate_limit
def _t2_check_rate_limit(request, scope="auth", *, max_attempts=None):
    return _original_check_rate_limit(
        request,
        scope,
        max_attempts=rate_limit.MAX_ATTEMPTS if max_attempts is None else max_attempts,
    )
rate_limit.check_rate_limit = _t2_check_rate_limit

from backend import database, models
from backend.models_imaging_p4 import ImagingTrashRecord  # noqa: F401 - register table in Base metadata
from backend.security import get_password_hash

def _write_t2_png(path: Path, width: int = 1935, height: int = 2400) -> None:
    """Generate a deterministic local grayscale PNG for isolated cephalo browser proof."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    raw = b"".join(b"\x00" + (b"\x30" * width) for _ in range(height))
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


runtime_password = os.environ.get("T2_PASSWORD")
if not runtime_password:
    raise RuntimeError("T2 runtime certification requires T2_PASSWORD")

models.Base.metadata.create_all(bind=database.engine)

with database.SessionLocal() as db:
    user = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").first()
    if not user:
        user = models.User(
            email="t2-browser@cabinet.ma",
            hashed_password=get_password_hash(runtime_password),
            role=models.UserRole.DENTISTE,
            nom_complet="Dr T2 Browser",
            is_active=True,
            is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Seed and claim the legacy dental catalog while the isolated T2 database has
    # exactly one root cabinet. Later certification fixtures intentionally add
    # other root users, at which point tenant ownership can no longer be inferred.
    from backend.seed_catalog import seed_catalog
    from backend.services import cabinet_catalog_store
    seed_catalog(db)
    cabinet_catalog_store.claim_legacy_if_unambiguous(db)

    restricted = db.query(models.User).filter(models.User.email == "t2-restricted@cabinet.ma").first()
    if not restricted:
        restricted = models.User(
            email="t2-restricted@cabinet.ma",
            hashed_password=get_password_hash(runtime_password),
            role=models.UserRole.SECRETAIRE,
            nom_complet="T2 Restricted Secretary",
            is_active=True,
            is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
            employer_id=user.id,
            permissions={
                "agenda": True,
                "patients": False,
                "prescriptions": False,
                "accounting": False,
                "payments": False,
                "clinical": False,
                "panoramic": False,
                "cephalo": False,
                "settings": False,
                "admin": False,
            },
        )
        db.add(restricted)
        db.commit()
        db.refresh(restricted)

    for setup_email, setup_name in (
        ("t2-setup-390@cabinet.ma", "Dr T2 Setup Mobile"),
        ("t2-setup-1280@cabinet.ma", "Dr T2 Setup Desktop"),
    ):
        setup_user = db.query(models.User).filter(models.User.email == setup_email).first()
        if not setup_user:
            setup_user = models.User(
                email=setup_email,
                hashed_password=get_password_hash(runtime_password),
                role=models.UserRole.DENTISTE,
                nom_complet=setup_name,
                is_active=True,
                is_licensed=True,
                approval_status=models.ApprovalStatus.APPROVED.value,
            )
            db.add(setup_user)
            db.commit()
            db.refresh(setup_user)

    superadmin_email = os.environ.get("T2_SUPERADMIN_EMAIL", "").strip().lower()
    if superadmin_email:
        superadmin = db.query(models.User).filter(models.User.email == superadmin_email).first()
        if not superadmin:
            superadmin = models.User(
                email=superadmin_email,
                hashed_password=get_password_hash(runtime_password),
                role=models.UserRole.ADMIN,
                nom_complet="T2 SuperAdmin",
                is_active=True,
                is_licensed=True,
                approval_status=models.ApprovalStatus.APPROVED.value,
            )
            db.add(superadmin)
            db.commit()
            db.refresh(superadmin)

    if not db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first():
        db.add(models.CabinetConfig(
            owner_id=user.id,
            nom_cabinet="Cabinet T2 Certification",
            nom_praticien="Dr T2 Browser",
            is_initialized=True,
            hide_header=False,
            hide_footer=False,
        ))

    if superadmin_email and superadmin and not db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == superadmin.id).first():
        db.add(models.CabinetConfig(
            owner_id=superadmin.id,
            nom_cabinet="Cabinet T2 SuperAdmin",
            nom_praticien="T2 SuperAdmin",
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
    cephalo_path = REPO_ROOT / "backend" / "static" / "uploads" / "radios" / "t2-cephalo-seeded.png"
    _write_t2_png(cephalo_path)
    cephalo_db_path = "api/static/uploads/radios/t2-cephalo-seeded.png"
    seeded_cephalo = db.query(models.CephaloAnalysis).filter(
        models.CephaloAnalysis.patient_id == patient.id,
        models.CephaloAnalysis.image_original_path == cephalo_db_path,
    ).first()
    if not seeded_cephalo:
        landmark_ids = [
            "S","N","Or","Po","A","B","Pog","Me","Gn","Go","L1_incisal","U1_incisal",
            "Ls_soft","Li_soft","Sn_soft","Pog_soft","PNS","ANS","Ar","D_point","U1_apex","L1_apex",
            "Cm","Ptm","Co","Prn","Ba","PT_point","Bo","Ls2","Li2","Gn_soft","Me_soft","G_soft",
            "N_soft","C_point","U6","L6",
        ]
        coords = [
            [831.9116,993.1177],[1468.1926,1036.5623],[1303.322,1275.3881],[615.2458,1215.3415],
            [1351.6111,1639.4705],[1358.4153,2047.656],[1329.1421,2206.1749],[1248.4201,2276.494],
            [1302.0494,2256.1332],[689.8349,1799.9835],[1453.6016,1867.1625],[1450.121,1866.3396],
            [1588.3028,1765.1489],[1574.0796,1994.5107],[1514.315,1618.1174],[1430.8679,2234.4681],
            [934.6211,1508.9828],[1391.5013,1555.837],[654.4276,1358.2056],[1268.7827,2187.1443],
            [1343.0314,1664.3263],[1311.7006,2031.8895],[1563.5106,1569.2036],[948.1152,1395.5343],
            [716.7104,1207.907],[1663.5152,1518.5116],[586.7122,1395.878],[969.6921,1202.4],
            [361.6976,1380.7694],[1558.6916,1720.6529],[1532.3763,2030.3445],[1372.2616,2316.6077],
            [1261.2317,2354.9537],[1591.902,906.9502],[1498.999,1144.5119],[967.8018,2306.8863],
            [1188.6565,1790.2074],[1208.6297,1844.3245],
        ]
        seeded_cephalo = models.CephaloAnalysis(
            patient_id=patient.id,
            image_original_path=cephalo_db_path,
            landmarks_data=[
                {"id": landmark_id, "x": xy[0], "y": xy[1]}
                for landmark_id, xy in zip(landmark_ids, coords)
            ],
            angles_data={
                "vision_metadata": {"mode_inference": "T2_SEEDED_CERTIFIED_SRPOSE38"},
                "calibration_status": "verified",
                "t1_projection": {},
                "t2_projection": {},
            },
            is_calibrated=True,
            mm_per_pixel=0.2,
            calibration_data={
                "method": "MANUAL_TWO_POINT",
                "state": "MANUAL_TWO_POINT",
                "p1": {"x": 100.0, "y": 100.0},
                "p2": {"x": 200.0, "y": 100.0},
                "distance_mm": 20.0,
            },
        )
        db.add(seeded_cephalo)
    db.commit()
    db.refresh(seeded_cephalo)
    print(f"T2_RUNTIME_CEPHALO_ID={seeded_cephalo.id}", flush=True)
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
