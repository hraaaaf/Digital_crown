from backend.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text('SELECT DISTINCT doc_type FROM document_archives')).fetchall()
    print("Distinct doc_type:")
    for r in res:
        print(f"  - {r[0]}")
