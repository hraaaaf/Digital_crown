from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# --- PASSWORD HASHING ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONFIGURATION DE LA CONNEXION (POSTGRESQL) ---
# On cible la BONNE base (digitalcrown_db)
# On FORCE le client_encoding=utf8 directement dans l'URL (Fix Nucléaire)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@localhost/digitalcrown_db?client_encoding=utf8"

# --- INITIALISATION DU MOTEUR ---
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"client_encoding": "utf8"}
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
        try:
            # Vérifier et ajouter les colonnes de branding et structure manquantes
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS selected_theme VARCHAR DEFAULT 'elite'"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS nom_cabinet VARCHAR DEFAULT ''"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS nom_praticien VARCHAR DEFAULT ''"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS nom_praticien_ar VARCHAR DEFAULT ''"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS secondary_color VARCHAR DEFAULT '#1e40af'"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS accent_color VARCHAR DEFAULT '#60a5fa'"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS cabinet_type VARCHAR DEFAULT 'PRIVE'"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS logo_path VARCHAR"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS letterhead_path VARCHAR"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS selected_template VARCHAR DEFAULT 'classic'"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS font_fr VARCHAR DEFAULT 'inter'"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS font_ar VARCHAR DEFAULT 'amiri'"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS margin_top FLOAT DEFAULT 3.6"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS margin_bottom FLOAT DEFAULT 3.2"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS ice VARCHAR DEFAULT ''"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS if_ VARCHAR DEFAULT ''"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS inpe VARCHAR DEFAULT ''"))
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN IF NOT EXISTS contacts_json JSONB DEFAULT '{}'"))
            conn.commit()
            print("Database check completed: All branding and layout columns verified.")
        except Exception as e:
            print(f"Migration notice: {e}")

# Exécuter au chargement du module
check_and_update_db()
