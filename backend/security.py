from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from jose import jwt
from passlib.context import CryptContext
from .config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Hash statique (bcrypt) utilisé pour la mitigation des Timing Attacks
# Correspond au mot de passe "dummy_password"
DUMMY_PASSWORD_HASH = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"


def verify_dummy_password():
    """Simule le coût de vérification bcrypt pour éviter le User Enumeration."""
    return pwd_context.verify("dummy_password", DUMMY_PASSWORD_HASH)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    to_encode["jti"] = str(uuid.uuid4())
    to_encode["type"] = "access"
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["jti"] = str(uuid.uuid4())
    to_encode["type"] = "refresh"
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class TokenBlacklist:
    """SQLite-backed JTI blacklist with in-memory fallback for pure unit tests."""

    def __init__(self):
        self._store: dict[str, datetime] = {}

    def revoke(self, token: str, db=None) -> None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None)
                
                # Stocker dans le fallback en mémoire
                self._store[jti] = expires_at
                
                # Tenter d'écrire en DB (uniquement si db est fourni ou hors mode tests unitaires purs)
                import sys
                is_testing = "pytest" in sys.modules
                if db is not None or not is_testing:
                    try:
                        from backend.database import SessionLocal
                        from backend.models import RevokedToken
                        
                        db_session = db
                        own_session = False
                        if db_session is None:
                            db_session = SessionLocal()
                            own_session = True
                            
                        try:
                            revoked = RevokedToken(jti=jti, expires_at=expires_at)
                            db_session.merge(revoked)
                            db_session.commit()
                        except Exception:
                            if own_session:
                                db_session.rollback()
                        finally:
                            if own_session:
                                db_session.close()
                    except Exception:
                        pass
                
                self._purge(db)
        except Exception:
            pass

    def is_revoked(self, jti: str, db=None) -> bool:
        if not jti:
            return False
            
        # 1. Vérifier le fallback en mémoire (avec résilience timezone)
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        if jti in self._store:
            val = self._store[jti]
            val_naive = val.replace(tzinfo=None) if val.tzinfo is not None else val
            if val_naive > now_naive:
                return True
            else:
                del self._store[jti]
                
        # 2. Vérifier en base
        import sys
        is_testing = "pytest" in sys.modules
        if db is not None or not is_testing:
            try:
                from backend.database import SessionLocal
                from backend.models import RevokedToken
                
                db_session = db
                own_session = False
                if db_session is None:
                    db_session = SessionLocal()
                    own_session = True
                    
                try:
                    exists = db_session.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None
                    return exists
                finally:
                    if own_session:
                        db_session.close()
            except Exception:
                # P1-2: une panne du store de révocation ne doit jamais rendre
                # un bearer potentiellement révoqué acceptable.
                return True
        return False

    def _purge(self, db=None) -> None:
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Purger la mémoire de façon résiliente
        new_store = {}
        for k, v in self._store.items():
            v_naive = v.replace(tzinfo=None) if v.tzinfo is not None else v
            if v_naive > now_naive:
                new_store[k] = v
        self._store = new_store
        
        # Purger la base de données
        import sys
        is_testing = "pytest" in sys.modules
        if db is not None or not is_testing:
            try:
                from backend.database import SessionLocal
                from backend.models import RevokedToken
                
                db_session = db
                own_session = False
                if db_session is None:
                    db_session = SessionLocal()
                    own_session = True
                    
                try:
                    db_session.query(RevokedToken).filter(RevokedToken.expires_at <= now_naive).delete()
                    db_session.commit()
                except Exception:
                    db_session.rollback()
                finally:
                    if own_session:
                        db_session.close()
            except Exception:
                pass


token_blacklist = TokenBlacklist()
