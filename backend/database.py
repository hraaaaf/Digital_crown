import os
import sys
import sqlite3
import logging
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

logger = logging.getLogger(__name__)

# --- CONFIGURATION & ENCRYPTION SQLCIPHER POUR SQLITE ---
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # Récupérer la clé principale Cabinet (ZKA) ou dériver depuis SECRET_KEY
    passphrase = os.getenv("CABINET_MASTER_KEY_HEX", os.getenv("SECRET_KEY", "default-dc-fallback-key"))
    
    # Si base sur disque (pas de :memory:), vérifier et migrer la base existante si elle est en clair
    if ":memory:" not in SQLALCHEMY_DATABASE_URL:
        db_file_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
        db_file_path = os.path.abspath(db_file_path)
        
        if os.path.exists(db_file_path):
            is_plaintext = False
            conn_test = None
            try:
                # Test d'ouverture en standard (sans clé)
                conn_test = sqlite3.connect(db_file_path)
                conn_test.execute("SELECT name FROM sqlite_master WHERE type='table'")
                is_plaintext = True
            except sqlite3.DatabaseError:
                # La base est chiffrée ou corrompue
                is_plaintext = False
            except Exception:
                is_plaintext = False
            finally:
                if conn_test:
                    try:
                        conn_test.close()
                    except Exception:
                        pass
            
            # Si elle est lisible en clair, on effectue la migration vers SQLCipher
            if is_plaintext:
                logger.warning(f"⚠️ Détection d'une base locale non chiffrée : {db_file_path}")
                logger.warning("🚀 Lancement de la migration transparente à chaud vers SQLCipher AES-256...")
                
                temp_unencrypted = db_file_path + ".unencrypted.tmp"
                try:
                    if os.path.exists(temp_unencrypted):
                        os.remove(temp_unencrypted)
                    os.rename(db_file_path, temp_unencrypted)
                    
                    # Créer la base chiffrée avec SQLCipher
                    from sqlcipher3 import dbapi2 as sqlcipher
                    enc_conn = sqlcipher.connect(db_file_path)
                    # Escape single quotes to prevent SQL injection in PRAGMA statements
                    safe_passphrase = passphrase.replace("'", "''")
                    safe_temp_path = temp_unencrypted.replace("'", "''")
                    enc_conn.execute(f"PRAGMA key = '{safe_passphrase}'")

                    # Attacher et copier
                    enc_conn.execute(f"ATTACH DATABASE '{safe_temp_path}' AS plaintext KEY ''")
                    enc_conn.execute("SELECT sqlcipher_export('main', 'plaintext')")
                    enc_conn.execute("DETACH DATABASE plaintext")
                    enc_conn.close()
                    
                    # Supprimer le fichier en clair temporaire
                    os.remove(temp_unencrypted)
                    logger.info("✅ Migration transparente vers SQLCipher terminée avec succès.")
                except Exception as e:
                    logger.error(f"❌ Échec de la migration transparente vers SQLCipher : {e}")
                    # En cas d'erreur fatale, restaurer le fichier d'origine
                    if os.path.exists(temp_unencrypted) and not os.path.exists(db_file_path):
                        os.rename(temp_unencrypted, db_file_path)

    # Injecter sqlcipher3 dans sys.modules pour que SQLAlchemy l'utilise comme pysqlcipher3
    try:
        import sqlcipher3
        sys.modules['pysqlcipher3'] = sqlcipher3
        
        # Mettre à jour la chaîne de connexion SQLAlchemy pour utiliser sqlite+pysqlcipher
        if ":memory:" in SQLALCHEMY_DATABASE_URL:
            SQLALCHEMY_DATABASE_URL = f"sqlite+pysqlcipher://:{passphrase}@/:memory:"
        else:
            db_file_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
            db_file_path = os.path.abspath(db_file_path).replace("\\", "/")
            SQLALCHEMY_DATABASE_URL = f"sqlite+pysqlcipher://:{passphrase}@/{db_file_path}"
        logger.info("🔒 Connexion SQLite sécurisée par chiffrement SQLCipher (AES-256).")
    except ImportError:
        logger.error("❌ Module 'sqlcipher3' non trouvé. La base SQLite ne sera pas chiffrée.")

# --- INITIALISATION DU MOTEUR ---
# Si SQLite, on utilise le dialecte pysqlcipher sécurisé
if "pysqlcipher" in SQLALCHEMY_DATABASE_URL or SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False} # Requis pour FastAPI
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
            logger.debug(f"Migration (ignoré): {sql[:60]!r} — {e}")

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
    safe_execute("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS reminder_sent BOOLEAN DEFAULT FALSE")
    safe_execute("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS reminder_sent_at TIMESTAMP WITH TIME ZONE")
    
    # --- MIGRATIONS USERS PERMISSIONS & MULTI-TENANCY ---
    safe_execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}'")
    safe_execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions JSON DEFAULT '{}'")
    safe_execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS employer_id INTEGER")
    
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
    
    # --- INDEX CRÉATION (idempotent via IF NOT EXISTS) ---
    safe_execute("CREATE INDEX IF NOT EXISTS idx_actes_patient_id ON actes(patient_id)")
    safe_execute("CREATE INDEX IF NOT EXISTS idx_actes_date_debut ON actes(date_debut)")
    safe_execute("CREATE INDEX IF NOT EXISTS idx_appointments_employer_date ON appointments(employer_id, datetime_start)")
    safe_execute("CREATE INDEX IF NOT EXISTS idx_documents_patient_created ON document_archives(patient_id, created_at)")

    # --- APPAIRAGE MOBILE ZKA (tokens éphémères) ---
    safe_execute("""
        CREATE TABLE IF NOT EXISTS zka_pairing_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token VARCHAR(36) NOT NULL UNIQUE,
            employer_id INTEGER NOT NULL REFERENCES users(id),
            public_id VARCHAR(16) NOT NULL,
            master_key VARCHAR(64) NOT NULL,
            expires_at DATETIME NOT NULL,
            used_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    safe_execute("CREATE INDEX IF NOT EXISTS idx_zka_tokens_token ON zka_pairing_tokens(token)")
    safe_execute("CREATE INDEX IF NOT EXISTS idx_zka_tokens_expires ON zka_pairing_tokens(expires_at)")

    print("Database self-healing migration successfully completed.")

# Exécuter au chargement du module
check_and_update_db()
