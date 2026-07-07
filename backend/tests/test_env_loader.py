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
    monkeypatch.setenv("SECRET_KEY", "orchestrator-injected-secret")

    with patch("backend.env_loader.BASE_DIR", tmp_path):
        load_backend_env(override=False)
        if os.environ.get("ENVIRONMENT", "development").lower() in ("development", "local", "test"):
            load_backend_env(override=True)

    assert os.environ["SECRET_KEY"] == "orchestrator-injected-secret"
