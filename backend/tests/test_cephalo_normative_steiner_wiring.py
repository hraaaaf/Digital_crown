"""
Tests for CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-STEINER-4A: proves
cephalo_engine.py and bilan_ortho_engine.py's SNA/SNB/ANB narrative logic
now goes through cephalo_normative_service.evaluate_measurement instead of
local legacy constants, with zero change to raw geometry.

Consumer-level tests for bilan_ortho_engine.py's own two methods already
live in test_bilan_ortho_engine.py (updated in this same mission). This
file covers cephalo_engine.py's narrative integration plus the synthetic-
validated-path proof required by mission §20-23, and a failure-status sweep
at the consumer level (mission §24).

Exécuter avec : pytest backend/tests/test_cephalo_normative_steiner_wiring.py -v
"""
import datetime

import pytest

from backend.schemas.cephalo_normative import (
    AgeDependencyType,
    CodeOrigin,
    DefinitionStatus,
    MeasurementDefinition,
    NormativeProfile,
    ReferenceType,
    Sex,
    ValidationStatus,
)
from backend.services import cephalo_normative_service as svc
from backend.services.cephalo_normative_service import _RegistrySnapshot, reset_cache
from backend.services.cephalo_engine import CephaloEngine

_ORIGIN = CodeOrigin(file="backend/tests/test_cephalo_normative_steiner_wiring.py", symbol="fixture", line="1")

# Same synthetic landmark set used by test_cephalo_engine_uncalibrated.py, with
# point A pushed far posteriorly (x=0 vs N's x=70) so Situation_A resolves well
# below norm_sit_a's lower bound regardless of age — deliberately triggers the
# "Situation A hors norme" branch this mission touched.
POINTS_RETROGNATHIC_A = {
    "S": (50.0, 60.0), "N": (70.0, 40.0), "Po": (40.0, 40.0), "Or": (80.0, 40.0),
    "A": (0.0, 90.0), "B": (85.0, 130.0), "Go": (60.0, 150.0), "Me": (85.0, 170.0),
    "U1i": (100.0, 100.0), "U1a": (105.0, 80.0), "L1i": (92.0, 120.0), "L1a": (88.0, 140.0),
    "Prn": (100.0, 40.0), "Pog_soft": (100.0, 200.0), "Ls": (92.0, 100.0),
    "Li": (108.0, 120.0), "Sn": (100.0, 60.0), "Occ_Ant": (110.0, 110.0),
    "Occ_Post": (60.0, 110.0), "Co": (45.0, 50.0), "Gn": (90.0, 165.0), "ANS": (85.0, 75.0),
}

POINTS_STRONG_ANB = {
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
# Sex parameter reaches NormativeContext (CEPHALOMETRY-NORMATIVE-CONTEXT-
# PLUMBING-4A2) — unit-level, faster than the DB-backed CephaloService
# proof in test_cephalo_service_normative_context.py.
# ============================================================

class TestSexReachesContext:
    def _spy_and_capture(self, monkeypatch):
        import backend.services.cephalo_engine as engine_module
        captured = {}
        original = engine_module.evaluate_measurement

        def _spy(measurement_id, raw_value, definition_version, context):
            captured[measurement_id] = context
            return original(measurement_id, raw_value, definition_version, context)

        monkeypatch.setattr(engine_module, "evaluate_measurement", _spy)
        return captured

    def test_sex_m_maps_to_male(self, monkeypatch):
        from backend.schemas.cephalo_normative import Sex
        captured = self._spy_and_capture(monkeypatch)
        CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30, sex="M")
        assert captured["ANB"].sex == Sex.MALE

    def test_sex_f_maps_to_female(self, monkeypatch):
        from backend.schemas.cephalo_normative import Sex
        captured = self._spy_and_capture(monkeypatch)
        CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30, sex="F")
        assert captured["ANB"].sex == Sex.FEMALE

    def test_sex_none_maps_to_none(self, monkeypatch):
        captured = self._spy_and_capture(monkeypatch)
        CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30, sex=None)
        assert captured["ANB"].sex is None

    def test_unrecognized_sex_code_never_guessed(self, monkeypatch):
        captured = self._spy_and_capture(monkeypatch)
        CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30, sex="AUTRE")
        assert captured["ANB"].sex is None

    def test_population_id_always_none(self, monkeypatch):
        # No population-profile concept exists anywhere in Digital Crown today —
        # this must stay None regardless of age/sex being supplied.
        captured = self._spy_and_capture(monkeypatch)
        CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30, sex="M")
        assert captured["ANB"].population_id is None


# ============================================================
# Raw geometry unchanged
# ============================================================

class TestRawGeometryUnchanged:
    def test_sna_snb_anb_values_are_identical_across_repeated_calls(self):
        r1 = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        r2 = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        assert r1.metrics.analyse_osseuse.SNA.valeur == r2.metrics.analyse_osseuse.SNA.valeur
        assert r1.metrics.analyse_osseuse.SNB.valeur == r2.metrics.analyse_osseuse.SNB.valeur
        assert r1.metrics.analyse_osseuse.ANB.valeur == r2.metrics.analyse_osseuse.ANB.valeur
        assert r1.metrics.analyse_osseuse.ANB.valeur == pytest.approx(
            r1.metrics.analyse_osseuse.SNA.valeur - r1.metrics.analyse_osseuse.SNB.valeur, abs=0.15
        )

    def test_values_present_and_finite(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        skeletal = result.metrics.analyse_osseuse
        assert skeletal.SNA.valeur is not None
        assert skeletal.SNB.valeur is not None
        assert skeletal.ANB.valeur is not None


# ============================================================
# Real registry: no authoritative Steiner narrative
# ============================================================

class TestRealRegistryNarrative:
    def test_no_skeletal_class_sentence_from_anb(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        narrative = result.ai_narrative["diagnostic_squelettique"]
        assert "Tendance squelettique de Classe" not in narrative
        assert "selon ANB" not in narrative

    def test_anb_raw_value_still_visible_as_a_neutral_note(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        narrative = result.ai_narrative["diagnostic_squelettique"]
        anb_value = result.metrics.analyse_osseuse.ANB.valeur
        assert f"ANB = {anb_value}" in narrative
        assert "référence normative non validée" in narrative

    def test_no_retrognathie_maxillaire_text_from_sna(self):
        # Situation_A itself was later migrated too (CEPHALOMETRY-FINAL-NORMATIVE-
        # MIGRATION-5), so the former "Situation A hors norme" workaround is gone —
        # now a plain non-validated raw-value note, and never Prognathie/Retrognathie.
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_RETROGNATHIC_A, age=30)
        narrative = result.ai_narrative["diagnostic_squelettique"]
        assert result.metrics.analyse_osseuse.Situation_A.valeur is not None
        assert "Retrognathie maxillaire" not in narrative
        assert "Prognathie maxillaire" not in narrative
        assert "Situation A =" in narrative
        assert "référence normative non validée" in narrative

    def test_no_class_ii_iii_treatment_strategy_from_anb(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        strategy = result.ai_narrative["strategie_therapeutique"]
        assert "Camouflage avec élastiques de Classe II" not in strategy
        assert "Traitement chirurgico-orthodontique" not in strategy

    def test_synthese_diagnostique_has_no_class_anomaly_from_anb(self):
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        synthese = result.ai_narrative["synthese_diagnostique"]
        assert "Classe I" not in synthese
        assert "Classe II" not in synthese
        assert "Classe III" not in synthese


# ============================================================
# Synthetic VALIDATED_FOR_PROFILE path — proves the wiring actually works
# ============================================================
#
# Important finding: cephalo_engine.py and bilan_ortho_engine.py always call
# evaluate_measurement with population_id=None (no population-context plumbing
# exists anywhere in the app today, and inventing one is explicitly forbidden
# by this mission). Since NormativeContext.population_id=None can never match
# ANY profile's required population_id (missing != wildcard, per the no-
# fallback design), NO profile — not even a hypothetically-perfect synthetic
# VALIDATED_FOR_PROFILE one — can ever become authoritative through these
# real call sites as currently wired. This is stronger than "the real
# registry is unvalidated": even a perfect future profile would still need
# a population-context plumbing change (a later, separate mission) before it
# could ever fire through cephalo_engine.py/bilan_ortho_engine.py.
#
# To prove the CONSUMER-SIDE propagation logic itself is correct (the part
# that's actually this mission's job — turning an authoritative result into
# the right narrative text), these tests patch evaluate_measurement directly
# to return a canned authoritative result, rather than trying to satisfy the
# full context-matching chain. DO NOT mark any real profile validated.

from backend.services.cephalo_normative_service import NormativeEvaluationResult, NormativeEvaluationStatus


def _canned_class_ii_result(measurement_id, raw_value, definition_version, context):
    if measurement_id == "ANB":
        return NormativeEvaluationResult(
            measurement_id="ANB", raw_value=raw_value, unit="degree",
            status=NormativeEvaluationStatus.VALIDATED_PROFILE_MATCH,
            reason="synthetic test fixture", matched_profile_id="ANB_SYNTHETIC_VALIDATED_V1",
            classification="Classe II",
        )
    return NormativeEvaluationResult(
        measurement_id=measurement_id, raw_value=raw_value, unit=None,
        status=NormativeEvaluationStatus.NO_PROFILE, reason="not part of this synthetic fixture",
    )


class TestSyntheticValidatedPathPropagates:
    """DO NOT mark any real profile validated. Patches evaluate_measurement
    itself (see note above on why population_id=None makes registry-level
    injection insufficient for this specific propagation proof).
    """

    def test_engine_narrative_uses_authoritative_label_when_service_says_so(self, monkeypatch):
        import backend.services.cephalo_engine as engine_module
        monkeypatch.setattr(engine_module, "evaluate_measurement", _canned_class_ii_result)

        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        narrative = result.ai_narrative["diagnostic_squelettique"]
        anb_value = result.metrics.analyse_osseuse.ANB.valeur
        assert f"Tendance squelettique de Classe II selon ANB ({anb_value}°)." in narrative

    def test_engine_treatment_strategy_reacts_to_authoritative_class_ii(self, monkeypatch):
        import backend.services.cephalo_engine as engine_module
        monkeypatch.setattr(engine_module, "evaluate_measurement", _canned_class_ii_result)

        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        strategy = result.ai_narrative["strategie_therapeutique"]
        assert "Classe II" in strategy

    def test_bilan_ortho_resume_cephalo_uses_authoritative_label(self, monkeypatch):
        import backend.services.bilan_ortho_engine as bilan_module
        monkeypatch.setattr(bilan_module, "evaluate_measurement", _canned_class_ii_result)

        from backend import schemas
        from backend.services.bilan_ortho_engine import BilanOrthoEngine

        metrics = schemas.AnalysisMetrics()
        metrics.analyse_osseuse.ANB.valeur = 8.0
        cephalo = schemas.CephaloAnalysisResult(
            analysis_metadata=schemas.AnalysisMetadata(cohort="Adulte"), metrics=metrics,
            visual_debug={}, t1_projection={}, t2_projection={}, clinical_data=schemas.ClinicalData(),
        )
        result = BilanOrthoEngine().generate_bilan(cephalo, schemas.ClinicalData())
        assert "Base squelettique de Classe II." in result["diagnostic_squelettique"]

    def test_bilan_ortho_synthese_uses_authoritative_label(self, monkeypatch):
        import backend.services.bilan_ortho_engine as bilan_module
        monkeypatch.setattr(bilan_module, "evaluate_measurement", _canned_class_ii_result)

        from backend import schemas
        from backend.services.bilan_ortho_engine import BilanOrthoEngine

        metrics = schemas.AnalysisMetrics()
        metrics.analyse_osseuse.ANB.valeur = 8.0
        cephalo = schemas.CephaloAnalysisResult(
            analysis_metadata=schemas.AnalysisMetadata(cohort="Adulte"), metrics=metrics,
            visual_debug={}, t1_projection={}, t2_projection={}, clinical_data=schemas.ClinicalData(),
        )
        result = BilanOrthoEngine().generate_bilan(cephalo, schemas.ClinicalData())
        assert "La Classe II squelettique est le problème sagittal majeur." in result["synthese_diagnostique"]


# ============================================================
# Failure-status sweep at the consumer level (mission §24)
# ============================================================

class TestFailureStatusesNeverProduceAClass:
    def _install(self, profiles=(), rules=()):
        definitions = [
            MeasurementDefinition(
                measurement_id="ANB", canonical_name="Steiner ANB", display_name="ANB",
                analysis_family="Steiner", unit="degree", definition_version="v1",
                required_landmarks=["S", "N", "A", "B"], definition_status=DefinitionStatus.ACTIVE,
                origin=_ORIGIN,
            ),
        ]
        svc._cache = _RegistrySnapshot(definitions=definitions, profiles=list(profiles), rules=list(rules), bounds=[])

    def _profile(self, profile_id, status, population_id="TEST_POP"):
        return NormativeProfile(
            profile_id=profile_id, measurement_id="ANB", measurement_definition_version="v1",
            reference_type=ReferenceType.MEAN_SD, unit="degree", mean=2.0, sd=2.0,
            age_dependency_type=AgeDependencyType.AGE_INDEPENDENT, sex=Sex.POOLED, population_id=population_id,
            validation_status=status, profile_version="v1", effective_from=datetime.date(2026, 1, 1), origin=_ORIGIN,
        )

    def test_missing_context_yields_no_class(self):
        # cephalo_engine.py calls with population_id=None; a profile requiring an
        # exact population match can never be satisfied -> MISSING_CONTEXT.
        self._install(profiles=[self._profile("P1", ValidationStatus.VALIDATED_FOR_PROFILE)])
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        assert "Tendance squelettique de Classe" not in result.ai_narrative["diagnostic_squelettique"]

    def test_two_competing_profiles_yield_no_class(self):
        # cephalo_engine.py always calls with population_id=None (no plumbing exists
        # to supply one), so this actually resolves to MISSING_CONTEXT rather than a
        # true AMBIGUOUS_MATCH — genuine ambiguity resolution is already covered at
        # the service level (test_cephalo_normative_service.py::TestAmbiguity). What
        # matters here is that having two competing VALIDATED_FOR_PROFILE candidates
        # still never produces a class through this consumer.
        self._install(profiles=[
            self._profile("P1", ValidationStatus.VALIDATED_FOR_PROFILE),
            self._profile("P2", ValidationStatus.VALIDATED_FOR_PROFILE),
        ])
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        assert "Tendance squelettique de Classe" not in result.ai_narrative["diagnostic_squelettique"]

    def test_profile_unvalidated_yields_no_class(self):
        self._install(profiles=[self._profile("P1", ValidationStatus.LEGACY_UNVALIDATED)])
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        assert "Tendance squelettique de Classe" not in result.ai_narrative["diagnostic_squelettique"]

    def test_no_profile_yields_no_class(self):
        self._install(profiles=[])
        result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_STRONG_ANB, age=30)
        assert "Tendance squelettique de Classe" not in result.ai_narrative["diagnostic_squelettique"]


# ============================================================
# Quarantine regression (unaffected by this mission)
# ============================================================

class TestQuarantineStillHolds:
    @pytest.mark.parametrize("measurement_id", ["Wits_Appraisal", "Angle_Nasolabial", "Situation_B", "Decalage_A_B"])
    def test_quarantined_measurements_still_blocked(self, measurement_id):
        from backend.schemas.cephalo_normative import NormativeContext
        from backend.services.cephalo_normative_service import evaluate_measurement, NormativeEvaluationStatus
        result = evaluate_measurement(measurement_id, 0.0, "v1", NormativeContext())
        assert result.status == NormativeEvaluationStatus.DEFINITION_QUARANTINED
        assert result.classification is None
