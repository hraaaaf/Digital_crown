"""Isolated CI-only SQLCipher fixture override for the *real* G2 FastAPI tests.

This is an API/database E2E gate, not the MainLayout/browser gate.
Never import in ordinary tests or connect to a cabinet database.
"""
import os
import secrets
import sqlite3
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

_tmp = None
_dbfile = None
_engine = None


def pytest_configure(config):
    global _tmp, _dbfile, _engine
    if os.getenv("GITHUB_ACTIONS") != "true" or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") not in {"1", "true"}:
        raise RuntimeError("G7_REFUSED_NOT_DISPOSABLE_CI")
    expected = os.getenv("CB03_G7_SOURCE_HEAD", "")
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if len(expected) != 40 or expected != actual:
        raise RuntimeError("G7_REFUSED_SHA_MISMATCH")
    from sqlcipher3 import dbapi2 as cipher
    import backend.tests.conftest as fixtures

    _tmp = tempfile.TemporaryDirectory(prefix="cb03-g7-cipher-")
    _dbfile = Path(_tmp.name) / "synthetic-only.db"
    key = secrets.token_hex(32)

    def connect():
        db = cipher.connect(str(_dbfile), timeout=15, check_same_thread=False)
        db.execute("PRAGMA key = \"x'%s'\"" % key)
        assert db.execute("PRAGMA cipher_version").fetchone(), "SQLCipher driver unavailable"
        db.execute("PRAGMA busy_timeout=15000")
        return db

    _engine = create_engine("sqlite://", creator=connect, poolclass=NullPool)
    fixtures._engine = _engine
    fixtures._SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    config._cb03_g7_key = key


def pytest_sessionfinish(session, exitstatus):
    try:
        if _engine is None:
            return
        _engine.dispose()
        if exitstatus != 0:
            return
        raw = _dbfile.read_bytes()
        assert raw[:16] != b"SQLite format 3\\x00", "G7_PLAINTEXT_HEADER"
        try:
            with sqlite3.connect(_dbfile) as db:
                db.execute("SELECT name FROM sqlite_master").fetchall()
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("G7_PLAINTEXT_DRIVER_READABLE")
        from sqlcipher3 import dbapi2 as cipher
        wrong = cipher.connect(str(_dbfile))
        try:
            wrong.execute("PRAGMA key = \"x'%s'\"" % secrets.token_hex(32))
            try:
                wrong.execute("SELECT count(*) FROM appointments").fetchone()
            except cipher.DatabaseError:
                pass
            else:
                raise AssertionError("G7_WRONG_KEY_READABLE")
        finally:
            wrong.close()
        print("CB03_G7_REAL_FASTAPI_SQLCIPHER_API_E2E_PASS")
    finally:
        if _tmp is not None:
            _tmp.cleanup()
