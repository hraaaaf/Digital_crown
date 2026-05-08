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
    """In-memory JTI blacklist. Auto-purges expired entries to avoid unbounded growth."""

    def __init__(self):
        # jti → expiry timestamp (UTC)
        self._store: dict[str, datetime] = {}

    def revoke(self, token: str) -> None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                self._store[jti] = datetime.fromtimestamp(exp, tz=timezone.utc)
                self._purge()
        except Exception:
            pass

    def is_revoked(self, jti: str) -> bool:
        return jti in self._store

    def _purge(self) -> None:
        now = datetime.now(timezone.utc)
        self._store = {k: v for k, v in self._store.items() if v > now}


token_blacklist = TokenBlacklist()
