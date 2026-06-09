from sqlalchemy import text
from backend.database import SessionLocal

def run_migration():
    db = SessionLocal()
    try:
        db.execute(text("ALTER TABLE patients ADD COLUMN telephone_2 VARCHAR(20);"))
        db.execute(text("ALTER TABLE patients ADD COLUMN telephone_3 VARCHAR(20);"))
        db.execute(text("ALTER TABLE patients ADD COLUMN assurance_complementaire BOOLEAN DEFAULT FALSE;"))
        db.execute(text("ALTER TABLE patients ADD COLUMN assurance_complementaire_nom VARCHAR(100);"))
        db.execute(text("ALTER TABLE patients ADD COLUMN assurance_privee_nom VARCHAR(100);"))
        db.execute(text("ALTER TABLE patients ADD COLUMN motif_consultation TEXT;"))
        db.commit()
        print("Migration successful")
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
