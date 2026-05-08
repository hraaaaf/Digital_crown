
from backend.database import SessionLocal
from backend.models import CabinetConfig

db = SessionLocal()
configs = db.query(CabinetConfig).all()
for c in configs:
    print(f"Owner: {c.owner_id}, Primary Color: {c.primary_color}, Margin Top: {c.margin_top}, Margin Bottom: {c.margin_bottom}")
db.close()
