from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@localhost/digitalcrown_db?client_encoding=utf8"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, email, role, nom_complet FROM users"))
        users = result.fetchall()
        print(f"Users found: {len(users)}")
        for u in users:
            print(f"ID: {u[0]}, Email: {u[1]}, Role: {u[2]}, Name: {u[3]}")
            
        result = conn.execute(text("SELECT id, nom_cabinet, is_initialized, owner_id FROM cabinet_configs"))
        configs = result.fetchall()
        print(f"\nConfigs found: {len(configs)}")
        for c in configs:
            print(f"ID: {c[0]}, Name: {c[1]}, Init: {c[2]}, OwnerID: {c[3]}")
except Exception as e:
    print(f"Error: {e}")
