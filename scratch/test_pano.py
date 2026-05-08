import os
import sys
import json

# Ajout du chemin racine pour les imports
sys.path.append(os.getcwd())

from backend.services.sota_panoramic_service import SOTAPanoramicEngine

def test():
    engine = SOTAPanoramicEngine()
    image_path = r"c:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\static\uploads\panoramic\e84d47af-9837-44f4-835d-cdf1bd5741de.jpg"
    
    print(f"--- Analyse exhaustive de l'image : {image_path} ---")
    
    # On force temporairement les seuils à 0 dans l'instance
    # (Ou on regarde comment accéder aux données brutes si possible)
    # Pour ce test, on va juste modifier l'instance pour voir TOUT
    result = engine.analyze(image_path)
    
    # On affiche aussi les coordonnées relatives pour débugger le mapping FDI
    print("Détails des détections :")
    for det in result.get("detections", []):
        print(f"- {det['pathology']} | Tooth: {det['tooth']} | Conf: {det['confidence']:.4f}")

if __name__ == "__main__":
    test()
