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
    """Persistent JTI blacklist plus tenant-scoped mobile revocation cutoffs."""

    MOBILE_JTI_PREFIX = "mobile:"
    MOBILE_EPOCH_PREFIX = "mobile-epoch:"
    MOBILE_TOKEN_TTL = timedelta(hours=24)
    MOBILE_EPOCH_RETENTION = timedelta(days=31)

    def __init__(self):
        self._store: dict[str, datetime] = {}
        self._mobile_cutoffs: dict[int, int] = {}

    def revoke(self, token: str, db=None) -> None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None)
                self._store[jti] = expires_at

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

    @staticmethod
    def _parse_mobile_jti(jti: str) -> tuple[int, int] | None:
        if not jti.startswith(TokenBlacklist.MOBILE_JTI_PREFIX):
            return None
        try:
            _, employer_id, issued_us, _nonce = jti.split(":", 3)
            return int(employer_id), int(issued_us)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_mobile_epoch_marker(marker: str, employer_id: int) -> int | None:
        prefix = f"{TokenBlacklist.MOBILE_EPOCH_PREFIX}{employer_id}:"
        if not marker.startswith(prefix):
            return None
        try:
            return int(marker[len(prefix):].split(":", 1)[0])
        except (TypeError, ValueError):
            return None

    def _mobile_cutoff(self, employer_id: int, db=None) -> int | None:
        cached = self._mobile_cutoffs.get(int(employer_id))
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        db_cutoff = None

        import sys
        is_testing = "pytest" in sys.modules
        if db is not None or not is_testing:
            from backend.database import SessionLocal
            from backend.models import RevokedToken

            db_session = db
            own_session = False
            if db_session is None:
                db_session = SessionLocal()
                own_session = True
            try:
                prefix = f"{self.MOBILE_EPOCH_PREFIX}{int(employer_id)}:"
                rows = db_session.query(RevokedToken.jti).filter(
                    RevokedToken.jti.like(f"{prefix}%"),
                    RevokedToken.expires_at > now_naive,
                ).all()
                for row in rows:
                    marker = row[0] if isinstance(row, tuple) else row.jti
                    parsed = self._parse_mobile_epoch_marker(marker, int(employer_id))
                    if parsed is not None and (db_cutoff is None or parsed > db_cutoff):
                        db_cutoff = parsed
            finally:
                if own_session:
                    db_session.close()

        cutoff = max(v for v in (cached, db_cutoff) if v is not None) if (cached is not None or db_cutoff is not None) else None
        if cutoff is not None:
            self._mobile_cutoffs[int(employer_id)] = cutoff
        return cutoff

    def revoke_mobile_access(self, employer_id: int, db=None) -> dict:
        """Persist a cabinet cutoff and invalidate its pending pairing codes.

        The marker is kept slightly longer than the maximum mobile JWT lifetime;
        once it expires, every token issued before it is already expired anyway.
        """
        from backend.database import SessionLocal
        from backend.models import MobilePairedDevice, RevokedToken, ZKAPairingToken

        employer_id = int(employer_id)
        now = datetime.now(timezone.utc)
        cutoff_us = int(now.timestamp() * 1_000_000)
        expires_at = (now + self.MOBILE_EPOCH_RETENTION).replace(tzinfo=None)
        marker = f"{self.MOBILE_EPOCH_PREFIX}{employer_id}:{cutoff_us}:{uuid.uuid4().hex[:12]}"

        db_session = db
        own_session = False
        if db_session is None:
            db_session = SessionLocal()
            own_session = True
        try:
            db_session.add(RevokedToken(jti=marker, expires_at=expires_at))
                    invalidated = db_session.query(ZKAPairingToken).filter(
                ZKAPairingToken.employer_id == employer_id,
                ZKAPairingToken.used_at.is_(None),
            ).delete(synchronize_session=False)
            revoked_devices = db_session.query(MobilePairedDevice).filter(
                MobilePairedDevice.employer_id == employer_id,
                MobilePairedDevice.revoked_at.is_(None),
            ).update({MobilePairedDevice.revoked_at: now.replace(tzinfo=None)}, synchronize_session=False)
            db_session.commit()
            self._mobile_cutoffs[employer_id] = cutoff_us
            return {
                "revoked_at": now.isoformat(),
                "pairing_tokens_invalidated": int(invalidated or 0),
                "devices_revoked": int(revoked_devices or 0),
            }
        except Exception:
            db_session.rollback()
            raise
        finally:
            if own_session:
                db_session.close()

    def is_revoked(self, jti: str, db=None) -> bool:
        if not jti:
            return False

        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        if jti in self._store:
            val = self._store[jti]
            val_naive = val.replace(tzinfo=None) if val.tzinfo is not None else val
            if val_naive > now_naive:
                return True
            del self._store[jti]

        mobile_identity = self._parse_mobile_jti(jti)
        if mobile_identity is not None:
            employer_id, issued_us = mobile_identity
            cutoff = self._mobile_cutoff(employer_id, db)
            if cutoff is not None and issued_us <= cutoff:
                return True

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
                return False
        return False

    def _purge(self, db=None) -> None:
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

        new_store = {}
        for k, v in self._store.items():
            v_naive = v.replace(tzinfo=None) if v.tzinfo is not None else v
            if v_naive > now_naive:
                new_store[k] = v
        self._store = new_store

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
