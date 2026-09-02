import os
import sys
import sqlite3
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from backend.core.paths import AppPaths
from backend.env_loader import load_backend_env

# Charger les variables d'environnement backend avant l'initialisation DB
load_backend_env(override=False)

# --- PASSWORD HASHING ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONFIGURATION DE LA CONNEXION ---
# En mode dev/prod locale, on utilise SQLite via AppPaths.
# En mode Cloud (si DATABASE_URL est présent), on garde PostgreSQL.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", AppPaths.get_db_url())
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()

logger = logging.getLogger(__name__)

# En mode cabinet on-premise, une SQLite sur disque DOIT être chiffrée.
# Les bases :memory: restent autorisées pour les tests/dev isolés.
SQLCIPHER_REQUIRED = (
    ENVIRONMENT == "cabinet"
    and SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    and ":memory:" not in SQLALCHEMY_DATABASE_URL
)

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
                conn_test = sqlite3.connect(db_file_path)
                conn_test.execute("SELECT name FROM sqlite_master WHERE type='table'")
                is_plaintext = True
            except sqlite3.DatabaseError:
                is_plaintext = False
            except Exception:
                is_plaintext = False
            finally:
                if conn_test:
                    try:
                        conn_test.close()
                    except Exception as e:
                        logger.debug(f"Could not close test connection: {e}")

            if is_plaintext:
                logger.warning(f"⚠️ Détection d'une base locale non chiffrée : {db_file_path}")
                logger.warning("🚀 Lancement de la migration transparente à chaud vers SQLCipher AES-256...")

                temp_unencrypted = db_file_path + ".unencrypted.tmp"
                try:
                    if os.path.exists(temp_unencrypted):
                        os.remove(temp_unencrypted)
                    os.rename(db_file_path, temp_unencrypted)

                    from sqlcipher3 import dbapi2 as sqlcipher
                    enc_conn = sqlcipher.connect(db_file_path)
                    safe_passphrase = passphrase.replace("'", "''")
                    safe_temp_path = temp_unencrypted.replace("'", "''")
                    enc_conn.execute(f"PRAGMA key = '{safe_passphrase}'")
                    enc_conn.execute(f"ATTACH DATABASE '{safe_temp_path}' AS plaintext KEY ''")
                    enc_conn.execute("SELECT sqlcipher_export('main', 'plaintext')")
                    enc_conn.execute("DETACH DATABASE plaintext")
                    enc_conn.close()
                    os.remove(temp_unencrypted)
                    logger.info("✅ Migration transparente vers SQLCipher terminée avec succès.")
                except Exception as e:
                    logger.error(f"❌ Échec de la migration transparente vers SQLCipher : {e}")
                    if os.path.exists(temp_unencrypted) and not os.path.exists(db_file_path):
                        os.rename(temp_unencrypted, db_file_path)
                    if SQLCIPHER_REQUIRED:
                        raise RuntimeError(
                            "SQLCipher requis en mode cabinet : migration de la base locale impossible. "
                            "Démarrage refusé pour éviter l'ouverture d'une base non chiffrée."
                        ) from e

    try:
        import sqlcipher3
        sys.modules["pysqlcipher3"] = sqlcipher3

        if ":memory:" in SQLALCHEMY_DATABASE_URL:
            SQLALCHEMY_DATABASE_URL = f"sqlite+pysqlcipher://:{passphrase}@/:memory:"
        else:
            db_file_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
            db_file_path = os.path.abspath(db_file_path).replace("\\", "/")
            SQLALCHEMY_DATABASE_URL = f"sqlite+pysqlcipher://:{passphrase}@/{db_file_path}"
        logger.info("🔒 Connexion SQLite sécurisée par chiffrement SQLCipher (AES-256).")
    except ImportError as e:
        logger.error("❌ Module 'sqlcipher3' non trouvé. La base SQLite ne sera pas chiffrée.")
        if SQLCIPHER_REQUIRED:
            raise RuntimeError(
                "SQLCipher requis en mode cabinet mais le driver 'sqlcipher3' est indisponible. "
                "Démarrage refusé pour éviter une SQLite non chiffrée."
            ) from e

# --- INITIALISATION DU MOTEUR ---
if "pysqlcipher" in SQLALCHEMY_DATABASE_URL or SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=10,
        max_overflow=5,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def migrate_appointment_columns():
    """Ajoute les colonnes frontdesk si absentes (ALTER TABLE, SQLite ou PostgreSQL)."""
    from sqlalchemy import text
    datetime_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"
    new_columns = [
        ("source", "VARCHAR(50)"),
        ("phone", "VARCHAR(30)"),
        ("confirmed_by_id", "INTEGER"),
        ("confirmed_at", datetime_type),
        ("expires_at", datetime_type),
    ]
    try:
        with engine.connect() as conn:
            for col_name, col_type in new_columns:
                try:
                    conn.execute(text(f"ALTER TABLE appointments ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"✅ Added column {col_name} to appointments table")
                except Exception as e:
                    conn.rollback()
                    logger.debug(f"Column {col_name} may already exist: {e}")
    except Exception as e:
        logger.warning(f"Migration warning: {e}")


def migrate_actes_columns():
    """Ajoute les colonnes additives de la table actes si absentes (ALTER TABLE, SQLite ou PostgreSQL)."""
    from sqlalchemy import text
    datetime_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"
    try:
        with engine.connect() as conn:
            try:
                conn.execute(text(
                    "ALTER TABLE actes ADD COLUMN document_archive_id INTEGER "
                    "REFERENCES document_archives(id)"
                ))
                conn.commit()
                logger.info("✅ Added column document_archive_id to actes table")
            except Exception as e:
                conn.rollback()
                logger.debug(f"Column document_archive_id may already exist: {e}")
            try:
                conn.execute(text(f"ALTER TABLE actes ADD COLUMN deleted_at {datetime_type}"))
                conn.commit()
                logger.info("✅ Added column deleted_at to actes table")
            except Exception as e:
                conn.rollback()
                logger.debug(f"Column deleted_at may already exist: {e}")
    except Exception as e:
        logger.warning(f"Migration warning (actes): {e}")


def migrate_patient_columns():
    """Ajoute Patient.deleted_at/deleted_by si absents (soft-delete P1)."""
    from sqlalchemy import text
    datetime_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"
    new_columns = [
        ("deleted_at", datetime_type),
        ("deleted_by", "INTEGER"),
    ]
    try:
        with engine.connect() as conn:
            for col_name, col_type in new_columns:
                try:
                    conn.execute(text(f"ALTER TABLE patients ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"✅ Added column {col_name} to patients table")
                except Exception as e:
                    conn.rollback()
                    logger.debug(f"Column {col_name} may already exist: {e}")
    except Exception as e:
        logger.warning(f"Migration warning (patients): {e}")


def migrate_proactive_alert_columns():
    """Ajoute ProactiveAlert.snoozed_until si absent (report/snooze persistant)."""
    from sqlalchemy import text
    datetime_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"
    try:
        with engine.connect() as conn:
            try:
                conn.execute(text(f"ALTER TABLE proactive_alerts ADD COLUMN snoozed_until {datetime_type}"))
                conn.commit()
                logger.info("✅ Added column snoozed_until to proactive_alerts table")
            except Exception as e:
                conn.rollback()
                logger.debug(f"Column snoozed_until may already exist: {e}")
    except Exception as e:
        logger.warning(f"Migration warning (proactive_alerts): {e}")


def migrate_cabinet_config_columns():
    """Ajoute les colonnes CabinetConfig additives absentes (SQLite/PostgreSQL)."""
    from sqlalchemy import text
    new_columns = [
        ("header_logo_offset_x", "FLOAT"),
        ("header_logo_offset_y", "FLOAT"),
        ("qr_code_offset_x", "FLOAT"),
        ("qr_code_offset_y", "FLOAT"),
        ("content_offset_y", "FLOAT DEFAULT 0.0"),
        ("custom_specialty_fr", "VARCHAR(255)"),
        ("custom_specialty_ar", "VARCHAR(255)"),
        ("header_customized", "BOOLEAN DEFAULT FALSE"),
    ]
    try:
        with engine.connect() as conn:
            for col_name, col_type in new_columns:
                try:
                    conn.execute(text(f"ALTER TABLE cabinet_configs ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"✅ Added column {col_name} to cabinet_configs table")
                except Exception as e:
                    conn.rollback()
                    logger.debug(f"Column {col_name} may already exist: {e}")
    except Exception as e:
        logger.warning(f"Migration warning (cabinet_configs): {e}")

    from backend.models_identity_p4 import migrate_identity_columns
    migrate_identity_columns(engine)



def migrate_zka_pairing_token_columns():
    """Ajoute l'identité utilisateur et le code manuel séparé aux tokens ZKA existants."""
    from sqlalchemy import text
    new_columns = [
        ("user_id", "INTEGER"),
        ("manual_code", "VARCHAR(6)"),
    ]
    try:
        with engine.connect() as conn:
            for col_name, col_type in new_columns:
                try:
                    conn.execute(text(f"ALTER TABLE zka_pairing_tokens ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info("Added column %s to zka_pairing_tokens", col_name)
                except Exception as exc:
                    conn.rollback()
                    logger.debug("Column %s may already exist: %s", col_name, exc)
    except Exception as exc:
        logger.warning("Migration warning (zka_pairing_tokens): %s", exc)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- AUTO-MIGRATION (Self-Healing) ---
