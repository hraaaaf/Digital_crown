"""
Tests for CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-TWEED-IMPA-FRANCFORT-4C:
proves cephalo_engine.py and bilan_ortho_engine.py's Angle_de_Tweed/IMPA/
I_Francfort narrative logic goes through cephalo_normative_service.
evaluate_measurement instead of local legacy constants, with zero change to
raw geometry — mirrors test_cephalo_normative_steiner_wiring.py's structure
for the ANB/SNA mission (4A).

Exécuter avec : pytest backend/tests/test_cephalo_normative_tweed_impa_francfort_wiring.py -v
"""
import pytest

from backend.services.cephalo_normative_service import (
    NormativeEvaluationResult,
    NormativeEvaluationStatus,
    reset_cache,
)
from backend.services.cephalo_engine import CephaloEngine

# Same synthetic landmark set as test_cephalo_normative_steiner_wiring.py's
# POINTS_STRONG_ANB — already includes Po/Or/Go/Me (Tweed), L1a/L1i/Go/Me
# (IMPA), and U1a/U1i/Po/Or (I_Francfort).
POINTS_ALL_MEASURES = {
    "S": (50.0, 60.0), "N": (70.0, 40.0), "Po": (40.0, 40.0), "Or": (80.0, 40.0),
    "A": (95.0, 90.0), "B": (60.0, 130.0), "Go": (60.0, 150.0), "Me": (85.0, 170.0),
    "U1i": (100.0, 100.0), "U1a": (105.0, 80.0), "L1i": (92.0, 120.0), "L1a": (88.0, 140.0),
    "Prn": (100.0, 40.0), "Pog_soft": (100.0, 200.0), "Ls": (92.0, 100.0),
    "Li": (108.0, 120.0), "Sn": (100.0, 60.0), "Occ_Ant": (110.0, 110.0),
    "Occ_Post": (60.0, 110.0), "Co": (45.0, 50.0), "Gn": (90.0, 165.0), "ANS": (85.0, 75.0),
}


@pytest.fixture(autouse=True)
def _clean_cache():
    reset_cache()
    yield
    reset_cache()


# ============================================================
# Real registry: no authoritative Tweed/IMPA/I_Francfort narrative
# ============================================================

class TestRealRegistryNarrative:
    def test_no_divergence_sentence_from_tweed(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_ALL_MEASURES, age=30)
        narrative = result.ai_narrative["diagnostic_squelettique"]
        assert "Hyperdivergent" not in narrative
        assert "Hypodivergent" not in narrative
        tweed_value = result.metrics.analyse_osseuse.Angle_de_Tweed.valeur
        assert tweed_value is not None
        assert f"Angle de Tweed = {tweed_value}° (référence normative non validée)." in narrative

    def test_no_alveolar_diag_from_impa_or_francfort(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_ALL_MEASURES, age=30)
        synthese = result.ai_narrative["synthese_diagnostique"]
        assert "proalveolie" not in synthese
        assert "retroalveolie" not in synthese
        assert "normoalveolie" not in synthese

    def test_impa_and_francfort_raw_values_present(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_ALL_MEASURES, age=30)
        assert result.metrics.analyse_dentaire.IMPA.valeur is not None
        assert result.metrics.analyse_dentaire.I_Francfort.valeur is not None

    def test_no_class_anomaly_words_from_tweed_impa_francfort_in_synthese(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_ALL_MEASURES, age=30)
        synthese = result.ai_narrative["synthese_diagnostique"]
        assert "hyperdivergent" not in synthese
        assert "hypodivergent" not in synthese


# ============================================================
# Synthetic VALIDATED_FOR_PROFILE path — proves the wiring actually works.
# Same population_id=None caveat as the Steiner wiring tests: these patch
# evaluate_measurement directly. DO NOT mark any real profile validated.
# ============================================================

def _canned_result(measurement_id, raw_value, definition_version, context):
    canned = {
        "Angle_de_Tweed": "Hyperdivergent",
        "IMPA": "Proalveolie mandibulaire",
        "I_Francfort": "Proalveolie maxillaire",
    }
    if measurement_id in canned:
        return NormativeEvaluationResult(
            measurement_id=measurement_id, raw_value=raw_value, unit="degree",
            status=NormativeEvaluationStatus.VALIDATED_PROFILE_MATCH,
            reason="synthetic test fixture", matched_profile_id=f"{measurement_id}_SYNTHETIC_VALIDATED_V1",
            classification=canned[measurement_id],
        )
    return NormativeEvaluationResult(
        measurement_id=measurement_id, raw_value=raw_value, unit=None,
        status=NormativeEvaluationStatus.NO_PROFILE, reason="not part of this synthetic fixture",
    )


class TestSyntheticValidatedPathPropagates:
    def test_engine_narrative_uses_authoritative_tweed_label(self, monkeypatch):
        import backend.services.cephalo_engine as engine_module
        monkeypatch.setattr(engine_module, "evaluate_measurement", _canned_result)

        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_ALL_MEASURES, age=30)
        narrative = result.ai_narrative["diagnostic_squelettique"]
        assert "Hyperdivergent" in narrative

    def test_engine_synthese_flags_impa_and_francfort_anomalies(self, monkeypatch):
        import backend.services.cephalo_engine as engine_module
        monkeypatch.setattr(engine_module, "evaluate_measurement", _canned_result)

        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_ALL_MEASURES, age=30)
        synthese = result.ai_narrative["synthese_diagnostique"]
        assert "proalveolie mandibulaire" in synthese
        assert "proalveolie maxillaire" in synthese

    def test_bilan_ortho_resume_cephalo_uses_authoritative_tweed_label(self, monkeypatch):
        import backend.services.bilan_ortho_engine as bilan_module
        monkeypatch.setattr(bilan_module, "evaluate_measurement", _canned_result)

        from backend import schemas
        from backend.services.bilan_ortho_engine import BilanOrthoEngine

        metrics = schemas.AnalysisMetrics()
        metrics.analyse_osseuse.Angle_de_Tweed.valeur = 35.0
        cephalo = schemas.CephaloAnalysisResult(
            analysis_metadata=schemas.AnalysisMetadata(cohort="Adulte"), metrics=metrics,
            visual_debug={}, t1_projection={}, t2_projection={}, clinical_data=schemas.ClinicalData(),
        )
        result = BilanOrthoEngine().generate_bilan(cephalo, schemas.ClinicalData())
        assert "Typologie faciale hyperdivergente (Tweed = 35.0°)." in result["diagnostic_squelettique"]

    def test_bilan_ortho_synthese_uses_authoritative_impa_label(self, monkeypatch):
        import backend.services.bilan_ortho_engine as bilan_module
        monkeypatch.setattr(bilan_module, "evaluate_measurement", _canned_result)

        from backend import schemas
        from backend.services.bilan_ortho_engine import BilanOrthoEngine

        metrics = schemas.AnalysisMetrics()
        metrics.analyse_osseuse.ANB.valeur = 8.0  # drives skeletal_class == "II" (still non-authoritative, so N/A here)
        metrics.analyse_dentaire.IMPA.valeur = 98.0
        cephalo = schemas.CephaloAnalysisResult(
            analysis_metadata=schemas.AnalysisMetadata(cohort="Adulte"), metrics=metrics,
            visual_debug={}, t1_projection={}, t2_projection={}, clinical_data=schemas.ClinicalData(),
        )
        # ANB itself is never canned here (only Tweed/IMPA/I_Francfort are), so
        # skeletal_class stays None and the IMPA-specific sentence (gated on
        # skeletal_class == "II"/"III") cannot fire — confirms IMPA's
        # classification alone never substitutes for the ANB gate.
        result = BilanOrthoEngine().generate_bilan(cephalo, schemas.ClinicalData())
        assert "proalvéolie mandibulaire" not in result["synthese_diagnostique"]


# ============================================================
# Failure-status sweep at the consumer level
# ============================================================

class TestFailureStatusesNeverProduceAClass:
    def test_no_profile_yields_no_tweed_class(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_ALL_MEASURES, age=30)
        assert "Hyperdivergent" not in result.ai_narrative["diagnostic_squelettique"]
        assert "Hypodivergent" not in result.ai_narrative["diagnostic_squelettique"]
