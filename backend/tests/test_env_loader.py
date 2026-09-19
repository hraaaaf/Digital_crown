"""Tests PREPROD-OPS-HARDENING-1 — load_backend_env(override=...) ne doit
jamais écraser silencieusement des variables d'environnement déjà injectées
par l'OS/l'orchestrateur en préprod/prod (risque documenté dans
docs/PREPROD_RUNBOOK.md et corrigé dans backend/main.py)."""
import os
from unittest.mock import patch
from backend.env_loader import load_backend_env


def test_override_false_does_not_overwrite_existing_env_var(tmp_path, monkeypatch):
    """override=False : une variable OS déjà présente doit rester intacte."""
    env_file = tmp_path / ".env.local"
    env_file.write_text("DATABASE_URL=postgresql://from-file/db\n")

    monkeypatch.setenv("DATABASE_URL", "postgresql://from-os-orchestrator/db")

    with patch("backend.env_loader.BASE_DIR", tmp_path):
        load_backend_env(override=False)

    assert os.environ["DATABASE_URL"] == "postgresql://from-os-orchestrator/db"


def test_override_true_overwrites_existing_env_var(tmp_path, monkeypatch):
    """override=True : le fichier .env.local fait foi même sur une variable déjà présente."""
    env_file = tmp_path / ".env.local"
    env_file.write_text("DATABASE_URL=postgresql://from-file/db\n")

    monkeypatch.setenv("DATABASE_URL", "postgresql://stale-shell-value/db")

    with patch("backend.env_loader.BASE_DIR", tmp_path):
        load_backend_env(override=True)

    assert os.environ["DATABASE_URL"] == "postgresql://from-file/db"


def test_environment_aware_override_pattern_dev_overrides(tmp_path, monkeypatch):
    """Reproduit la logique de main.py : ENVIRONMENT=development → override autorisé."""
    env_file = tmp_path / ".env.local"
    env_file.write_text("SECRET_KEY=from-file-secret\n")

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SECRET_KEY", "stale-value")

    with patch("backend.env_loader.BASE_DIR", tmp_path):
        load_backend_env(override=False)
        if os.environ.get("ENVIRONMENT", "development").lower() in ("development", "local", "test"):
            load_backend_env(override=True)

    assert os.environ["SECRET_KEY"] == "from-file-secret"


def test_environment_aware_override_pattern_prod_does_not_override(tmp_path, monkeypatch):
    """Reproduit la logique de main.py : ENVIRONMENT=production → l'OS reste prioritaire."""
    env_file = tmp_path / ".env.local"
    env_file.write_text("SECRET_KEY=from-file-secret\n")

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "orchestrator-injected-secret-value-1234567890")
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "11" * 32)

    with patch("backend.env_loader.BASE_DIR", tmp_path):
        load_backend_env(override=False)
        if os.environ.get("ENVIRONMENT", "development").lower() in ("development", "local", "test"):
            load_backend_env(override=True)

    assert os.environ["SECRET_KEY"] == "orchestrator-injected-secret"


def test_cabinet_rejects_weak_jwt_secret_even_with_strong_master_key(tmp_path, monkeypatch):
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "ENVIRONMENT=cabinet\n"
        "SECRET_KEY=SET_A_REAL_SECRET_KEY_IN_ENV\n"
        f"CABINET_MASTER_KEY_HEX={'22' * 32}\n"
    )
    monkeypatch.setenv("ENVIRONMENT", "cabinet")

    with patch("backend.env_loader.BASE_DIR", tmp_path):
        try:
            load_backend_env(override=True)
        except RuntimeError as exc:
            assert "SECRET_KEY" in str(exc)
        else:
            raise AssertionError("weak cabinet JWT secret was accepted")


def test_cabinet_rejects_missing_or_malformed_master_key(tmp_path, monkeypatch):
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "ENVIRONMENT=cabinet\n"
        "SECRET_KEY=strong-jwt-secret-0123456789-abcdef-XYZ\n"
        "CABINET_MASTER_KEY_HEX=not-hex\n"
    )
    monkeypatch.setenv("ENVIRONMENT", "cabinet")

    with patch("backend.env_loader.BASE_DIR", tmp_path):
        try:
            load_backend_env(override=True)
        except RuntimeError as exc:
            assert "CABINET_MASTER_KEY_HEX" in str(exc)
        else:
            raise AssertionError("malformed cabinet master key was accepted")


def test_production_enforces_both_security_keys(tmp_path, monkeypatch):
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "ENVIRONMENT=production\n"
        "SECRET_KEY=strong-production-jwt-secret-0123456789\n"
        f"CABINET_MASTER_KEY_HEX={'33' * 32}\n"
    )

    with patch("backend.env_loader.BASE_DIR", tmp_path):
        loaded = load_backend_env(override=True)

    assert loaded == env_file
    assert os.environ["ENVIRONMENT"] == "production"


def test_cabinet_rejects_missing_database_url(tmp_path, monkeypatch):
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "ENVIRONMENT=cabinet\n"
        "SECRET_KEY=strong-cabinet-jwt-secret-0123456789\n"
        f"CABINET_MASTER_KEY_HEX={'44' * 32}\n"
    )
    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with patch("backend.env_loader.BASE_DIR", tmp_path):
        try:
            load_backend_env(override=True)
        except RuntimeError as exc:
            assert "DATABASE_URL" in str(exc)
        else:
            raise AssertionError("cabinet startup accepted an implicit database fallback")


def test_superadmin_identity_has_no_hardcoded_default():
    from backend.config import Settings

    assert Settings.model_fields["SUPERADMIN_EMAIL"].default == ""
