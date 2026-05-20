import os
import sys
import time
import logging
import contextlib
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from backend import models, database
from backend.services.sync_manager import sync_manager
from backend.seed_templates import run_full_seed
from backend.seed_user import seed_admin_user
from backend.services.panoramic_service import panoramic_engine
from backend.core.paths import AppPaths
from backend.services.license_service import LicenseService
import webbrowser

# --- CONFIGURATION LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION CHEMINS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# --- LIFESPAN ---
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Demarrage de Digital Crown API...")
    
    # 1. Vérification du Kill-Switch Firebase
    clinic_id = os.getenv("CLINIC_ID", "default_clinic")
    license_ok = await LicenseService().validate_license(clinic_id)
    
    if not license_ok:
        logger.error("❌ LICENCE EXPIREE OU DESACTIVEE. L'application va s'arreter.")
        # On pourrait lever une exception ici pour empêcher le démarrage
        # raise SystemExit("Licence invalide")
    
    try:
        # 2. Initialisation DB dans %APPDATA% via AppPaths
        models.Base.metadata.create_all(bind=database.engine)
        
        # Activation de la synchronisation Zero-Knowledge (Observer Mode)
        sync_manager.start_listening()
        
        with database.SessionLocal() as db:
            run_full_seed(db)
        
        # S'assure que l'admin par defaut existe
        seed_admin_user()
        
        # Initialisation asynchrone du moteur panoramique (OPG)
        await panoramic_engine.initialize()

        # 3. Ouverture automatique du navigateur (Build mode uniquement)
        if hasattr(sys, '_MEIPASS'):
            webbrowser.open("http://127.0.0.1:8000")

    except Exception as e:
        logger.error(f"Erreur Initialisation : {e}")
    yield
    logger.info("Arret de l'API...")

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
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["X-Total-Count"],
)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000)
    # Ne pas logger les assets statiques pour éviter le bruit
    if not request.url.path.startswith(("/static", "/api/static")):
        user_agent = request.headers.get("user-agent", "")[:40]
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)"
        )
    return response

# --- INCLUSION DES ROUTERS ---
from backend.routers import auth, clinics, patients, ia, documents, admin, appointments, templates, prescriptions, accounting, team, intelligence

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clinics.router, prefix="/api/clinics", tags=["Clinics"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(ia.router, prefix="/api/ia", tags=["IA & Analysis"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Agenda"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(prescriptions.prescription_router, prefix="/api/prescriptions", tags=["Prescriptions"])
app.include_router(prescriptions.actes_router, prefix="/api/actes", tags=["Actes Cliniques"])
app.include_router(accounting.router, prefix="/api/accounting", tags=["Accounting & Payments"])
app.include_router(team.router, prefix="/api/team", tags=["Team Management"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["Elite Intelligence"])

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

# --- STATIC FILES & UI ---

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# 1. Dossier Static des Médias (Photos patients, etc.)
# En prod, on utilise un dossier dans %APPDATA%
MEDIA_DIR = AppPaths.get_user_data_dir() / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# Mount pour les uploads locaux (dev & reports)
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# /api/static/uploads est prioritaire pour le dossier local dev
app.mount("/api/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="api_uploads")
# /api/static sert le reste depuis MEDIA_DIR (logo, etc.)
app.mount("/api/static", StaticFiles(directory=str(MEDIA_DIR)), name="static")
# Mount legacy pour compatibilité
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 2. Servage du Frontend React (SPA)
FRONTEND_DIST = AppPaths.get_static_dir()

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
    logger.info(f"Frontend servit depuis : {FRONTEND_DIST}")
else:
    @app.get("/")
    def root():
        return {"status": "online", "message": "API Active (Frontend non trouve)"}
