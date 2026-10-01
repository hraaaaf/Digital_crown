"""Reset only the isolated T2 workstation identity fixture between legacy browser probes."""
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "t2-runtime-cert.db"

with sqlite3.connect(DB_PATH, timeout=10) as connection:
    connection.execute("DELETE FROM workstation_modes")
    connection.commit()

print("T2_WORKSTATION_FIXTURE_RESET")
