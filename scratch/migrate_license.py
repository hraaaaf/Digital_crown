
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:admin@localhost/digitalcrown_db"

def run_migration():
    print(f"Connexion database: {DATABASE_URL}")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("Verification is_licensed...")
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_licensed BOOLEAN DEFAULT FALSE NOT NULL"))
            
            print("Verification license_expires_at...")
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS license_expires_at TIMESTAMP WITHOUT TIME ZONE"))
            
            conn.commit()
            print("Migration SUCCESS.")
            
    except Exception as e:
        print(f"Migration ERROR: {e}")

if __name__ == "__main__":
    run_migration()
