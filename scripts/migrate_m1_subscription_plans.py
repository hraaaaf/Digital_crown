#!/usr/bin/env python
"""
M1 — Migration abonnements & approbation équipe (idempotente, rejouable).

Ajoute les colonnes :
  - users.subscription_plan  VARCHAR(20) NULL  (propriétaires -> 'GOLD')
  - users.approval_status    VARCHAR(20) NOT NULL DEFAULT 'approved'
  - users.approval_note      TEXT NULL

Backfill :
  - Utilisateurs existants (employer_id IS NULL = propriétaire) -> GOLD + approved
  - Sous-comptes existants (employer_id IS NOT NULL) -> approved (plan hérité du propriétaire)

Garanties :
  - count_before == count_after (aucune ligne créée/supprimée)
  - Transaction unique — tout ou rien
  - Idempotente : re-jouer ne provoque aucune erreur
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from backend.database import SessionLocal

def run():
    db = SessionLocal()
    try:
        with db.begin():
            # 1. Compter avant
            count_before = db.execute(text("SELECT COUNT(*) FROM users")).scalar()

            # 2. Ajouter les colonnes si elles n'existent pas (idempotent)
            existing_cols = {
                row[0] for row in db.execute(
                    text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
                )
            }

            if "subscription_plan" not in existing_cols:
                db.execute(text("ALTER TABLE users ADD COLUMN subscription_plan VARCHAR(20) NULL"))
                print("  + Colonne subscription_plan ajoutée")
            else:
                print("  ~ subscription_plan déjà présente")

            if "approval_status" not in existing_cols:
                db.execute(text(
                    "ALTER TABLE users ADD COLUMN approval_status VARCHAR(20) NOT NULL DEFAULT 'approved'"
                ))
                print("  + Colonne approval_status ajoutée")
            else:
                print("  ~ approval_status déjà présente")

            if "approval_note" not in existing_cols:
                db.execute(text("ALTER TABLE users ADD COLUMN approval_note TEXT NULL"))
                print("  + Colonne approval_note ajoutée")
            else:
                print("  ~ approval_note déjà présente")

            # 3. Backfill subscription_plan -> propriétaires uniquement
            updated_plan = db.execute(text(
                """
                UPDATE users
                SET subscription_plan = 'GOLD'
                WHERE employer_id IS NULL AND subscription_plan IS NULL
                """
            )).rowcount
            print(f"  -> {updated_plan} propriétaire(s) mis à GOLD")

            # 4. Backfill approval_status -> tous les utilisateurs existants non encore renseignés
            updated_status = db.execute(text(
                "UPDATE users SET approval_status = 'approved' WHERE approval_status IS NULL OR approval_status = ''"
            )).rowcount
            print(f"  -> {updated_status} utilisateur(s) mis à approved")

            # 5. Vérifier count_after
            count_after = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            assert count_before == count_after, (
                f"ABORT : count_before={count_before} ≠ count_after={count_after}"
            )

        print("=" * 60)
        print(f"M1 — Migration OK. {count_before} utilisateur(s) — counts intacts.")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"ERREUR — rollback automatique : {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run())
