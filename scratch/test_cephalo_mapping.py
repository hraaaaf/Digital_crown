import sys
import os

# Add the backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".")))

from backend.services.cephalo_engine import cephalo_engine

def test_mapping():
    # Simulation de points venant du modèle 19 points (avec UL/LL)
    raw_points = {
        "S": (100, 100),
        "N": (200, 100),
        "UL": (250, 150),  # Synonyme de Ls
        "LL": (250, 200),  # Synonyme de Li
        "stPog": (230, 250), # Synonyme de Pog_soft
        "Po": (50, 120),
        "Or": (150, 120)
    }
    
    print("Testing Landmark Mapping with Synonyms...")
    
    # On force un ratio de 1.0 pour simplifier
    try:
        # On n'appelle pas calculate_metrics car il nécessite beaucoup de points
        # On teste directement _get_point qui est le coeur du fix
        ls = cephalo_engine._get_point(raw_points, "Ls")
        li = cephalo_engine._get_point(raw_points, "Li")
        pog = cephalo_engine._get_point(raw_points, "Pog_soft")
        
        print(f"Ls (from UL): {ls}")
        print(f"Li (from LL): {li}")
        print(f"Pog_soft (from stPog): {pog}")
        
        assert ls == (250, 150)
        assert li == (250, 200)
        assert pog == (230, 250)
        
        print("\n✅ MAPPING TEST PASSED!")
    except Exception as e:
        print(f"\n❌ MAPPING TEST FAILED: {e}")

if __name__ == "__main__":
    test_mapping()
