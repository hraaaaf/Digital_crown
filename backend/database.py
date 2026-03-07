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