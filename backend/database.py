import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Charger les variables d'environnement depuis le fichier .env dans le dossier backend
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

# --- PASSWORD HASHING ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONFIGURATION DE LA CONNEXION (POSTGRESQL) ---
# Priorité à la variable d'environnement DATABASE_URL, sinon fallback sécurisé.
DEFAULT_DB_URL = "postgresql://postgres:admin@localhost/digitalcrown_db?client_encoding=utf8"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# --- INITIALISATION DU MOTEUR ---
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
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
    with engine.connect() as conn:
        # Utiliser une approche ligne par ligne pour éviter que tout le bloc échoue
        def safe_execute(sql):
            try:
                conn.execute(text(sql))
            except Exception as e:
                pass # Ignorer les erreurs si la colonne existe déjà ou syntaxe incompatible (SQLite)

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
        safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS margin_top FLOAT DEFAULT 3.6")
        safe_execute("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS margin_bottom FLOAT DEFAULT 3.2")
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
        
        try:
            conn.commit()
            print("Database check completed.")
        except:
            pass

# Exécuter au chargement du module
check_and_update_db()
