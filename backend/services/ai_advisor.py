import logging
from typing import Dict, Optional, Any
from backend import schemas
from backend.config import settings
from backend.schemas.cephalo_normative import NormativeContext, Sex
from backend.services.cephalo_normative_service import evaluate_measurement, NormativeEvaluationStatus

logger = logging.getLogger(__name__)

# Patient.sexe is stored as "M"/"F" — anything else maps to None, never
# guessed (same convention as cephalo_engine.py/bilan_ortho_engine.py,
# CEPHALOMETRY-NORMATIVE-CONTEXT-PLUMBING-4A2).
_SEX_CODE_TO_ENUM = {"M": Sex.MALE, "F": Sex.FEMALE}


def _map_sex(sex_code: Optional[str]) -> Optional[Sex]:
    if sex_code is None:
        return None
    return _SEX_CODE_TO_ENUM.get(sex_code)


def _authoritative_label(
    measurement_id: str,
    value: Optional[float],
    age: Optional[int] = None,
    sex: Optional[str] = None,
) -> Optional[str]:
    """Returns a classification label only if the normative service
    considers it authoritative — None otherwise (no silent fallback to
    local legacy constants/`.status`). Duplicated from cephalo_engine.py's
    identical helper rather than cross-imported, to keep these modules
    independent as they already are (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-
    TWEED-IMPA-FRANCFORT-4C). population_id stays None: no population-profile
    concept exists anywhere in Digital Crown today (documented limitation).
    """
    if value is None:
        return None
    result = evaluate_measurement(
        measurement_id, value, "v1",
        NormativeContext(age=age, sex=_map_sex(sex), population_id=None),
    )
    if result.status == NormativeEvaluationStatus.VALIDATED_PROFILE_MATCH and result.classification:
        return result.classification
    return None


class ClinicalNorms:
    CHILD = {
        "a_mean": 2.8, "a_dev": 3.3,
    }
    ADULT = {
        "a_mean": 2.3, "a_dev": 3.0,
    }

    @classmethod
    def get(cls, is_child: bool) -> Dict[str, float]:
        return cls.CHILD if is_child else cls.ADULT

class AIAdvisor:
    """
    Clinical Intelligence Service (Ghost Brain V2 - NLG Déterministe).
    Remplace le LLM local (Ollama) par un moteur de règles expert (NLG) 
    qui génère un texte médical fluide, précis et instantané (<10ms).
    """

    def __init__(self):
        # Configuration purement symbolique pour compatibilité avec l'existant
        self.model_name = "ghost-brain-nlg"

    def generate_diagnostic(
        self,
        result: schemas.CephaloAnalysisResult,
        use_slm: bool = False,
        age: Optional[int] = None,
        sex: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Génère un diagnostic expert instantané. Le paramètre use_slm est ignoré.
        age/sex (numeric age, "M"/"F") are optional and, when provided by the
        caller, reach the normative service for Tweed/IMPA/I_Francfort — never
        inferred here (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-TWEED-IMPA-FRANCFORT-4C).
        """
        metrics = result.metrics
        cohort = result.analysis_metadata.cohort # "Enfant (9 ans)" or "Adulte"

        logger.info("Ghost Brain V2: Génération déterministe (NLG) de l'analyse céphalométrique")
        return self._generate_nlg_report(metrics, cohort, age=age, sex=sex)

    def _generate_nlg_report(
        self,
        metrics: schemas.AnalysisMetrics,
        cohort: str,
        age: Optional[int] = None,
        sex: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Deterministic expert rule engine (NLG).
        Génère un rapport clinique complet basé sur les standards COM.
        """
        osseuse = metrics.analyse_osseuse
        dentaire = metrics.analyse_dentaire
        is_child = "Enfant" in cohort

        tweed_data = osseuse.Angle_de_Tweed
        sit_a_data = osseuse.Situation_A
        tweed_value = tweed_data.valeur
        sit_a_value = sit_a_data.valeur
        # Tweed no longer classifies via the shared `.status` field (that field
        # stays DISPLAY_ONLY for frontend/PDF cards, per Phase 4A precedent) —
        # only an authoritative service classification may drive this narrative
        # (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-TWEED-IMPA-FRANCFORT-4C).
        tweed_label = _authoritative_label("Angle_de_Tweed", tweed_value, age, sex)

        # --- SYNTHESE SQUELETTIQUE ---
        diag_os_parts = ["L'analyse céphalométrique révèle"]

        # Situation_A no longer classifies via local ClinicalNorms constants
        # (CEPHALOMETRY-FINAL-NORMATIVE-MIGRATION-5) — only an authoritative service
        # classification may name a maxillary position (prognathique/rétrognathique)
        # or assert "bien positionnées"; none exists in the registry today, so the
        # raw value is stated without any normative claim.
        sit_a_label = _authoritative_label("Situation_A", sit_a_value, age, sex)
        if sit_a_label is not None:
            diag_os_parts.append(f"une Situation A classée {sit_a_label} ({sit_a_value} mm).")
        elif sit_a_value is not None:
            diag_os_parts.append(f"une Situation A = {sit_a_value} mm (référence normative non validée).")

        if tweed_value is not None and tweed_label == "Hyperdivergent":
            diag_os_parts.append(f"une typologie hyperdivergente (Tweed = {tweed_value}°), caractérisant une face longue avec un risque d'ouverture de l'occlusion.")
        elif tweed_value is not None and tweed_label == "Hypodivergent":
            diag_os_parts.append(f"une typologie hypodivergente (Tweed = {tweed_value}°), caractérisant une face courte avec un risque de surplomb.")
        elif tweed_value is not None and tweed_label == "Normodivergent":
            diag_os_parts.append(f"un équilibre normodivergent favorable (Tweed = {tweed_value}°).")
        elif tweed_value is not None:
            diag_os_parts.append(f"Tweed = {tweed_value}° (référence normative non validée).")
            
        diag_os = " ".join(diag_os_parts)
        
        # --- SYNTHESE DENTAIRE ---
        impa_data = dentaire.IMPA
        if_data = dentaire.I_Francfort
        surplomb_data = dentaire.Surplomb
        recouv_data = dentaire.Recouvrement
        
        impa_value = impa_data.valeur
        if_value = if_data.valeur
        # IMPA/I_Francfort no longer classify via the shared `.status` field
        # (same reasoning as Tweed above).
        impa_label = _authoritative_label("IMPA", impa_value, age, sex)
        if_label = _authoritative_label("I_Francfort", if_value, age, sex)

        diag_dent_parts = ["Au niveau dento-alvéolaire,"]

        if impa_value is not None and impa_label == "Proalveolie mandibulaire":
            diag_dent_parts.append(f"l'incisive inférieure est vestibuloversée (IMPA = {impa_value}°).")
        elif impa_value is not None and impa_label == "Retroalveolie mandibulaire":
            diag_dent_parts.append(f"l'incisive inférieure est linguoversée (IMPA = {impa_value}°).")
        elif impa_value is not None and impa_label == "Normoalveolie":
            diag_dent_parts.append(f"les incisives inférieures sont bien positionnées sur leur base (IMPA = {impa_value}°).")
        elif impa_value is not None:
            diag_dent_parts.append(f"IMPA = {impa_value}° (référence normative non validée).")

        if if_value is not None and if_label == "Proalveolie maxillaire":
            diag_dent_parts.append(f"On note également une proalvéolie maxillaire (I/F = {if_value}°).")
        elif if_value is not None and if_label == "Retroalveolie maxillaire":
            diag_dent_parts.append(f"On note également une rétroalvéolie maxillaire (I/F = {if_value}°).")

        # Note: the previous "Compensated" sentence (keyed off the shared
        # `.status` field's third state, driven by _evaluate_metric's own
        # comp_range logic) has no equivalent in the registry's IMPA
        # classification rule (a plain 2-threshold rule with no compensation
        # concept) — omitted rather than invented, per the established
        # "never invent semantics" precedent (CEPHALOMETRY-NORMATIVE-
        # BACKEND-WIRING-TWEED-IMPA-FRANCFORT-4C).

        # Surplomb/Recouvrement no longer classify via local raw>3 cutoffs
        # (CEPHALOMETRY-FINAL-NORMATIVE-MIGRATION-5) — only an authoritative service
        # classification may assert overjet/deep-bite; none exists today.
        surplomb_label = _authoritative_label("Surplomb", surplomb_data.valeur, age, sex)
        recouv_label = _authoritative_label("Recouvrement", recouv_data.valeur, age, sex)
        if surplomb_label is not None and surplomb_label not in ("Normal", "Normal ou diminue"):
            diag_dent_parts.append(f"Cliniquement, le surplomb est classé {surplomb_label} ({surplomb_data.valeur} mm).")
        if recouv_label is not None and recouv_label not in ("Normal ou diminue", "Normoclusie", "Normal"):
            diag_dent_parts.append(f"Le recouvrement est classé {recouv_label} ({recouv_data.valeur} mm).")

        diag_dent = " ".join(diag_dent_parts)
        
        # --- STRATEGIE ---
        strat_parts = []
        strat_parts.append("🎯 OBJECTIFS THÉRAPEUTIQUES :")
        if is_child:
            strat_parts.append("Patient en croissance : L'objectif prioritaire est la modification orthopédique.")
        else:
            strat_parts.append("Patient adulte : L'objectif est la compensation orthodontique ou la chirurgie.")
            
        if tweed_value is not None and tweed_label == "Hyperdivergent":
            strat_parts.append("- ⚠️ Contrôle vertical strict impératif (ancrage absolu, éviter les extractions maxillaires seules).")

        if impa_value is not None and impa_label == "Proalveolie mandibulaire" and not is_child:
            strat_parts.append("- Rétroclinaison incisive mandibulaire nécessaire pour l'esthétique du profil.")
            
        strat_parts.append("\n🛠 MOYENS PROPOSÉS :")
        if is_child:
            strat_parts.append("Appareillage fonctionnel interceptif, suivi d'un traitement multi-attaches post-éruptif.")
        else:
            strat_parts.append("Multi-attaches auto-ligaturants. Mini-vis d'ancrage recommandées.")
            
        return {
            "diagnostic_squelettique": diag_os,
            "analyse_dentaire": diag_dent,
            "strategie_therapeutique": "\n".join(strat_parts),
            "is_fallback": False # GhostBrain NLG est la source officielle
        }

ai_advisor = AIAdvisor()
