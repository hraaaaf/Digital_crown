import sys
import os
import secrets
import logging

# Rigueur CTO : On force Python à trouver le dossier racine du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
from backend import models
from backend.config import settings
from backend.security import get_password_hash

logger = logging.getLogger(__name__)


def automatic_admin_seed_allowed(environment: str) -> bool:
    """Autorise le seed admin uniquement hors runtime cabinet/production.

    Un cabinet réel doit être initialisé explicitement via son workflow d'installation,
    jamais par un seed automatique au démarrage. Cela empêche aussi la génération ou
    l'impression accidentelle d'un mot de passe superadmin dans les logs cabinet.
    """
    return (environment or "").strip().lower() not in {"cabinet", "production"}


def seed_admin_user():
    environment = os.getenv(
        "ENVIRONMENT",
        str(getattr(settings, "ENVIRONMENT", "development")),
    ).strip().lower()
    if not automatic_admin_seed_allowed(environment):
        logger.info(
            "Automatic superadmin seed disabled in %s environment; explicit setup is required.",
            environment,
        )
        return

    db = SessionLocal()
    try:
        admin_email = settings.SUPERADMIN_EMAIL.strip().lower()
        admin_password = os.getenv("SUPERADMIN_INITIAL_PASSWORD", "")

        if not admin_email:
            logger.error("SUPERADMIN_EMAIL env var non défini. Seed annulé.")
            return

        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            logger.warning(
                "Mot de passe admin de développement généré automatiquement. "
                "Définissez SUPERADMIN_INITIAL_PASSWORD pour éviter cette génération."
            )

        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(models.User).filter(models.User.email == admin_email).first()
        if existing_user:
            logger.info("L'utilisateur admin existe déjà.")
            return

        # Création de l'admin
        new_admin = models.User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            role=models.UserRole.ADMIN,
            nom_complet="Administrateur Digital Crown"
        )

        db.add(new_admin)
        db.commit()
        logger.info("Utilisateur admin de développement créé.")

    except Exception as e:
        logger.error("Erreur lors du seeding de l'utilisateur : %s", e)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin_user()
