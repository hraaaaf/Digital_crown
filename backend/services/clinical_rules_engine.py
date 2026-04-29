import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# --- CONSTANTES MÉDICALES DÉTERMINISTES ---

@dataclass
class RuleWarning:
    level: str  # 'CRITICAL', 'WARNING', 'INFO'
    message: str
    code: str

class ClinicalRulesEngine:
    """
    Moteur de règles cliniques LOCAL-FIRST.
    Aucun LLM, aucune API. 100% Déterministe et Sécurisé.
    """

    # --- MATRICE DE CONTRE-INDICATIONS ---
    # { 'Antécédent': [ 'Molécule/Classe bannie' ] }
    CONTRE_INDICATIONS = {
        "ASTHME": ["IBUPROFENE", "ACIDE_TIAPROFRENIQUE", "ASPIRINE", "AINS"],
        "INSUFFISANCE_RENALE": ["IBUPROFENE", "AINS", "ASPIRINE"],
        "ULCERE_GASTRIQUE": ["IBUPROFENE", "AINS", "ASPIRINE", "CORTICOIDES"],
        "GROSSESSE": ["TETRACYCLINES", "AINS_T3"],
        "ALLAITEMENT": ["METRONIDAZOLE"],
        "ALLERGIE_PENICILLINE": ["AMOXICILLINE", "AUGMENTIN", "CLAMOXYL", "CEPHALOSPORINES"]
    }

    # --- PHARMACOPÉE MAROCAINE (Scientist Agent Knowledge) ---
    # { 'MOLÉCULE': { 'noms': ['Nom1', 'Nom2'], 'dosage_standard': '...', 'forme': '...' } }
    MAROC_PHARMACOPEIA = {
        "AMOXICILLINE": {
            "noms": ["CLAMOXYL", "AMOPÉN", "BRISTAMOX"],
            "dosages": ["500mg", "1g"],
            "forme": "Gélules / Sachets"
        },
        "AUGMENTIN": {
            "noms": ["AUGMENTIN", "AMOCLAN", "CLAVUMOX"],
            "dosages": ["1g/125mg"],
            "forme": "Sachets / Comprimés"
        },
        "METRONIDAZOLE": {
            "noms": ["FLAGYL", "METRONAL"],
            "dosages": ["500mg"],
            "forme": "Comprimés"
        },
        "SPIRAMYCINE_METRONIDAZOLE": {
            "noms": ["BI-RODOGYL", "BI-MISSIL", "BI-OROGYL"],
            "dosages": ["1.5MUI/250mg"],
            "forme": "Comprimés"
        },
        "PARACETAMOL": {
            "noms": ["DOLIPRANE", "DOLOSTOP", "PARALGAN"],
            "dosages": ["500mg", "1g"],
            "forme": "Comprimés / Effervescents"
        },
        "PARACETAMOL_CODEINE": {
            "noms": ["CLARADOL CODÉINE", "ALGODOL"],
            "dosages": ["500mg/30mg"],
            "forme": "Comprimés"
        },
        "IBUPROFENE": {
            "noms": ["ALGOFÈNE", "ADVIL", "Nurofen"],
            "dosages": ["200mg", "400mg", "600mg"],
            "forme": "Comprimés / Capsules"
        },
        "CHLORHEXIDINE": {
            "noms": ["ELUDRIL", "HEXYDRIL", "ORALDINE"],
            "dosages": ["Bain de bouche"],
            "forme": "Solution"
        },
        "CLINDAMYCINE": {
            "noms": ["DALACINE"],
            "dosages": ["150mg", "300mg"],
            "forme": "Gélules"
        },
        "PREDNISOLONE": {
            "noms": ["SOLUPRED", "CORTANCYL"],
            "dosages": ["5mg", "20mg"],
            "forme": "Comprimés Orodispersibles"
        }
    }

    # --- PROTOCOLES PAR ACTE (STANDARDS HAS/SFCO) ---
    PROTOCOLS = {
        "EXTRACTION_SIMPLE": {
            "molecules": ["PARACETAMOL"],
            "conseil": "Application de glace locale. Alimentation tiède (pendant 24h)."
        },
        "EXTRACTION_CHIRURGICALE": {
            "molecules": ["PARACETAMOL_CODEINE", "IBUPROFENE", "CHLORHEXIDINE"],
            "conseil": "Ne pas rincer trop fort les 24h premières heures. Éviter le tabac."
        },
        "ABCES_DENTAIRE": {
            "molecules": ["AMOXICILLINE", "METRONIDAZOLE", "PARACETAMOL"],
            "conseil": "Traitement étiologique indispensable dès que possible."
        },
        "ABCES_PARODONTAL": {
            "molecules": ["SPIRAMYCINE_METRONIDAZOLE", "CHLORHEXIDINE", "PARACETAMOL"],
            "conseil": "Détartrage/Surfaçage après phase aiguë."
        },
        "PULPITE": {
            "molecules": ["PARACETAMOL_CODEINE", "IBUPROFENE"],
            "conseil": "Urgence endodontique à réaliser sous anesthésie."
        },
        "IMPLANT": {
            "molecules": ["AUGMENTIN", "IBUPROFENE", "CHLORHEXIDINE"],
            "conseil": "Antibioprophylaxie pré-opératoire (2g 1h avant) recommandée."
        }
    }

    def analyze_case(self, patient_data: Dict[str, Any], acts: List[str]) -> Dict[str, Any]:
        """
        Analyse déterministe ELITE du cas patient avec focus Maroc.
        """
        warnings = []
        recommended_molecules = set()
        
        # 1. Analyse des antécédents et allergies
        antecedents = str(patient_data.get("antecedents", "")).upper()
        age = patient_data.get("age", 30)
        poids = patient_data.get("poids", 70)

        # Détection automatique des risques liés aux antécédents
        for condition, banni in self.CONTRE_INDICATIONS.items():
            if condition in antecedents:
                for mol in banni:
                    warnings.append(RuleWarning(
                        level="CRITICAL",
                        message=f"Contre-indication majeure : {mol} banni car le patient présente {condition}.",
                        code=f"CI_{mol}"
                    ))

        # 2. Recommandations basées sur les actes
        strategy = "Traitement symptomatique et curatif."
        for act in acts:
            act_key = self._normalize_act_name(act)
            if act_key in self.PROTOCOLS:
                p = self.PROTOCOLS[act_key]
                for mol in p["molecules"]:
                    recommended_molecules.add(mol)
                strategy = p["conseil"]

        # 3. Filtrage et Mapping Commercial (Focus Maroc)
        final_molecules = []
        banned_mols = [w.code.replace("CI_", "") for w in warnings]
        
        selected_mols_for_interactions = []

        for mol in recommended_molecules:
            selected_mol = mol
            justif = "Protocole standard pour l'acte."
            
            # Gestion des classes (AINS)
            is_ains = mol in ["IBUPROFENE", "ACIDE_TIAPROFRENIQUE", "AINS"]
            if is_ains and "AINS" in banned_mols:
                selected_mol = "PARACETAMOL" # Fallback sécurisé universel
                justif = "Substitution AINS -> Paracétamol par sécurité."
            
            if selected_mol in banned_mols:
                selected_mol = self._get_alternative(selected_mol, banned_mols)
                justif = f"Alternative à {mol} (banni par antécédents)."
                if not selected_mol:
                    warnings.append(RuleWarning("CRITICAL", f"Aucune alternative trouvée pour {mol}. Risque élevé.", "NO_ALT"))
                    continue

            selected_mols_for_interactions.append(selected_mol)

            # Mapping vers noms commerciaux marocains
            commercial = self.MAROC_PHARMACOPEIA.get(selected_mol, {"noms": [selected_mol], "dosages": ["N/A"], "forme": "N/A"})
            
            # Ajustement du dosage par défaut selon le poids/âge
            dosage_suggere = commercial["dosages"][0]
            if age < 15:
                dosage_suggere = self._calculate_pediatric_dosage(selected_mol, poids)

            final_molecules.append({
                "molecule": selected_mol,
                "noms_commerciaux": commercial["noms"],
                "dosage_defaut": dosage_suggere,
                "forme": commercial["forme"] if age >= 12 else "Sirop/Suspension",
                "justification": justif,
                "priorite": "haute"
            })

        # 4. Détection d'interactions entre les molécules sélectionnées
        for interaction in self.DRUG_INTERACTIONS:
            hits = [m for m in interaction["molecules"] if m in selected_mols_for_interactions]
            if len(hits) >= 2:
                warnings.append(RuleWarning(
                    level=interaction["level"],
                    message=interaction["message"],
                    code="DRUG_INTERACT"
                ))

        # 5. Calcul de dose et alertes globales
        dosage_note = "Posologie adulte standard."
        if age < 15:
            dosage_note = f"⚠️ AJUSTEMENT PÉDIATRIQUE REQUIS ({poids}kg). Ne jamais dépasser les doses par kg/24h."

        return {
            "risques_identifies": [w.message for w in warnings],
            "recommandations_moleculaires": final_molecules,
            "strategie_globale": strategy,
            "dosage_note": dosage_note,
            "is_child": age < 15,
            "moteur": "Local Scientist Engine v1.5 (Elite-Secure)"
        }

    def _calculate_pediatric_dosage(self, molecule: str, weight: float) -> str:
        """Calcul déterministe des doses pédiatriques standards."""
        if molecule == "AMOXICILLINE":
            return f"{int(weight * 50 / 2)}mg x 2/jour (50mg/kg/j)"
        if molecule == "PARACETAMOL":
            return f"{int(weight * 15)}mg x 4/jour (60mg/kg/j)"
        if molecule == "IBUPROFENE":
            return f"{int(weight * 10)}mg x 3/jour (30mg/kg/j)"
        return "Dosage à confirmer (Poids)"

    def _normalize_act_name(self, name: str) -> str:
        name = name.upper()
        if "EXTRACTION" in name:
            if "CHIRURGICALE" in name or "COMPLEXE" in name: return "EXTRACTION_CHIRURGICALE"
            return "EXTRACTION_SIMPLE"
        if "ABCES" in name or "INFECT" in name:
            if "PARO" in name: return "ABCES_PARODONTAL"
            return "ABCES_DENTAIRE"
        if "PULPITE" in name or "DOULEUR" in name: return "PULPITE"
        if "IMPLANT" in name: return "IMPLANT"
        return "DEFAULT"

    def _get_alternative(self, mol: str, banned: List[str]) -> Optional[str]:
        alternatives = {
            "AMOXICILLINE": ["CLINDAMYCINE", "SPIRAMYCINE_METRONIDAZOLE"],
            "AUGMENTIN": ["CLINDAMYCINE", "SPIRAMYCINE_METRONIDAZOLE"],
            "IBUPROFENE": ["PARACETAMOL"],
            "AINS": ["PARACETAMOL"],
            "PARACETAMOL_CODEINE": ["PARACETAMOL"]
        }
        options = alternatives.get(mol, [])
        for opt in options:
            if opt not in banned:
                return opt
        return None

clinical_rules = ClinicalRulesEngine()
