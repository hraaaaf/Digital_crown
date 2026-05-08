import asyncio
import json
import sys
import os

# Ajout du chemin racine au PYTHONPATH pour importer les services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.panoramic_ai_advisor import PanoramicAIAdvisor

async def test_antigravity_pipeline():
    print("START: Test d'integration ANTIGRAVITY...")
    
    # 1. Simulation des détections brutes de Loki-Silvres (Format PanoramicEngine)
    mock_detections = [
        {
            "tooth": 46,
            "pathology": "Caries",
            "confidence": 0.94,
            "bbox": [100.0, 200.0, 150.0, 250.0]
        },
        {
            "tooth": 46,
            "pathology": "Periapical Lesion",
            "confidence": 0.88,
            "bbox": [100.0, 200.0, 150.0, 250.0]
        },
        {
            "tooth": 27,
            "pathology": "Implant",
            "confidence": 0.99,
            "bbox": [400.0, 180.0, 440.0, 220.0]
        }
    ]

    advisor = PanoramicAIAdvisor()

    # 2. Test du Grounding (Traduction et Formatage du Prompt)
    print("\nCHECK: Verification du Grounding...")
    grounded_text = advisor._ground_detections(mock_detections)
    print(f"Facteurs cliniques injectés : \n{grounded_text}")
    
    # Validation manuelle : Vérifier que 'caries' est devenu 'carie' 
    # et 'periapical_lesion' est devenu 'lésion périapicale'.
    assert "carie" in grounded_text.lower()
    assert "lésion périapicale" in grounded_text.lower()
    print("OK: Grounding valide (Traduction OK)")

    # 3. Simulation de l'appel OralGPT (Ollama)
    print("\nAI: Appel OralGPT (Timeout 8s)...")
    try:
        # Note: generate_report est asynchrone
        result = await advisor.generate_report(detections=mock_detections)
        
        # Le service renvoie un dictionnaire avec narrative_report et engine
        report = result.get("narrative_report", "")
        engine = result.get("engine", "Inconnu")
        
        print(f"\nREPORT: Rapport genere par {engine} :")
        print("-" * 30)
        print(report)
        print("-" * 30)
        
        # Validation du Disclaimer
        assert "expertise clinique finale" in report.lower()
        print("\nOK: Test reussi : Le pipeline est integre et conforme.")
        
    except Exception as e:
        print(f"\nERROR: Echec du test : {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Correction pour l'encodage console Windows
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
    async def run_main():
        await test_antigravity_pipeline()
        
    asyncio.run(run_main())
