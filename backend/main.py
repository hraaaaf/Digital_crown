import os
import sys
import time
import asyncio
import logging
import contextlib
from datetime import datetime
from pathlib import Path
from backend.env_loader import load_backend_env

# Charger l'env backend explicitement avant toute lecture de os.getenv().
# Deux passes : 1) override=False pour ne JAMAIS écraser des variables déjà
# injectées par l'OS/l'orchestrateur (Docker/systemd/k8s secrets) en
# préprod/prod — sinon un fichier .env.local oublié dans l'image écraserait
# silencieusement la config réelle du déploiement. 2) en dev/local/test
# uniquement, on recharge avec override=True pour garder le confort habituel
# (le fichier fait toujours foi, même si le shell a des variables résiduelles).
load_backend_env(override=False)
if os.environ.get("ENVIRONMENT", "development").lower() in ("development", "local", "test"):
    load_backend_env(override=True)
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from backend import models, database
from backend.services.sync_manager import sync_manager
from backend.seed_templates import run_full_seed
from backend.seed_user import seed_admin_user
from backend.seed_clinical import seed_clinical_data
from backend.services.panoramic_service import panoramic_engine
from backend.core.media_paths import get_media_root
from backend.core.paths import AppPaths
from backend.services.license_service import LicenseService
import sentry_sdk
from backend.config import settings as app_settings

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# --- CONFIGURATION LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION CHEMINS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# --- CACHE LICENCES PER-USER ---
# Structure : {identity: (is_ok: bool, reason: str, cached_at: float)}
# TTL court uniquement pour éviter de revalider la même preuve signée à chaque requête.
_license_cache: dict[str, tuple[bool, str, float]] = {}
_CACHE_TTL = 60  # secondes


def invalidate_license_cache(_identity: str = "") -> None:
    """Toute mutation de licence invalide le cache web + mobile du cabinet."""
    _license_cache.clear()


from fastapi.concurrency import run_in_threadpool


def _resolve_license_context(db, user):
    """Résout le cabinet licencié sans jamais utiliser is_licensed comme autorité."""
    if not user:
        return (None, "USER_NOT_FOUND")
    if user.is_suspended:
        return (None, "SUSPENDED")
    if user.is_archived:
        return (None, "ARCHIVED")

    license_owner = user
    if user.employer_id is not None:
        license_owner = db.query(models.User).filter(models.User.id == user.employer_id).first()
        if not license_owner:
            return (None, "USER_NOT_FOUND")
        if license_owner.is_suspended:
            return (None, "SUSPENDED")
        if license_owner.is_archived:
            return (None, "ARCHIVED")

    cabinet = db.query(models.CabinetConfig).filter(
        models.CabinetConfig.owner_id == license_owner.id
    ).first()
    if not cabinet:
        return (None, "SIGNED_LICENSE_NOT_CONFIGURED")

    clinic_id = str(cabinet.clinic_id or cabinet.public_id)
    if not clinic_id:
        return (None, "SIGNED_LICENSE_NOT_CONFIGURED")
    return (clinic_id, None)


def _get_user_license_context_sync(email: str):
    with database.SessionLocal() as db:
        user = db.query(models.User).filter(models.User.email == email).first()
        return _resolve_license_context(db, user)


def _get_mobile_license_context_sync(user_id: int):
    with database.SessionLocal() as db:
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        return _resolve_license_context(db, user)


async def _get_signed_license_status(identity: str, context_loader, identity_value) -> tuple[bool, str]:
    now = time.time()
    cached = _license_cache.get(identity)
    if cached and (now - cached[2]) < _CACHE_TTL:
        return cached[0], cached[1]

    try:
        clinic_id, context_error = await run_in_threadpool(context_loader, identity_value)
        if context_error:
            result = (False, context_error)
        else:
            entitlement = await LicenseService().get_effective_license(clinic_id)
            if entitlement.get("active"):
                result = (True, "OK")
            else:
                result = (
                    False,
                    str(entitlement.get("reason") or "SIGNED_LICENSE_REQUIRED"),
                )
    except Exception as e:
        logger.error("Erreur vérification licence signée pour %s: %s", identity, e)
        result = (False, "LICENSE_STATUS_UNAVAILABLE")

    _license_cache[identity] = (*result, now)
    return result


async def get_user_license_status(email: str) -> tuple[bool, str]:
    """Vérifie la preuve signée effective du cabinet d'un utilisateur web."""
    return await _get_signed_license_status(
        f"web:{email.lower()}",
        _get_user_license_context_sync,
        email,
    )


async def get_mobile_user_license_status(user_id: int) -> tuple[bool, str]:
    """Vérifie la même preuve signée pour un JWT mobile lié au cabinet."""
    return await _get_signed_license_status(
        f"mobile-user:{int(user_id)}",
        _get_mobile_license_context_sync,
        int(user_id),
    )


def validate_environment_invariants(cfg) -> list[str]:
    """Invariants de démarrage par environnement — retourne la liste des erreurs bloquantes.

    - production : DEBUG interdit, SQLite interdit (PostgreSQL exigé), pas de
      wildcard CORS.
    - cabinet (on-premise, production-like) : mêmes invariants QUE production
      SAUF SQLite — le mode cabinet solo repose sur SQLite/SQLCipher local
      (chiffré AES-256, cf. database.py), qui y est donc explicitement autorisé.
    - development/local/test : aucun invariant bloquant (la vérification
      SECRET_KEY reste appliquée séparément, dans tous les environnements).
    """
    env = str(cfg.ENVIRONMENT).lower()
    if env not in ("production", "cabinet"):
        return []

    errors = []
    if cfg.DEBUG:
        errors.append(f"DEBUG=True interdit en {env} (fuite de stack traces).")
    if env == "production" and cfg.DATABASE_URL.strip().lower().startswith("sqlite"):
        errors.append("DATABASE_URL pointe sur SQLite — la production exige PostgreSQL.")
    if "*" in cfg.ALLOWED_ORIGINS:
        errors.append("ALLOWED_ORIGINS contient un wildcard '*' (incompatible avec allow_credentials).")
    return errors


# --- LIFESPAN ---
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Demarrage de Digital Crown API...")

    # Sécurité : refuser le démarrage si la clé secrète par défaut est utilisée
    from backend.config import settings as _cfg
    _weak_keys = {"SET_A_REAL_SECRET_KEY_IN_ENV", "dev_only_secret_key_change_me", "changeme", "secret"}
    if _cfg.SECRET_KEY in _weak_keys or len(_cfg.SECRET_KEY) < 32:
        raise RuntimeError(
            "SECURITE : SECRET_KEY non configurée. "
            "Ajoutez SECRET_KEY=<clé_aléatoire_longue> dans votre fichier .env avant de démarrer."
        )

    # S9 : invariants PRODUCTION/CABINET — fail-fast pour éviter d'exposer des
    # données patients réelles avec une config non durcie. N'affecte pas le
    # mode développement.
    _prod_errors = validate_environment_invariants(_cfg)
    if _prod_errors:
        raise RuntimeError(
            "SECURITE : démarrage refusé. " + " ".join(_prod_errors)
        )

    try:
        # 1. Initialisation DB dans %APPDATA% via AppPaths
        models.Base.metadata.create_all(bind=database.engine)

        # 2. Migration des colonnes frontdesk pour les appointments
        database.migrate_appointment_columns()
        database.migrate_actes_columns()
        database.migrate_patient_columns()
        database.migrate_proactive_alert_columns()
        database.migrate_cabinet_config_columns()
        database.migrate_zka_pairing_token_columns()

        # Activation de la synchronisation Zero-Knowledge (Observer Mode)
        sync_manager.start_listening()

        with database.SessionLocal() as db:
            run_full_seed(db)
            seed_clinical_data(db)
            # Catalogue Dynamique (spécialités/actes) — seed additif idempotent,
            # source unique partagée par les Réglages ET la recherche d'actes agenda.
            from backend.seed_catalog import seed_catalog
            seed_catalog(db)

        # Bootstrap plateforme uniquement si le control-plane dédié est activé.
        seed_admin_user()

        # 2. Vérification des licences Firebase (par cabinet via public_id)
        #    Chaque CabinetConfig.public_id est l'identifiant unique du document Firestore
        await _sync_all_licenses_from_firebase()

        # 3. Initialisation asynchrone du moteur panoramique (OPG)
        await panoramic_engine.initialize()

        # Ghost Hub — FTS5 bulk index au démarrage (background)
        import threading
        def _bulk_index():
            try:
                from backend.services.fts_indexer import bulk_index_unindexed_patients
                with database.SessionLocal() as idx_db:
                    bulk_index_unindexed_patients(idx_db)
            except Exception as _e:
                logger.warning("FTS bulk index startup failed: %s", _e)
        threading.Thread(target=_bulk_index, daemon=True).start()

        # E1 — Scheduler quotidien alertes proactives
        from backend.services.daily_scheduler import start_daily_scheduler
        start_daily_scheduler()

        # 4. Tâche background : re-synchronisation Firebase toutes les 6h
        firebase_sync_task = asyncio.create_task(_periodic_firebase_sync())

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Erreur Initialisation : {e}")
        raise

    yield

    firebase_sync_task.cancel()
    logger.info("Arret de l'API...")


async def _sync_all_licenses_from_firebase() -> None:
    """Vérifie les licences signées et ne garde SQLite que comme miroir d'affichage."""
    license_service = LicenseService()
    try:
        with database.SessionLocal() as db:
            configs = db.query(models.CabinetConfig).all()
            if not configs:
                logger.warning("Aucun cabinet trouvé en DB. Vérification Firebase ignorée.")
                return

            for config in configs:
                public_id = config.public_id
                clinic_id = str(config.clinic_id or public_id)
                owner = db.query(models.User).filter(models.User.id == config.owner_id).first()
                if not owner:
                    continue

                firebase_result = await license_service.validate_license_with_expiry(clinic_id)
                license_ok = firebase_result["active"]
                expiry = firebase_result.get("expiration_date")

                # active=None → Firebase injoignable : on CONSERVE le miroir local.
                # L'autorité runtime reste la preuve signée du coffre hors-ligne.
                if license_ok is None:
                    logger.warning(
                        f"Licence cabinet '{clinic_id}' (user: {owner.email}) : "
                        "Firebase injoignable — miroir local conservé."
                    )
                    continue

                owner.is_licensed = bool(license_ok)
                owner.license_expires_at = expiry
                db.commit()

                invalidate_license_cache(owner.email)

                status = "✅ ACTIVE" if license_ok else "❌ EXPIRÉE/INVALIDE"
                logger.info(f"Licence signée cabinet '{clinic_id}' (public_id: {public_id}, user: {owner.email}) : {status}")

    except Exception as e:
        logger.error(f"Erreur sync licences Firebase : {e}")


async def _periodic_firebase_sync() -> None:
    """Tâche background : re-vérifie Firebase toutes les 6 heures."""
    while True:
        try:
            await asyncio.sleep(6 * 3600)
            logger.info("🔄 Re-synchronisation périodique des licences depuis Firebase...")
            await _sync_all_licenses_from_firebase()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Erreur sync périodique licences : {e}")

app = FastAPI(
    title="Digital Crown API - SANINOVA Edition",
    version="1.2.0",
    lifespan=lifespan
)

# --- EXCEPTION HANDLERS ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error: {str(exc.errors())}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# --- MIDDLEWARES ---
# CORS is added further down after HTTP middlewares

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000)
    # Ne pas logger les assets statiques pour éviter le bruit
    if not request.url.path.startswith(("/static", "/api/static")):
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)"
        )
    return response

@app.middleware("http")
async def license_check_middleware(request: Request, call_next):
    # Routes qui ne doivent pas créer une boucle bootstrap/licence.
    allowed_prefixes = (
        "/static", "/api/static", "/assets",
        "/api/auth",
        "/api/superadmin",  # protégé séparément par control-plane + RBAC
        "/api/clinics/recheck-license", "/api/clinics/license-status",
        "/api/clinics/init-status",
        "/health"
    )
    if request.url.path.startswith(allowed_prefixes) or request.method == "OPTIONS":
        return await call_next(request)
    if request.method == "POST" and request.url.path.rstrip("/") == "/api/clinics":
        # Création initiale du shell cabinet avant activation commerciale.
        return await call_next(request)

    # Extraire et décoder le JWT (cookie-first, fallback Authorization header)
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        # Pas de token → laisser FastAPI gérer l'auth/publicité de la route.
        return await call_next(request)
    try:
        from jose import jwt
        from backend.security import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        subject = payload.get("sub", "")
    except Exception as e:
        err_str = str(e).lower()
        if "expired" in err_str or "signature" in err_str:
            logger.warning(f"JWT Expiré (Normal): {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": "TOKEN_EXPIRED", "message": "Session expirée. Veuillez vous reconnecter."}
            )
        # Token invalide/corrompu → laisser FastAPI gérer
        logger.error(f"JWT Decode error in middleware: {e}")
        return await call_next(request)

    # SEC-1 : web et mobile consultent exactement la même preuve signée.
    if token_type == "mobile":
        try:
            mobile_user_id = int(subject)
        except (TypeError, ValueError):
            return JSONResponse(status_code=401, content={"detail": "TOKEN_INVALID"})
        is_ok, reason = await get_mobile_user_license_status(mobile_user_id)
    else:
        email = str(subject)
        is_ok, reason = await get_user_license_status(email)

    if not is_ok and request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        messages = {
            "NOT_LICENSED": "Mode lecture seule : Votre cabinet n'a pas de licence active.",
            "LICENSE_EXPIRED": "Mode lecture seule : Votre licence a expiré.",
            "SUSPENDED": "Votre accès a été suspendu.",
            "ARCHIVED": "Ce compte est archivé.",
            "USER_NOT_FOUND": "Compte introuvable. Veuillez vous reconnecter.",
            "SIGNED_LICENSE_NOT_CONFIGURED": "Mode lecture seule : licence signée non configurée.",
            "SIGNED_LICENSE_REQUIRED": "Mode lecture seule : aucune preuve de licence signée valide.",
            "unsigned_license": "Mode lecture seule : licence legacy non signée refusée.",
            "invalid_signature_or_claims": "Mode lecture seule : preuve de licence invalide.",
            "LICENSE_STATUS_UNAVAILABLE": "Mode lecture seule : état de licence indisponible temporairement.",
        }
        return JSONResponse(
            status_code=403,
            content={
                "detail": reason,
                "message": messages.get(reason, "Accès refusé. Vérifiez votre licence signée.")
            }
        )

    return await call_next(request)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# --- INCLUSION DES ROUTERS ---
from backend.config import settings as _settings
ALLOWED_ORIGINS = [o.strip() for o in _settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    # http ET https : le LAN tourne en HTTP par défaut (HTTPS seulement si certs).
    # Couvre toute IP LAN privée sur :5173 → robuste aux changements d'IP DHCP
    # (évite de devoir mettre à jour ALLOWED_ORIGINS dans .env à chaque bail DHCP).
    allow_origin_regex=r"https?://((192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}):5173",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["X-Total-Count"],
)
from backend.routers import (
    auth, clinics, patients, ia, documents, stats, admin,
    appointments, templates, prescriptions, accounting, team,
    intelligence, clinical_data, mobile, installments, lab_jobs, stock,
    bot, catalog, verification, analytics, agenda_settings, medications, frontdesk, partner_orders, partner_catalog
)
from backend.routers import ai_feedback as ai_feedback_router

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clinics.router, prefix="/api/clinics", tags=["Clinics"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(ia.router, prefix="/api/ia", tags=["IA & Analysis"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(verification.router, prefix="/api/documents", tags=["Vérification publique"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistiques"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics & Finance"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Agenda"])
app.include_router(frontdesk.router, prefix="/api", tags=["Frontdesk"])
app.include_router(agenda_settings.router, prefix="/api", tags=["Agenda Settings"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(prescriptions.prescription_router, prefix="/api/prescriptions", tags=["Prescriptions"])
app.include_router(prescriptions.actes_router, prefix="/api/actes", tags=["Actes Cliniques"])
app.include_router(accounting.router, prefix="/api/accounting", tags=["Accounting & Payments"])
app.include_router(team.router, prefix="/api/team", tags=["Team Management"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["Elite Intelligence"])
app.include_router(clinical_data.router, prefix="/api/clinical-data", tags=["Données Cliniques"])
app.include_router(mobile.router, prefix="/api/mobile", tags=["Mobile ZKA"])
app.include_router(ai_feedback_router.router, prefix="/api/ai", tags=["Ghost Hub Feedback"])
app.include_router(installments.router, prefix="/api/installments", tags=["Installments"])
app.include_router(lab_jobs.router, prefix="/api/lab-jobs", tags=["Lab Jobs"])
app.include_router(stock.router, prefix="/api/stock", tags=["Stock"])
app.include_router(partner_orders.router, prefix="/api/partner-orders", tags=["Partner Orders"])
app.include_router(partner_catalog.router, prefix="/api/partner-catalog", tags=["Partner Catalog"])
app.include_router(bot.router, prefix="/api/bot", tags=["Crown Bot"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["Catalog"])
app.include_router(medications.router, prefix="/api/medications", tags=["Medications"])

from backend.routers import superadmin
app.include_router(superadmin.router, prefix="/api/superadmin", tags=["Super Admin"])

from backend.routers import public as public_router
app.include_router(public_router.router, prefix="/api/public", tags=["Public"])

# --- HEALTH CHECK ---
@app.get("/health", include_in_schema=False)
async def health_check():
    try:
        with database.SessionLocal() as db:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "degraded", "db": str(e)})


def _get_app_version() -> str:
    """Retourne le hash court du commit git déployé, ou 'unknown' hors dépôt git."""
    try:
        import subprocess
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=BASE_DIR, stderr=subprocess.DEVNULL, timeout=2,
        ).decode().strip()
    except Exception:
        return "unknown"


_APP_VERSION = _get_app_version()


@app.get("/api/health", include_in_schema=False)
async def api_health_check():
    """Health check pré-prod/prod — statut app + DB + environnement + version déployée."""
    db_status = "ok"
    try:
        with database.SessionLocal() as db:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"

    payload = {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "environment": str(app_settings.ENVIRONMENT),
        "version": _APP_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    return JSONResponse(status_code=200 if db_status == "ok" else 503, content=payload)


@app.get("/api/health/db", include_in_schema=False)
async def api_health_db():
    """Vérifie uniquement la connexion DB (SELECT 1)."""
    try:
        with database.SessionLocal() as db:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


@app.get("/api/health/storage", include_in_schema=False)
async def api_health_storage():
    """Vérifie que le dossier de stockage média est accessible en écriture."""
    try:
        media_dir = get_media_root()
        media_dir.mkdir(parents=True, exist_ok=True)
        probe = media_dir / ".health_probe"
        probe.write_text("ok")
        probe.unlink()
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})

# --- STATIC FILES & UI ---

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# 1. Dossier Static des Médias (Photos patients, etc.)
# En prod, on utilise un dossier dans %APPDATA%. MEDIA_ROOT permet d'isoler
# une instance de test/rehearsal (jamais défini en cabinet réel -> comportement inchangé).
MEDIA_DIR = get_media_root()
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# Mount pour les uploads locaux (dev & reports)
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- P0.2 : PROTECTION DES FICHIERS PATIENTS ---------------------------------
# Avant ce correctif, l'imagerie patient (panoramiques, céphalo) et les
# documents (ordonnances, notes — avec le nom du patient dans le fichier)
# étaient servis PUBLIQUEMENT via les mounts StaticFiles ci-dessous.
#
# On enregistre ici des routes AUTHENTIFIÉES pour les seuls sous-chemins
# sensibles. Starlette évalue les routes dans l'ordre d'enregistrement
# (premier match gagnant) : ces routes étant déclarées AVANT les mounts,
# elles interceptent les fichiers patients tandis que les mounts ne servent
# plus que le branding/logo/polices/modèles (assets non sensibles, publics).
#
# Les URLs sont INCHANGÉES → aucune modification frontend : le navigateur
# joint automatiquement le cookie `access_token` aux balises <img>.
from fastapi import Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.routers.auth import get_current_user
from backend import database, models

def _serve_protected_file(base_dir: str, rel_path: str) -> FileResponse:
    """Sert un fichier sous base_dir avec protection contre le path traversal."""
    safe_root = os.path.realpath(base_dir)
    abs_path = os.path.realpath(os.path.join(safe_root, rel_path))
    if not abs_path.startswith(safe_root + os.sep) and abs_path != safe_root:
        raise HTTPException(status_code=400, detail="Chemin de fichier invalide")
    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return FileResponse(abs_path)

def _assert_media_tenant(db: Session, employer_id: int, model_cls, path_col_name: str, path_fragment: str, current_user=None):
    """
    Vérifie que le fichier appartient au cabinet de l'utilisateur.
    Stratégie : si un enregistrement DB existe pour ce chemin mais appartient à un
    autre cabinet → 403. Si aucun enregistrement → laisser passer (fichier legacy
    non référencé). Empêche le cross-tenant sur tous les fichiers tracés en base.
    """
    path_col = getattr(model_cls, path_col_name)
    record = (
        db.query(model_cls)
        .filter(path_col.like(f"%{path_fragment}"))
        .join(models.Patient, getattr(model_cls, "patient_id") == models.Patient.id)
        .first()
    )
    if record is not None and record.patient.employer_id != employer_id:
        if current_user is not None:
            from backend.services.audit_service import audit_service
            audit_service.log(
                db=db, user_id=current_user.id, employer_id=employer_id,
                action="MEDIA_ACCESS_DENIED", resource_type=model_cls.__name__, resource_id=path_fragment,
                severity="WARNING", details=f"Tentative d'accès média cross-tenant : {path_fragment}",
            )
        raise HTTPException(status_code=403, detail="Accès refusé")

# Imagerie patient (radios) — AUTH + tenant requis.
@app.get("/api/static/uploads/panoramic/{rel_path:path}", include_in_schema=False)
@app.get("/static/uploads/panoramic/{rel_path:path}", include_in_schema=False)
async def serve_panoramic(
    rel_path: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_media_tenant(db, current_user.get_employer_id(), models.PanoramicAnalysis, "image_path", f"panoramic/{rel_path}", current_user)
    return _serve_protected_file(os.path.join(UPLOAD_DIR, "panoramic"), rel_path)

@app.get("/api/static/uploads/radios/{rel_path:path}", include_in_schema=False)
@app.get("/static/uploads/radios/{rel_path:path}", include_in_schema=False)
async def serve_radios(
    rel_path: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_media_tenant(db, current_user.get_employer_id(), models.CephaloAnalysis, "image_original_path", f"radios/{rel_path}", current_user)
    return _serve_protected_file(os.path.join(UPLOAD_DIR, "radios"), rel_path)

# Documents patients archivés (ordonnances, notes…) — AUTH + tenant requis.
@app.get("/api/static/archives/{rel_path:path}", include_in_schema=False)
async def serve_archives(
    rel_path: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_media_tenant(db, current_user.get_employer_id(), models.DocumentArchive, "file_path", rel_path, current_user)
    return _serve_protected_file(os.path.join(str(MEDIA_DIR), "archives"), rel_path)

@app.get("/api/static/documents/{rel_path:path}", include_in_schema=False)
async def serve_documents(
    rel_path: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_media_tenant(db, current_user.get_employer_id(), models.DocumentArchive, "file_path", rel_path, current_user)
    return _serve_protected_file(os.path.join(str(MEDIA_DIR), "documents"), rel_path)

# Pièces jointes d'actes — AUTH + tenant requis (stockées dans uploads/actes/).
@app.get("/api/static/uploads/actes/{filename}", include_in_schema=False)
async def serve_acte_attachment(
    filename: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    # Path traversal guard
    safe = os.path.basename(filename)
    if safe != filename or ".." in filename:
        raise HTTPException(status_code=403, detail="Chemin non autorisé")

    # Retrouver le patient propriétaire via la table Acte
    from sqlalchemy import cast, String
    acte = (
        db.query(models.Acte)
        .filter(cast(models.Acte.attachments, String).like(f"%{safe}%"))
        .join(models.Patient, models.Acte.patient_id == models.Patient.id)
        .first()
    )
    if acte is not None and acte.patient.employer_id != current_user.get_employer_id():
        raise HTTPException(status_code=403, detail="Accès refusé")

    return _serve_protected_file(os.path.join(UPLOAD_DIR, "actes"), safe)

# Branding cabinet (logos, en-têtes) — AUTH requise, pas de contrôle patient.
@app.get("/api/static/uploads/clinics/{rel_path:path}", include_in_schema=False)
@app.get("/static/uploads/clinics/{rel_path:path}", include_in_schema=False)
async def serve_clinic_asset(
    rel_path: str,
    current_user=Depends(get_current_user),
):
    return _serve_protected_file(os.path.join(UPLOAD_DIR, "clinics"), rel_path)

# --- SECURITE P0 : mounts StaticFiles publics supprimés ----------------------
# Tous les chemins patients (panoramic, radios, archives, documents, actes, clinics)
# sont couverts par des routes authentifiées ci-dessus.
# Tout chemin non couvert retourne 404 (comportement sûr par défaut).

# 2. Servage du Frontend React (SPA)
FRONTEND_DIST = AppPaths.get_static_dir()

if FRONTEND_DIST.exists():
    from fastapi.responses import FileResponse

    # Assets statiques (JS, CSS, images, sw.js, manifest.json…)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend_assets")

    # Fichiers à la racine du dist (sw.js, manifest.json, logo_gold.png…)
    _dist_root_files = {p.name for p in FRONTEND_DIST.iterdir() if p.is_file()}

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str, request: Request):
        if full_path.startswith("api/"):
            if not full_path.endswith("/"):
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=f"/{full_path}/", status_code=307)
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API Route Not Found")
            
        # Fichier statique connu à la racine du dist → le servir directement
        if full_path in _dist_root_files:
            return FileResponse(str(FRONTEND_DIST / full_path))
        # Toute autre route SPA → index.html (React Router gère)
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    logger.info(f"Frontend servit depuis : {FRONTEND_DIST}")
else:
    @app.get("/")
    def root():
        return {"status": "online", "message": "API Active (Frontend non trouve)"}
