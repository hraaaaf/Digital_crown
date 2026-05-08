import os
import shutil
from backend.database import SessionLocal
from backend.models import CabinetConfig

def fix():
    db = SessionLocal()
    config = db.query(CabinetConfig).first()
    if not config:
        print("No config found")
        return
    
    source = "backend/static/uploads/clinics/9e4dcf4de20d4d42/letterhead_198822fd.jpg"
    dest_dir = f"backend/static/uploads/clinics/{config.public_id}"
    dest_file = f"{dest_dir}/letterhead_fixed.jpg"
    
    os.makedirs(dest_dir, exist_ok=True)
    if os.path.exists(source):
        shutil.copy(source, dest_file)
        config.letterhead_path = f"clinics/{config.public_id}/letterhead_fixed.jpg"
        config.watermark_enabled = False # Désactiver Wizard pour forcer Letterhead
        db.commit()
        print(f"Fixed! Path set to: {config.letterhead_path}")
    else:
        print(f"Source file not found at {source}")
    db.close()

if __name__ == "__main__":
    fix()
