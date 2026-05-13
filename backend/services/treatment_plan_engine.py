import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TreatmentPlanEngine:
    """
    Moteur de planification de traitement méthodique.
    Organise les détections cliniques en phases logiques et prioritaires.
    """

    # Définition des priorités par type de pathologie
    PRIORITY_MAP = {
        "infection": 1,      # Phase Urgence
        "douleur": 1,        # Phase Urgence
        "abcès": 1,         # Phase Urgence
        "pulpite": 1,       # Phase Urgence
        "carie_profonde": 2, # Phase Initiale / Assainissement
        "parodontite": 2,    # Phase Initiale / Assainissement
        "détartrage": 2,     # Phase Initiale / Assainissement
        "extraction": 2,     # Phase Initiale / Assainissement
        "carie": 3,          # Phase Conservatrice
        "restauration": 3,   # Phase Conservatrice
        "prothèse": 4,       # Phase Réhabilitation
        "implant": 4,        # Phase Réhabilitation
        "couronne": 4,       # Phase Réhabilitation
        "orthodontie": 5,    # Phase Spécialisée
        "suivi": 6           # Phase Maintenance
    }

    def generate_plan(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transforme une liste de détections panoramiques en un plan de traitement structuré.
        """
        try:
            # 1. Classification par phases
            phases = {
                "URGENCE": [],
                "INITIALE": [],
                "CONSERVATRICE": [],
                "REHABILITATION": [],
                "MAINTENANCE": []
            }

            for det in detections:
                label = det.get("label", "").lower()
                fdi = det.get("fdi", "Global")
                
                # Détermination de la phase basée sur le label
                phase_key = self._map_to_phase(label)
                
                # Création de l'acte suggéré
                act_suggestion = {
                    "id": f"act_{datetime.now().timestamp()}_{fdi}",
                    "fdi": fdi,
                    "diagnosis": label.capitalize(),
                    "suggested_act": self._suggest_act(label),
                    "priority": self.PRIORITY_MAP.get(label, 99),
                    "status": "SUGGESTED"
                }
                
                phases[phase_key].append(act_suggestion)

            # 2. Tri interne par priorité dans chaque phase
            for key in phases:
                phases[key] = sorted(phases[key], key=lambda x: x["priority"])

            return {
                "patient_id": None, # Sera injecté par le service appelant
                "created_at": datetime.now().isoformat(),
                "phases": phases,
                "summary": self._generate_summary(phases)
            }

        except Exception as e:
            logger.error(f"Error in TreatmentPlanEngine: {e}")
            return {"error": str(e)}

    def _map_to_phase(self, label: str) -> str:
        """Mappe une détection à une phase clinique standard."""
        if any(x in label for x in ["abcès", "pulpite", "infection", "douleur"]):
            return "URGENCE"
        if any(x in label for x in ["détartrage", "parodontite", "extraction", "carie_profonde"]):
            return "INITIALE"
        if any(x in label for x in ["carie", "restauration"]):
            return "CONSERVATRICE"
        if any(x in label for x in ["prothèse", "implant", "couronne", "bridge"]):
            return "REHABILITATION"
        return "MAINTENANCE"

    def _suggest_act(self, label: str) -> str:
        """Suggère un acte CCAM ou un libellé basé sur le diagnostic."""
        suggestions = {
            "carie": "Obturation 3 faces",
            "carie_profonde": "Traitement endodontique + Obturation",
            "abcès": "Drainage / Urgence dentaire",
            "détartrage": "Détartrage complet",
            "implant": "Pose d'implant dentaire",
            "couronne": "Pose de couronne céramo-métallique",
            "extraction": "Extraction d'une dent monoradiculée"
        }
        return suggestions.get(label, "Examen approfondi requis")

    def _generate_summary(self, phases: Dict) -> str:
        """Génère un résumé textuel de la stratégie."""
        counts = {k: len(v) for k, v in phases.items() if v}
        if not counts:
            return "Aucun traitement particulier suggéré. Maintenance périodique."
        
        main_focus = max(counts, key=counts.get)
        return f"Plan de traitement orienté vers la {main_focus.lower()}. Priorité aux soins de la phase {list(counts.keys())[0]}."

treatment_plan_engine = TreatmentPlanEngine()
