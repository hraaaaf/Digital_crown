#!/usr/bin/env python3
"""
Test du SLM (Ollama/Llama3.2) pour génération de diagnostic orthodontique.
"""
import json
import requests
import sys

# Données cliniques réalistes d'un patient
clinical_data = {
    "Contexte": "Patient: Adulte 25 ans. Stade CVM: CS6 (croissance terminée).",
    "Deviations_Severes_Ou_Compensees": {
        "Decalage_A_B": {
            "Valeur": 6.5,
            "Norme": "[2.3 - 5.4]",
            "Statut": "High",
            "Interprétation_Moteur": "Décalage Classe II"
        },
        "Situation_A": {
            "Valeur": 5.5,
            "Norme": "[2.3 - 5.3]",
            "Statut": "High",
            "Interprétation_Moteur": "Maxillaire en avant"
        },
        "Situation_B": {
            "Valeur": -1.0,
            "Norme": "[-4.9 - 4.9]",
            "Statut": "Normal",
            "Interprétation_Moteur": "Position mandibulaire normale"
        },
        "Angle_de_Tweed": {
            "Valeur": 28,
            "Norme": "[22 - 30]",
            "Statut": "Normal",
            "Interprétation_Moteur": "Normodivergent"
        },
        "IMPA": {
            "Valeur": 97,
            "Norme": "[85 - 95]",
            "Statut": "Compensated",
            "Interprétation_Moteur": "Proalvéolie mandibulaire (Compensé)"
        },
        "I_Francfort": {
            "Valeur": 112,
            "Norme": "[102 - 112]",
            "Statut": "Compensated",
            "Interprétation_Moteur": "Proalvéolie maxillaire (Compensé)"
        }
    }
}

SYSTEM_PROMPT = """Tu es un Expert Orthodontiste Senior au sein du Centre d'Orthodontie Moderne (COM).
Ta mission est de rédiger une synthèse diagnostique basée sur les métriques céphalométriques fournies.

RÈGLES CLINIQUES :
1. Ton ton doit être purement médical, factuel, et synthétique (style compte-rendu radiologique).
2. Analyse en priorité les valeurs ayant un Z-score > 1.5 (déviations sévères).
3. Identifie et nomme explicitement les phénomènes marqués comme "Compensated" (Compensations dento-alvéolaires).
4. Utilise un vocabulaire strict : prognathie, rétrognathie, biproalvéolie, hyperdivergent, hypodivergent, etc.

CONTRAINTE DE SORTIE ABSOLUE :
Tu ne dois produire AUCUN texte libre, AUCUN commentaire d'introduction ou de conclusion.
Ta réponse doit être EXCLUSIVEMENT un objet JSON valide, strictement structuré selon ce schéma exact :
{
    "diagnostic_squelettique": "Analyse de la position des bases osseuses (A/B) et du type de croissance (Tweed).",
    "analyse_dentaire": "Évaluation des inclinaisons incisives (IMPA, I/Francfort) et des phénomènes de compensation.",
    "strategie_therapeutique": "Recommandations globales basées sur les objectifs COM (ex: contrôle vertical, propulsion mandibulaire, levée de compensation)."
}"""

def test_slm():
    print("=" * 70)
    print("TEST SLM - Digital Crown AI Advisor")
    print("=" * 70)
    
    prompt = f"Analyse ces données cliniques et génère le JSON attendu :\n{json.dumps(clinical_data, ensure_ascii=False, indent=2)}"
    
    print("\n--- DONNÉES CLINIQUES ENVOYÉES ---")
    print(json.dumps(clinical_data, ensure_ascii=False, indent=2))
    
    print("\n--- APPEL À OLLAMA (llama3.2) ---")
    print("Patientez, la génération peut prendre 10-30 secondes...")
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2',
                'system': SYSTEM_PROMPT,
                'prompt': prompt,
                'format': 'json',
                'stream': False,
                'options': {'temperature': 0.1}
            },
            timeout=180
        )
        response.raise_for_status()
        
        print(f"Status HTTP: {response.status_code} OK")
        
        raw_response = response.json().get('response', '{}')
        
        print("\n" + "=" * 70)
        print("RÉPONSE BRUTE DU SLM:")
        print("=" * 70)
        print(raw_response)
        
        print("\n" + "=" * 70)
        print("JSON PARSE:")
        print("=" * 70)
        try:
            parsed = json.loads(raw_response)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
            
            print("\n" + "=" * 70)
            print("ANALYSE DES SECTIONS:")
            print("=" * 70)
            for key in ['diagnostic_squelettique', 'analyse_dentaire', 'strategie_therapeutique']:
                value = parsed.get(key, 'MANQUANT')
                status = "[OK]" if value and value != 'MANQUANT' else "[KO]"
                print(f"{status} {key}:")
                print(f"   {value[:150]}{'...' if len(str(value)) > 150 else ''}")
                print()
                
            return True
            
        except json.JSONDecodeError as e:
            print(f"ERREUR PARSING JSON: {e}")
            print("La reponse n'est pas un JSON valide!")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERREUR: Impossible de se connecter à Ollama sur localhost:11434")
        print("   Verifiez qu'Ollama est demarre: ollama serve")
        return False
    except requests.exceptions.Timeout:
        print("ERREUR: Timeout après 180 secondes")
        return False
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = test_slm()
    sys.exit(0 if success else 1)
