
from backend.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = [c['name'] for c in inspector.get_columns('document_archives')]
print(f"Columns in document_archives: {columns}")
