from backend.database import SessionLocal
from backend.models import User

db = SessionLocal()
try:
    users = db.query(User).all()
    for u in users:
        print(f"User: {u.email} | Role: {u.role}")
finally:
    db.close()
