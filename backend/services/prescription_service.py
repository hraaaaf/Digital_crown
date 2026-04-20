from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import Patient, Acte

# --- BASE DE CONNAISSANCES CLINIQUE (Déterministe) ---
# Unités : Adultes (doses fixes), Enfants (mg/kg - indicatif pour le praticien)

DRUG_KNOWLEDGE = {
    "AMOXICILLINE": {
        "family": "penicilline",
        "forms": ["Gélules 1g", "Suspension 500mg/5ml"],
        "adult": "1g, 2 fois par jour pendant 6 jours.",
        "child": "50mg/kg/jour, répartis en 2 prises.",
    },
    "DALACINE": {
        "family": "lincosamide",
        "forms": ["Gélules 300mg"],
        "adult": "600mg par jour (1 gélule matin et soir) pendant 6 jours.",
        "child": "20mg/kg/jour en 2 prises.",
    },
    "BI-RODOGYL": {
        "family": "association_atb",
        "forms": ["Comprimés"],
        "adult": "1 comprimé 3 fois par jour au milieu des repas pendant 6 jours.",
        "child": "Contre-indiqué avant 15 ans.",
    },
    "PARACETAMOL": {
        "family": "antalgique",
        "forms": ["Gélules 1g", "Sachets 500mg"],
        "adult": "1g à renouveler toutes les 6 heures en cas de douleur.",
        "child": "15mg/kg toutes les 6 heures sans dépasser 4 prises par jour.",
    },
    "IBUPROFENE": {
        "family": "ains",
        "forms": ["Comprimés 400mg"],
        "adult": "1 comprimé toutes les 8 heures au milieu des repas pendant 3 jours.",
        "child": "10mg/kg toutes les 8 heures.",
    },
    "BDB_CHLORHEXIDINE": {
        "family": "antiseptique",
        "forms": ["Flacon 200ml"],
        "adult": "Bains de bouche purs pendant 1 minute, 2 fois par jour, à débuter 24h après l'acte.",
        "child": "Usage déconseillé avant 6 ans.",
    }
}

PROTOCOLS = {
    "EXTRACTION_SIMPLE": {
        "atb": "AMOXICILLINE",
        "antalgique": "PARACETAMOL",
        "antiseptique": "BDB_CHLORHEXIDINE",
        "fallback_atb": "DALACINE"
    },
    "EXTRACTION_CHIRURGICALE": {
        "atb": "AMOXICILLINE",
        "ains": "IBUPROFENE",
        "antalgique": "PARACETAMOL",
        "antiseptique": "BDB_CHLORHEXIDINE",
        "fallback_atb": "DALACINE"
    },
    "IMPLANTOLOGIE": {
        "atb": "AMOXICILLINE",
        "ains": "IBUPROFENE",
        "antalgique": "PARACETAMOL",
        "antiseptique": "BDB_CHLORHEXIDINE",
        "fallback_atb": "DALACINE"
    },
    "ABCES_DENTAIRE": {
        "atb": "BI-RODOGYL",  # Association Métronidazole/Spiramycine
        "antalgique": "PARACETAMOL",
        "fallback_atb": "DALACINE"
    }
}

class PrescriptionService:
    @staticmethod
    def calculate_age(birth_date) -> int:
        if not birth_date: return 30 # Default adult
        today = datetime.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def resolve_smart_prescription(self, db: Session, patient_id: int, act_names: List[str], doctor_id: Optional[int] = None) -> Dict:
        """
        Résout l'ordonnance idéale basée sur le contexte.
        Priorité : Préférence Médecin > Standard Système > Filtre Sécurité.
        """
        from ..models import DoctorPrescriptionPreference # Import local pour éviter les cycles
        
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"error": "Patient introuvable"}

        age = self.calculate_age(patient.date_naissance)
        is_child = age < 12
        # On utilise antecedents_medicaux pour chercher les allergies (car allergies n'est pas un champ séparé)
        allergies = (patient.antecedents_medicaux or "").lower()
        has_penicillin_allergy = any(x in allergies for x in ["pénicilline", "amoxicilline", "atb", "penicilline"])

        # 1. Identifier l'acte dominant
        dominant_protocol_code = "EXTRACTION_SIMPLE"
        for act in act_names:
            act_up = act.upper()
            if "IMPLANT" in act_up: dominant_protocol_code = "IMPLANTOLOGIE"; break
            if "CHIRURGIE" in act_up or "EXTRACTION" in act_up: dominant_protocol_code = "EXTRACTION_CHIRURGICALE"
            if "ABCÈS" in act_up or "INFECTION" in act_up: dominant_protocol_code = "ABCES_DENTAIRE"

        # 2. Chercher la surcharge PRATICIEN
        base_drugs = []
        source = "system"
        
        if doctor_id:
            pref = db.query(DoctorPrescriptionPreference).filter(
                DoctorPrescriptionPreference.doctor_id == doctor_id,
                DoctorPrescriptionPreference.act_code == dominant_protocol_code
            ).first()
            if pref:
                base_drugs = pref.drugs_json
                source = "doctor_preference"

        # 3. Si pas de préférence, charger le protocole SYSTEME
        if not base_drugs:
            protocol_data = PROTOCOLS.get(dominant_protocol_code)
            # Construction de la liste des médicaments de base à partir du dico global
            for drug_type in ["atb", "ains", "antalgique", "antiseptique"]:
                d_key = protocol_data.get(drug_type)
                if not d_key: continue
                d_info = DRUG_KNOWLEDGE.get(d_key)
                base_drugs.append({
                    "nom": d_key,
                    "dosage": d_info["forms"][0],
                    "forme": "Gélules" if "Gélules" in d_info["forms"][0] else "Comprimés",
                    "posologie": d_info["adult"],
                    "molecule_family": d_info["family"]
                })

        # 4. FILTRE DE SÉCURITÉ (Appliqué sur base_drugs, quelle que soit la source)
        final_drugs = []
        warnings = []
        
        for drug in base_drugs:
            d_key = drug["nom"]
            # Récupérer les infos de référence si possible
            ref_info = DRUG_KNOWLEDGE.get(d_key)
            
            # --- SÉCURITÉ ALLERGIE ---
            if has_penicillin_allergy and ref_info and ref_info["family"] == "penicilline":
                # On bascule sur le fallback prévu dans le système pour cet acte
                fallback_key = PROTOCOLS.get(dominant_protocol_code, {}).get("fallback_atb", "DALACINE")
                fallback_info = DRUG_KNOWLEDGE.get(fallback_key)
                
                warnings.append(f"⚠️ ALLERGIE : Substitution de {d_key} par {fallback_key}.")
                
                final_drugs.append({
                    "nom": fallback_key,
                    "dosage": fallback_info["forms"][0],
                    "forme": "Gélules",
                    "posologie": fallback_info["adult"] if not is_child else fallback_info["child"]
                })
                continue # On passe au suivant, substitution faite

            # --- SÉCURITÉ PÉDIATRIE ---
            if is_child and ref_info:
                poso_child = ref_info["child"]
                if "Contre-indiqué" in poso_child:
                    warnings.append(f"❌ {d_key} est contre-indiqué chez l'enfant.")
                
                final_drugs.append({
                    "nom": d_key,
                    "dosage": ref_info["forms"][1] if len(ref_info["forms"]) > 1 else drug["dosage"],
                    "forme": "Suspension" if len(ref_info["forms"]) > 1 else drug["forme"],
                    "posologie": poso_child
                })
            else:
                # On garde la version adulte (soit pref doc, soit systeme)
                final_drugs.append(drug)

        return {
            "protocol_name": dominant_protocol_code.replace("_", " "),
            "source": source,
            "patient_context": {"age": age, "is_child": is_child, "has_allergies": has_penicillin_allergy},
            "suggestions": final_drugs,
            "warnings": warnings,
            "can_auto_fill": len(warnings) < 2
        }


prescription_service = PrescriptionService()
