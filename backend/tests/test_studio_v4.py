import pytest
pytestmark = pytest.mark.skip(reason="Legacy test — requires live PostgreSQL DB, not part of isolated test suite")

import os
import sys
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend import models
from backend.services.clinical_intelligence import clinical_intel
from backend.services.base_template import BaseTemplate
from unittest.mock import MagicMock

def test_branding_logic():
    """Test de la logique de persistance du branding."""
    print("Testing Branding Logic...")
    db = SessionLocal()
    try:
        config = db.query(models.CabinetConfig).first()
        if not config:
            print("Skipping Branding Test: No CabinetConfig found in DB.")
            return
            
        original_theme = config.selected_theme
        
        # Simulation d'un update
        config.selected_theme = "rose"
        db.commit()
        db.refresh(config)
        assert config.selected_theme == "rose"
        
        # Reset
        config.selected_theme = original_theme
        db.commit()
        print("[OK] Branding Logic : PASS")
    finally:
        db.close()

def test_iamina_logic():
    """Test de l'instanciation de IAmina."""
    print("Testing IAmina Intelligence...")
    assert clinical_intel is not None
    print("[OK] IAmina Logic : PASS")

def test_qr_path_resolution():
    """Test de la resolution du chemin du logo pour le QR Code."""
    print("Testing QR Code Path Resolution...")
    mock_config = MagicMock()
    mock_config.logo_path = "clinics/test/logo.png"
    
    # Simulation de la logique dans _draw_qr_code
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(models.__file__)))
    logo_filename = mock_config.logo_path
    actual_logo_path = os.path.join(base_path, "static", "uploads", logo_filename)
    
    print(f"Resolved Path: {actual_logo_path}")
    assert "static" in actual_logo_path
    assert "uploads" in actual_logo_path
    assert "clinics" in actual_logo_path
    print("[OK] QR Path Resolution : PASS")

if __name__ == "__main__":
    print("[START] Demarrage des Tests Unitaires (v4.7)...")
    try:
        test_branding_logic()
        test_iamina_logic()
        test_qr_path_resolution()
        print("\n[FIN] Bilan : Tous les tests ont reussi !")
    except Exception as e:
        print(f"\n[ERROR] ERREUR lors des tests : {e}")
        sys.exit(1)
