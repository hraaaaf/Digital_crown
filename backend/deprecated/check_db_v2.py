
import sqlite3
import os

# Try to find the database URL from env or default
# The AGENTS.md says it's PostgreSQL: postgres:admin@localhost/digitalcrown_db
# But I can't run psql easily. I'll use sqlalchemy if I can find where it is.
# Actually, I'll just use a python script that imports correctly.

import sys
sys.path.append(os.getcwd())

from database import SessionLocal
from models import CabinetConfig

db = SessionLocal()
configs = db.query(CabinetConfig).all()
for c in configs:
    print(f"Owner: {c.owner_id}, Margin Top: {c.margin_top}")
db.close()
