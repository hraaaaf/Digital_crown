import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine
from backend import models

print("Creating new tables...")
models.Base.metadata.create_all(bind=engine)

print("Adding ticket_number to appointments...")
try:
    with engine.connect() as conn:
        conn.execute("ALTER TABLE appointments ADD COLUMN ticket_number INTEGER;")
except Exception as e:
    print(f"Error (maybe already exists): {e}")

print("Done.")
