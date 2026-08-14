import os
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_database_import(database_url: str, environment: str) -> subprocess.CompletedProcess[str]:
    code = r'''
import builtins

_real_import = builtins.__import__

def _blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "sqlcipher3" or name.startswith("sqlcipher3."):
        raise ImportError("forced missing sqlcipher3 for P0-3 test")
    return _real_import(name, globals, locals, fromlist, level)

builtins.__import__ = _blocked_import
import backend.database  # noqa: F401
print("DATABASE_IMPORT_OK")
'''
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": database_url,
            "ENVIRONMENT": environment,
            "SECRET_KEY": "p0-3-test-secret-key-that-is-long-enough",
            "CABINET_MASTER_KEY_HEX": "p0-3-test-cabinet-key",
        }
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cabinet_disk_sqlite_refuses_startup_without_sqlcipher(tmp_path):
    db_path = tmp_path / "cabinet.db"

    result = _run_database_import(f"sqlite:///{db_path}", "cabinet")
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "SQLCipher requis en mode cabinet" in output
    assert "Démarrage refusé" in output
    assert "DATABASE_IMPORT_OK" not in output


def test_cabinet_plaintext_migration_failure_restores_db_and_refuses_startup(tmp_path):
    db_path = tmp_path / "cabinet-existing.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE sentinel (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO sentinel(value) VALUES ('preserve-me')")
        conn.commit()

    result = _run_database_import(f"sqlite:///{db_path}", "cabinet")
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "migration de la base locale impossible" in output
    assert db_path.exists()
    assert not Path(str(db_path) + ".unencrypted.tmp").exists()
    with sqlite3.connect(db_path) as conn:
        value = conn.execute("SELECT value FROM sentinel").fetchone()[0]
    assert value == "preserve-me"


def test_development_disk_sqlite_can_fallback_without_sqlcipher(tmp_path):
    db_path = tmp_path / "development.db"

    result = _run_database_import(f"sqlite:///{db_path}", "development")
    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    assert "DATABASE_IMPORT_OK" in output
