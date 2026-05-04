import os
import logging
import contextlib
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from backend import models, database
from backend.seed_templates import run_full_seed
from backend.services.panoramic_service import panoramic_engine

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
    logger.info("🚀 Démarrage de Digital Crown API...")
    try:
        models.Base.metadata.create_all(bind=database.engine)
        with database.SessionLocal() as db:
            run_full_seed(db)
        
        # Initialisation asynchrone du moteur panoramique (OPG)
        await panoramic_engine.initialize()
    except Exception as e:
        logger.error(f"❌ Erreur Initialisation : {e}")
    yield
    logger.info("🛑 Arrêt de l'API...")

app = FastAPI(
    title="Digital Crown API - SANINOVA Edition",
    version="1.2.0",
    lifespan=lifespan
)

# --- EXCEPTION HANDLERS ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"❌ Validation Error: {exc.errors()}")
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
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

# --- INCLUSION DES ROUTERS ---
from backend.routers import auth, clinics, patients, ia, documents, admin, appointments, templates, prescriptions, accounting

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

# --- STATIC FILES ---
# Placé à la fin pour éviter de masquer des routes d'API
app.mount("/api/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static_legacy")

@app.get("/")
def root():
    return {"status": "online", "message": "Digital Crown API is running."}
