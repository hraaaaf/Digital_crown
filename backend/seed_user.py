import os
import sys

# Rigueur CTO : On force Python à trouver le dossier racine du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
from backend import models
from backend.config import settings
from backend.security import get_password_hash


def seed_admin_user():
    """Bootstrap the platform owner only on the dedicated control plane.

    SEC-1 rules:
    - cabinet installs never create/provision the platform owner;
    - SUPERADMIN_DISPLAY_EMAIL is only a bootstrap locator/display value;
    - SUPERADMIN_USER_ID is the sole platform authority root;
    - no password is generated or printed;
    - a configured immutable id mismatch fails closed.
    """
    if not bool(getattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", False)):
        return None

    db = SessionLocal()
    try:
        bootstrap_email = settings.SUPERADMIN_DISPLAY_EMAIL.strip().lower()
        configured_owner_id = int(getattr(settings, "SUPERADMIN_USER_ID", 0) or 0)
        admin_password = os.getenv("SUPERADMIN_INITIAL_PASSWORD", "")

        if not bootstrap_email:
            print("ERROR: SUPERADMIN_DISPLAY_EMAIL non défini. Seed annulé.")
            return None

        existing_user = db.query(models.User).filter(models.User.email == bootstrap_email).first()
        if existing_user:
            if configured_owner_id > 0 and existing_user.id != configured_owner_id:
                raise RuntimeError(
                    "SECURITY: SUPERADMIN_USER_ID ne correspond pas au compte bootstrap existant."
                )
            print(
                f"Bootstrap owner existant: user_id={existing_user.id}. "
                "Autorité SuperAdmin active uniquement si SUPERADMIN_USER_ID correspond."
            )
            return existing_user

        if not admin_password:
            print(
                "ERROR: SUPERADMIN_INITIAL_PASSWORD requis pour créer le compte bootstrap. "
                "Aucun mot de passe n'a été généré ni journalisé."
            )
            return None

        new_admin = models.User(
            email=bootstrap_email,
            hashed_password=get_password_hash(admin_password),
            role=models.UserRole.ADMIN,
            nom_complet="Administrateur Digital Crown",
            is_active=True,
        )

        db.add(new_admin)
        db.flush()

        if configured_owner_id > 0 and new_admin.id != configured_owner_id:
            db.rollback()
            raise RuntimeError(
                "SECURITY: le user_id attribué au compte bootstrap ne correspond pas à "
                "SUPERADMIN_USER_ID. Aucun compte propriétaire n'a été validé."
            )

        db.commit()
        db.refresh(new_admin)
        print(
            f"SUCCESS: compte bootstrap créé user_id={new_admin.id}. "
            "Provisionnez SUPERADMIN_USER_ID avec cet ID pour activer l'autorité plateforme."
        )
        return new_admin

    except Exception as e:
        print(f"ERROR: Erreur lors du seeding de l'utilisateur : {e}")
        db.rollback()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin_user()
