"""
Crown Bot — Base de Connaissances Statique

Ce module centralise la connaissance métier de l'application Digital Crown.
Il permet au Crown Bot de répondre aux questions sur le fonctionnement du cabinet, 
les règles cliniques, ou la manière d'utiliser les fonctionnalités.
"""
from typing import Dict, Any

KNOWLEDGE: Dict[str, Dict[str, Any]] = {
    "app_features": {
        "devis": "Pour créer un devis, vous pouvez utiliser l'onglet 'Finances' ou me demander directement 'crée un devis pour [Patient]'. Le devis inclut les actes prothétiques, les soins, et permet la signature électronique.",
        "ordonnance": "Pour générer une ordonnance, allez dans le dossier patient ou demandez-moi 'ordonnance pour [Patient]'. Je peux vous suggérer des prescriptions types basées sur l'acte (ex: post-extraction, endo).",
        "rendez_vous": "L'agenda vous permet de gérer vos RDV. Vous pouvez me demander 'prends RDV pour [Patient] demain à 10h'.",
        "signature_fauteuil": "La 'Signature Fauteuil' permet au patient de signer un devis ou un consentement directement sur une tablette ou un mobile.",
        "alertes": "Le système d'alertes proactives (dans Intelligence) vous signale les patients à risque (impayés, annulations fréquentes, allergies).",
    },
    "clinical_rules": {
        "extraction_recommandation": "Après une extraction, il est recommandé de prescrire des antalgiques (ex: Paracétamol), et potentiellement des antibiotiques (ex: Amoxicilline) selon le cas clinique.",
        "endodontie": "Pour un traitement endodontique, un devis pour reconstitution corono-radiculaire et couronne est généralement associé.",
        "implantologie": "Le flux implantaire requiert un cone beam (CBCT) préalable et un devis détaillé incluant l'implant, le pilier, et la couronne.",
    },
    "medication_info": {
        "paracetamol": "Antalgique de palier 1. Posologie standard adulte : 1g toutes les 6h, max 4g/jour.",
        "amoxicilline": "Antibiotique de la famille des pénicillines. Posologie standard adulte en dentaire : 1g matin et soir pendant 6 jours.",
        "ibuprofene": "AINS. Posologie standard adulte : 400mg toutes les 8h. Attention aux contre-indications gastriques et risques hémorragiques post-opératoires.",
    },
    "document_types": {
        "devis_standard": "Devis détaillé avec schéma dentaire et plan de traitement.",
        "consentement": "Formulaire légal informant le patient des risques de l'intervention (ex: extraction, implant).",
        "certificat_medical": "Certificat d'absence pour le travail ou l'école suite à une intervention.",
    },
}

def search_knowledge(query: str) -> str:
    """Recherche basique dans la base de connaissances."""
    query = query.lower()
    results = []
    
    for category, items in KNOWLEDGE.items():
        for key, text in items.items():
            if key.replace("_", " ") in query or any(word in text.lower() for word in query.split() if len(word) > 4):
                results.append(f"**{key.replace('_', ' ').capitalize()}** : {text}")
                
    if not results:
        return "Je n'ai pas trouvé d'information exacte dans ma base de connaissances. Pouvez-vous reformuler votre question ?"
        
    return "\n\n".join(results[:3])  # Retourner les 3 meilleurs résultats
