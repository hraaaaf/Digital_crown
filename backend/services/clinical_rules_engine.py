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
        "ULCERE_GASTRIQUE": ["IBUPROFENE", "AINS", "ASPIRINE", "CORTICOIDES", "PREDNISOLONE"],
        "GROSSESSE": ["TETRACYCLINES", "IBUPROFENE", "AINS", "ASPIRINE"],
        "ALLAITEMENT": ["METRONIDAZOLE"],
        "ALLERGIE_PENICILLINE": ["AMOXICILLINE", "AUGMENTIN", "CLAMOXYL", "CEPHALOSPORINES"],
        "ANTICOAGULANT": ["IBUPROFENE", "AINS", "ASPIRINE"]
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
        },
        "SACCHAROMYCES_BOULARDII": {
            "noms": ["ULTRA-LEVURE", "FLORATIL"],
            "dosages": ["250mg"],
            "forme": "Gélules / Sachets"
        },
        "ACIDE_TRANEXAMIQUE": {
            "noms": ["EXACYL"],
            "dosages": ["500mg/5ml (ampoule locale)"],
            "forme": "Solution pour application locale (ampoules buvables pour compresse)"
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
        },
        "HYDROXYDE_DE_CALCIUM": {
            "molecules": [],
            "conseil": "🔬 Médication intra-canalaire temporaire à l'Hydroxyde de Calcium : Indiqué pour son pH alcalin (pH ~12.5) antiseptique et bactéricide. Insérer la pâte dans les canaux séchés et laisser agir pendant 7 à 14 jours entre deux séances sous pansement hermétique (ex: Cavit)."
        },
        "MISE_EN_FORME_CANALAIRE": {
            "molecules": ["CHLORHEXIDINE"],
            "conseil": "🦷 Mise en forme canalaire & Biopulpectomie : Réaliser l'irrigation abondante au Sodium Hypochlorite (NaOCl) à 2.5% ou 5% (dissolution organique + désinfection). Mise en forme mécanique rotative suivie d'une obturation tridimensionnelle à la gutta-percha étanche."
        }
    }

    # --- MATRICE D'INTERACTIONS (SÉCURITÉ ÉLITE) ---
    DRUG_INTERACTIONS = [
        {
            "molecules": ["AINS", "CORTICOIDES"],
            "level": "WARNING",
            "message": "Association AINS + Corticoïdes : Risque ulcérogène accru."
        },
        {
            "molecules": ["IBUPROFENE", "PREDNISOLONE"],
            "level": "WARNING",
            "message": "Association Ibuprofène + Prednisolone : Risque ulcérogène accru."
        },
        {
            "molecules": ["AMOXICILLINE", "METRONIDAZOLE"],
            "level": "INFO",
            "message": "Association synergique classique pour les infections parodontales."
        }
    ]

    def analyze_case(self, patient_data: Dict[str, Any], acts: List[str]) -> Dict[str, Any]:
        """
        Analyse déterministe ELITE du cas patient avec focus Maroc.
        """
        warnings = []
        recommended_molecules = set()
        
        # 1. Analyse des antécédents et allergies avec synonymes
        antecedents = str(patient_data.get("antecedents", "")).upper()
        age = patient_data.get("age", 30)
        poids = patient_data.get("poids", 70)

        # Détection résiliente des pathologies critiques (Synonymes)
        detected_conditions = []
        if any(x in antecedents for x in ["ENCEINTE", "GROSSESSE", "PREGNANT", "MATERNITÉ", "T1", "T2", "T3"]):
            detected_conditions.append("GROSSESSE")
        if any(x in antecedents for x in ["ULCÈRE", "ULCERE", "ESTOMAC", "GASTRITE", "GASTRIQUE"]):
            detected_conditions.append("ULCERE_GASTRIQUE")
        if any(x in antecedents for x in ["ASTHME", "ASTHMATIQUE", "RESPIRATOIRE"]):
            detected_conditions.append("ASTHME")
        if any(x in antecedents for x in ["REIN", "RÉNAL", "INSUFFISANCE RÉNALE", "RENALE"]):
            detected_conditions.append("INSUFFISANCE_RENALE")
        if any(x in antecedents for x in ["ALLAITEMENT", "NOURRISSON", "ALLAITE"]):
            detected_conditions.append("ALLAITEMENT")
        if any(x in antecedents for x in ["ALLERGIE PENI", "PENICILL", "PÉNICILL"]):
            detected_conditions.append("ALLERGIE_PENICILLINE")
        if any(x in antecedents for x in ["ANTICOAGULANT", "SINTROM", "PLAVIX", "ASPIRINE 100", "KARDÉGIC", "KARDEGIC", "AVK", "ELIQUIS", "XARELTO", "PREVISCAN"]):
            detected_conditions.append("ANTICOAGULANT")
        if any(x in antecedents for x in ["CARDIOPATHIE", "VALVE", "PROTHÈSE VALVULAIRE", "PROTHESE VALVULAIRE", "ENDOCARDITE", "SOUFFLE AU CŒUR", "SOUFFLE AU COEUR", "VALVULOPATHIE"]):
            detected_conditions.append("CARDIOPATHIE_HAUT_RISQUE")
        if any(x in antecedents for x in ["HYPERTENSION", "HTA", "TENSION", "HYPERTENDU"]):
            detected_conditions.append("HYPERTENSION")
        if any(x in antecedents for x in ["DIABÈTE", "DIABETE", "DIABÉT", "DIABET", "GLYCÉMIE", "GLYCEMIE", "GLYCEM"]):
            if "HBA1C" in antecedents:
                import re
                match = re.search(r"HBA1C\s*[:=>]?\s*(\d+([.,]\d+)?)", antecedents)
                if match:
                    val = float(match.group(1).replace(",", "."))
                    if val > 8.0:
                        detected_conditions.append("DIABETE_DESEQUILIBRE")
                    else:
                        detected_conditions.append("DIABETE_CONTROLE")
                else:
                    detected_conditions.append("DIABETE_INDETERMINE")
            else:
                detected_conditions.append("DIABETE_INDETERMINE")

        # --- PARODONTOLOGIE ---
        if any(x in antecedents for x in ["PARODONTITE", "POCHE", "PERTE D'ATTACHE", "PERTE D'ATTACHE", "SAIGNEMENT GINGIVAL"]):
            detected_conditions.append("PARODONTITE")

        # --- PÉDODONTIE & TRAUMATOLOGIE ---
        if any(x in antecedents for x in ["DENT DE LAIT", "DENT TEMPORAIRE", "DENT DÉCIDUALE", "DENT DECIDUALE"]):
            detected_conditions.append("DENT_TEMPORAIRE")

        # --- PROTHÈSE & ESPACE BIOLOGIQUE ---
        if any(x in antecedents for x in ["SOUS-GINGIVAL", "CARIE PROFONDE", "FRACTURE SOUS-GINGIVALE", "LIMITE PROTHÉTIQUE", "LIMITE PROTHETIQUE"]):
            detected_conditions.append("LIMITE_SOUS_GINGIVALE")

        # --- SÉCURITÉ NERF ALVÉOLAIRE (IMPLANTOLOGY / CHIRURGIE) ---
        if any(x in antecedents for x in ["PROXIMITÉ CANAL", "PROXIMITE CANAL", "PROXIMITÉ NERF", "PROXIMITE NERF", "CANAL DENTAIRE PROCHE"]):
            detected_conditions.append("PROXIMITE_NERVEUSE")

        # --- MUQUEUSE & PATHOLOGIE BUCCALE (RÈGLE DES 14 JOURS) ---
        if any(x in antecedents for x in ["LÉSION", "LESION", "ULCÉRATION", "ULCERATION", "ZONE BLANCHE", "ZONE ROUGE"]):
            import re
            if re.search(r"(1[4-9]|[2-9]\d)\s*(JOURS|JOUR|J)|([3-9]|[1-9]\d)\s*(SEMAINES|SEMAINE)", antecedents):
                detected_conditions.append("LESION_PERSISTANTE")
            else:
                detected_conditions.append("LESION_MUQUEUSE")

        # Application de la matrice de contre-indications
        for condition in detected_conditions:
            banni = self.CONTRE_INDICATIONS.get(condition, [])
            for mol in banni:
                msg = f"Contre-indication majeure : {mol} banni car le patient présente {condition}."
                if condition == "GROSSESSE":
                    msg = f"🤰 Alerte Grossesse : {mol} est formellement contre-indiqué en cours de grossesse (risque de toxicité fœtale cardio-pulmonaire pour les AINS, ou coloration des dents pour les Tétracyclines). Préférer le Paracétamol."
                elif condition == "ULCERE_GASTRIQUE":
                    msg = f"⚠️ Danger Gastro : {mol} est strictement contre-indiqué en cas d'ulcère gastroduodénal actif ou d'antécédents d'hémorragie digestive. Préférer le Paracétamol."
                elif condition == "ANTICOAGULANT":
                    msg = f"🩸 Danger Anticoagulant : {mol} est formellement contre-indiqué en association avec un traitement anticoagulant ou antiagrégant plaquettaire (risque d'hémorragie sévère). Préférer le Paracétamol."
                
                warnings.append(RuleWarning(
                    level="CRITICAL",
                    message=msg,
                    code=f"CI_{mol}"
                ))

        # --- SÉCURITÉ DE RADIOLOGIE EN COURS DE GROSSESSE ---
        if "GROSSESSE" in detected_conditions:
            warnings.append(RuleWarning(
                level="CRITICAL",
                message="📸 Radiographie & Grossesse : Les radiographies diagnostiques doivent être limitées au strict minimum. Si une radiographie est indispensable, le port d'un TABLIER DE PLOMB avec collerette thyroïdienne est OBLIGATOIRE pour protéger le fœtus.",
                code="PREGNANCY_RADIO"
            ))
            # Si anesthésie requise pour des actes invasifs
            if any(self._normalize_act_name(act) in ["IMPLANT", "EXTRACTION_CHIRURGICALE", "EXTRACTION_SIMPLE", "PULPITE"] for act in acts):
                warnings.append(RuleWarning(
                    level="WARNING",
                    message="💉 Anesthésie & Grossesse : L'utilisation d'anesthésiques locaux usuels (Articaïne, Lidocaïne) avec vasoconstricteur (Adrénaline) est autorisée pour réduire le passage systémique. Réaliser systématiquement une aspiration avant injection pour éviter un passage intra-vasculaire.",
                    code="PREGNANCY_ANESTHESIA"
                ))

        # --- HÉMOSTASE ET ANTICOAGULANTS ---
        if "ANTICOAGULANT" in detected_conditions:
            warnings.append(RuleWarning(
                level="CRITICAL",
                message="🩸 Vigilance Anticoagulants : Patient sous traitement anticoagulant/antiagrégant. Ne jamais arrêter le traitement de votre propre initiative (risque thromboembolique). Pour toute extraction, assurer une hémostase locale stricte.",
                code="ANTICOAGULANT_VIGILANCE"
            ))
            # Si extraction prévue, prescrire d'office de l'Exacyl pour l'hémostase locale
            if any("EXTRACTION" in act.upper() for act in acts):
                recommended_molecules.add("ACIDE_TRANEXAMIQUE")
                warnings.append(RuleWarning(
                    level="INFO",
                    message="🩸 Hémostase locale : Exacyl (Acide Tranexamique ampoules) prescrit d'office en application locale (sur compresse stérile) pour stabiliser le caillot.",
                    code="EXACYL_HEMOSTASE"
                ))

        # --- PATHOLOGIES CARDIOVASCULAIRES & ENDOCARDITE ---
        if "CARDIOPATHIE_HAUT_RISQUE" in detected_conditions:
            warnings.append(RuleWarning(
                level="CRITICAL",
                message="❤️ Risque d'Endocardite Infectieuse : Patient à haut risque cardiologique. Antibioprophylaxie OBLIGATOIRE (Amoxicilline 2g ou Clindamycine 600mg) 1h avant tout acte sanglant. Les anesthésies intraligamentaires et intraosseuses sont formellement PROSCRITES.",
                code="IE_HAUT_RISQUE"
            ))

        # --- TROUBLES CARDIAQUES SÉVÈRES & VASOCONSTRICTEURS ---
        if any(x in antecedents for x in ["ARYTHMIE", "INFARCTUS RÉCENT", "INFARCTUS RECENT", "ANGINE DE POITRINE", "ISCHÉMIQUE", "ISCHEMIQUE", "TROUBLE DU RYTHME"]):
            warnings.append(RuleWarning(
                level="CRITICAL",
                message="💉 Contre-indication Vasoconstricteurs : Anesthésie adrénalinée formellement contre-indiquée en raison des antécédents cardiaques sévères. Utiliser impérativement de la Mépivacaïne pure à 3% (Scandonest) sans vasoconstricteur.",
                code="ANESTHESIE_SANS_VASO"
            ))

        # --- HYPERTENSION ARTÉRIELLE (HTA) ---
        if "HYPERTENSION" in detected_conditions:
            warnings.append(RuleWarning(
                level="WARNING",
                message="🩸 Vigilance Tensionnelle : Patient hypertendu. Limiter l'usage de l'adrénaline (maximum 2 cartouches à 1/200 000). Réaliser une aspiration stricte pour éviter tout pic hypertensif accidentel.",
                code="HTA_PRECAUTION"
            ))

        # --- DIABÈTE ET COMPLICATIONS ---
        if "DIABETE_DESEQUILIBRE" in detected_conditions:
            warnings.append(RuleWarning(
                level="CRITICAL",
                message="🍭 Diabète Déséquilibré (HbA1c > 8%) : Risque infectieux majeur et retard de cicatrisation sévère. Différer les actes chirurgicaux invasifs non urgents. En cas d'urgence absolue, instaurer une antibioprophylaxie post-opératoire rigoureuse.",
                code="DIABETE_DESEQUILIBRE_ALERT"
            ))
        elif "DIABETE_INDETERMINE" in detected_conditions:
            warnings.append(RuleWarning(
                level="WARNING",
                message="🍭 Diabète non documenté : Penser à demander le dernier taux d'HbA1c au patient. Si HbA1c > 8%, des précautions opératoires et une antibioprophylaxie sont requises.",
                code="DIABETE_VERIF_HBA1C"
            ))

        # --- PATHOLOGIE BUCCALE : RÈGLE DES 14 JOURS ---
        if "LESION_PERSISTANTE" in detected_conditions:
            warnings.append(RuleWarning(
                level="CRITICAL",
                message="🔍 Règle des 14 jours (Dépistage Cancer Buccal) : Lésion muqueuse persistante depuis plus de 14 jours. Orientation OBLIGATOIRE pour une biopsie anatomo-pathologique afin d'exclure tout carcinome épidermoïde débutant.",
                code="LESION_BIOPSIE_REQUIS"
            ))
        elif "LESION_MUQUEUSE" in detected_conditions:
            warnings.append(RuleWarning(
                level="WARNING",
                message="🔍 Surveillance Lésion Muqueuse : Lésion suspecte détectée. Si celle-ci ne guérit pas sous 14 jours après élimination de tout facteur traumatique local, planifier impérativement une biopsie.",
                code="LESION_SURVEILLANCE"
            ))

        # --- PARODONTOLOGIE ---
        if "PARODONTITE" in detected_conditions:
            warnings.append(RuleWarning(
                level="WARNING",
                message="🦷 Diagnostic Parodontal (AAP 2017) : Signes de parodontite active ou perte d'attache détectés. Planifier un bilan parodontal complet (sondage systématique) et un surfaçage radiculaire (SRP) sous couverture locale.",
                code="PARODONTITE_SRP_REQUIS"
            ))

        # --- PÉDODONTIE & TRAUMATOLOGIE ---
        if "DENT_TEMPORAIRE" in detected_conditions:
            warnings.append(RuleWarning(
                level="CRITICAL",
                message="🍭 Contre-indication Avulsion (Dent Temporaire) : En cas d'expulsion traumatique d'une dent de lait, NE JAMAIS RÉIMPLANTER la dent pour préserver l'intégrité du germe de la dent permanente sous-jacente.",
                code="AVULSION_TEMPORAIRE_ALERT"
            ))

        # --- PROTHÈSE & ESPACE BIOLOGIQUE ---
        if "LIMITE_SOUS_GINGIVALE" in detected_conditions:
            warnings.append(RuleWarning(
                level="WARNING",
                message="📐 Respect de l'Espace Biologique (2mm) : Limite de carie ou de fracture sous-gingivale suspectée. Assurer une distance minimale de 2 mm entre la future limite prothétique et la crête osseuse. Envisager une élongation coronaire chirurgicale ou extrusion.",
                code="VIOLATION_ESPACE_BIOLOGIQUE"
            ))

        # --- IMPLANTOLOGY & PROXIMITÉ NERF ---
        if "PROXIMITE_NERVEUSE" in detected_conditions:
            warnings.append(RuleWarning(
                level="CRITICAL",
                message="📐 Distance de Sécurité Implantaire (2mm) : Proximité suspectée avec le canal alvéolaire inférieur. Maintenir une marge apicale stricte de 2 mm lors du forage et de la pose pour éliminer tout risque de paresthésie définitive.",
                code="IMPLANT_NERVE_SAFETY"
            ))

        # --- RULE 1A : Antibioprophylaxie pré-opératoire automatique ---
        for act in acts:
            act_key = self._normalize_act_name(act)
            if act_key in ["IMPLANT", "EXTRACTION_CHIRURGICALE"]:
                has_penicillin_allergy = "PENICILL" in antecedents or "PÉNICILL" in antecedents or "AMOXI" in antecedents
                if has_penicillin_allergy:
                    warnings.append(RuleWarning(
                        level="INFO",
                        message="🛡️ Antibioprophylaxie requise (allergie pénicilline) : Clindamycine (DALACINE) 600mg par voie orale, 1h avant l'acte.",
                        code="ANTIBIOPROPHYLAXIE_ALT"
                    ))
                else:
                    warnings.append(RuleWarning(
                        level="INFO",
                        message="🛡️ Antibioprophylaxie requise : 2g d'Amoxicilline (CLAMOXYL) par voie orale, 1h avant l'acte.",
                        code="ANTIBIOPROPHYLAXIE"
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

        # --- CO-PRESCRIPTION PROTECTRICE DE LA FLORE INTESTINALE (Ultra-Levure) ---
        if any(x in recommended_molecules for x in ["AMOXICILLINE", "AUGMENTIN"]):
            recommended_molecules.add("SACCHAROMYCES_BOULARDII")
            warnings.append(RuleWarning(
                level="INFO",
                message="🛡️ Prévention Colite/Diarrhée : Ultra-Levure (Saccharomyces boulardii 250mg) suggéré en co-prescription pour prévenir la diarrhée post-antibiotique.",
                code="PREV_DIARRHEE"
            ))

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
            
            if selected_mol == "SACCHAROMYCES_BOULARDII":
                justif = "🛡️ Prévention de la diarrhée post-antibiotique."

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
        if "HYDROXYDE" in name or "CALCIUM" in name or "INTER-SEANCE" in name or "MÉDICATION" in name or "MEDICATION" in name:
            return "HYDROXYDE_DE_CALCIUM"
        if "MISE EN FORME" in name or "CANALAIRE" in name or "BIOPULPECTOMIE" in name or "ENDO" in name or "TRAITEMENT CANALAIRE" in name:
            return "MISE_EN_FORME_CANALAIRE"
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
