from backend import database
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    engine = database.engine
    with engine.connect() as conn:
        # Check if column exists
        try:
            # SQLite specific check
            res = conn.execute(text("PRAGMA table_info(patients)"))
            columns = [row[1] for row in res.fetchall()]
            if "adresse" not in columns:
                logger.info("Adding column 'adresse' to 'patients' table...")
                conn.execute(text("ALTER TABLE patients ADD COLUMN adresse VARCHAR(255)"))
                conn.commit()
                logger.info("Success.")
            else:
                logger.info("Column 'adresse' already exists.")
        except Exception as e:
            logger.error(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
