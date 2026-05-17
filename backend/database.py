import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from backend.core.paths import AppPaths

# Charger les variables d'environnement depuis le fichier .env dans le dossier backend
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

# --- PASSWORD HASHING ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONFIGURATION DE LA CONNEXION ---
# En mode dev/prod locale, on utilise SQLite via AppPaths.
# En mode Cloud (si DATABASE_URL est présent), on garde PostgreSQL.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", AppPaths.get_db_url())

# --- INITIALISATION DU MOTEUR ---
# Si SQLite, on désactive les paramètres spécifiques PostgreSQL (pool_size, etc.)
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False} # Requis pour FastAPI + SQLite
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- AUTO-MIGRATION (Self-Healing) ---
def check_and_update_db():
    from sqlalchemy import text
    
    # Utiliser une approche ligne par ligne avec des transactions isolées (engine.begin)
    # pour éviter qu'un échec sur PostgreSQL n'annule les requêtes suivantes.
    def safe_execute(sql):
        try:
            with engine.begin() as conn:
                conn.execute(text(sql))
        except Exception as e:
            pass # Ignorer si la colonne existe déjà ou autre erreur (ex: SQLite compatibility)

    # Vérifier et ajouter les colonnes de branding et structure manquantes
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS selected_theme VARCHAR DEFAULT 'elite'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS nom_cabinet VARCHAR DEFAULT ''")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS nom_praticien VARCHAR DEFAULT ''")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS nom_praticien_ar VARCHAR DEFAULT ''")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS secondary_color VARCHAR DEFAULT '#1e40af'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS accent_color VARCHAR DEFAULT '#60a5fa'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS cabinet_type VARCHAR DEFAULT 'PRIVE'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS logo_path VARCHAR")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS letterhead_path VARCHAR")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS selected_template VARCHAR DEFAULT 'classic'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS font_fr VARCHAR DEFAULT 'inter'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS font_ar VARCHAR DEFAULT 'amiri'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS header_lines_fr JSONB DEFAULT '[]'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS header_lines_ar JSONB DEFAULT '[]'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS specialty_ids JSONB DEFAULT '[]'")

    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS margin_top FLOAT DEFAULT 3.6")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS margin_bottom FLOAT DEFAULT 3.2")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS header_font_scale FLOAT DEFAULT 1.0")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS header_logo_scale FLOAT DEFAULT 1.0")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS header_line_height FLOAT DEFAULT 1.0")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS footer_font_scale FLOAT DEFAULT 1.0")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS footer_qr_scale FLOAT DEFAULT 1.0")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS footer_line_height FLOAT DEFAULT 1.0")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS ice VARCHAR DEFAULT ''")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS if_ VARCHAR DEFAULT ''")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS inpe VARCHAR DEFAULT ''")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS contacts_json JSONB DEFAULT '{}'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS cloture_note_template TEXT DEFAULT 'Arrêtée la présente note à la somme de {total_words} TTC.'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS cloture_devis_template TEXT DEFAULT 'Arrêté le présent devis à la somme de {total_words} TTC.'")
    
    # --- QR CODE STRATEGY ---
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS qr_code_enabled BOOLEAN DEFAULT FALSE")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS qr_code_type VARCHAR DEFAULT 'VCARD'")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS qr_code_value VARCHAR(500)")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS qr_code_color VARCHAR(7)")
    safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS qr_code_label VARCHAR(100)")
    
    # --- MIGRATIONS PATIENTS & ACCESS CONTROL ---
    safe_execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS adresse VARCHAR(255)")
    safe_execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS assurance VARCHAR(50)")
    safe_execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS numero_dossier VARCHAR(20)")
    safe_execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS employer_id INTEGER DEFAULT 1")
    
    safe_execute("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS employer_id INTEGER DEFAULT 1")
    
    def add_column(table, column, type, default):
        try:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type} DEFAULT {default}"))
            print(f"Added column {column} to {table}")
        except Exception:
            pass # Already exists or other error

    add_column("document_archives", "payment_status", "VARCHAR(20)", "'EN_ATTENTE'")
    add_column("document_archives", "is_accounted", "BOOLEAN", "1")
    add_column("document_archives", "is_collected", "BOOLEAN", "0")
    add_column("document_archives", "is_latest_version", "BOOLEAN", "1")
    add_column("document_archives", "status", "VARCHAR(20)", "'ACTIF'")
    
    add_column("actes", "is_accounted", "BOOLEAN", "0")
    add_column("actes", "is_collected", "BOOLEAN", "0")
    
    print("Database self-healing migration successfully completed.")

# Exécuter au chargement du module
check_and_update_db()
