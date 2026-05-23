import os
import sys

# Add ROOT to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        print("Migrating appointments table...")
        
        # 1. Create the enum type if it doesn't exist
        try:
            conn.execute(text("CREATE TYPE schedulingtype AS ENUM ('EXACT_TIME', 'MORNING', 'AFTERNOON', 'FULL_DAY');"))
            print("Created enum schedulingtype.")
        except Exception as e:
            print(f"Enum might already exist: {e}")
        
        # 2. Add the column
        try:
            conn.commit()
            conn.execute(text("ALTER TABLE appointments ADD COLUMN scheduling_type schedulingtype DEFAULT 'EXACT_TIME';"))
            print("Added scheduling_type column.")
        except Exception as e:
            print(f"Column might already exist: {e}")
            
        conn.commit()
        print("Migration done.")

if __name__ == "__main__":
    run_migration()
