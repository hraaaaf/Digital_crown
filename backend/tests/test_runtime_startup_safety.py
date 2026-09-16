from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text

from backend.core import runtime_safety
from backend.core.schema_runtime import CURRENT_ALEMBIC_HEAD, assert_database_at_current_head


def _cfg(environment="development", database_url="sqlite:///:memory:"):
    return SimpleNamespace(ENVIRONMENT=environment, DATABASE_URL=database_url)


def test_in_memory_test_runtime_requires_and_accepts_explicit_isolation(monkeypatch):
    monkeypatch.delenv("DIGITALCROWN_ISOLATED_RUNTIME", raising=False)
    with pytest.raises(RuntimeError, match="attestation explicite"):
        runtime_safety.assert_runtime_startup_allowed(_cfg("test"))

    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    assert runtime_safety.assert_runtime_startup_allowed(_cfg("test")) == runtime_safety.DEV_BOOTSTRAP


def test_persistent_development_runtime_requires_exact_target_fingerprint(monkeypatch):
    url = "postgresql://operator:secret@127.0.0.1:55432/digitalcrown_rehearsal"
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.delenv("DIGITALCROWN_ISOLATION_DB_FINGERPRINT", raising=False)

    with pytest.raises(RuntimeError, match="attestation explicite"):
        runtime_safety.assert_runtime_startup_allowed(_cfg("development", url))

    monkeypatch.setenv("DIGITALCROWN_ISOLATION_DB_FINGERPRINT", runtime_safety.database_target_fingerprint(url))
    assert runtime_safety.assert_runtime_startup_allowed(_cfg("development", url)) == runtime_safety.DEV_BOOTSTRAP


def test_known_cabinet_target_is_rejected_even_with_matching_attestation(monkeypatch):
    cabinet_url = "postgresql://operator:secret@localhost:5432/digitalcrown_db"
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv(
        "DIGITALCROWN_ISOLATION_DB_FINGERPRINT",
        runtime_safety.database_target_fingerprint(cabinet_url),
    )
    monkeypatch.setattr(runtime_safety, "_known_cabinet_database_urls", lambda: [cabinet_url])

    with pytest.raises(RuntimeError, match="attestation explicite"):
        runtime_safety.assert_runtime_startup_allowed(_cfg("development", cabinet_url))


@pytest.mark.parametrize(
    "alias",
    [
        "postgresql+psycopg2://operator:secret@127.0.0.1/digitalcrown_db?sslmode=disable",
        "postgres://operator:secret@[::1]:5432/digitalcrown_db",
    ],
)
def test_equivalent_postgres_urls_are_same_known_cabinet_target(monkeypatch, alias):
    cabinet_url = "postgresql://operator:secret@localhost:5432/digitalcrown_db"
    monkeypatch.setattr(runtime_safety, "_known_cabinet_database_urls", lambda: [cabinet_url])

    assert runtime_safety.is_known_cabinet_database(alias)


def test_cabinet_runtime_rejects_reload_before_release_check(monkeypatch):
    monkeypatch.setattr(runtime_safety.sys, "argv", ["uvicorn", "--reload"])
    monkeypatch.setattr(runtime_safety, "is_certified_release", lambda: True)

    with pytest.raises(RuntimeError, match="--reload est interdit"):
        runtime_safety.assert_runtime_startup_allowed(_cfg("cabinet", "postgresql://u:p@host/cabinet"))


def test_cabinet_runtime_requires_certified_release(monkeypatch):
    monkeypatch.setattr(runtime_safety.sys, "argv", ["uvicorn"])
    monkeypatch.setattr(runtime_safety, "is_certified_release", lambda: False)

    with pytest.raises(RuntimeError, match="INSTALLABLE_CERTIFIED"):
        runtime_safety.assert_runtime_startup_allowed(_cfg("cabinet", "postgresql://u:p@host/cabinet"))


def test_rehearsal_returns_read_only_schema_policy(monkeypatch):
    url = "postgresql://operator:secret@127.0.0.1:55432/digitalcrown_rehearsal"
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DIGITALCROWN_ISOLATION_DB_FINGERPRINT", runtime_safety.database_target_fingerprint(url))

    assert runtime_safety.assert_runtime_startup_allowed(_cfg("e2e_install_rehearsal", url)) == runtime_safety.REHEARSAL_MIGRATION_ONLY


def test_schema_gate_supports_existing_sqlite_without_write_side_effect(tmp_path):
    database_path = tmp_path / "cabinet.db"
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(
            text("INSERT INTO alembic_version(version_num) VALUES (:revision)"),
            {"revision": CURRENT_ALEMBIC_HEAD},
        )

    assert_database_at_current_head(engine)
    assert database_path.is_file()


def test_schema_gate_does_not_create_missing_sqlite_file(tmp_path):
    database_path = tmp_path / "missing.db"
    engine = create_engine(f"sqlite:///{database_path}")

    with pytest.raises(RuntimeError, match="fichier SQLite absent"):
        assert_database_at_current_head(engine)
    assert not database_path.exists()
