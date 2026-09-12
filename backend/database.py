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
    passphrase = os.getenv("CABINET_MASTER_KEY_HEX", os.getenv("SECRET_KEY", "default-dc-fallback-key"))

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

# Additive layout fields are attached once before routers create/query CabinetConfig.
from backend.models_document_layout import attach_document_layout_columns
attach_document_layout_columns()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def migrate_appointment_columns(bind=None):
    """Ajoute les colonnes additives appointments réellement attendues au runtime.

    Le cabinet historique n'exécute pas automatiquement Alembic. Cette migration
    self-healing doit donc couvrir aussi `praticien_id` introduit par P0, sans
    backfill ni réécriture des rendez-vous existants.
    """
    from sqlalchemy import inspect, text

    db_engine = bind or engine
    datetime_type = "TIMESTAMP" if db_engine.dialect.name == "postgresql" else "DATETIME"
    new_columns = [
        ("source", "VARCHAR(50)"),
        ("phone", "VARCHAR(30)"),
        ("confirmed_by_id", "INTEGER"),
        ("confirmed_at", datetime_type),
        ("expires_at", datetime_type),
        ("praticien_id", "INTEGER REFERENCES users(id) ON DELETE SET NULL"),
    ]
    try:
        with db_engine.connect() as conn:
            for col_name, col_type in new_columns:
                try:
                    conn.execute(text(f"ALTER TABLE appointments ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"✅ Added column {col_name} to appointments table")
                except Exception as e:
                    conn.rollback()
                    logger.debug(f"Column {col_name} may already exist: {e}")
            try:
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_appointments_praticien_id "
                    "ON appointments (praticien_id)"
                ))
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.debug("Appointment practitioner index may already exist: %s", e)
    except Exception as e:
        raise RuntimeError(f"Critical appointments schema migration failed: {e}") from e

    inspector = inspect(db_engine)
    columns = {column["name"] for column in inspector.get_columns("appointments")}
    if "praticien_id" not in columns:
        raise RuntimeError(
            "Critical appointments schema mismatch: praticien_id is still missing after migration"
        )
    indexes = {index["name"] for index in inspector.get_indexes("appointments")}
    if "ix_appointments_praticien_id" not in indexes:
        raise RuntimeError(
            "Critical appointments schema mismatch: ix_appointments_praticien_id is missing"
        )


def migrate_payment_status_enum(bind=None):
    """Aligne l'enum PostgreSQL PaiementStatut sur le modèle, de façon additive.

    SQLAlchemy `create_all()` ne modifie pas un enum PostgreSQL déjà existant.
    Les cabinets historiques peuvent donc avoir EN_ATTENTE/PAYE/PARTIEL sans la
    valeur A_ENCAISSER désormais déclarée dans le modèle. On découvre le type
    réellement porté par `actes.statut_paiement`, puis on ajoute uniquement la
    valeur manquante. SQLite n'a pas besoin de cette étape.
    """
    from sqlalchemy import text

    db_engine = bind or engine
    if db_engine.dialect.name != "postgresql":
        return

    with db_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        enum_row = conn.execute(text("""
            SELECT n.nspname AS schema_name, t.typname AS type_name
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_type t ON t.oid = a.atttypid
            WHERE c.relname = 'actes'
              AND a.attname = 'statut_paiement'
              AND a.attnum > 0
              AND NOT a.attisdropped
              AND t.typtype = 'e'
              AND n.nspname = current_schema()
            LIMIT 1
        """)).mappings().first()
        if not enum_row:
            raise RuntimeError(
                "Critical payment schema mismatch: actes.statut_paiement PostgreSQL enum not found"
            )

        value_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_enum e ON e.enumtypid = t.oid
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE n.nspname = :schema_name
                  AND t.typname = :type_name
                  AND e.enumlabel = 'A_ENCAISSER'
            )
        """), {
            "schema_name": enum_row["schema_name"],
            "type_name": enum_row["type_name"],
        }).scalar()
        if value_exists:
            return

        preparer = db_engine.dialect.identifier_preparer
        qualified_type = (
            f"{preparer.quote(enum_row['schema_name'])}."
            f"{preparer.quote(enum_row['type_name'])}"
        )
        conn.execute(text(
            f"ALTER TYPE {qualified_type} ADD VALUE IF NOT EXISTS 'A_ENCAISSER'"
        ))
        logger.info("✅ Added A_ENCAISSER to PostgreSQL payment status enum")


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

    # Fail-closed sur PostgreSQL : la divergence d'enum provoque sinon un HTTP 500
    # dès la lecture Finances (`A_ENCAISSER`). Cette étape est additive uniquement.
    migrate_payment_status_enum()


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
                logger.info(f"✅ Added column snoozed_until to proactive_alerts table")
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
