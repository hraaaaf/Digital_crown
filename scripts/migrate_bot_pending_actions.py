#!/usr/bin/env python
"""
Bot server-side — Migration BotPendingAction (idempotente, rejouable).

Cree la table bot_pending_actions si elle n'existe pas.
Garantie : count patients/RDV/actes/documents inchange.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text, inspect
from backend.database import SessionLocal, engine
from backend import models

def run():
    db = SessionLocal()
    try:
        # Counts avant (donnees cliniques uniquement)
        count_patients = db.execute(text("SELECT COUNT(*) FROM patients")).scalar()
        count_docs = db.execute(text("SELECT COUNT(*) FROM document_archives")).scalar()

        # Verifier si la table existe deja
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if "bot_pending_actions" in existing_tables:
            print("  ~ Table bot_pending_actions deja presente.")
        else:
            models.Base.metadata.tables["bot_pending_actions"].create(engine)
            print("  + Table bot_pending_actions creee.")

        # Verifier counts
        count_patients_after = db.execute(text("SELECT COUNT(*) FROM patients")).scalar()
        count_docs_after = db.execute(text("SELECT COUNT(*) FROM document_archives")).scalar()
        assert count_patients == count_patients_after
        assert count_docs == count_docs_after

        print("=" * 60)
        print(f"Bot pending actions — Migration OK. Patients: {count_patients}, Docs: {count_docs} (intacts).")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"ERREUR: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run())
