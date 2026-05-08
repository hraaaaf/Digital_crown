import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal
from backend import models

db = SessionLocal()
config = db.query(models.CabinetConfig).first()
if config:
    print(f"Cabinet: {config.owner_id}")
    print(f"Is Initialized: {config.is_initialized}")
    print(f"Watermark Enabled: {config.watermark_enabled}")
    print(f"Logo Path: {config.logo_path}")
    print(f"Letterhead Path: {config.letterhead_path}")
    
    # Vérifier l'existence physique
    base_path = os.path.dirname(os.path.abspath(__file__))
    if config.letterhead_path:
        full_path = os.path.join(base_path, "static", "uploads", config.letterhead_path)
        print(f"Full Path computed: {full_path}")
        print(f"Physical Exists: {os.path.exists(full_path)}")
else:
    print("No CabinetConfig found.")
db.close()
