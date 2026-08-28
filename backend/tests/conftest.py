"""
Test fixtures — SQLite in-memory partagé (StaticPool), isolé de la DB production.
L'env var DATABASE_URL est forcée AVANT tout import backend.
"""
import os
import uuid

# Doit être fait avant tout import backend (database.py lit l'env au chargement)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-minimum-32chars-x")

from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# StaticPool : toutes les connexions partagent la même DB in-memory
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Crée toutes les tables SQLAlchemy une seule fois pour la session de tests."""
    from backend import models, database
    # Les modèles modulaires partagent models.Base mais ne sont pas tous importés
    # par backend.models. Ils doivent être enregistrés avant create_all(), sinon un
    # import ultérieur de backend.main ajoute de la metadata sans créer les tables.
    from backend import (  # noqa: F401
        models_catalog_plan,
        models_clinical_p3,
        models_identity_p4,
        models_imaging_p4,
        models_mobile_passkey,
        models_mobile_push,
        models_platform,
    )
    database.engine = _engine
    database.SessionLocal = _SessionLocal
    models.Base.metadata.create_all(bind=_engine)
    yield
    models.Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db():
    """Session SQLite — les données sont supprimées entre tests via delete."""
    from backend import models
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        # Purge toutes les tables en ordre inverse des FK pour isoler les tests
        for table in reversed(models.Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture()
def client(db):
    """
    TestClient FastAPI :
      - get_db overridé sur la session SQLite de test
      - lifespan patché (pas de chargement ML, pas de seed prod)
      - le garde licence runtime central est mocké explicitement ; ses tests SEC-1
        dédiés couvrent séparément les chemins signed/fail-closed
      - les routes métier historiques ne dépendent pas d'une vraie licence signée
        dans ce fixture générique ; les tests SEC-1 testent require_elite_license
        directement et les scénarios API de plateforme séparément
      - rate limiter désactivé
    """
    from backend import models
    from backend.main import app
    from backend.routers import (
        auth, patients, clinics, documents,
        appointments, prescriptions, accounting, team,
    )

    # backend.main charge tous les routers, y compris ceux qui déclarent directement
    # des tables SQLAlchemy (ex. mobile_resource_bridge). Resynchroniser ici rend le
    # schéma de test fidèle à la metadata réellement chargée au lieu de maintenir une
    # liste manuelle fragile de tables tardives.
    models.Base.metadata.create_all(bind=_engine)

    def _override_get_db():
        yield db

    async def _override_elite_license():
        return True

    for module in (auth, patients, clinics, documents, appointments, prescriptions, accounting, team):
        if hasattr(module, "get_db"):
            app.dependency_overrides[module.get_db] = _override_get_db

    # Existing business/router tests are intentionally license-agnostic. The signed
    # entitlement contract has its own SEC-1 tests, so this override prevents the
    # generic suite from depending on a real control-plane key/trust anchor.
    app.dependency_overrides[auth.require_elite_license] = _override_elite_license

    with patch("backend.main.panoramic_engine.initialize", new_callable=AsyncMock), \
         patch("backend.main.run_full_seed", return_value=None), \
         patch("backend.main.seed_admin_user", return_value=None), \
         patch("backend.main.sync_manager.start_listening", return_value=None), \
         patch("backend.main._sync_all_licenses_from_firebase", new_callable=AsyncMock), \
         patch("backend.main.get_user_license_status", new_callable=AsyncMock, return_value=(True, "OK")), \
         patch("backend.main.get_mobile_user_license_status", new_callable=AsyncMock, return_value=(True, "OK")), \
         patch("backend.services.daily_scheduler.start_daily_scheduler", return_value=None), \
         patch("backend.routers.auth.check_rate_limit", return_value=None):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

    app.dependency_overrides.clear()


# ---- helpers ----------------------------------------------------------------

def make_user(db, email=None, password="TestPass123!", role="DENTISTE", active=True):
    """Crée un utilisateur en DB. Email unique par défaut (évite les contraintes UNIQUE)."""
    from backend import models
    from backend.security import get_password_hash
    if email is None:
        email = f"test-{uuid.uuid4().hex[:8]}@cabinet.ma"
    user = models.User(
        email=email,
        hashed_password=get_password_hash(password),
        role=role,
        nom_complet="Dr. Test",
        is_active=active,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def dentiste(db):
    return make_user(db)


@pytest.fixture()
def auth_headers(client, dentiste):
    resp = client.post(
        "/api/auth/login",
        data={"username": dentiste.email, "password": "TestPass123!"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def refresh_token(client, dentiste):
    resp = client.post(
        "/api/auth/login",
        data={"username": dentiste.email, "password": "TestPass123!"},
    )
    return resp.json()["refresh_token"]
