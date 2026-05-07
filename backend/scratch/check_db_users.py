from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@localhost/digitalcrown_db?client_encoding=utf8"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT email FROM users"))
        users = result.fetchall()
        print(f"Users found: {len(users)}")
        for u in users:
            print(f"- {u[0]}")
except Exception as e:
    print(f"Error: {e}")
