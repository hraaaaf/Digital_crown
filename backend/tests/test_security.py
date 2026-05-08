"""Tests unitaires purs — security.py (aucune DB, aucun réseau)."""
import time
import pytest
from datetime import timedelta
from jose import jwt

from backend.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    TokenBlacklist,
    SECRET_KEY,
    ALGORITHM,
)


# ---- password hashing -------------------------------------------------------

class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "MonMotDePasse!123"
        h = get_password_hash(pw)
        assert h != pw
        assert verify_password(pw, h)

    def test_wrong_password_fails(self):
        h = get_password_hash("correct")
        assert not verify_password("wrong", h)

    def test_hash_is_bcrypt(self):
        h = get_password_hash("x")
        assert h.startswith("$2b$")

    def test_two_hashes_differ(self):
        """bcrypt doit saler différemment chaque fois."""
        h1 = get_password_hash("same")
        h2 = get_password_hash("same")
        assert h1 != h2


# ---- access token -----------------------------------------------------------

class TestAccessToken:
    def test_creates_valid_jwt(self):
        token = create_access_token({"sub": "user@test.ma"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user@test.ma"
        assert payload["type"] == "access"

    def test_contains_jti(self):
        token = create_access_token({"sub": "a@b.com"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "jti" in payload
        assert len(payload["jti"]) == 36  # uuid4

    def test_two_tokens_have_different_jti(self):
        t1 = create_access_token({"sub": "a@b.com"})
        t2 = create_access_token({"sub": "a@b.com"})
        p1 = jwt.decode(t1, SECRET_KEY, algorithms=[ALGORITHM])
        p2 = jwt.decode(t2, SECRET_KEY, algorithms=[ALGORITHM])
        assert p1["jti"] != p2["jti"]

    def test_custom_expiry(self):
        token = create_access_token({"sub": "a@b.com"}, expires_delta=timedelta(hours=1))
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["exp"] > 0

    def test_expired_token_raises(self):
        from jose import ExpiredSignatureError
        token = create_access_token({"sub": "a@b.com"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(ExpiredSignatureError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    def test_wrong_secret_raises(self):
        from jose import JWTError
        token = create_access_token({"sub": "a@b.com"})
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret", algorithms=[ALGORITHM])


# ---- refresh token ----------------------------------------------------------

class TestRefreshToken:
    def test_type_is_refresh(self):
        token = create_refresh_token({"sub": "a@b.com"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "refresh"

    def test_longer_lived_than_access(self):
        access = create_access_token({"sub": "a@b.com"})
        refresh = create_refresh_token({"sub": "a@b.com"})
        pa = jwt.decode(access, SECRET_KEY, algorithms=[ALGORITHM])
        pr = jwt.decode(refresh, SECRET_KEY, algorithms=[ALGORITHM])
        assert pr["exp"] > pa["exp"]


# ---- blacklist --------------------------------------------------------------

class TestTokenBlacklist:
    def test_fresh_token_not_revoked(self):
        bl = TokenBlacklist()
        token = create_access_token({"sub": "a@b.com"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert not bl.is_revoked(payload["jti"])

    def test_revoked_token_is_revoked(self):
        bl = TokenBlacklist()
        token = create_access_token({"sub": "a@b.com"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        bl.revoke(token)
        assert bl.is_revoked(payload["jti"])

    def test_revoke_invalid_token_does_not_raise(self):
        bl = TokenBlacklist()
        bl.revoke("not.a.valid.token")  # doit être silencieux

    def test_purge_removes_expired_entries(self):
        bl = TokenBlacklist()
        # Token qui expire dans -1s (déjà expiré)
        token = create_access_token({"sub": "a@b.com"}, expires_delta=timedelta(seconds=-1))
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception:
            # Le token est expiré, on décode sans vérifier l'expiry
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        jti = payload["jti"]
        # Insérer manuellement
        from datetime import datetime, timezone
        bl._store[jti] = datetime.now(timezone.utc)  # déjà passé
        bl._purge()
        assert jti not in bl._store

    def test_independent_blacklists_dont_share_state(self):
        bl1 = TokenBlacklist()
        bl2 = TokenBlacklist()
        token = create_access_token({"sub": "a@b.com"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        bl1.revoke(token)
        assert not bl2.is_revoked(payload["jti"])
